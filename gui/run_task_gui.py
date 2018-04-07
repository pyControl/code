import os
import sys
import time
import pyqtgraph as pg
import numpy as np
from pyqtgraph.Qt import QtGui, QtCore
from datetime import datetime
from serial import SerialException

# Add parent directory to path to allow imports.
top_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not top_dir in sys.path: sys.path.insert(0, top_dir)

from com.pycboard import Pycboard, PyboardError
from com.data_logger import Data_logger
from config.paths import data_dir, tasks_dir

# Configure pyqtgraph.
pg.setConfigOption('background', 'w') 
pg.setConfigOption('foreground', 'k')

# Run_task_gui ------------------------------------------------------------------------

app = QtGui.QApplication([])  # Start QT

## Create widgets.

class Run_task_gui(QtGui.QWidget):

    def __init__(self, parent=None):
        super(QtGui.QWidget, self).__init__(parent)
        self.setWindowTitle('pyControl run task GUI')

        # Variables.

        self.board = None  # Pycboard class instance.
        self.task = None   # Task currently uploaded on pyboard. 
        self.subject_ID = None
        self.sm_info = None # Information about uploaded state machine.
        self.update_interval = 50 # Time between updates (ms)

        # Create widgets.

        self.status_label = QtGui.QLabel("Status:")
        self.status_text = QtGui.QLineEdit('Not connected')
        self.status_text.setStyleSheet('background-color:rgb(210, 210, 210);')
        self.status_text.setReadOnly(True)
        self.port_label = QtGui.QLabel("Serial port:")
        self.port_text = QtGui.QLineEdit('com1')
        self.connect_button = QtGui.QPushButton('Connect')
        self.task_label = QtGui.QLabel("Task:")
        self.task_select = QtGui.QComboBox()
        self.upload_button = QtGui.QPushButton('Upload')
        self.data_dir_label = QtGui.QLabel("Data dir:")
        self.data_dir_text = QtGui.QLineEdit('Select directory')
        self.data_dir_button = QtGui.QPushButton('...')
        self.data_dir_button.setFixedWidth(30)
        self.subject_label = QtGui.QLabel("Subject ID:")
        self.subject_text = QtGui.QLineEdit(self.subject_ID)
        self.subject_text.setFixedWidth(80)
        self.subject_text.setMaxLength(12)
        self.start_button = QtGui.QPushButton('Start')
        self.stop_button = QtGui.QPushButton('Stop')
        self.log_text = QtGui.QTextEdit()
        self.log_text.setReadOnly(True)

        self.task_plot = Task_plotter()

        # Create layout

        self.vertical_layout     = QtGui.QVBoxLayout()
        self.horizontal_layout_1 = QtGui.QHBoxLayout()
        self.horizontal_layout_2 = QtGui.QHBoxLayout()

        self.horizontal_layout_1.addWidget(self.status_label)
        self.horizontal_layout_1.addWidget(self.status_text)
        self.horizontal_layout_1.addWidget(self.port_label)
        self.horizontal_layout_1.addWidget(self.port_text)
        self.port_text.setFixedWidth(70)
        self.horizontal_layout_1.addWidget(self.connect_button)
        self.horizontal_layout_1.addWidget(self.task_label)
        self.horizontal_layout_1.addWidget(self.task_select)
        self.horizontal_layout_1.addWidget(self.upload_button)
        self.horizontal_layout_2.addWidget(self.data_dir_label)
        self.horizontal_layout_2.addWidget(self.data_dir_text)
        self.horizontal_layout_2.addWidget(self.data_dir_button)
        self.horizontal_layout_2.addWidget(self.subject_label)
        self.horizontal_layout_2.addWidget(self.subject_text)
        self.horizontal_layout_2.addWidget(self.start_button)
        self.horizontal_layout_2.addWidget(self.stop_button)

        self.vertical_layout.addLayout(self.horizontal_layout_1)
        self.vertical_layout.addLayout(self.horizontal_layout_2)
        self.vertical_layout.addWidget(self.task_plot, 70)
        self.vertical_layout.addWidget(self.log_text , 30)

        self.setLayout(self.vertical_layout)

        # Connect widgets

        self.port_text.returnPressed.connect(self.connect)
        self.connect_button.clicked.connect(self.connect)
        self.upload_button.clicked.connect(self.upload_task)
        self.start_button.clicked.connect(self.start_task)
        self.stop_button.clicked.connect(self.stop_task)

        # Widget initial setup.

        self.get_tasks()     # Populate task select widget.
        self.not_connected() # Configure not connected state.

        # Create timers

        self.process_timer = QtCore.QTimer() # Timer to regularly call process_data() during run.        
        self.process_timer.timeout.connect(self.process_data)

    # Widget functions

    def get_tasks(self):
        # Set task select widget values.
        tasks =  [t.split('.')[0] for t in os.listdir(tasks_dir)
                  if t[-3:] == '.py']
        for task in tasks:
            self.task_select.addItem(task)

    def connect(self):
        try:
            self.status_text.setText('Connecting...')
            self.board = Pycboard(self.port_text.text())
            self.connect_button.setEnabled(False)
            self.port_text.setEnabled(False)
            self.task_select.setEnabled(True)
            self.upload_button.setEnabled(True)
            self.status_text.setText('Connected')
        except SerialException:
            self.status_text.setText('Connection failed')

    def upload_task(self):
        try:
            task = self.task_select.currentText()
            self.status_text.setText('Uploading..')
            self.sm_info = self.board.setup_state_machine(task)
            self.data_logger = Data_logger(data_dir, 'run_task', task, self.sm_info)
            self.task_plot.set_state_machine(self.sm_info)
            self.start_button.setEnabled(True)
            self.status_text.setText('Uploaded : ' + task)
            self.task = task
        except PyboardError as e:
            print(e)
            self.status_text.setText('Upload failed.')

    def not_connected(self):
        # Configure buttons for not connected state.
        self.task_select.setEnabled(False)
        self.upload_button.setEnabled(False)
        self.data_dir_text.setEnabled(False)
        self.data_dir_button.setEnabled(False)
        self.subject_text.setEnabled(False)
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(False)

    def start_task(self):
        self.board.start_framework()
        self.task_plot.run_start()
        self.start_button.setEnabled(False)
        self.task_select.setEnabled(False)
        self.upload_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.log_text.insertPlainText(
            '\nRun started at: {}\n\n'.format(
            datetime.now().strftime('%Y/%m/%d %H:%M:%S')))
        self.process_timer.start(self.update_interval)
        self.status_text.setText('Running: ' + self.task)

    def stop_task(self):
        self.board.stop_framework()
        self.start_button.setEnabled(True)
        self.task_select.setEnabled(True)
        self.upload_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.process_timer.stop()
        QtCore.QTimer.singleShot(100, self.process_data) # Catch output after framework stops.
        self.status_text.setText('Uploaded : ' + self.task)

    # Update functions called while task running.

    def process_data(self):
        # Called regularly during run to process data from board.
        new_data = self.board.process_data()
        self.task_plot.process_data(new_data)
        if new_data:
            self.log_text.insertPlainText(
                self.data_logger.data_to_string(new_data, verbose=True))
            self.log_text.moveCursor(QtGui.QTextCursor.End)

    # Cleanup.

    def closeEvent(self, event):
        # Called when GUI window is closed.
        if self.board: self.board.close()
        event.accept()

