from pyControl.hardware import *
from pyControl.audio import Audio_output

class Audio_board(Audio_output):
    def __init__(self,  port):
    	assert port.DAC is not None, 'Audio board needs port with DAC.'
    	assert port.I2C is not None, 'Audio board needs port with I2C.'
    	self.I2C = port.I2C
    	super().__init__(port.DAC)

    def set_volume(self, V): # Set volume of audio output, range 0 - 127
   		pyb.I2C(self.I2C, pyb.I2C.MASTER).mem_write(V, 46, 0)