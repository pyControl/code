import pyb
import pyControl.framework as fw
import pyControl.hardware as hw
import pyControl.state_machine as sm


class Frame_logger(hw.IO_object):
    def __init__(self, pin, rising_event=None, decimate=False, pull=None):
        # Record the times of camara frames or other high frequency digital
        # input pulses to the data file.  Events generated are saved to the
        # data file but not otherwise processed by the state machine.
        # Arguments:
        # pin           - micropython pin to use
        # rising_event  - Name of event that will be recorded in the log.
        # decimate      - set to n to only generate one event every n pulses.
        # pull          - used to enable internal pullup or pulldown resitors.
        if pull is None:
            pull = pyb.Pin.PULL_NONE
        elif pull == "up":
            pull = pyb.Pin.PULL_UP
        elif pull == "down":
            pull = pyb.Pin.PULL_DOWN
        self.pull = pull
        self.pin = pyb.Pin(pin, pyb.Pin.IN, pull=pull)
        self.rising_event = rising_event
        self.decimate = decimate
        hw.assign_ID(self)

    def _initialise(self):
        # Set event codes for rising and falling events, configure interrupts.
        self.rising_event_ID = sm.events[self.rising_event] if self.rising_event in sm.events else False
        if self.rising_event_ID:  # Setup interrupts.
            pyb.ExtInt(self.pin, pyb.ExtInt.IRQ_RISING, self.pull, self._ISR)

    def _run_start(self):
        if self.decimate:
            self.decimate_counter = -1
        self.interrupt_timestamp = 0

    def _ISR(self, line):
        if self.decimate:
            self.decimate_counter = (self.decimate_counter + 1) % self.decimate
            if not self.decimate_counter == 0:
                return  # ignore input due to decimation.
        self.interrupt_timestamp = fw.current_time
        hw.interrupt_queue.put(self.ID)

    def _process_interrupt(self):
        fw.data_output_queue.put(fw.Datatuple(self.interrupt_timestamp, fw.EVENT_TYP, "s", self.rising_event_ID))