# Task_plotter -----------------------------------------------------------------------

class Task_plotter(QtGui.QWidget):
    ''' Widget for plotting the states, events and analog inputs output by a state machine.'''

    def __init__(self, parent=None):
        super(QtGui.QWidget, self).__init__(parent)

        # Create widgets

        self.state_axis = pg.PlotWidget(title="States")
        self.event_axis = pg.PlotWidget(title="Events", 
                                        labels={'bottom':'Time (seconds)'})
        self.analog_axis = pg.PlotWidget(title="Analog")

        # Setup plots

        self.state_plot = self.state_axis.plot(pen=pg.mkPen('k', width=3))
        self.event_plot = self.event_axis.plot(pen=None, symbol='o', symbolSize=4, symbolPen=None)
        self.event_axis.setXLink(self.state_axis)

        # create layout

        self.vertical_layout = QtGui.QVBoxLayout()
        self.vertical_layout.addWidget(self.state_axis)
        self.vertical_layout.addWidget(self.event_axis)
        self.vertical_layout.addWidget(self.analog_axis)
        self.analog_axis.setVisible(False)

        self.setLayout(self.vertical_layout)

    def set_state_machine(self, sm_info):
        self.events = sm_info['events'] # dict {event_name: ID}
        self.states = sm_info['states'] # dict {state_name: ID}
        self.analog_inputs = sm_info['analog_inputs']
        if self.states:
            self.state_axis.getAxis('left').setTicks([[(i, n) for (n, i) in self.states.items()]])
            self.state_axis.setYRange(min(self.states.values()), max(self.states.values()), padding=0.2)
            self.state_data = expanding_data_array()
        if self.events:
            self.event_axis.getAxis('left').setTicks([[(i, n) for (n, i) in self.events.items()]])
            self.event_axis.setYRange(min(self.events.values()), max(self.events.values()), padding=0.2)
            self.event_data = expanding_data_array()
        if self.analog_inputs:
            self.analog_axis.setVisible(True)

    def run_start(self):
        self.start_time = time.time()
        self.current_state = None

    def process_data(self, new_data):
        run_time = time.time() - self.start_time
        self.state_axis.setRange(xRange=[run_time-10, run_time])
        # Plot new states or events.
        for nd in new_data:
            if nd[0] == 'D': # State entry or event.
                if nd[2] in self.states.values(): # State entry.
                    self.current_state = nd[2]
                    self.state_data.put(nd[1], nd[2]) # New state entry.
                    self.state_data.put(nd[1], nd[2]) # New state exit, overwritten each update.
                else: # Event
                    self.event_data.put(nd[1], nd[2])
                    self.event_plot.setData(*self.event_data.get())
        # Extend current state line.
        self.state_data.put(int(run_time*1000), self.current_state, replace=True)
        self.state_plot.setData(*self.state_data.get(), connect='pairs')

class expanding_data_array():

    def __init__(self, dtype=int):
        self.dtype = dtype
        self.data = np.empty([1000,2], dtype)
        self.i = 0
        self.len = self.data.shape[0]

    def put(self,timestamp, ID, replace=False):
        # Put new data into array expanding if necessary,
        if replace: # Replace previous sample.
            self.i -= 1
        self.data[self.i,:] = (timestamp, ID)
        self.i += 1
        if self.i >= self.len: # Double array size.
            temp = self.data
            self.data = np.empty([self.len*2,2], self.dtype)
            self.data[:self.len] = temp
            self.len =self.len*2

    def get(self, seconds_timestamps=True):
        # Get all valid data from array
        if seconds_timestamps: # Convert timestamps to seconds.
            return (self.data[:self.i,0]/1000, self.data[:self.i,1])
        else:
            return (self.data[:self.i,0], self.data[:self.i,1])


# Start GUI.

if __name__ == '__main__':
    run_task_gui = Run_task_gui()
    run_task_gui.show() 
    app.exec_()
