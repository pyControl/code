# pyControl driver for NAU7802 load cell amplifier.
# Adapted from https://github.com/longapalooza/nau7802py

import time
from machine import I2C, SoftI2C

ADDR = 0x2A  # I2C address of NAU7802

# NAU7802 register addresses
REGISTER_ADDR = {
    "PU_CTRL": 0x00,
    "CTRL1": 1,
    "CTRL2": 2,
    "ADCO_B2": 18,
    "ADC": 0x15,
    "PGA_PWR": 0x1C,
}

# Bits in the PU_CRTL register
PU_CTRL_BITS = {
    "PU_CTRL_RR": 0,
    "PU_CTRL_PUD": 1,
    "PU_CTRL_PUA": 2,
    "PU_CTRL_PUR": 3,
    "PU_CTRL_CS": 4,
    "PU_CTRL_CR": 5,
    "PU_CTRL_OSCS": 6,
    "PU_CTRL_AVDDS": 7,
}


# Bits in the CTRL1 register
CTRL1_BITS = {
    "CTRL1_GAIN": 2,
    "CTRL1_VLDO": 5,
    "CTRL1_DRDY_SEL": 6,
    "CTRL1_CRP": 7,
}


# Bits to set LDO values
LDO_BITS = {
    2.4: 0b111,
    2.7: 0b110,
    3.0: 0b101,
    3.3: 0b100,
    3.6: 0b011,
    3.9: 0b010,
    4.2: 0b001,
    4.5: 0b000,
}

# Allowed gains
GAIN_BITS = {
    128: 0b111,
    64: 0b110,
    32: 0b101,
    16: 0b100,
    8: 0b011,
    4: 0b010,
    2: 0b001,
    1: 0b000,
}

# Allowed samples per second
SAMPLE_RATE_BITS = {
    320: 0b111,
    80: 0b011,
    40: 0b010,
    20: 0b001,
    10: 0b000,
}


class Load_cell:
    # pyControl device for measuring a load cell using the NAU782 amplifier.

    def __init__(self, port, offset=0, scale=1):
        if port.I2C:
            self.i2c = I2C(port.I2C, freq=100000)
        else:
            self.i2c = SoftI2C(scl=port.DIO_A, sda=port.DIO_B, freq=100000)
        self.OFFSET = offset  # weight = slope * (DAC_value - offset)
        self.SCALE = scale
        # Initialise
        self.reset()  # Reset all registers
        self.power_up()  # Power on analog and digital sections of the scale
        self.set_LDO_voltage(4.5)  # Set LDO to 4.5V
        self.set_gain(128)  # Set gain to 128
        self.set_sample_rate(80)  # Set samples per second to 80
        self.set_register(REGISTER_ADDR["ADC"], 0x30)  # Turn off CLK_CHP. From 9.1 power on sequencing.
        self.set_bit(7, REGISTER_ADDR["PGA_PWR"])  # Enable decoupling cap on chan 2.

    # User functions.

    def weigh(self, times=1):
        return (self.read_average(times) - self.OFFSET) / self.SCALE

    def read(self):
        value_bytes = self.i2c.readfrom_mem(ADDR, REGISTER_ADDR["ADCO_B2"], 3)
        value = int.from_bytes(value_bytes, "big")
        if value > 0x7FFFFF:  # Handle negative values given conversion to unsigned int.
            value -= 0x1000000
        return value

    def read_average(self, times=3):
        sum = 0
        for i in range(times):
            sum += self.read()
        return sum / times

    def tare(self, times=15):
        # Set the 0 value.
        self.OFFSET = self.read_average(times)

    def calibrate(self, weight=1, times=15):
        # Calibrate the scale using a known weight, must be done after scale has beenn tared.
        self.SCALE = (self.read_average(times) - self.OFFSET) / weight

    def available(self):
        # Returns true if Cycle Ready bit is set (conversion is complete)
        return self.get_bit(PU_CTRL_BITS["PU_CTRL_CR"], REGISTER_ADDR["PU_CTRL"])

    # Configuration functions.

    def reset(self):
        # Resets all registers to Power Of Defaults
        self.set_bit(PU_CTRL_BITS["PU_CTRL_RR"], REGISTER_ADDR["PU_CTRL"])  # Set RR
        time.sleep(0.001)
        self.clear_bit(PU_CTRL_BITS["PU_CTRL_RR"], REGISTER_ADDR["PU_CTRL"])  # Clear RR to leave reset state

    def power_up(self):  # Power up digital and analog sections of scale, ~2mA
        self.set_bit(PU_CTRL_BITS["PU_CTRL_PUD"], REGISTER_ADDR["PU_CTRL"])
        self.set_bit(PU_CTRL_BITS["PU_CTRL_PUA"], REGISTER_ADDR["PU_CTRL"])
        time.sleep(0.001)

    def set_gain(self, gain):
        # Set the gain.
        assert gain in GAIN_BITS.keys(), "Invalid gain value"
        value = self.get_register(REGISTER_ADDR["CTRL1"])
        value &= 0b11111000  # Clear gain bits
        value |= GAIN_BITS[gain]  # Mask in new bits
        self.set_register(REGISTER_ADDR["CTRL1"], value)

    def set_LDO_voltage(self, voltage):
        # Set the onboard LDO voltage regulator to a given value.
        assert voltage in LDO_BITS.keys(), "Invalid LDO value"
        value = self.get_register(REGISTER_ADDR["CTRL1"])
        value &= 0b11000111  # Clear LDO bits
        value |= LDO_BITS[voltage] << 3  # Mask in new LDO bits
        self.set_register(REGISTER_ADDR["CTRL1"], value)
        self.set_bit(PU_CTRL_BITS["PU_CTRL_AVDDS"], REGISTER_ADDR["PU_CTRL"])  # Enable the internal LDO

    def set_sample_rate(self, rate):
        # Set the readings per second.
        self.sample_rate = rate
        assert rate in SAMPLE_RATE_BITS.keys(), "Invalid sample rate."
        value = self.get_register(REGISTER_ADDR["CTRL2"])
        value &= 0b10001111  # Clear CRS bits
        value |= SAMPLE_RATE_BITS[rate] << 4  # Mask in new CRS bits
        self.set_register(REGISTER_ADDR["CTRL2"], value)

    # I2C read/write operations.

    def set_register(self, register_address, value):
        self.i2c.writeto_mem(ADDR, register_address, value.to_bytes(2, "little"))

    def get_register(self, register_address):
        # Get contents of a register
        return self.i2c.readfrom_mem(ADDR, register_address, 1)[0]

    def clear_bit(self, bit, register_address):
        # Set specified bit in register to 0.
        value = self.get_register(register_address) & ~(1 << bit)
        self.set_register(register_address, value)

    def set_bit(self, bit, register_address):
        # Set specified bit in register to 1.
        value = self.get_register(register_address) | (1 << bit)
        return self.set_register(register_address, value)

    def get_bit(self, bit, register_address):
        # Return value of a given bit within a register.
        return bool(self.get_register(register_address) >> bit & 1)
