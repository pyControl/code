import os

# ----------------------------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------------------------

data_dir = os.path.join('..', 'data')  # Path to data storage folder 

transfer_dir = None                    # Folder to copy data files to at end of run.

# ----------------------------------------------------------------------------------------
# Hardware serial ports
# ----------------------------------------------------------------------------------------

board_serials={1:'COM1',  # Dictionary of board numbers with respective serial port addresses.
               2:'COM2'}    

# ----------------------------------------------------------------------------------------
# Other configuration options.
# ----------------------------------------------------------------------------------------

hardware_test = 'hardware_test'      # Script to use for hardware test.

hardware_test_display_output = False # Dispalay states and events during hw test.