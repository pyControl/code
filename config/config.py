import os

# ----------------------------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------------------------

#tasks_dir = 'path\\to\\tasks\\dir' # Uncomment to overwrite default tasks directory.
#data_dir  = 'path\\to\\data\\dir'  # Uncomment to overwrite default data directory.
transfer_dir = None                 # Folder to copy data files to at end of run.

# ----------------------------------------------------------------------------------------
# Hardware serial ports
# ----------------------------------------------------------------------------------------

board_serials={1:'COM1',  # Dictionary of board numbers with serial port addresses.
               2:'COM2'}    

# ----------------------------------------------------------------------------------------
# Other configuration options.
# ----------------------------------------------------------------------------------------

hardware_test = 'hardware_test'      # Script to use for run_experiments hardware test.

hardware_test_display_output = False # Dispalay states and events during hw test.