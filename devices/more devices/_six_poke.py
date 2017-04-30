from devices._poke import _Poke

class Six_poke():
    # 6 IR beams, each with LED.
    def __init__(self, ports, rising_event_1 = None, falling_event_1 = None,
                              rising_event_2 = None, falling_event_2 = None, 
                              rising_event_3 = None, falling_event_3 = None, 
                              rising_event_4 = None, falling_event_4 = None,
                              rising_event_5 = None, falling_event_5 = None,
                              rising_event_6 = None, falling_event_6 = None,
                              debounce = 5):
        port_1, port_2, port_3 = ports # ports argument must be list of two Ports objects.
        self.poke_1 = _Poke(port_1.DIO_A, port_1.POW_A, rising_event_1, falling_event_1, debounce)
        self.poke_2 = _Poke(port_1.DIO_B, port_1.POW_B, rising_event_2, falling_event_2, debounce)
        self.poke_3 = _Poke(port_2.DIO_A, port_2.POW_A, rising_event_3, falling_event_3, debounce)
        self.poke_4 = _Poke(port_2.DIO_B, port_2.POW_B, rising_event_4, falling_event_4, debounce)
        self.poke_5 = _Poke(port_3.DIO_A, port_3.POW_A, rising_event_5, falling_event_5, debounce)
        self.poke_6 = _Poke(port_3.DIO_B, port_3.POW_B, rising_event_6, falling_event_6, debounce)