from .hardware import *

# ----------------------------------------------------------------------------------------
# Poke
# ----------------------------------------------------------------------------------------

class Poke():
    # Single IR beam, LED and Solenoid.
  
    def __init__(self, rising_event = None, falling_event = None, debounce = 5):
        self.input = Digital_input(rising_event, falling_event, debounce)

    def connect(self, port = None, pull = pyb.Pin.PULL_NONE,
                input_pin = None, SOL_pin = None, LED_pin = None):
        if port:
            input_pin = port['DIO_A']
            LED_pin   = port['POW_A']
            SOL_pin   = port['POW_B']

        self.input.connect(input_pin, pull)
        if LED_pin: 
            self.LED = Digital_output()
            self.LED.connect(LED_pin)
        if SOL_pin:
            self.SOL = Digital_output()
            self.SOL.connect(SOL_pin)

    def value(self):
        return self.input.value()

# ----------------------------------------------------------------------------------------
# Double_poke
# ----------------------------------------------------------------------------------------

class Double_poke():
    # Two IR beams, single LED and Solenoid.
    
    def __init__(self, rising_event_A = None, falling_event_A = None,
                       rising_event_B = None, falling_event_B = None, debounce = 5):
        self.SOL     = Digital_output()
        self.LED     = Digital_output()
        self.input_A = Digital_input(rising_event_A, falling_event_A, debounce)
        self.input_B = Digital_input(rising_event_B, falling_event_B, debounce)

    def connect(self, port, pull = pyb.Pin.PULL_NONE):
        self.input_A.connect(port['DIO_A'], pull)
        self.input_B.connect(port['DIO_B'], pull)
        self.LED.connect(port['POW_A'])
        self.SOL.connect(port['POW_B'])

    def value(self):
        # Return the state of input A.
        return self.input_A.value()

# ----------------------------------------------------------------------------------------
# Twin_poke
# ----------------------------------------------------------------------------------------

class Twin_poke():
    # Two IR beams, each with their own LED.
    def __init__(self, rising_event_A = None, falling_event_A = None,
                       rising_event_B = None, falling_event_B = None, debounce = 5):
        self.poke_A = Poke(rising_event_A, falling_event_A, debounce)
        self.poke_B = Poke(rising_event_B, falling_event_B, debounce)

    def connect(self, port, pull = pyb.Pin.PULL_NONE):
        self.poke_A.connect(input_pin = port['DIO_A'], LED_pin = port['POW_A'], pull = pull)
        self.poke_B.connect(input_pin = port['DIO_B'], LED_pin = port['POW_B'], pull = pull)

# ----------------------------------------------------------------------------------------
# Quad_poke
# ----------------------------------------------------------------------------------------

class Quad_poke():
    # 4 IR beams, 3 of which have
    def __init__(self, rising_event_A = None, falling_event_A = None,
                       rising_event_B = None, falling_event_B = None, 
                       rising_event_C = None, falling_event_C = None, 
                       rising_event_D = None, falling_event_D = None, 
                       debounce = 5):
        self.poke_A = Poke(rising_event_A, falling_event_A, debounce)
        self.poke_B = Poke(rising_event_B, falling_event_B, debounce)
        self.poke_C = Poke(rising_event_C, falling_event_C, debounce)
        self.poke_D = Poke(rising_event_D, falling_event_D, debounce)
        self.SOL = Digital_output()

    def connect(self, two_ports, pull = pyb.Pin.PULL_NONE):
        port_1, port_2 = two_ports
        self.poke_A.connect(input_pin = port_1['DIO_A'], LED_pin = port_1['POW_A'], pull = pull)
        self.poke_B.connect(input_pin = port_1['DIO_B'], LED_pin = port_1['POW_B'], pull = pull)
        self.poke_C.connect(input_pin = port_2['DIO_A'], LED_pin = port_2['POW_A'], pull = pull)
        self.poke_D.connect(input_pin = port_2['DIO_B'], pull = pull)
        self.SOL.connect(port_2['POW_B'])

# ----------------------------------------------------------------------------------------
# Board pin mapping dictionaries.
# ----------------------------------------------------------------------------------------

# These dictionaries provide pin mappings for specific boards whose schematics are
# provided in the pyControl/schematics folder.

breakout_1_0 = {'ports': {1: {'DIO_A': 'X1',   # RJ45 connector port pin mappings.
                              'DIO_B': 'X2',
                              'POW_A': 'Y8',
                              'POW_B': 'Y4'},
         
                          2: {'DIO_A': 'X3',
                              'DIO_B': 'X4',
                              'POW_A': 'Y7',
                              'POW_B': 'Y3'},
         
                          3: {'DIO_A': 'X7',
                              'DIO_B': 'X8',
                              'POW_A': 'Y6',
                              'POW_B': 'Y2'},
         
                          4: {'DIO_A': 'X12',
                              'DIO_B': 'X11',
                              'POW_A': 'Y5',
                              'POW_B': 'Y1'}},
                'BNC_1': 'Y11',      # BNC connector pins.
                'BNC_2': 'Y12',
                'DAC_1': 'X5',
                'DAC_2': 'X6',
                'button_1': 'X9',    # User pushbuttons.
                'button_2': 'X10'}

devboard_1_0 = {'ports': {1: {'DIO_A': 'Y1',   # Use buttons and LEDs to emulate breakout board ports.
                              'DIO_B': 'Y4',
                              'POW_A': 'Y7',
                              'POW_B': 'Y8'},

                          2: {'DIO_A': 'Y2',
                              'DIO_B': 'Y5',
                              'POW_A': 'Y9',
                              'POW_B': 'Y10'},

                          3: {'DIO_A': 'Y3',
                              'DIO_B': 'Y6',
                              'POW_A': 'Y11',
                              'POW_B': 'Y12'}},
                'button_1': 'Y1',  # Access buttons and pins directly. 
                'button_2': 'Y2',
                'button_3': 'Y3',
                'button_4': 'Y4',
                'button_5': 'Y5',
                'button_6': 'Y6',
                'LED_1': 'Y7',
                'LED_2': 'Y8',
                'LED_3': 'Y9',
                'LED_4': 'Y10',
                'LED_5': 'Y11',
                'LED_6': 'Y12',
                'BNC_1': 'X7',     # BNC connector pins.
                'BNC_2': 'X8',
                'DAC_1': 'X5',
                'DAC_2': 'X6',
                }