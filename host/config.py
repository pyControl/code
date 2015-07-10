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

box_serials={1:'COM1',    #Dictionary of box numbers with respective serial port addresses.
             2:'COM2',
             3:'COM3',
             4:'COM4',
             5:'COM5',
             6:'COM6',
             7:'COM7',
             8:'COM8',
             9:'COM9',
             10:'COM10',
             11:'COM11',
             12:'COM12',
             13:'COM13',
             14:'COM14'}

box_unique_IDs = {1:  b'?\x00@\x00\x13Q332574',  # Dictionary of boxes unique hardware ID numbers 
                  2:  b'L\x005\x00\x16Q332574',
                  3:  b'7\x00 \x00\x15Q332574',
                  4:  b';\x00X\x00\x15Q332574',
                  5:  b'6\x005\x00\x16Q332574',
                  6:  b'8\x00@\x00\x13Q332574',
                  7:  b'G\x00@\x00\x13Q332574',
                  8:  b'H\x00 \x00\x15Q332574',
                  9:  b'V\x00>\x00\x13Q332574',
                  10: b'9\x005\x00\x16Q332574',
                  11: b':\x00@\x00\x13Q332574',
                  12: b':\x00 \x00\x15Q332574',
                  13: b'E\x005\x00\x16Q332574',
                  14: b'K\x005\x00\x16Q332574'}

