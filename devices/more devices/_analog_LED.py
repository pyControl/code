import pyb

class Analog_LED():

    def __init__(self,  port):
        assert port.DAC is not None, '! Analog LED needs port with DAC.'
        self.DAC = pyb.DAC(port.DAC, bits=12)
        self.off()

    def on(self, LED_current_mA):
    	assert 1 <= LED_current_mA <= 400, 'LED_current_mA must be between 1 and 400.'
    	self.DAC.write(round(9.7237*LED_current_mA+48.36))

    def off(self):
    	self.DAC.write(0)