import pyb
import pyControl.hardware as hw
from pyControl.framework import pyControlError
from pyControl.utility import warning


class _MCP(hw.IO_object):
    # Parent class for MCP23017 and MCP23008 port expanders.

    def __init__(self, I2C_bus, interrupt_pin, addr, name, baudrate=400000):
        self.i2c = pyb.I2C(I2C_bus, mode=pyb.I2C.MASTER, baudrate=baudrate)
        self.timer = pyb.Timer(hw.available_timers.pop())
        self.addr = addr  # Device I2C address
        self.name = name
        self.interrupts_enabled = False
        self.interrupt_pin = interrupt_pin
        self.reg_values = {}  # Register values set by user.
        hw.assign_ID(self)

    def reset(self):
        self.write_register("IODIR", 0)  # Set pins as outputs.
        self.write_register("OLAT", 0)  # Set pins low.
        self.write_register("GPINTEN", 0)  # Disable interrupts on all pins.
        self.write_register("IOCON", 0)  # Set configuration to default.

    def read_register(self, register, n_bytes=None):
        # Read specified register, convert to int, store in reg_values, return value.
        if n_bytes is None:
            n_bytes = self.reg_size
        for attempt in range(5):
            try:
                v = int.from_bytes(self.i2c.mem_read(n_bytes, self.addr, self.reg_addr[register], timeout=5), "little")
                if attempt > 0:
                    warning("Intermittant serial communication with device " + self.name)
                return v
            except:
                pass
        raise pyControlError("Unable to communicate with device " + self.name)

    def write_register(self, register, values, n_bytes=None):
        # Write values to specified register, values must be int which is converted to n_bytes bytes.
        if n_bytes is None:
            n_bytes = self.reg_size
        self.reg_values[register] = values
        for attempt in range(5):
            try:
                self.i2c.mem_write(values.to_bytes(n_bytes, "little"), self.addr, self.reg_addr[register], timeout=5)
                if attempt > 0:
                    warning("Intermittant serial communication with device " + self.name)
                return
            except:
                pass
        raise pyControlError("Unable to communicate with device " + self.name)

    def write_bit(self, register, bit, value, n_bytes=None):
        # Write the value of specified bit to specified register.
        if n_bytes is None:
            n_bytes = self.reg_size
        if value:
            self.reg_values[register] |= 1 << bit  # Set bit
        else:
            self.reg_values[register] &= ~(1 << bit)  # Clear bit
        self.write_register(register, self.reg_values[register], n_bytes)

    def enable_interrupts(self):
        self.write_register("INTCON", 0)  # Set all interrupts to IRQ_RISING_FALLING mode.
        self.write_bit("IOCON", 1, True, n_bytes=1)  # Set interrupt pin active high.
        self.write_bit("IOCON", 6, True, n_bytes=1)  # Set port A, B interrupt pins to mirror.
        self.extint_pin = pyb.Pin(self.interrupt_pin, mode=pyb.Pin.IN)
        self.extint = pyb.ExtInt(self.extint_pin, pyb.ExtInt.IRQ_RISING, pyb.Pin.PULL_NONE, self.extint_ISR)
        self.rising_ints = 0  # Binary mask indicating which pins have rising edge interupts.
        self.falling_ints = 0  # Binary mask indicating which pins have falling edge interupts.
        self.pin_callbacks = {}  # Dictionary of {pin: callback}
        self.interrupts_enabled = True

    def extint_ISR(self, i):
        hw.interrupt_queue.put(self.ID)

    def timer_ISR(self, i):
        if self.extint_pin.value():
            hw.interrupt_queue.put(self.ID)

    def _process_interrupt(self):
        # Find out which pin triggered the interrupt and call the appropriate function.
        self._process_changed_inputs(self.read_register("INTCAP"))
        self._process_changed_inputs(self.read_register("GPIO"))

    def _process_changed_inputs(self, new_GPIO_state):
        # Detect which pins have changed and call any relevant callbacks. Store new GPIO pin state.
        changed_bits = self.GPIO_state ^ new_GPIO_state
        active_edges = (changed_bits & (new_GPIO_state & self.rising_ints)) | (
            changed_bits & (~new_GPIO_state & self.falling_ints)
        )
        self.GPIO_state = new_GPIO_state
        if active_edges:
            for pin in self.pin_callbacks.keys():
                if (1 << pin) & active_edges:
                    self.pin_callbacks[pin](pin)  # Called with pin as an argument for consistency with pyb.ExtInt

    def Pin(self, id, mode=None, pull=None):
        # Instantiate and return a Pin object, pull argument currently ignored.
        return _Pin(self, id, mode)

    def ExtInt(self, pin, mode, pull, callback):
        # Enable interrupt on specified pin using syntax compatible with pyb.ExtInt. Pull argument ignored.
        pin.enable_interrupt(callback, mode)

    def _run_start(self):
        self.GPIO_state = self.read_register("GPIO")  # Clear any interrupts.
        if self.interrupts_enabled:
            self.timer.init(freq=10)
            self.timer.callback(self.timer_ISR)

    def _run_stop(self):
        self.timer.deinit()


