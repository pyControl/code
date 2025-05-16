import pyb
import math
from machine import Signal, Pin
from pyControl.hardware import interrupt_queue, assign_ID, IO_object, Port, Digital_input
import pyControl.framework as fw
import pyControl.state_machine as sm
import pyControl.hardware as hw
from pyControl.audio import Audio_output
from pyControl.framework import pyControlError
from pyControl.utility import warning


class Grid_maze(IO_object):
    def __init__(self, n_exp):
        self.imap = {v: k for k, v in self.map.items()}  # Inverse mapping from expander and port to location.
        self.timestamp = 0
        self.n_exp = n_exp
        self.events = [loc + "_in" for loc in self.map.keys()] + [loc + "_out" for loc in self.map.keys()]
        self.addr = [0x20 + i for i in range(n_exp)]  # Addresses of MCP chips for each expander.
        self.reg_addr = {  # MCP Register memory addresses.
            "IODIR": 0x00,  # Input / output direction.
            "GPIO": 0x12,  # Pin state.
            "GPINTEN": 0x04,  # Interrupt on change enable.
            "INTF": 0x0E,  # Interrupt flag.
            "INTCON": 0x08,  # Interupt compare mode.
            "DEFVAL": 0x06,  # Interupt compare default.
            "IOCON": 0x0A,  # Configuration
            "GPPU": 0x06,  # GPIO pull up resistor enable.
        }  # Configuration.

        self.I2C = [pyb.I2C(1, mode=pyb.I2C.MASTER, baudrate=40000), pyb.I2C(2, mode=pyb.I2C.MASTER, baudrate=40000)]

        self.BNC_1 = "X12"
        self.BNC_2 = "X11"

        self.port_1 = Port(DIO_A="X1", DIO_B="X2", POW_A="Y1", POW_B="Y2", DIO_C=self.BNC_1, UART=4)
        self.port_2 = Port(DIO_A="X3", DIO_B="X4", POW_A="Y3", POW_B="Y4", DIO_C=self.BNC_2)
        self.port_3 = Port(DIO_A="X7", DIO_B="X8", POW_A="Y5", POW_B="Y6")
        self.port_4 = Port(DIO_A="Y11", DIO_B="X6", POW_A="Y7", POW_B="Y8")

        self.extint = pyb.ExtInt("Y12", pyb.ExtInt.IRQ_FALLING, pyb.Pin.PULL_NONE, self.ISR)
        self.audio = Audio_output(1)
        self.audio.set_volume = self._set_volume
        self.timer = pyb.Timer(hw.available_timers.pop())
        self.pulse_timer = None  # only ask for a timer if we're going to need one
        self.stop_pulse = False

        # Initialise pins used for pokes that are directly connected to mazehub.

        self.hub_pokes = {}
        for loc, (ex, port) in self.map.items():
            if ex == -1:  # Poke is directly connected to hub.
                port_obj = getattr(self, "port_{}".format(port))
                self.hub_pokes[port] = {
                    "IR": Digital_input(port_obj.DIO_A, rising_event=loc + "_in", falling_event=loc + "_out"),
                    "LED": Signal(port_obj.POW_A, mode=Pin.OUT),
                    "SOL": Signal(port_obj.POW_B, mode=Pin.OUT),
                    "speaker": Signal(port_obj.DIO_B, mode=Pin.OUT, invert=True),
                }

        assign_ID(self)

        for exp_n in range(n_exp):
            # Configure MCP23017s used for IR beam and speaker enable lines.
            # IR beams are pins 0,2,...,14. Speaker enable are pins 1,3,...,15
            self.write_register(exp_n, 0, "IODIR", int("01" * 8, 2))  # Set IR pins as inputs, speaker enable as outputs
            self.write_register(exp_n, 0, "GPPU", int("10" * 8, 2))  # Enable pullups on IR pins.
            self.write_register(exp_n, 0, "GPIO", int("10" * 8, 2))  # Set speaker enable pins high (disable speakers).
            self.write_register(exp_n, 0, "INTCON", 0)  # Set all interupts to IRQ_RISING_FALLING mode.
            self.write_register(exp_n, 0, "DEFVAL", 0)  # Set default compare value to low.
            self.write_register(exp_n, 0, "IOCON", 0)
            self.write_bit(exp_n, 0, "IOCON", 2, True, n_bytes=1)  # Set interrupt output to open drain.
            self.write_bit(exp_n, 0, "IOCON", 6, True, n_bytes=1)  # Set port A, B interrupt pins to mirror.
            # self.write_register(exp_n, 0, 'IOCON'  , int('01000100',2)) # Set interupt pins to mirror and open drain.
            self.write_register(exp_n, 0, "GPINTEN", int("01" * 8, 2))  # Enable interrupts on IR pins.
            # Configure MCP23017s used for LED and SOL lines.
            # LEDs are pins 0,2,...,14. SOLs are pins 1,3,...,15
            self.write_register(exp_n, 1, "IODIR", 0)  # Set pins as ouptuts.
            self.write_register(exp_n, 1, "GPIO", 0)  # Set LED and SOL pins low.
            self.write_register(exp_n, 1, "GPINTEN", 0)  # Disable interrupts on all pins.
            self.write_register(exp_n, 1, "IOCON", 0)  # Set configuration to default.

    def _initialise(self):
        # Set event codes for events used in task.
        self.event_IDs = {k: sm.events[k] for k in self.events if k in sm.events.keys()}

    def LED_on(self, loc):
        exp_n, port = self.map[loc]
        if exp_n == -1:
            self.hub_pokes[port]["LED"].on()
        else:
            self.write_bit(exp_n, 1, "GPIO", 2 * (port - 1), True)

    def LED_off(self, loc):
        if self.pulse_timer is not None: # If there's a timer delegate led off
            self.stop_pulse = True
            return None
        exp_n, port = self.map[loc]
        if exp_n == -1:
            self.hub_pokes[port]["LED"].off()
        else:
            self.write_bit(exp_n, 1, "GPIO", 2 * (port - 1), False)

    def LED_pulse(self, loc, freq, duty_cycle=50, n_pulses=False):
        # NOTE: (1) pulsing an LED takes a lot of CPU, and (ii) in this version
        # of the code, when a LED is pusling, you CANNOT use other LEDs or
        # solenoids - though in principle the code can be updated for that.
        # Mouse critical flicker fusion frequency is estimated to be 14Hz; see
        # https://www.sciencedirect.com/science/article/pii/S0168010218303882

        # Turn on pulsed output with specified frequency and duty cycle.
        if self.pulse_timer is None:
            self.pulse_timer = pyb.Timer(hw.available_timers.pop())
        self.fm = int(100 / next(x for x in (50, 25, 20, 10, 5, 1) if duty_cycle % x == 0))
        self.off_ind = int(duty_cycle / 100 * self.fm)
        self.i = 0
        self.pulse_timer.init(freq=freq*self.fm)
        exp_n, port = self.map[loc]
        reg_value = self.read_register(exp_n, 1, "GPIO", 2)

        # In ISR we cannot allocate memory, and we need to be fast to prevent
        # problems, see:
        # https://docs.micropython.org/en/latest/reference/isr_rules.html
        # Therefore we pre-allocate a buffer for led on and off, and just write
        # this in the callback, which is fast, doesn't allocate memory, etc.
        # However, this means that other code that touches the reg_values will
        # be overwritten by this tight loop, unless they update the LED_buf
        # variuables themselves.
        if exp_n == 0:
            self.LED_buf_off = reg_value.to_bytes(2, "little")
            self.LED_buf_on = (reg_value | 1 << (2 * (port - 1))).to_bytes(2, "little")
        self.pulse_timer.callback(lambda _: self._LED_pulse_callback(exp_n, port))

    @micropython.native
    def _LED_pulse_callback(self, exp_n, port):
        self.i += 1
        if self.i == self.off_ind or self.stop_pulse:
            # LED_off but use the buffer to avoid memory allocation in tight loop
            if exp_n == -1:
                 self.hub_pokes[port]["LED"].off()
            else:
                self.I2C[1].mem_write(self.LED_buf_off, self.addr[exp_n], self.reg_addr["GPIO"], timeout=15)
            # Stop from the callback (plus run rest of it) to avoid race conditions.
            if self.stop_pulse:
                self.pulse_timer.deinit()
                self.stop_pulse = False
        elif self.i == self.fm:
            # LED_on but use the buffer to avoid memory allocation in tight loop
            self.i = 0
            if exp_n == -1:
                self.hub_pokes[port]["LED"].on()
            else:
                self.I2C[1].mem_write(self.LED_buf_on, self.addr[exp_n], self.reg_addr["GPIO"], timeout=15)

    def SOL_on(self, loc):
        # This error should never be raised BUT there's a possibility of a race
        # condition. I have never seen it given how the rest of the code is
        # structured. This _can_ be fixed but I'm delaying fixing this to this
        # being an actual problem.
        if self.stop_pulse:
            pyControlError("race condition: fix LED_off happening after SOL_off.")
        exp_n, port = self.map[loc]
        if exp_n == -1:
            self.hub_pokes[port]["SOL"].on()
        else:
            self.write_bit(exp_n, 1, "GPIO", 1 + 2 * (port - 1), True)

    def SOL_off(self, loc):
        exp_n, port = self.map[loc]
        if exp_n == -1:
            self.hub_pokes[port]["SOL"].off()
        else:
            self.write_bit(exp_n, 1, "GPIO", 1 + 2 * (port - 1), False)

    def speaker_on(self, loc):
        exp_n, port = self.map[loc]
        if exp_n == -1:
            self.hub_pokes[port]["speaker"].on()
        else:
            self.write_bit(exp_n, 0, "GPIO", 1 + 2 * (port - 1), False)

    def speaker_off(self, loc):
        exp_n, port = self.map[loc]
        if exp_n == -1:
            self.hub_pokes[port]["speaker"].off()
        else:
            self.write_bit(exp_n, 0, "GPIO", 1 + 2 * (port - 1), True)

    def _run_start(self):
        # Read the GPIO registers to clear interrupts.
        for exp_n in range(self.n_exp):
            self.read_register(exp_n, 0, "GPIO")
        # Set timer to call ISR every second to avoid lockup if an interrupt is missed.
        self.timer.init(freq=1)
        self.timer.callback(self.ISR)

    def _run_stop(self):
        # Turn off outputs
        self.timer.deinit()
        if self.pulse_timer is not None:
            self.pulse_timer.deinit()
        for exp_n in range(self.n_exp):  # Turn off outputs on expanders.
            self.write_register(exp_n, 0, "GPIO", int("01" * 8, 2))  # Set speaker enable pins high (disable speakers).
            self.write_register(exp_n, 1, "GPIO", 0)  # Set LED and SOL pins low.
        for hub_poke in self.hub_pokes.values():  # Turn off outputs on hub.
            hub_poke["LED"].off()
            hub_poke["SOL"].off()
            hub_poke["speaker"].off()

    def read_register(self, exp_n, i2c, register, n_bytes=2):
        # Read specified register, convert to int, store in reg_values, return value.
        for attempt in range(5):
            try:
                v = int.from_bytes(self.I2C[i2c].mem_read(n_bytes, self.addr[exp_n], self.reg_addr[register], timeout=5), "little")
                if attempt > 0:
                    warning("Intermittant serial communication with maze_expander board.")
                return v
            except:
                pass
        raise pyControlError("Unable to communicate with maze_expander board.")

    def write_register(self, exp_n, i2c, register, values, n_bytes=2):
        # Write values to specified register, values must be int which is converted to n_bytes bytes.
        for attempt in range(5):
            try:
                self.I2C[i2c].mem_write(values.to_bytes(n_bytes, "little"), self.addr[exp_n], self.reg_addr[register], timeout=5)
                if attempt > 0:
                    warning("Intermittant serial communication with maze_expander board.")
                return
            except:
                pass
        raise pyControlError("Unable to communicate with maze_expander board.")

    def write_bit(self, exp_n, i2c, register, bit, value, n_bytes=2):
        # Write the value of specified bit to specified register.
        reg_values = self.read_register(exp_n, i2c, register, n_bytes)
        if value:
            reg_values |= 1 << bit  # Set bit
        else:
            reg_values &= ~(1 << bit)  # Clear bit
        self.write_register(exp_n, i2c, register, reg_values, n_bytes)
        
    def ISR(self, i):
        self.timestamp = fw.current_time
        interrupt_queue.put(self.ID)

    def _process_interrupt(self):
        for exp_n in range(self.n_exp):
            INTF = self.read_register(exp_n, 0, "INTF")
            if INTF > 0:
                GPIO = self.read_register(exp_n, 0, "GPIO")
                pin = int(math.log2(INTF) + 0.1)
                pinstate = bool(GPIO & INTF)
                event_name = self.imap[(exp_n, 1 + pin / 2)] + ("_in" if pinstate else "_out")
                if event_name in self.event_IDs.keys():
                    fw.event_queue.put(fw.Datatuple(self.timestamp, fw.EVENT_TYP, "i", self.event_IDs[event_name]))

    def _set_volume(self, V):  # Set volume of audio output, range 0 - 127
        self.I2C[0].mem_write(int(V), 46, 0)


class Grid_maze_3x3(Grid_maze):
    def __init__(self):
        self.map = {
            "A1": (-1, 4),  # Dict mapping grid locations to expander and port.
            "A2": (0, 1),
            "A3": (0, 2),
            "B1": (0, 3),
            "B2": (0, 4),
            "B3": (0, 5),
            "C1": (0, 6),
            "C2": (0, 7),
            "C3": (0, 8),
        }

        super().__init__(n_exp=1)


class Grid_maze_7x7(Grid_maze):
    def __init__(self):
        self.map = {"A1": (-1, 4)}  # Dict mapping grid locations to expander and port.
        x = 1
        y = 0
        for e in range(6):  # expander n
            for p in range(8):  # port n
                self.map["ABCDEFG"[y] + str(x + 1)] = (e, p + 1)
                x = (x + 1) % 7
                if x == 0:
                    y += 1

        super().__init__(n_exp=6)
