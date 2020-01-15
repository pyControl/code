# Check that depndencies are installed then launch the pyControl GUI.

import sys
import os

# Check dependencies are installed.
try:
    import numpy
    import serial
    import pyqtgraph
except Exception as e:
    print('Unable to import dependencies:\n\n'+str(e))
    input('\nPress enter to close.')
    sys.exit()

# Launch the GUI.
from gui.GUI_main import launch_GUI
launch_GUI()