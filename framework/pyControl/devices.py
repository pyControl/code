from .hardware import *


# EXTERNAL DEVICES

class ExternalDevice(object):
    pass

class SinglePokeDevice(ExternalDevice):
# Two IR beams, single LED and Solenoid.

    def __init__(self, board, poke_in_event=None, poke_out_event=None, debounce=5, pull=pyb.Pin.PULL_NONE):
        self.IR = Digital_input(poke_in_event, poke_out_event, debounce=debounce)
        self.IR.connect(board.rj45_port4.DIO_A, pull)

        self.LED = Digital_output()
        self.LED.connect(board.rj45_port4.POW_A)
        
        self.SOL = Digital_output()
        self.SOL.connect(board.rj45_port4.POW_B)

    def value(self):
        # Return the state of input A.
        return self.IR.value()

class LoadCellsDevice(ExternalDevice):
    def __init__(self, board, pull=pyb.Pin.PULL_NONE, debounce=5):

        self.cell1_threshold_high = Digital_input(rising_event="cell1_threshold_high_rise", falling_event="cell1_threshold_high_fall", debounce=debounce)
        self.cell1_threshold_high.connect(board.generic_io1.DIO_pin, pull)

        self.cell1_threshold_low = Digital_input(rising_event= "cell1_threshold_low_rise", falling_event="cell1_threshold_low_fall", debounce=debounce)
        self.cell1_threshold_low.connect(board.generic_io2.DIO_pin, pull)

        self.cell2_threshold_high = Digital_input(rising_event="cell2_threshold_high_rise", falling_event="cell2_threshold_high_fall", debounce=debounce)
        self.cell2_threshold_high.connect(board.generic_io3.DIO_pin, pull)

        self.cell2_threshold_low = Digital_input(rising_event="cell2_threshold_low_rise", falling_event="cell2_threshold_low_fall", debounce=debounce)
        self.cell2_threshold_low.connect(board.generic_io4.DIO_pin, pull)

        self.task_status = Digital_output()
        self.task_status.connect(board.generic_io9.DIO_pin)

        self.solenoid_status = Digital_output()
        self.solenoid_status.connect(board.generic_io10.DIO_pin)

        self.poke_status = Digital_output()
        self.poke_status.connect(board.generic_io11.DIO_pin)

    def start_task(self):
        self.task_status.on()

    def stop_task(self):
        self.task_status.off()

    def solenoid_opening(self):
        self.solenoid_status.on()

    def solenoid_closing(self):
        self.solenoid_status.off()        
    
    def infrared_cross_in(self):
        self.poke_status.on()     

    def infrared_cross_out(self):
        self.poke_status.off()     

class LedDevice(ExternalDevice):
  def __init__(self, board_pin):

    self.led = Digital_output()
    self.led.connect(board_pin)

  def on(self):
    self.led.on()

  def off(self):
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

