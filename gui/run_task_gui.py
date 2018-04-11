import os
import sys
from pyqtgraph.Qt import QtGui, QtCore
from datetime import datetime
from serial import SerialException
from serial.tools import list_ports

# Add parent directory to path to allow imports.
top_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not top_dir in sys.path: sys.path.insert(0, top_dir)

from com.pycboard import Pycboard, PyboardError
from com.data_logger import Data_logger
from config.paths import data_dir, tasks_dir

from gui.dialogs import Board_config_dialog, Variables_dialog
from gui.plotting import Task_plotter

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
        self.update_interval = 20 # Time between updates (ms)
        self.subject_ID = None
        self.status = {'connected': False}

        # Create widgets.

        self.status_label = QtGui.QLabel('Status:')
        self.status_text = QtGui.QLineEdit('Not connected')
        self.status_text.setStyleSheet('background-color:rgb(210, 210, 210);')
        self.status_text.setReadOnly(True)
        self.refresh_button = QtGui.QPushButton('Refresh')
        self.port_label = QtGui.QLabel('Serial port:')
        self.port_select = QtGui.QComboBox()
        self.port_select.setEditable(True)
        self.port_select.setFixedWidth(80)
        self.connect_button = QtGui.QPushButton('Connect')
        self.config_button = QtGui.QPushButton('Config')
        self.task_label = QtGui.QLabel('Task:')
        self.task_select = QtGui.QComboBox()
        self.upload_button = QtGui.QPushButton('Upload')
        self.variables_button = QtGui.QPushButton('Variables')
        self.data_dir_label = QtGui.QLabel('Data dir:')
        self.data_dir_text = QtGui.QLineEdit(data_dir)
        self.data_dir_button = QtGui.QPushButton('...')
        self.data_dir_button.setFixedWidth(30)
        self.subject_label = QtGui.QLabel('Subject ID:')
        self.subject_text = QtGui.QLineEdit(self.subject_ID)
        self.subject_text.setFixedWidth(80)
        self.subject_text.setMaxLength(12)
        self.start_button = QtGui.QPushButton('Start')
        self.stop_button = QtGui.QPushButton('Stop')
        self.log_text = QtGui.QTextEdit()
        self.log_text.setFont(QtGui.QFont('Courier', 9))
        self.log_text.setReadOnly(True)

        self.task_plot = Task_plotter()

        # Create layout

        self.vertical_layout     = QtGui.QVBoxLayout()
        self.horizontal_layout_1 = QtGui.QHBoxLayout()
        self.horizontal_layout_2 = QtGui.QHBoxLayout()
        self.horizontal_layout_3 = QtGui.QHBoxLayout()

        self.horizontal_layout_1.addWidget(self.status_label)
        self.horizontal_layout_1.addWidget(self.status_text)
        self.horizontal_layout_1.addWidget(self.refresh_button)
        self.horizontal_layout_1.addWidget(self.port_label)
        self.horizontal_layout_1.addWidget(self.port_select)
        self.horizontal_layout_1.addWidget(self.connect_button)
        self.horizontal_layout_1.addWidget(self.config_button)
        self.horizontal_layout_2.addWidget(self.task_label)
        self.horizontal_layout_2.addWidget(self.task_select)
        self.horizontal_layout_2.addWidget(self.upload_button)
        self.horizontal_layout_2.addWidget(self.variables_button)
        self.horizontal_layout_2.addStretch()
        self.horizontal_layout_3.addWidget(self.data_dir_label)
        self.horizontal_layout_3.addWidget(self.data_dir_text)
        self.horizontal_layout_3.addWidget(self.data_dir_button)
        self.horizontal_layout_3.addWidget(self.subject_label)
        self.horizontal_layout_3.addWidget(self.subject_text)
        self.horizontal_layout_3.addWidget(self.start_button)
        self.horizontal_layout_3.addWidget(self.stop_button)

        self.vertical_layout.addLayout(self.horizontal_layout_1)
        self.vertical_layout.addLayout(self.horizontal_layout_2)
        self.vertical_layout.addLayout(self.horizontal_layout_3)
        self.vertical_layout.addWidget(self.log_text , 20)
        self.vertical_layout.addWidget(self.task_plot, 80)

        self.setLayout(self.vertical_layout)

        # Create dialogs.

        self.config_dialog = Board_config_dialog(parent=self)

        # Connect widgets

        self.refresh_button.clicked.connect(self.refresh)
        self.connect_button.clicked.connect(self.connect_disconnect)
        self.config_button.clicked.connect(lambda x: self.config_dialog.exec_())
        self.upload_button.clicked.connect(self.upload_task)
        self.variables_button.clicked.connect(lambda x: self.variables_dialog.exec_())
        self.data_dir_text.textChanged.connect(self.data_dir_text_change)
        self.data_dir_button.clicked.connect(self.select_data_dir)
        self.subject_text.textChanged.connect(self.subject_text_change)
        self.start_button.clicked.connect(self.start_task)
        self.stop_button.clicked.connect(self.stop_task)

        # Widget initial setup.

        self.refresh()     # Populate port and task select widgets.
        self.disconnect()  # Configure not connected state.

        # Create timers

        self.process_timer = QtCore.QTimer() # Timer to regularly call process_data() during run.        
        self.process_timer.timeout.connect(self.process_data)

    # General methods

    def print_to_log(self, print_string, end='\n'):
        self.log_text.moveCursor(QtGui.QTextCursor.End)
        self.log_text.insertPlainText(print_string+end)
        self.log_text.moveCursor(QtGui.QTextCursor.End)
        self.log_text.repaint()

    def test_data_path(self):
        # Checks whether data dir and subject ID are valid.
        if  os.path.isdir(self.data_logger.data_dir) and self.subject_ID:
            self.start_button.setText('Record')
            return True
        else:
            self.start_button.setText('Start')
            return False

    # Widget methods.

    def refresh(self):
        # Refresh serial ports and task list controls.
        prev_status= self.status_text.text()
        QtCore.QTimer.singleShot(1000, lambda : self.status_text.setText(prev_status))
        self.status_text.setText('Refreshing ports and tasks...')
        self.repaint()   
        ports = [c[0] for c in list_ports.comports()
                 if ('Pyboard' in c[1]) or ('USB Serial Device' in c[1])]
        self.port_select.clear()
        self.port_select.addItems(ports)
        tasks =  [t.split('.')[0] for t in os.listdir(tasks_dir)
                  if t[-3:] == '.py']
        self.task_select.clear()
        self.task_select.addItems(tasks)

    def connect_disconnect(self):
        if self.status['connected'] == True:
            self.disconnect()
        else:
            self.connect()

    def connect(self):
        # Connect to pyboard.
        try:
            self.status_text.setText('Connecting...')
            self.repaint()            
            self.board = Pycboard(self.port_select.currentText(),
                                  print_func=self.print_to_log)
            self.connect_button.setText('Disconnect')
            self.config_button.setEnabled(True)
            self.port_select.setEnabled(False)
            self.task_select.setEnabled(True)
            self.upload_button.setEnabled(True)
            self.status['connected'] = True
            if not self.board.status['framework']:
                self.board.load_framework()
            self.status_text.setText('Connected')
        except SerialException:
            self.status_text.setText('Connection failed')

    def disconnect(self):
        # Disconnect from pyboard.
        if self.board: self.board.close()
        self.board = None
        self.port_select.setEnabled(True)
        self.connect_button.setText('Connect')
        self.connect_button.setEnabled(True)
        self.config_button.setEnabled(False)
        self.task_select.setEnabled(False)
        self.upload_button.setEnabled(False)
        self.variables_button.setEnabled(False)
        self.data_dir_text.setEnabled(False)
        self.data_dir_button.setEnabled(False)
        self.subject_text.setEnabled(False)
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.status_text.setText('Not connected')
        self.status['connected'] = False

    def upload_task(self):
        try:
            task = self.task_select.currentText()
            self.status_text.setText('Uploading..')
            self.start_button.setEnabled(False)
            self.variables_button.setEnabled(False)
            self.repaint()
            self.sm_info = self.board.setup_state_machine(task)
            self.variables_dialog = Variables_dialog(self)
            self.variables_button.setEnabled(True)
            self.data_logger = Data_logger(data_dir, 'run_task', task, self.sm_info)
            self.task_plot.set_state_machine(self.sm_info)
            self.data_dir_text.setEnabled(True)
            self.data_dir_button.setEnabled(True)
            self.subject_text.setEnabled(True)
            self.start_button.setEnabled(True)
            self.status_text.setText('Uploaded : ' + task)
            self.task = task
        except PyboardError as e:
            print(e)
            self.status_text.setText('Upload failed.')

    def select_data_dir(self):
        self.data_dir_text.setText(
            QtGui.QFileDialog.getExistingDirectory(self, 'Select data folder'))

    def data_dir_text_change(self, text):
        self.data_logger.data_dir = text
        self.test_data_path()

    def subject_text_change(self, text):
        self.subject_ID = text
        self.test_data_path()

    def start_task(self):
        if self.test_data_path():
            self.data_logger.open_data_file(self.subject_ID)
        self.board.start_framework()
        self.task_plot.run_start()
        self.config_button.setEnabled(False)
        self.start_button.setEnabled(False)
        self.refresh_button.setEnabled(False)
        self.connect_button.setEnabled(False)
        self.task_select.setEnabled(False)
        self.upload_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.print_to_log(
            '\nRun started at: {}\n'.format(
            datetime.now().strftime('%Y/%m/%d %H:%M:%S')))
        self.process_timer.start(self.update_interval)
        self.status_text.setText('Running: ' + self.task)

    def stop_task(self, error=False):
        self.process_timer.stop()
        if not error: 
            self.board.stop_framework()
            QtCore.QTimer.singleShot(100, self.process_data) # Catch output after framework stops.
        self.data_logger.close_files()
        self.config_button.setEnabled(True)
        self.refresh_button.setEnabled(True)
        self.connect_button.setEnabled(True)
        self.start_button.setEnabled(True)
        self.task_select.setEnabled(True)
        self.upload_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_text.setText('Uploaded : ' + self.task)

    # Update functions called while task running.

    def process_data(self):
        # Called regularly during run to process data from board.
        try:
            new_data = self.board.process_data()
            self.task_plot.process_data(new_data)
            if new_data:
                if self.data_logger.data_file: 
                    self.data_logger.write_to_file(new_data)
                data_string = self.data_logger.data_to_string(new_data, True) 
                self.print_to_log(data_string, end='')
        except PyboardError as e:
            self.print_to_log('\nError during run:\n\n' + str(e))
            self.stop_task(error=True)

    # Cleanup.

    def closeEvent(self, event):
        # Called when GUI window is closed.
        if self.board: self.board.close()
        event.accept()


# Main ----------------------------------------------------------------

if __name__ == '__main__':
    run_task_gui = Run_task_gui()
    run_task_gui.show() 
    app.exec_()
