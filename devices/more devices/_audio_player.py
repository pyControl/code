from machine import UART
from array import array
import pyb

class Dfplayer():

    def __init__(self, uart=1, timeout=1):
        self.uart = UART(uart, 9600)
        self.uart.init(9600, bits=8, parity=None, stop=1, timeout=timeout)
        self.cmd_bytes = array('B', [0x7E, 0xFF, 0x06, 0, 0, 0, 0, 0, 0, 0xEF])
        self.command(0x3F) # Initialisation.

    def command(self, cmd, param_1=0, param_2=0):
        self.cmd_bytes[3] = cmd
        self.cmd_bytes[5] = param_1
        self.cmd_bytes[6] = param_2
        self.cmd_bytes[7:9] = (-sum(self.cmd_bytes[1:7])).to_bytes(2,'big') # checksum
        self.uart.write(self.cmd_bytes)

    def play(self, folder_num, file_num):
        self.command(0x0F, folder_num, file_num)

    def stop(self):
        self.command(0x16)

    def set_volume(self, volume): # Between 1 - 30
        self.command(0x06, 0, volume)

class Audio_player(Dfplayer):

    def __init__(self, port):
        self._enable_L = pyb.Pin(port.POW_A, pyb.Pin.OUT)
        self._enable_R = pyb.Pin(port.POW_B, pyb.Pin.OUT)
        self.set_enabled(True, True)
        super().__init__(port.UART)

    def set_enabled(self, left=True, right=True):
        self._enable_L.value(bool(left))
        self._enable_R.value(bool(right))
