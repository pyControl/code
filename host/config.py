import os

# ----------------------------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------------------------

pyControl_dir = os.path.join('..', 'pyControl') # Path to folder of pyControl framwork files.

examples_dir = os.path.join('..', 'examples')   # Path to folder of example scripts.

data_dir = os.path.join('..', 'data')   # Path to data storage folder

# ----------------------------------------------------------------------------------------
# Hardware serial ports
# ----------------------------------------------------------------------------------------

box_serials={1:'COM6',    #Dictionary of box numbers with respective serial port addresses.
             2:'COM7'}
             #3:'COM3',
             #4:'COM4'}

# box_unique_IDs = {1: b':\x00@\x00\x13Q332574',  # Dictionary of boxes unique hardware ID numbers 
#  				  2: b':\x00 \x00\x15Q332574',
#  				  3: b'E\x005\x00\x16Q332574',
#  				  4: b'K\x005\x00\x16Q332574'} 


