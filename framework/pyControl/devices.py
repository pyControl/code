from .hardware import *


class ExternalDevice(object):

    counter = 1

    def get_uid(self):
      ExternalDevice.counter += 1
      return ExternalDevice.counter

    def connect(self, port, pull=pyb.Pin.PULL_NONE):
        pass

# ----------------------------------------------------------------------------------------
# Poke
# ----------------------------------------------------------------------------------------


# class Poke(ExternalDevice):
#     # Single IR beam, LED and Solenoid.

#     def __init__(self, rising_event=None, falling_event=None, debounce=5):
#         self.input = Digital_input(rising_event, falling_event, debounce)

#     def connect(self, port=None, pull=pyb.Pin.PULL_NONE,
#                 input_pin=None, SOL_pin=None, LED_pin=None):
#         if port:
#             input_pin = port['DIO_A']
#             LED_pin = port['POW_A']
#             SOL_pin = port['POW_B']

#         self.input.connect(input_pin, pull)
#         if LED_pin:
#             self.LED = Digital_output()
#             self.LED.connect(LED_pin)
#         if SOL_pin:
#             self.SOL = Digital_output()
#             self.SOL.connect(SOL_pin)

#     def value(self):
#         return self.input.value()

# # ----------------------------------------------------------------------------------------
# # Double_poke
# # ----------------------------------------------------------------------------------------




# # ----------------------------------------------------------------------------------------
# # Twin_poke
# # ----------------------------------------------------------------------------------------


# class Twin_poke(ExternalDevice):
#     # Two IR beams, each with their own LED.

#     def __init__(self, rising_event_A=None, falling_event_A=None,
#                  rising_event_B=None, falling_event_B=None, debounce=5):
#         self.poke_A = Poke(rising_event_A, falling_event_A, debounce)
#         self.poke_B = Poke(rising_event_B, falling_event_B, debounce)

#     def connect(self, port, pull=pyb.Pin.PULL_NONE):
#         self.poke_A.connect(input_pin=port['DIO_A'], LED_pin=port['POW_A'], pull=pull)
#         self.poke_B.connect(input_pin=port['DIO_B'], LED_pin=port['POW_B'], pull=pull)
#         self.LED = Digital_output_group([self.poke_A.LED, self.poke_B.LED])

# # ----------------------------------------------------------------------------------------
# # Quad_poke
# # ----------------------------------------------------------------------------------------


# class Quad_poke():
#     # 4 IR beams, 3 of which have LEDs, 1 solenoid,

#     def __init__(self, rising_event_A=None, falling_event_A=None,
#                  rising_event_B=None, falling_event_B=None,
#                  rising_event_C=None, falling_event_C=None,
#                  rising_event_D=None, falling_event_D=None,
#                  debounce=5):
#         self.poke_A = Poke(rising_event_A, falling_event_A, debounce)
#         self.poke_B = Poke(rising_event_B, falling_event_B, debounce)
#         self.poke_C = Poke(rising_event_C, falling_event_C, debounce)
#         self.poke_D = Poke(rising_event_D, falling_event_D, debounce)
#         self.SOL = Digital_output()

#     def connect(self, two_ports, pull=pyb.Pin.PULL_NONE):
#         port_1, port_2 = two_ports
#         self.poke_A.connect(input_pin=port_1['DIO_A'], LED_pin=port_1['POW_A'], pull=pull)
#         self.poke_B.connect(input_pin=port_1['DIO_B'], LED_pin=port_1['POW_B'], pull=pull)
#         self.poke_C.connect(input_pin=port_2['DIO_A'], LED_pin=port_2['POW_A'], pull=pull)
#         self.poke_D.connect(input_pin=port_2['DIO_B'], pull=pull)
#         self.SOL.connect(port_2['POW_B'])

# ----------------------------------------------------------------------------------------
# Board pin mapping dictionaries.
# ----------------------------------------------------------------------------------------

# These dictionaries provide pin mappings for specific boards whose schematics are
# provided in the pyControl/schematics folder.

# EXTERNAL DEVICES

class ExternalDevice(object):
  pass

