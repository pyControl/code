import os
from pyControl.hardware import Digital_input, Digital_output, Analog_input, Rsync, off

_driver_files = [f.split('.')[0] for f in os.listdir('devices') if 'init' not in f]

for _driver_file in _driver_files:
    exec('from devices.{} import *'.format(_driver_file))