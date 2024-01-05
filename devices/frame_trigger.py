import pyb
import pyControl.hardware as hw
import pyControl.utility as ut


class Frame_trigger(hw.IO_object):
    def __init__(self, pin, pulse_rate, name="frame_trigger"):
        self.timer = pyb.Timer(hw.available_timers.pop())
        self.pin = pyb.Pin(pin, mode=pyb.Pin.OUT, value=0)
        self.name = name
        self.pulse_rate = pulse_rate
        self.analog_channel = hw.Analog_channel(name, pulse_rate, data_type="I", plot=False)
        hw.assign_ID(self)

    def _run_start(self):
        self.pulse_n = 0
        self.pinstate = False
        self.pin.value(False)
        self.timer.init(freq=2 * self.pulse_rate)  # Set timer to trigger subsequent pulses.
        self.timer.callback(self.ISR)
        ut.print("{} outputting pulses at {}Hz".format(self.name, self.pulse_rate))

    def _run_stop(self):
        self.pin.value(False)
        self.timer.deinit()

    def ISR(self, t):
        self.pinstate = not self.pinstate
        self.pin.value(self.pinstate)
        if self.pinstate:
            self.pulse_n += 1
            self.analog_channel.put(self.pulse_n)