class MCP23017(_MCP):
    # MCP23017 16 bit port expander. Ports A and B are addressed as single 16 bit port
    # and use a single interrupt pin.

    def __init__(self, I2C_bus=1, interrupt_pin="X5", addr=0x20, name="MCP23017"):
        super().__init__(I2C_bus, interrupt_pin, addr, name)
        self.reg_addr = {  # Register memory addresses.
            "IODIR": 0x00,  # Input / output direction.
            "GPIO": 0x12,  # Pin state.
            "GPINTEN": 0x04,  # Interrupt on change enable.
            "INTF": 0x0E,  # Interrupt flag.
            "INTCON": 0x08,  # Interupt compare mode.
            "DEFVAL": 0x06,  # Interupt compare default.
            "IOCON": 0x0A,  # Configuration.
            "OLAT": 0x14,  # Output latches.
            "INTCAP": 0x10,
        }  # Interupt capture.
        self.reg_size = 2  # Bytes to read/write for each register.
        self.reset()


class MCP23008(_MCP):
    # MCP23008 8 bit port expander.

    def __init__(self, I2C_bus=1, interrupt_pin="X5", addr=0x20, name="MCP23017"):
        super().__init__(I2C_bus, interrupt_pin, addr, name)
        self.reg_addr = {  # Register memory addresses.
            "IODIR": 0x00,  # Input / output direction.
            "GPIO": 0x09,  # Pin state.
            "GPINTEN": 0x02,  # Interrupt on change enable.
            "INTF": 0x07,  # Interrupt flag.
            "INTCON": 0x04,  # Interupt compare mode.
            "DEFVAL": 0x03,  # Interupt compare default.
            "IOCON": 0x05,  # Configuration.
            "OLAT": 0x0A,  # Output latches.
            "INTCAP": 0x08,
        }  # Interupt capture.
        self.reg_size = 1  # Bytes to read/write for each register.
        self.reset()


class _Pin(hw.IO_expander_pin):
    # GPIO pin on MCP IO expander.

    def __init__(self, IOx, id, mode=None):
        assert isinstance(IOx, _MCP), "mcp argument must be instance of MCP23017 or MCP23008"
        assert (id[0] in ["A", "B"]) and (
            id[1] in [str(i) for i in range(8)]
        ), "Invalid id argument, valid arguments are e.g. 'A0' or 'B7'"
        self.IOx = IOx  # IO expander the pin is located on.
        self.pin = int(id[1]) + 8 * (id[0] == "B")  # pin number (0 - 15).
        self.mode = mode
        self.interrupt_enabled = False
        if mode:
            self.set_mode(mode)

    def set_mode(self, mode):
        # Set the pin to be an input or output.
        assert mode in [pyb.Pin.IN, pyb.Pin.OUT], "Mode must be pyb.Pin.IN or pyb.Pin.OUT"
        self.mode = mode
        self.IOx.write_bit("IODIR", self.pin, mode == pyb.Pin.IN)
        if mode == pyb.Pin.IN:
            if not self.IOx.interrupts_enabled:
                self.IOx.enable_interrupts()
            self.IOx.write_bit("GPINTEN", self.pin, True)

    def value(self, value=None):
        # Get or set the digital logic level of the pin.
        if value is None:  # Return the state of the pin.
            return bool(self.IOx.GPIO_state & (1 << self.pin))
        else:  # Set the logic level of the pin.
            self.IOx.write_bit("OLAT", self.pin, value)

    def enable_interrupt(self, callback, mode):
        # Enable interrupt to call specified callback function.
        assert not self.interrupt_enabled, "Interrupt already set on pin."
        assert mode in [
            pyb.ExtInt.IRQ_RISING,
            pyb.ExtInt.IRQ_FALLING,
            pyb.ExtInt.IRQ_RISING_FALLING,
        ], "Invalid interrupt mode, valid values e.g. pyb.ExtInt.IRQ_RISING"
        if not self.mode == pyb.Pin.IN:
            self.set_mode(pyb.Pin.IN)
        if mode in [pyb.ExtInt.IRQ_RISING_FALLING, pyb.ExtInt.IRQ_RISING]:
            self.IOx.rising_ints |= 1 << self.pin
        if mode in [pyb.ExtInt.IRQ_RISING_FALLING, pyb.ExtInt.IRQ_FALLING]:
            self.IOx.falling_ints |= 1 << self.pin
        self.interrupt_enabled = True
        self.IOx.pin_callbacks[self.pin] = callback
