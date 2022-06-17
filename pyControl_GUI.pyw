# Check that depndencies are installed then launch the pyControl GUI.

import sys
import logging

# Setup error logging.
logging.basicConfig(level=logging.ERROR, 
    handlers=[logging.FileHandler('ErrorLog.txt', delay=True)],
    format='%(asctime)s %(message)s')

# Check dependencies are installed.
try:
    import numpy
    import serial
    import pyqtgraph
except Exception as e:
    logging.error('  Unable to import dependencies:\n\n'+str(e)+'\n\n')
    sys.exit()

# Launch the GUI.
from gui.GUI_main import launch_GUI
launch_GUI()