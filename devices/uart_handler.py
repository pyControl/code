import sys
from pyControl.hardware import IO_object, assign_ID, interrupt_queue, fw, sm


class UART_handler(IO_object):
    """
    This class is used to generate a framework event when a UART message is received.
    """

    def __init__(self, event_name):
        major, minor, *_ = sys.implementation.version
        assert (major > 1) or (major == 1 and minor >= 26), "UART_handler requires MicroPython version >= 1.26"

        self.event_name = event_name
        assign_ID(self)

    def _initialise(self):
        self.event_ID = sm.events[self.event_name] if self.event_name in sm.events else False

    def ISR(self, _):
        if self.event_ID:
            self.timestamp = fw.current_time
            interrupt_queue.put(self.ID)

    def _process_interrupt(self):
        fw.event_queue.put(fw.Datatuple(self.timestamp, fw.EVENT_TYP, "i", self.event_ID))
