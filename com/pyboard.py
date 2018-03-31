#!/usr/bin/env python

"""
pyboard interface
This module provides the Pyboard class, used to communicate with and
control the pyboard over a serial USB connection.
Example usage:
    import pyboard
    pyb = pyboard.Pyboard('/dev/ttyACM0')
    pyb.enter_raw_repl()
    pyb.exec('pyb.LED(1).on()')
    pyb.exit_raw_repl()
To run a script from the local machine on the board and print out the results:
    import pyboard
    pyboard.execfile('test.py', device='/dev/ttyACM0')
This script can also be run directly.  To execute a local script, use:
    ./pyboard.py test.py
Or:
    python pyboard.py test.py
"""

import sys
import time
import serial

def stdout_write_bytes(b):
    sys.stdout.buffer.write(b)
    sys.stdout.buffer.flush()

class PyboardError(BaseException):
    pass

class Pyboard:
    def __init__(self, serial_device, baudrate=115200):
        self.serial = serial.Serial(serial_device, baudrate=baudrate, interCharTimeout=1)

    def close(self):
        self.serial.close()

    def read_until(self, min_num_bytes, ending, timeout=10, data_consumer=None):
        data = self.serial.read(min_num_bytes)
        if data_consumer:
            data_consumer(data)
        timeout_count = 0
        while True:
            if data.endswith(ending):
                break
            elif self.serial.inWaiting() > 0:
                new_data = self.serial.read(1)
                data = data + new_data
                if data_consumer:
                    data_consumer(new_data)
                #time.sleep(0.01)
                timeout_count = 0
            else:
                timeout_count += 1
                if timeout is not None and timeout_count >= 10 * timeout:
                    break
                time.sleep(0.1)
        return data

    def enter_raw_repl(self):
        self.serial.write(b'\r\x03\x03') # ctrl-C twice: interrupt any running program
        # flush input (without relying on serial.flushInput())
        n = self.serial.inWaiting()
        while n > 0:
            self.serial.read(n)
            n = self.serial.inWaiting()
        self.serial.write(b'\r\x01') # ctrl-A: enter raw REPL
        data = self.read_until(1, b'to exit\r\n>')
        if not data.endswith(b'raw REPL; CTRL-B to exit\r\n>'):
            print(data)
            raise PyboardError('could not enter raw repl')
        self.serial.write(b'\x04') # ctrl-D: soft reset
        data = self.read_until(1, b'to exit\r\n>')
        if not data.endswith(b'raw REPL; CTRL-B to exit\r\n>'):
            print(data)
            raise PyboardError('could not enter raw repl')

    def exit_raw_repl(self):
        self.serial.write(b'\r\x02') # ctrl-B: enter friendly REPL

    def follow(self, timeout, data_consumer=None):
        # wait for normal output
        data = self.read_until(1, b'\x04', timeout=timeout, data_consumer=data_consumer)
        if not data.endswith(b'\x04'):
            raise PyboardError('timeout waiting for first EOF reception')
        data = data[:-1]

        # wait for error output
        data_err = self.read_until(2, b'\x04>', timeout=timeout)
        if not data_err.endswith(b'\x04>'):
            raise PyboardError('timeout waiting for second EOF reception')
        data_err = data_err[:-2]

        # return normal and error output
        return data, data_err

    def exec_raw_no_follow(self, command):
        if isinstance(command, bytes):
            command_bytes = command
        else:
            command_bytes = bytes(command, encoding='utf8')

        # write command
        for i in range(0, len(command_bytes), 256):
            self.serial.write(command_bytes[i:min(i + 256, len(command_bytes))])
            time.sleep(0.01)
        self.serial.write(b'\x04')

        # check if we could exec command
        data = self.serial.read(2)
        if data != b'OK':
            raise PyboardError('could not exec command')

    def exec_raw(self, command, timeout=10, data_consumer=None):
        self.exec_raw_no_follow(command);
        return self.follow(timeout, data_consumer)

    def eval(self, expression):
        ret = self.exec('print({})'.format(expression))
        ret = ret.strip()
        return ret

    def exec(self, command):
        ret, ret_err = self.exec_raw(command)
        if ret_err:
            raise PyboardError('exception', ret, ret_err)
        return ret

    def execfile(self, filename):
        with open(filename, 'rb') as f:
            pyfile = f.read()
        return self.exec(pyfile)

    def get_time(self):
        t = str(self.eval('pyb.RTC().datetime()'), encoding='utf8')[1:-1].split(', ')
        return int(t[4]) * 3600 + int(t[5]) * 60 + int(t[6])

def execfile(filename, device='/dev/ttyACM0'):
    pyb = Pyboard(device)
    pyb.enter_raw_repl()
    output = pyb.execfile(filename)
    stdout_write_bytes(output)
    pyb.exit_raw_repl()
    pyb.close()