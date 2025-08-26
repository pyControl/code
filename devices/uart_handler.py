from pyControl.hardware import IO_object, assign_ID, interrupt_queue, fw, sm


class UART_handler(IO_object):
    """
    This class is used to generate a framework event when a UART message is received.
    """

    def __init__(self, event_name, mcu="STM32_F4"):
        self.event_name = event_name
        self.last_interrupt_time = 0
        self.mcu = mcu
        if self.mcu == "STM32_F4":
            self.accept_interrupt = True
        assign_ID(self)

    def _initialise(self):
        self.event_ID = sm.events[self.event_name] if self.event_name in sm.events else False

    def ISR(self, _):
        if self.event_ID:
            # - pyboard v1.1 (and other STM32F4 boards): IRQ_RXIDLE interrupt is triggered after the first character
            #   AND at the end when the RX is idle.
            # - pyboard D-series board (STM32F7): IRQ_RXIDLE interrupt is triggered ONLY at the end when the RX is idle
            # - see Micropytyhon UART docs for more info: https://docs.micropython.org/en/latest/library/machine.UART.html
            if self.mcu == "STM32_F4":  # respond to every other interrupt when using pyboard v1.1
                if self.accept_interrupt:
                    self.timestamp = fw.current_time
                    interrupt_queue.put(self.ID)
                self.accept_interrupt = not self.accept_interrupt
            elif self.mcu == "STM32_F7":  # respond to every interrupt when using pyboard D-series
                self.timestamp = fw.current_time
                interrupt_queue.put(self.ID)

    def _process_interrupt(self):
        fw.event_queue.put(fw.Datatuple(self.timestamp, fw.EVENT_TYP, "i", self.event_ID))
