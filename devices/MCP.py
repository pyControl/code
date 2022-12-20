import pyb
import math
import pyControl.hardware as hw
import pyControl.framework as fw

class _MCP(hw.IO_object):
    # Parent class for MCP23017 and MCP23008 port expanders.

    def __init__(self, I2C_bus, interrupt_pin, addr, name):
        self.baudrate = 400000
        self.i2c = pyb.I2C(I2C_bus, mode=pyb.I2C.MASTER, baudrate=self.baudrate) 
        self.timer = pyb.Timer(hw.available_timers.pop())
        self.addr = addr   # Device I2C address
        self.name = name
        self.interrupt_timestamp = 0  # Time of last interrupt.
        self.check_config = False     # Set True by timer to periodically check registers are set correctly.
        self.interrupts_enabled = False
        self.interrupt_pin = interrupt_pin
        self.reg_values = {} # Register values set by user.
        hw.assign_ID(self)

    def reset(self):
        self.write_register('IODIR'  , 0) # Set pins as ouptuts.
        self.write_register('GPIO'   , 0) # Set pins low.
        self.write_register('GPINTEN', 0) # Disable interrupts on all pins.
        self.write_register('IOCON'  , 0) # Set configuration to default.

    def read_register(self, register, n_bytes=None):
        # Read specified register, convert to int, store in reg_values, return value. 
        if n_bytes is None: n_bytes = self.reg_size
        for attempt in range(7):
            if attempt > 1:
                self._reduce_baudrate()
            try:
                v = int.from_bytes(self.i2c.mem_read(n_bytes, self.addr, self.reg_addr[register], timeout=5), 'little')
                self.reg_values[register] = v
                if attempt > 1:
                    self._baudrate_warning()
                return v
            except:
                pass

    def write_register(self, register, values, n_bytes=None):
        # Write values to specified register, values must be int which is converted to n_bytes bytes.
        if n_bytes is None: n_bytes = self.reg_size
        self.reg_values[register] = values
        for attempt in range(7):
            if attempt > 1:
                self._reduce_baudrate()
            try:
                self.i2c.mem_write(values.to_bytes(n_bytes,'little'), self.addr, self.reg_addr[register], timeout=5)
                if attempt > 1:
                    self._baudrate_warning()
                return
            except:
                pass

    def _reduce_baudrate(self):
        # Reduce i2c baudrate to overcome intermittant connection.
        if self.baudrate > 30000: 
            self.baudrate = self.baudrate//2
            self.i2c.init(mode=pyb.I2C.MASTER, baudrate=self.baudrate)
        else:
            raise fw.pyControlError('Unable to communicate with device ' + self.name)

    def _baudrate_warning(self):
        # Notify user that baudrate has been reduced.
        fw.data_output_queue.put((fw.current_time, fw.warng_typ, 
            'Intermittant serial communication with device ' + self.name + ', reduced baudrate to ' + str(self.baudrate)))

    def write_bit(self, register, bit, value, n_bytes=None):
        # Write the value of specified bit to specified register.
        if n_bytes is None: n_bytes = self.reg_size
        if value:
            self.reg_values[register] |=  (1<<bit)  # Set bit
        else:
            self.reg_values[register] &= ~(1<<bit)  # Clear bit
        self.write_register(register, self.reg_values[register], n_bytes)

    def enable_interrupts(self):
        self.write_register('INTCON', 0) # Set all interupts to IRQ_RISING_FALLING mode.
        self.write_register('DEFVAL', 0) # Set default compare value to low.
        self.write_bit('IOCON',1,True, n_bytes=1) # Set interrupt pin active high.
        self.write_bit('IOCON',6,True, n_bytes=1) # Set port A, B interrupt pins to mirror.
        self.extint = pyb.ExtInt(self.interrupt_pin, pyb.ExtInt.IRQ_RISING, pyb.Pin.PULL_NONE, self.ISR)
        self.pin_callbacks = {} # Dictionary of {pin: callback}
        self.interrupts_enabled = True

    def ISR(self, i):
        hw.interrupt_queue.put(self.ID)

    def timer_ISR(self,i):
        self.check_config = True
        hw.interrupt_queue.put(self.ID)
        
    def _process_interrupt(self):
        # Find out which pin triggered the interrupt and call the appropriate function.
        INTF = self.read_register('INTF')
        self.read_register('GPIO')
        if INTF > 0:
            pin = int(math.log2(INTF)+0.1)
            self.pin_callbacks[pin](pin) # Called with pin as an argument for consistency with pyb.ExtInt
        if self.check_config: 
           # Check the state of the registers on the MCP device is correct and correct them if not.
            self.check_config = False
            for register, values in self.reg_values.items():
                if register in ('GPIO', 'INTF'):
                    continue
                n_bytes = 1 if register == 'IOCON' else self.reg_size
                read_values = self.read_register(register, n_bytes=n_bytes)
                if read_values != values:
                    self.write_register(register, values, n_bytes=n_bytes)
                    fw.data_output_queue.put((fw.current_time, fw.print_typ, 'Corrected bad '+ register + ' register value on device ' + self.name))

    def Pin(self, id, mode=None, pull=None):
        # Instantiate and return a Pin object, pull argument currently ignored.
        return _Pin(self, id, mode)

    def ExtInt(self, pin, mode, pull, callback):
        # Enable interrupt on specified pin using syntax compatible with pyb.ExtInt. Pull argument ignored.
        pin.enable_interrupt(callback, mode)

    def _run_start(self):
        self.read_register('GPIO') # Read the GPIO register to clear interrupts.
        # Set timer to call ISR every second to avoid lockup if an interrupt is missed.
        self.timer.init(freq=1)
        self.timer.callback(self.timer_ISR)
        self.check_config = False

    def _run_stop(self):
        self.timer.deinit()

