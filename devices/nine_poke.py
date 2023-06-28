from devices.poke import _Poke
from devices.MCP import MCP23017, MCP23008
from pyControl.hardware import Digital_output


class Nine_poke:
    # 9 IR beams, each with LED, controlled by MCP23017 i2c port expander.
    def __init__(
        self,
        port,
        rising_event_1="poke_1",
        falling_event_1="poke_1_out",
        rising_event_2="poke_2",
        falling_event_2="poke_2_out",
        rising_event_3="poke_3",
        falling_event_3="poke_3_out",
        rising_event_4="poke_4",
        falling_event_4="poke_4_out",
        rising_event_5="poke_5",
        falling_event_5="poke_5_out",
        rising_event_6="poke_6",
        falling_event_6="poke_6_out",
        rising_event_7="poke_7",
        falling_event_7="poke_7_out",
        rising_event_8="poke_8",
        falling_event_8="poke_8_out",
        rising_event_9="poke_9",
        falling_event_9="poke_9_out",
        debounce=5,
        solenoid_driver=True,
    ):
        self.mcp1 = MCP23017(port.I2C, port.DIO_C, 0x20, "Nine_poke")
        self.poke_1 = _Poke(self.mcp1.Pin("A0"), self.mcp1.Pin("B0"), rising_event_1, falling_event_1, debounce)
        self.poke_2 = _Poke(self.mcp1.Pin("A1"), self.mcp1.Pin("B1"), rising_event_2, falling_event_2, debounce)
        self.poke_3 = _Poke(self.mcp1.Pin("A2"), self.mcp1.Pin("B2"), rising_event_3, falling_event_3, debounce)
        self.poke_4 = _Poke(self.mcp1.Pin("A3"), self.mcp1.Pin("B3"), rising_event_4, falling_event_4, debounce)
        self.poke_5 = _Poke(self.mcp1.Pin("A4"), self.mcp1.Pin("B4"), rising_event_5, falling_event_5, debounce)
        self.poke_6 = _Poke(self.mcp1.Pin("A5"), self.mcp1.Pin("B5"), rising_event_6, falling_event_6, debounce)
        self.poke_7 = _Poke(self.mcp1.Pin("A6"), self.mcp1.Pin("B6"), rising_event_7, falling_event_7, debounce)
        self.poke_8 = _Poke(self.mcp1.Pin("A7"), port.POW_A, rising_event_8, falling_event_8, debounce)
        self.poke_9 = _Poke(self.mcp1.Pin("B7"), port.POW_B, rising_event_9, falling_event_9, debounce)
        if solenoid_driver:
            self.mcp2 = MCP23008(port.I2C, None, 0x21, "Nine_poke_solenoids")
            self.SOL_1 = Digital_output(self.mcp2.Pin("A0"))
            self.SOL_2 = Digital_output(self.mcp2.Pin("A1"))
            self.SOL_3 = Digital_output(self.mcp2.Pin("A2"))
            self.SOL_4 = Digital_output(self.mcp2.Pin("A3"))
            self.SOL_5 = Digital_output(self.mcp2.Pin("A4"))
            self.SOL_6 = Digital_output(self.mcp2.Pin("A5"))
            self.SOL_7 = Digital_output(self.mcp2.Pin("A6"))
            self.SOL_8 = Digital_output(self.mcp2.Pin("A7"))
