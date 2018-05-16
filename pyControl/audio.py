import pyb
import math
from . import hardware as hw

_sine_len = 100 # Number of points in sine wave.
_sine_buf = bytearray([128+int(127*math.sin(2*math.pi*i/_sine_len)) for i in range(_sine_len)])
_sqr_buf = bytearray([255,0])
_click_buf = bytearray([255,0,255,255,0,0]+4*[255]+4*[0]+8*[255]+8*[0]
                       +16*[255]+16*[0]+32*[255]+32*[0]+[128])
_off_buf = bytearray([128])

# Audio output ----------------------------------------------------------------

class Audio_output(hw.IO_object):
    def __init__(self, channel=1):
        assert channel in [1,2], '! Channel number invalid, must be 1 or 2.'
        self._DAC = pyb.DAC(channel) 
        self._timer = pyb.Timer(hw.available_timers.pop())
        self._func = None # Function currently being used for sweeped sound (sine, square or noise)
        self._freq = 0
        self._freq_ind = 0
        self.off()
        hw.assign_ID(self)

    # User functions

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

    def click(self, timer=None): # Play a single click.
        self._DAC.write_timed(_click_buf, 40000, mode=pyb.DAC.NORMAL)  

    def clicks(self, rate): # Play clicks at specified rate.
        self._timer.init(freq=rate)
        self._timer.callback(self.click)

    def pulsed_sine(self, freq, pulse_rate): # Play a sine wave pulsed at the specified rate.
        self._pulsed_sound(freq, pulse_rate, self.sine)

    def pulsed_square(self, freq, pulse_rate): # Play a square wave pulsed at the specified rate.
        self._pulsed_sound(freq, pulse_rate, self.square)

    def pulsed_noise(self, freq, pulse_rate):
        self._pulsed_sound(freq, pulse_rate, self.noise)

    def stepped_sine(self, start_freq, end_freq, n_steps, step_rate):
        self._sound_step(start_freq, end_freq, n_steps, step_rate, self.sine)

    def stepped_square(self, start_freq, end_freq, n_steps, step_rate):
        self._sound_step(start_freq, end_freq, n_steps, step_rate, self.square)

    def play_file(self, file_name):
        with open(file_name, 'rb') as f:
            freq      = int.from_bytes(f.read(4), 'little')
            bit_depth = int.from_bytes(f.read(1), 'little') # Currently ignored - treated as 8bit.
            wave_data = f.read()
        self._DAC.write_timed(wave_data, freq)

    # Support functions

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

    def _sound_step(self, start_freq, end_freq, n_steps, step_rate, func):
        freq_ratio = (end_freq/start_freq)**(1./(n_steps-1))
        self._freq = [int(start_freq * (freq_ratio**i)) for i in range(n_steps)]
        self._freq_ind = 0
        self._func = func
        self._timer.init(freq=step_rate)
        self._timer.callback(self._step_sound)

    def _step_sound(self, timer): # Timer callback to increment frequency during sweeped sounds.
        self._func(self._freq[self._freq_ind])
        self._freq_ind = (self._freq_ind+1) % len(self._freq)