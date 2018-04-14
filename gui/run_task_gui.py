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

from gui.dialogs import Settings_dialog, Board_config_dialog, Variables_dialog
from gui.plotting import Task_plotter

# Run_task_gui ------------------------------------------------------------------------

app = QtGui.QApplication([])  # Start QT

## Create widgets.

class Run_task_gui(QtGui.QWidget):

    def __init__(self, parent=None):
        super(QtGui.QWidget, self).__init__(parent)
        self.setWindowTitle('pyControl run task GUI')

        # Variables.
        self.board = None      # Pycboard class instance.
        self.task = None       # Task currently uploaded on pyboard. 
        self.sm_info = None    # Information about current state machine.
        self.data_dir = None
        self.subject_ID = None 
        self.update_interval = 10 # Time between updates (ms)
        self.data_logger = Data_logger(print_func=self.print_to_log)
        self.connected     = False # Whether gui is conencted to pyboard.
        self.uploaded = False # Whether selected task is on board.
        self.subject_changed = False

        # GUI groupbox.

        self.gui_groupbox = QtGui.QGroupBox('GUI')

        self.status_label = QtGui.QLabel('Status:')
        self.status_text = QtGui.QLineEdit('Not connected')
        self.status_text.setStyleSheet('background-color:rgb(210, 210, 210);')
        self.status_text.setReadOnly(True)
        self.refresh_button = QtGui.QPushButton('Refresh')
        self.settings_button = QtGui.QPushButton('Settings')

        self.guigroup_layout = QtGui.QHBoxLayout()
        self.guigroup_layout.addWidget(self.status_label)
        self.guigroup_layout.addWidget(self.status_text)
        self.guigroup_layout.addWidget(self.refresh_button)
        self.guigroup_layout.addWidget(self.settings_button)
        self.gui_groupbox.setLayout(self.guigroup_layout)  

        # Board groupbox

        self.board_groupbox = QtGui.QGroupBox('Board')

        self.port_label = QtGui.QLabel('Serial port:')
        self.port_select = QtGui.QComboBox()
        self.port_select.setEditable(True)
        self.port_select.setFixedWidth(80)
        self.connect_button = QtGui.QPushButton('Connect')
        self.config_button = QtGui.QPushButton('Config')

        self.boardgroup_layout = QtGui.QHBoxLayout()
        self.boardgroup_layout.addWidget(self.port_label)
        self.boardgroup_layout.addWidget(self.port_select)
        self.boardgroup_layout.addWidget(self.connect_button)
        self.boardgroup_layout.addWidget(self.config_button)
        self.board_groupbox.setLayout(self.boardgroup_layout)

        # Task groupbox

        self.task_groupbox = QtGui.QGroupBox('Task')

        self.task_label = QtGui.QLabel('Task:')
        self.task_select = QtGui.QComboBox()
        self.upload_button = QtGui.QPushButton('Upload')
        self.variables_button = QtGui.QPushButton('Variables')

        self.taskgroup_layout = QtGui.QHBoxLayout()
        self.taskgroup_layout.addWidget(self.task_label)
        self.taskgroup_layout.addWidget(self.task_select)
        self.taskgroup_layout.addWidget(self.upload_button)
        self.taskgroup_layout.addWidget(self.variables_button)
        self.task_groupbox.setLayout(self.taskgroup_layout)

        # File groupbox

        self.file_groupbox = QtGui.QGroupBox('Data file')

        self.data_dir_label = QtGui.QLabel('Data dir:')
        self.data_dir_text = QtGui.QLineEdit(data_dir)
        self.data_dir_button = QtGui.QPushButton('...')
        self.data_dir_button.setFixedWidth(30)
        self.subject_label = QtGui.QLabel('Subject ID:')
        self.subject_text = QtGui.QLineEdit(self.subject_ID)
        self.subject_text.setFixedWidth(80)
        self.subject_text.setMaxLength(12)

        self.filegroup_layout = QtGui.QHBoxLayout()
        self.filegroup_layout.addWidget(self.data_dir_label)
        self.filegroup_layout.addWidget(self.data_dir_text)
        self.filegroup_layout.addWidget(self.data_dir_button)
        self.filegroup_layout.addWidget(self.subject_label)
        self.filegroup_layout.addWidget(self.subject_text)
        self.file_groupbox.setLayout(self.filegroup_layout)

        # Session groupbox.

        self.session_groupbox = QtGui.QGroupBox('Session')

        self.start_button = QtGui.QPushButton('Start')
        self.stop_button = QtGui.QPushButton('Stop')

        self.sessiongroup_layout = QtGui.QHBoxLayout()
        self.sessiongroup_layout.addWidget(self.start_button)
        self.sessiongroup_layout.addWidget(self.stop_button)
        self.session_groupbox.setLayout(self.sessiongroup_layout)

        # Log text and task plots.

        self.log_textbox = QtGui.QTextEdit()
        self.log_textbox.setFont(QtGui.QFont('Courier', 9))
        self.log_textbox.setReadOnly(True)

        self.task_plot = Task_plotter()

        # Main layout

        self.vertical_layout     = QtGui.QVBoxLayout()
        self.horizontal_layout_1 = QtGui.QHBoxLayout()
        self.horizontal_layout_2 = QtGui.QHBoxLayout()
        self.horizontal_layout_3 = QtGui.QHBoxLayout()

        self.horizontal_layout_1.addWidget(self.gui_groupbox)
        self.horizontal_layout_1.addWidget(self.board_groupbox)
        self.horizontal_layout_2.addWidget(self.file_groupbox)
        self.horizontal_layout_3.addWidget(self.task_groupbox)
        self.horizontal_layout_3.addWidget(self.session_groupbox)
        self.vertical_layout.addLayout(self.horizontal_layout_1)
        self.vertical_layout.addLayout(self.horizontal_layout_2)
        self.vertical_layout.addLayout(self.horizontal_layout_3)
        self.vertical_layout.addWidget(self.log_textbox , 20)
        self.vertical_layout.addWidget(self.task_plot, 80)
        self.setLayout(self.vertical_layout)

        # Create dialogs.

        self.settings_dialog = Settings_dialog(parent=self)
        self.config_dialog = Board_config_dialog(parent=self)

        # Connect widgets

        self.settings_button.clicked.connect(lambda: self.settings_dialog.exec_())
        self.refresh_button.clicked.connect(self.refresh)
        self.connect_button.clicked.connect(lambda:
            self.disconnect() if self.connected else self.connect())
        self.config_button.clicked.connect(lambda x: self.config_dialog.exec_())
        self.task_select.currentTextChanged.connect(self.task_changed)
        self.upload_button.clicked.connect(self.setup_task)        
        self.variables_button.clicked.connect(lambda x: self.variables_dialog.exec_())
        self.data_dir_text.textChanged.connect(self.test_data_path)
        self.data_dir_button.clicked.connect(self.select_data_dir)
        self.subject_text.textChanged.connect(self.test_data_path)
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
        self.log_textbox.moveCursor(QtGui.QTextCursor.End)
        self.log_textbox.insertPlainText(print_string+end)
        self.log_textbox.moveCursor(QtGui.QTextCursor.End)
        self.log_textbox.repaint()

    def test_data_path(self):
        # Checks whether data dir and subject ID are valid.
        self.data_dir = self.data_dir_text.text()
        subject_ID = self.subject_text.text()
        if  os.path.isdir(self.data_dir) and subject_ID:
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

    def connect(self):
        # Connect to pyboard.
        try:
            self.status_text.setText('Connecting...')
            self.repaint()            
            self.board = Pycboard(self.port_select.currentText(),
                                  print_func=self.print_to_log, data_logger=self.data_logger)
            self.port_select.setEnabled(False)
            self.config_button.setEnabled(True)
            self.task_groupbox.setEnabled(True)
            self.variables_button.setEnabled(False)
            
            self.connected = True
            if not self.board.status['framework']:
                self.board.load_framework()
            self.connect_button.setText('Disconnect')
            self.status_text.setText('Connected')
        except SerialException:
            self.status_text.setText('Connection failed')

    def disconnect(self):
        # Disconnect from pyboard.
        if self.board: self.board.close()
        self.board = None
        self.task_groupbox.setEnabled(False)
        self.file_groupbox.setEnabled(False)
        self.session_groupbox.setEnabled(False)
        self.config_button.setEnabled(False)
        self.connect_button.setText('Connect')
        self.status_text.setText('Not connected')
        self.connected = False

    def task_changed(self):
        self.uploaded = False
        self.upload_button.setText('Upload')

    def setup_task(self):
        try:
            task = self.task_select.currentText()
            if self.uploaded:
                self.status_text.setText('Resetting task..')
            else:
                self.status_text.setText('Uploading..')
            self.start_button.setEnabled(False)
            self.variables_button.setEnabled(False)
            self.repaint()
            self.sm_info = self.board.setup_state_machine(task, uploaded=self.uploaded)
            self.variables_dialog = Variables_dialog(self)
            self.variables_button.setEnabled(True)
            self.task_plot.set_state_machine(self.sm_info)
            self.file_groupbox.setEnabled(True)
            self.session_groupbox.setEnabled(True)
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.status_text.setText('Uploaded : ' + task)
            self.task = task
            self.uploaded = True
            self.upload_button.setText('Reset')
        except PyboardError as e:
            print(e)
            self.status_text.setText('Upload failed.')
     
    def select_data_dir(self):
        self.data_dir_text.setText(
            QtGui.QFileDialog.getExistingDirectory(self, 'Select data folder', data_dir))

    def start_task(self):
        if self.test_data_path():
            subject_changed = (self.subject_ID is not None and 
                str(self.subject_text.text()) != self.subject_ID)
            self.subject_ID = str(self.subject_text.text())
            if subject_changed:
                reset_task = QtGui.QMessageBox.question(self, 'Subject changed', 
                    'Subject ID changed, reset task?'
                    ,QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
                if reset_task == QtGui.QMessageBox.Yes:
                    self.setup_task()
                    return
            self.data_logger.open_data_file(self.data_dir, 'run_task', self.subject_ID)
        self.board.start_framework()
        self.task_plot.run_start()
        self.task_select.setEnabled(False)
        self.upload_button.setEnabled(False)
        self.file_groupbox.setEnabled(False)
        self.start_button.setEnabled(False)
        self.board_groupbox.setEnabled(False)
        self.refresh_button.setEnabled(False)
        self.settings_button.setEnabled(False)
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
        self.board_groupbox.setEnabled(True)
        self.file_groupbox.setEnabled(True)
        self.refresh_button.setEnabled(True)
        self.settings_button.setEnabled(True)
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
        except PyboardError as e:
            self.print_to_log('\nError during framework run.')
            self.stop_task(error=True)

    # Cleanup.

    def closeEvent(self, event):
        # Called when GUI window is closed.
        if self.board:
            self.board.stop_framework()
            self.board.close()
        event.accept()

# Main ----------------------------------------------------------------

if __name__ == '__main__':
    run_task_gui = Run_task_gui()
    run_task_gui.show() 
    app.exec_()
