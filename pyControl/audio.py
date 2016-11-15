import pyb
import math

_sine_len = 100 # Number of points in sine wave.
_sine_buf = bytearray([128+int(127*math.sin(2*math.pi*i/_sine_len)) for i in range(_sine_len)])
_sqr_buf = bytearray([255,0])
_off_buf = bytearray([0])

#-----------------------------------------------------------------------------------
# Audio output
#-----------------------------------------------------------------------------------

class Audio_output():
    def __init__(self, channel=1):
        assert channel in [1,2], 'channel number invalid, must be 1 or 2.'
        self._DAC = pyb.DAC(channel) 
        self._timer = pyb.Timer(channel)
        self._playing = False
        self._func = None # Function currently being used for sweeped sound (sine, square or noise)
        self._freq = 0
        self._freq_ind = 0
        self.click_freq = 10000 # Frequency of square wave cycle used to generate click.

    # User functions-------------------------------------------------------------------

    def off(self):
            self._DAC.write_timed(_off_buf, 10000, mode=pyb.DAC.NORMAL)
            self._timer.deinit()
            self._playing = False

    def sine(self, freq):  # Play a sine wave tone at the specified frequency.
        self._DAC.write_timed(_sine_buf, freq*_sine_len, mode=pyb.DAC.CIRCULAR)

    def square(self, freq): # Play a square wave tone at the specified frequency.
        self._DAC.write_timed(_sqr_buf, freq*2, mode=pyb.DAC.CIRCULAR)    

    def noise(self, freq=10000): # Play white noise with specified maximum frequency.
        self._DAC.noise(freq*2)

    def clicks(self, rate): # Play clicks at specified rate, f controls click frequency content. 
        self._timer.init(freq=rate)
        self._timer.callback(self._click)

    def pulsed_sine(self, freq, pulse_rate):
        self._pulsed_sound(freq, pulse_rate, self.sine)

    def pulsed_square(self, freq, pulse_rate):
        self._pulsed_sound(freq, pulse_rate, self.square)

    def pulsed_noise(self, freq=10000, pulse_rate=10):
        self._pulsed_sound(freq, pulse_rate, self.noise)

    def sweeped_sine(self, start_freq, end_freq, n_steps, step_rate):
        self._sound_sweep(start_freq, end_freq, n_steps, step_rate, self.sine)

    def sweeped_square(self, start_freq, end_freq, n_steps, step_rate):
        self._sound_sweep(start_freq, end_freq, n_steps, step_rate, self.square)

    def sweeped_noise(self, start_freq, end_freq, n_steps, step_rate):
        self._sound_sweep(start_freq, end_freq, n_steps, step_rate, self.noise)

    # Support functions-----------------------------------------------------------------

    def _click(self, timer=None): # Play a single click.
        self._DAC.write_timed(_sqr_buf, self.click_freq, mode=pyb.DAC.NORMAL)  

    def _pulsed_sound(self, freq, pulse_rate, func):
        self._freq = freq
        self._func = func
        self._timer.init(freq=2*pulse_rate)
        self._timer.callback(self._toggle_sound)

    def _toggle_sound(self, timer):
        if self._playing:
            self._DAC.write(127)
            self._playing = False
        else:
            self._func(self._freq)
            self._playing = True

    def _sound_sweep(self, start_freq, end_freq, n_steps, step_rate, func):
        freq_ratio = (end_freq/start_freq)**(1./(n_steps-1))
        self._freq = [int(start_freq * (freq_ratio**i)) for i in range(n_steps)]
        self._freq_ind = 0
        self._func = func
        self._timer.init(freq=step_rate)
        self._timer.callback(self._step_sound)

    def _step_sound(self, timer): # Timer callback to increment frequency during sweeped sounds.
        self._func(self._freq[self._freq_ind])
        self._freq_ind = (self._freq_ind+1) % len(self._freq)