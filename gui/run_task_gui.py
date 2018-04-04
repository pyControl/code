import os
import sys
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
from datetime import datetime
from serial import SerialException

# Add parent directory to path to allow imports.
top_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not top_dir in sys.path: sys.path.insert(0, top_dir)

from com.pycboard import Pycboard, PyboardError
from com.data_logger import Data_logger
from config.paths import data_dir, tasks_dir

# GUI ----------------------------------------------------------------------------------

app = QtGui.QApplication([])  # Start QT

## Create widgets.

class Run_task_gui(QtGui.QWidget):

    def __init__(self, parent=None):
        super(QtGui.QWidget, self).__init__(parent)
        self.setWindowTitle('pyControl run task GUI')

        # Variables.

        self.port  = 'com1'# Serial port address for pyboard
        self.board = None  # Pycboard class instance.
        self.subject_ID = None
        self.sm_info = None # Information about uploaded state machine.

        # Create widgets.

        self.status_label = QtGui.QLabel("Status:")
        self.status_text = QtGui.QLineEdit('Not connected')
        self.status_text.setStyleSheet('background-color:rgb(210, 210, 210);')
        self.status_text.setReadOnly(True)
        self.port_label = QtGui.QLabel("Serial port:")
        self.port_text = QtGui.QLineEdit(self.port)
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
        self.vertical_layout.addWidget(self.log_text)

        self.setLayout(self.vertical_layout)

        # Connect widgets

        self.port_text.textChanged.connect(self.port_change)
        self.port_text.returnPressed.connect(self.connect)
        self.connect_button.clicked.connect(self.connect)
        self.task_select.activated[str].connect(self.select_task)
        self.upload_button.clicked.connect(self.upload_task)
        self.start_button.clicked.connect(self.start_task)
        self.stop_button.clicked.connect(self.stop_task)

        # Setup widgets

        self.get_tasks()     # Populate task select widget.
        self.not_connected() # Configure not connected state.

        # Create timers

        self.process_timer = QtCore.QTimer() # Timer to regularly call process_data() during run.        
        self.process_timer.timeout.connect(self.process_data)

    # Widget functions

    def get_tasks(self):
        # Return list of task names in tasks folder.
        tasks =  [t.split('.')[0] for t in os.listdir(tasks_dir)
                  if t[-3:] == '.py']
        for task in tasks:
            self.task_select.addItem(task)
        self.task = tasks[0]

    def quit_func(self):
        # Called when window closed.
        if self.board: self.board.close()

    def port_change(self, text):
        self.port = text

    def select_task(self, task):
        self.task = task

    def connect(self):
        try:
            self.status_text.setText('Connecting...')
            self.board = Pycboard(self.port)
            self.connect_button.setEnabled(False)
            self.port_text.setEnabled(False)
            self.task_select.setEnabled(True)
            self.upload_button.setEnabled(True)
            self.status_text.setText('Connected')
        except SerialException:
            self.status_text.setText('Connection failed')

    def upload_task(self):
        try:
            self.status_text.setText('Uploading..')
            self.sm_info = self.board.setup_state_machine(self.task)
            self.data_logger = Data_logger(data_dir, 'run_task', self.task, self.sm_info)
            self.status_text.setText(self.task)
            self.start_button.setEnabled(True)
            self.status_text.setText('Uploaded : ' + self.task)
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
        self.start_button.setEnabled(False)
        self.task_select.setEnabled(False)
        self.upload_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.log_text.insertPlainText(
            '\nRun started at: {}\n\n'.format(
            datetime.now().strftime('%Y/%m/%d %H:%M:%S')))
        self.process_timer.start(50)
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

    # Running task timer function.

    def process_data(self):
        # Called regularly during run to process data from board.
        new_data = self.board.process_data()
        if new_data:
            self.log_text.insertPlainText(
                self.data_logger.data_to_string(new_data, verbose=True))
            self.log_text.moveCursor(QtGui.QTextCursor.End)

# Start App.

run_task_gui = Run_task_gui()
app.aboutToQuit.connect(run_task_gui.quit_func)

run_task_gui.show() 
app.exec_()