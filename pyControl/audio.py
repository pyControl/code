import pyb
import math

_dacs = (pyb.DAC(1), pyb.DAC(2)) # Digital to analog converters.
_timers = [pyb.Timer(1),pyb.Timer(2)] # Timers used to control pulsing etc.

_sine_len = 100 # Number of points in sine wave.
_sine_buf = bytearray([128+int(127*math.sin(2*math.pi*i/_sine_len)) for i in range(_sine_len)])

_sqr_buf = bytearray([255,0])

# Variables used for timer updated sounds.

_playing   = [False, False]
_func      = [None, None]
_freq      = [0, 0]
_freq_ind =  [0, 0]

#-----------------------------------------------------------------------------------
# User functions
#-----------------------------------------------------------------------------------

def off(chnl=None):
    # Stop sound playing, if no channel is specified stops both channels.
    if chnl is None:
        off(0)
        off(1)
    else:
        _dacs[chnl].write(127)
        _timers[chnl].deinit()
        _playing[chnl] = False

def sine(freq, chnl=0):
    # Play a sine wave tone at the specified frequency on the specified channel.
    _dacs[chnl].write_timed(_sine_buf, freq*_sine_len, mode=pyb.DAC.CIRCULAR)

def square(freq, chnl=0):
    # Play a square wave tone at the specified frequency on the specified channel.
    _dacs[chnl].write_timed(_sqr_buf, freq*2, mode=pyb.DAC.CIRCULAR)    

def pulsed_square(freq, pulse_rate, chnl = 0):
    _pulsed_sound(freq, pulse_rate, square, chnl)

def pulsed_sine(freq, pulse_rate, chnl = 0):
    _pulsed_sound(freq, pulse_rate, sine, chnl)

def sine_sweep(start_freq, end_freq, n_steps, step_rate, chnl = 0):
    _sound_sweep(start_freq, end_freq, n_steps, step_rate, sine, chnl)

def square_sweep(start_freq, end_freq, n_steps, step_rate, chnl = 0):
    _sound_sweep(start_freq, end_freq, n_steps, step_rate, square, chnl)

#-----------------------------------------------------------------------------------
# Support functions
#-----------------------------------------------------------------------------------

def _pulsed_sound(freq, pulse_rate, func, chnl):
    global _playing, _freq, _func
    _freq[chnl] = freq
    _func[chnl] = func
    _timers[chnl].init(freq=2*pulse_rate)
    _timers[chnl].callback(_toggle_sound)

def _toggle_sound(timer):
    global _playing
    chnl = int(timer is _timers[1])
    if _playing[chnl]:
        _dacs[chnl].write(127)
        _playing[chnl] = False
    else:
        _func[chnl](_freq[chnl], chnl)
        _playing[chnl] = True

def _sound_sweep(start_freq, end_freq, n_steps, step_rate, func, chnl):
    global _playing, _freq, _freq_ind 
    freq_ratio = (end_freq/start_freq)**(1./(n_steps-1))
    _freq[chnl] = [int(start_freq * (freq_ratio**i)) for i in range(n_steps)]
    _freq_ind[chnl] = 0
    _func[chnl] = func
    _timers[chnl].init(freq=step_rate)
    _timers[chnl].callback(_step_sound)

def _step_sound(timer):
    global _freq_ind
    chnl = int(timer is _timers[1])
    _func[chnl](_freq[chnl][_freq_ind[chnl]], chnl)
    _freq_ind[chnl] = (_freq_ind[chnl]+1) % len(_freq[chnl])






