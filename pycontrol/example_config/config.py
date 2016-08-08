import os

# ----------------------------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------------------------

data_dir = os.path.join('.', 'data')  # Path to data storage folder
framework_dir = os.path.join('.', 'framework', 'pyControl')
tasks_dir = os.path.join('.', 'tasks')
config_dir = os.path.join('.', 'pycontrol', 'config')
hwd_path = os.path.join(config_dir, 'hardware_definition.py')

transfer_dir = None  # Folder to copy data files to at end of run.

# ----------------------------------------------------------------------------------------
# Hardware serial ports
# ----------------------------------------------------------------------------------------

box_serials = {
    1: 'COM1'
}  # Dictionary of box numbers with respective serial port addresses.

# ----------------------------------------------------------------------------------------
# Other configuration options.
# ----------------------------------------------------------------------------------------

hardware_test = 'hardware_test'  # Script to use for hardware test.

hardware_test_display_output = False  # Display states and events during hw test.
