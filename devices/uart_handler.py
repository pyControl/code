from pyControl.hardware import IO_object, assign_ID, interrupt_queue, fw, sm


class UART_handler(IO_object):
    """
    This class is used to generate a framework event when a UART message is received.
    """

    def __init__(self, event_name, first_char_interrupt=True):
        self.event_name = event_name
        self.last_interrupt_time = 0
        self.first_char_interrupt = first_char_interrupt
        if self.first_char_interrupt:
            self.msg_starting = False
        assign_ID(self)

    def _initialise(self):
        self.event_ID = sm.events[self.event_name] if self.event_name in sm.events else False

    def ISR(self, _):
        if self.event_ID:
            # - pyboard v1.1 (and other STM32F4 boards): IRQ_RXIDLE interrupt is triggered after the first character
            #   AND at the end when the RX is idle.
            # - pyboard D-series board (STM32F7): IRQ_RXIDLE interrupt is triggered ONLY at the end when the RX is idle
            # - see Micropytyhon UART docs for more info: https://docs.micropython.org/en/latest/library/machine.UART.html
            if self.first_char_interrupt:
                self.msg_starting = not self.msg_starting
                if self.msg_starting:
                    # ignore the first interrupt after the message starts (when using pyboard v1.1)
                    return
            self.timestamp = fw.current_time
            interrupt_queue.put(self.ID)

    def _process_interrupt(self):
        fw.event_queue.put(fw.Datatuple(self.timestamp, fw.EVENT_TYP, "i", self.event_ID))
