from devices._poke import _Poke

class Five_poke():
    # 5 IR beams, each with LED.
    def __init__(self, ports, rising_event_1='poke_1', falling_event_1='poke_1_out',
                              rising_event_2='poke_2', falling_event_2='poke_2_out', 
                              rising_event_3='poke_3', falling_event_3='poke_3_out', 
                              rising_event_4='poke_4', falling_event_4='poke_4_out',
                              rising_event_5='poke_5', falling_event_5='poke_5_out',
                              debounce = 5):
        port_1, port_2 = ports # ports argument must be list of two Ports objects.
        assert port_1.POW_C is not None, '! Five poke port_1 must have POW_C.'
        assert port_2.DIO_C is not None, '! Five poke port_2 must have DIO_C.'
        self.poke_1 = _Poke(port_1.DIO_A, port_1.POW_A, rising_event_1, falling_event_1, debounce)
        self.poke_2 = _Poke(port_1.DIO_B, port_1.POW_B, rising_event_2, falling_event_2, debounce)
        self.poke_3 = _Poke(port_2.DIO_A, port_1.POW_C, rising_event_3, falling_event_3, debounce)
        self.poke_4 = _Poke(port_2.DIO_B, port_2.POW_A, rising_event_4, falling_event_4, debounce)
        self.poke_5 = _Poke(port_2.DIO_C, port_2.POW_B, rising_event_5, falling_event_5, debounce)