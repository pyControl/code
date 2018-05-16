import pyb
import pyControl.audio as _a

class Audio_board(_a.Audio_output):

    def __init__(self,  port):
        assert port.DAC is not None, '! Audio board needs port with DAC.'
        assert port.I2C is not None, '! Audio board needs port with I2C.'
        self.I2C = pyb.I2C(port.I2C)
        self.I2C.init(pyb.I2C.MASTER)
        super().__init__(port.DAC)

    def set_volume(self, V): # Set volume of audio output, range 0 - 127      
        self.I2C.mem_write(int(V), 46, 0)