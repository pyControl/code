from pyControl.hardware import Port
from devices.MCP import MCP23017


class Port_expander:
    # IO expander board which runs 8 behaviour ports from an MCP23017 i2c port expander.
    def __init__(self, port):
        assert port.I2C, "Port expander must be connected to port that supports I2C."
        self.mcp1 = MCP23017(port.I2C, port.DIO_C, 0x20, "Port_expander")
        self.mcp2 = MCP23017(port.I2C, None, 0x21, "Port_expander")
        self.port_1 = Port(
            DIO_A=self.mcp1.Pin("A0"),
            DIO_B=self.mcp1.Pin("A1"),
            POW_A=self.mcp2.Pin("A0"),
            POW_B=self.mcp2.Pin("A1"),
        )
        self.port_2 = Port(
            DIO_A=self.mcp1.Pin("A2"),
            DIO_B=self.mcp1.Pin("A3"),
            POW_A=self.mcp2.Pin("A2"),
            POW_B=self.mcp2.Pin("A3"),
        )
        self.port_3 = Port(
            DIO_A=self.mcp1.Pin("A4"),
            DIO_B=self.mcp1.Pin("A5"),
            POW_A=self.mcp2.Pin("A4"),
            POW_B=self.mcp2.Pin("A5"),
        )
        self.port_4 = Port(
            DIO_A=self.mcp1.Pin("A6"),
            DIO_B=self.mcp1.Pin("A7"),
            POW_A=self.mcp2.Pin("A6"),
            POW_B=self.mcp2.Pin("A7"),
        )
        self.port_5 = Port(
            DIO_A=self.mcp1.Pin("B0"),
            DIO_B=self.mcp1.Pin("B1"),
            POW_A=self.mcp2.Pin("B0"),
            POW_B=self.mcp2.Pin("B1"),
        )
        self.port_6 = Port(
            DIO_A=self.mcp1.Pin("B2"),
            DIO_B=self.mcp1.Pin("B3"),
            POW_A=self.mcp2.Pin("B2"),
            POW_B=self.mcp2.Pin("B3"),
        )
        self.port_7 = Port(
            DIO_A=self.mcp1.Pin("B4"),
            DIO_B=self.mcp1.Pin("B5"),
            POW_A=self.mcp2.Pin("B4"),
            POW_B=self.mcp2.Pin("B5"),
        )
        self.port_8 = Port(
            DIO_A=self.mcp1.Pin("B6"),
            DIO_B=self.mcp1.Pin("B7"),
            POW_A=self.mcp2.Pin("B6"),
            POW_B=self.mcp2.Pin("B7"),
        )