class MCP23017(_MCP):
    # MCP23017 16 bit port expander. Ports A and B are addressed as single 16 bit port
    # and use a single interrupt pin.

    def __init__(self, I2C_bus=1, interrupt_pin='X5', addr=0x20, name='MCP23017'):
        super().__init__(I2C_bus, interrupt_pin, addr, name)
        self.reg_addr = {                 # Register memory addresses.
                         'IODIR'  : 0x00, # Input / output direction.
                         'GPIO'   : 0x12, # Pin state.
                         'GPINTEN': 0x04, # Interrupt on change enable.
                         'INTF'   : 0x0E, # Interrupt flag.
                         'INTCON' : 0x08, # Interupt compare mode.
                         'DEFVAL' : 0x06, # Interupt compare default.
                         'IOCON'  : 0x0A} # Configuration.
        self.reg_size = 2 # Bytes to read/write for each register.
        self.reset()


class MCP23008(_MCP):
    # MCP23008 8 bit port expander.

    def __init__(self, I2C_bus=1, interrupt_pin='X5', addr=0x20, name='MCP23017'):
        super().__init__(I2C_bus, interrupt_pin, addr, name)
        self.reg_addr = {                 # Register memory addresses.
                         'IODIR'  : 0x00, # Input / output direction.
                         'GPIO'   : 0x09, # Pin state.
                         'GPINTEN': 0x02, # Interrupt on change enable.
                         'INTF'   : 0x07, # Interrupt flag.
                         'INTCON' : 0x04, # Interupt compare mode.
                         'DEFVAL' : 0x03, # Interupt compare default.
                         'IOCON'  : 0x05} # Configuration.
        self.reg_size = 1 # Bytes to read/write for each register.
        self.reset()


class _Pin(hw.IO_expander_pin):
    # GPIO pin on MCP IO expander.

    def __init__(self, IOx, id, mode=None):
        assert isinstance(IOx, _MCP), 'mcp argument must be instance of MCP23017 or MCP23008'
        assert (id[0] in ['A','B']) and (id[1] in [str(i) for i in range(8)]), \
            "Invalid id argument, valid arguments are e.g. 'A0' or 'B7'"
        self.IOx = IOx # IO expander the pin is located on.
        self.pin = int(id[1]) + 8*(id[0]=='B') # pin number (0 - 15).
        self.mode = mode
        self.interrupt_enabled = False
        if mode: self.set_mode(mode)

    def set_mode(self,mode):
        # Set the pin to be an input or output.
        assert mode in [pyb.Pin.IN, pyb.Pin.OUT], 'Mode must be pyb.Pin.IN or pyb.Pin.OUT'
        self.mode = mode
        self.IOx.write_bit('IODIR', self.pin, mode==pyb.Pin.IN)


    def value(self,value=None):
        # Get or set the digital logic level of the pin.
        if value is None: # Return the state of the pin.
            if self.mode == pyb.Pin.OUT or self.interrupt_enabled: # Use stored value.
                return bool(self.IOx.reg_values['GPIO'] & (1<<self.pin))
            return bool(self.IOx.read_register('GPIO') & (1<<self.pin))
        else: # Set the logic level of the pin.
            self.IOx.write_bit('GPIO', self.pin, value)

    def enable_interrupt(self, callback, mode):
        assert not self.interrupt_enabled, 'Interrupt already set on pin.'
        assert mode in [pyb.ExtInt.IRQ_RISING, pyb.ExtInt.IRQ_FALLING, pyb.ExtInt.IRQ_RISING_FALLING], \
            'Invalid interrupt mode, valid values e.g. pyb.ExtInt.IRQ_RISING'
        if mode != pyb.ExtInt.IRQ_RISING_FALLING:
            self.IOx.write_bit('INTCON', self.pin, True) 
            if mode == pyb.ExtInt.IRQ_FALLING:
                self.IOx.write_bit('DEFVAL', self.pin, True) 
        if not self.mode == pyb.Pin.IN: self.set_mode(pyb.Pin.IN)
        if not self.IOx.interrupts_enabled: self.IOx.enable_interrupts()
        self.interrupt_enabled = True
        self.IOx.write_bit('GPINTEN', self.pin, True)
        self.IOx.pin_callbacks[self.pin] = callback