class DoublePokeDevice(ExternalDevice):
  # Two IR beams, single LED and Solenoid.

  def __init__(self, board, pull=pyb.Pin.PULL_NONE, debounce=5):

    self.IR_high = Digital_input(debounce=debounce)
    self.IR_high.connect(board.rj45_port4.DIO_A, pull)
    
    self.IR_low = Digital_input(debounce=debounce)
    self.IR_low.connect(board.rj45_port4.DIO_B, pull)

    self.LED = Digital_output()
    self.LED.connect(board.rj45_port4.POW_A)
    
    self.SOL = Digital_output()
    self.SOL.connect(board.rj45_port4.POW_B)

  def value(self):
    # Return the state of input A.
    return self.IR_high.value()

class ScyBoardDevice(ExternalDevice):
   def __init__(self, board, pull=pyb.Pin.PULL_NONE, debounce=5):

    self.input1 = Digital_input(debounce=debounce)
    self.input1.connect(board.generic_io1.DIO_pin, pull)

    self.input2 = Digital_input(debounce=debounce)
    self.input2.connect(board.generic_io2.DIO_pin, pull)

    self.input3 = Digital_input(debounce=debounce)
    self.input3.connect(board.generic_io3.DIO_pin, pull)

    self.input4 = Digital_input(debounce=debounce)
    self.input4.connect(board.generic_io4.DIO_pin, pull)

    self.input5 = Digital_input(debounce=debounce)
    self.input5.connect(board.generic_io5.DIO_pin, pull)

    self.input6 = Digital_input(debounce=debounce)
    self.input6.connect(board.generic_io6.DIO_pin, pull)

    self.input7 = Digital_input(debounce=debounce)
    self.input7.connect(board.generic_io7.DIO_pin, pull)                                        

    self.input8 = Digital_input(debounce=debounce)
    self.input8.connect(board.generic_io8.DIO_pin, pull)

    self.output1 = Digital_output()
    self.output1.connect(board.generic_io9.DIO_pin)

    self.output2 = Digital_output()
    self.output2.connect(board.generic_io10.DIO_pin)

    self.output3 = Digital_output()
    self.output3.connect(board.generic_io11.DIO_pin)

    self.output4 = Digital_output()
    self.output4.connect(board.generic_io12.DIO_pin)

class LoadCellsDevice(ScyBoardDevice):
  def __init__(self, board, pull=pyb.Pin.PULL_NONE, debounce=5):
    super().__init__(board, pull, debounce)

    # events aliases
    self.cell1_threshold_high = self.input1.rising_event
    self.cell1_threshold_low = self.input2.falling_event

    self.cell2_threshold_high = self.input3.rising_event
    self.cell2_threshold_low = self.input4.falling_event

    self.cell3_threshold_high = self.input7.rising_event
    self.cell3_threshold_low = self.input8.falling_event

    # self.cell4_threshold_high = self.input7.rising_event
    # self.cell4_threshold_low = self.input8.falling_event


  def start_stop_task(self):
    self.output1.on()

  def solenoid_opening(self):
    self.output2.on()
    
  def infrafred_cross(self):
    self.output3.on()


class LedDevice(ExternalDevice):
  def __init__(self, board_pin):

    self.led = Digital_output()
    self.led.connect(board_pin)

  def turn_on(self):
    self.led.on()

  def turn_off(self):
    self.led.off()

class LedMatrixDevice(ExternalDevice):
  def __init__(self, board):
    self.led1 = LedDevice(board.generic_io13.DIO_pin)
    self.led2 = LedDevice(board.generic_io14.DIO_pin)
    self.led3 = LedDevice(board.generic_io15.DIO_pin)
    self.led4 = LedDevice(board.generic_io16.DIO_pin)
    self.led5 = LedDevice(board.generic_io17.DIO_pin)
    self.led6 = LedDevice(board.generic_io18.DIO_pin)


# class PushButtonDevice(ExternalDevice):
#   def __init__(self, board_pin, pull=pyb.Pin.PULL_NONE, debounce=5):
#     # events
#     self.pressed = self.get_uid()
#     self.released = self.get_uid()

#     self.button = Digital_input(self.pressed, self.released, debounce)
#     self.button.connect(board_pin, pull)    

