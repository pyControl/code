from pyb import UART
from time import sleep


class uRFID:
    # Class for using the Priority 1 Design Micro RFID module to read FDX-B tags.
    # http://www.priority1design.com.au/rfid_reader_modules.html

    def __init__(self, port):
        self.uart = UART(port.UART)
        self.uart.init(baudrate=9600, bits=8, parity=None, stop=1, timeout=1)
        self.uart.write(b"ST2\r")  # Put reader in FDX-B tag mode.
        sleep(0.01)
        self.uart.read()  # Clear input buffer.

    def read_tag(self):
        # Return the ID of the most recent tag read, if no tag has been read return None.
        read_bytes = self.uart.read()
        if not read_bytes:
            return
        try:
            ID = int(read_bytes[-13:-1])
            return ID
        except ValueError:
            return