# CONNECTORS

class Connector():
  pass

class RJ45Connector(Connector):
  def __init__(self, dio_a, dio_b, pow_a, pow_b):
    self.DIO_A = dio_a
    self.DIO_B = dio_b
    self.POW_A = pow_a
    self.POW_B = pow_b

class GenericIOConnector(Connector):
  def __init__(self, pin):
    self.DIO_pin = pin

# BOARDS

class BaseBoard(object):
  pass

class InesBoard(BaseBoard):
  def __init__(self):
        
    self.rj45_port4 = RJ45Connector('X12','X11','Y5','Y1')
    
    self.generic_io1 = GenericIOConnector('X1')
    self.generic_io2 = GenericIOConnector('X2')
    self.generic_io3 = GenericIOConnector('X3')
    self.generic_io4 = GenericIOConnector('X4')
    self.generic_io5 = GenericIOConnector('X5')
    self.generic_io6 = GenericIOConnector('X6')
    self.generic_io7 = GenericIOConnector('X7')
    self.generic_io8 = GenericIOConnector('X8')
    self.generic_io9 = GenericIOConnector('Y9')
    self.generic_io10 = GenericIOConnector('Y10')
    self.generic_io11 = GenericIOConnector('Y11')
    self.generic_io12 = GenericIOConnector('Y12')

    # connectors with a resistor 330R
    self.generic_io13 = GenericIOConnector('Y2')
    self.generic_io14 = GenericIOConnector('Y3')
    self.generic_io15 = GenericIOConnector('Y4')
    self.generic_io16 = GenericIOConnector('Y6')
    self.generic_io17 = GenericIOConnector('Y7')
    self.generic_io18 = GenericIOConnector('Y8')





# breakout_1_0 = {'ports': {1: {'DIO_A': 'X1',   # RJ45 connector port pin mappings.
#                               'DIO_B': 'X2',
#                               'POW_A': 'Y8',
#                               'POW_B': 'Y4'},

#                           2: {'DIO_A': 'X3',
#                               'DIO_B': 'X4',
#                               'POW_A': 'Y7',
#                                'POW_B': 'Y3'},

#                           3: {'DIO_A': 'X7',
#                               'DIO_B': 'X8',
#                               'POW_A': 'Y6',
#                               'POW_B': 'Y2'},

#                             4: {'DIO_A': 'X12',
#                               'DIO_B': 'X11',
#                               'POW_A': 'Y5',
#                               'POW_B': 'Y1'}},
#                 'BNC_1': 'Y11',      # BNC connector pins.
#                 'BNC_2': 'Y12',
#                 'DAC_1': 'X5',
#                 'DAC_2': 'X6',
#                 'button_1': 'X9',    # User pushbuttons.
#                 'button_2': 'X10'}

# devboard_1_0 = {'ports': {1: {'DIO_A': 'Y1',   # Use buttons and LEDs to emulate breakout board ports.
#                               'DIO_B': 'Y4',
#                               'POW_A': 'Y7',
#                               'POW_B': 'Y8'},

#                           2: {'DIO_A': 'Y2',
#                               'DIO_B': 'Y5',
#                               'POW_A': 'Y9',
#                               'POW_B': 'Y10'},

#                           3: {'DIO_A': 'Y3',
#                               'DIO_B': 'Y6',
#                               'POW_A': 'Y11',
#                               'POW_B': 'Y12'}},
#                 'button_1': 'Y1',  # Access buttons and pins directly.
#                 'button_2': 'Y2',
#                 'button_3': 'Y3',
#                 'button_4': 'Y4',
#                 'button_5': 'Y5',
#                 'button_6': 'Y6',
#                 'LED_1': 'Y7',
#                 'LED_2': 'Y8',
#                 'LED_3': 'Y9',
#                 'LED_4': 'Y10',
#                 'LED_5': 'Y11',
#                 'LED_6': 'Y12',
#                 'BNC_1': 'X7',     # BNC connector pins.
#                 'BNC_2': 'X8',
#                 'DAC_1': 'X5',
#                 'DAC_2': 'X6',
#                 }
