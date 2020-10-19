import os
import time
from pyqtgraph.Qt import QtGui, QtCore
from datetime import datetime
from serial import SerialException, SerialTimeoutException

from com.pycboard import Pycboard, PyboardError, _djb2_file
from com.data_logger import Data_logger

from config.paths import dirs
from config.gui_settings import update_interval

from gui.dialogs import Variables_dialog
from gui.plotting import Task_plot
from gui.utility import init_keyboard_shortcuts,TaskSelectMenu

# Run_task_gui ------------------------------------------------------------------------

## Create widgets.

class Run_task_tab(QtGui.QWidget):

    def __init__(self, parent=None):
        super(QtGui.QWidget, self).__init__(parent)

        # Variables.
        self.GUI_main = self.parent()
        self.board = None      # Pycboard class instance.
        self.task = None       # Task currently uploaded on pyboard. 
        self.task_hash = None  # Used to check if file has changed.
        self.data_dir = None   # Folder to save data files.
        self.custom_dir = False  # True if data_dir field has been changed from default.
        self.connected = False # Whether gui is conencted to pyboard.
        self.uploaded = False # Whether selected task file is on board.
        self.fresh_task = None # Whether task has been run or variables edited.
        self.running = False
        self.subject_changed = False
        self.variables_dialog = None

        # GUI groupbox.

        self.status_groupbox = QtGui.QGroupBox('Status')

        self.status_text = QtGui.QLineEdit('Not connected')
        self.status_text.setReadOnly(True)

        self.guigroup_layout = QtGui.QHBoxLayout()
        self.guigroup_layout.addWidget(self.status_text)
        self.status_groupbox.setLayout(self.guigroup_layout)  

        # Board groupbox

        self.board_groupbox = QtGui.QGroupBox('Setup')

        self.board_label = QtGui.QLabel('Select:')
        self.board_select = QtGui.QComboBox()
        self.board_select.setEditable(True)
        self.board_select.setFixedWidth(100)
        self.connect_button = QtGui.QPushButton('Connect')
        self.connect_button.setIcon(QtGui.QIcon("gui/icons/connect.svg"))
        self.connect_button.setEnabled(False)
        self.config_button = QtGui.QPushButton('Config')
        self.config_button.setIcon(QtGui.QIcon("gui/icons/settings.svg"))

        self.boardgroup_layout = QtGui.QHBoxLayout()
        self.boardgroup_layout.addWidget(self.board_label)
        self.boardgroup_layout.addWidget(self.board_select)
        self.boardgroup_layout.addWidget(self.connect_button)
        self.boardgroup_layout.addWidget(self.config_button)
        self.board_groupbox.setLayout(self.boardgroup_layout)

        self.connect_button.clicked.connect(
            lambda: self.disconnect() if self.connected else self.connect())
        self.config_button.clicked.connect(self.open_config_dialog)

        # File groupbox

        self.file_groupbox = QtGui.QGroupBox('Data file')

        self.data_dir_label = QtGui.QLabel('Data dir:')
        self.data_dir_text = QtGui.QLineEdit(dirs['data'])
        self.data_dir_button = QtGui.QPushButton()
        self.data_dir_button.setIcon(QtGui.QIcon("gui/icons/folder.svg"))
        self.data_dir_button.setFixedWidth(30)
        self.subject_label = QtGui.QLabel('Subject ID:')
        self.subject_text = QtGui.QLineEdit()
        self.subject_text.setFixedWidth(80)
        self.subject_text.setMaxLength(12)

        self.filegroup_layout = QtGui.QHBoxLayout()
        self.filegroup_layout.addWidget(self.data_dir_label)
        self.filegroup_layout.addWidget(self.data_dir_text)
        self.filegroup_layout.addWidget(self.data_dir_button)
        self.filegroup_layout.addWidget(self.subject_label)
        self.filegroup_layout.addWidget(self.subject_text)
        self.file_groupbox.setLayout(self.filegroup_layout)

        self.data_dir_text.textChanged.connect(self.test_data_path)
        self.data_dir_text.textEdited.connect(lambda: setattr(self, 'custom_dir', True))
        self.data_dir_button.clicked.connect(self.select_data_dir)
        self.subject_text.textChanged.connect(self.test_data_path)

        # Task groupbox

        self.task_groupbox = QtGui.QGroupBox('Task')

        self.task_label = QtGui.QLabel('Task:')
        self.task_select = TaskSelectMenu('select task')
        self.task_select.set_callback(self.task_changed)
        self.upload_button = QtGui.QPushButton('Upload')
        self.upload_button.setIcon(QtGui.QIcon("gui/icons/circle-arrow-up.svg"))
        self.variables_button = QtGui.QPushButton('Variables')
        self.variables_button.setIcon(QtGui.QIcon("gui/icons/filter.svg"))

        self.taskgroup_layout = QtGui.QHBoxLayout()
        self.taskgroup_layout.addWidget(self.task_label)
        self.taskgroup_layout.addWidget(self.task_select)
        self.taskgroup_layout.addWidget(self.upload_button)
        self.taskgroup_layout.addWidget(self.variables_button)
        self.task_groupbox.setLayout(self.taskgroup_layout)

        self.upload_button.clicked.connect(self.setup_task)        

        # Session groupbox.

        self.session_groupbox = QtGui.QGroupBox('Session')

        self.start_button = QtGui.QPushButton('Start')
        self.start_button.setIcon(QtGui.QIcon("gui/icons/play.svg"))
        self.stop_button = QtGui.QPushButton('Stop')
        self.stop_button.setIcon(QtGui.QIcon("gui/icons/stop.svg"))

        self.sessiongroup_layout = QtGui.QHBoxLayout()
        self.sessiongroup_layout.addWidget(self.start_button)
        self.sessiongroup_layout.addWidget(self.stop_button)
        self.session_groupbox.setLayout(self.sessiongroup_layout)

        self.start_button.clicked.connect(self.start_task)
        self.stop_button.clicked.connect(self.stop_task)

        # Log text and task plots.

        self.log_textbox = QtGui.QTextEdit()
        self.log_textbox.setFont(QtGui.QFont('Courier', 9))
        self.log_textbox.setReadOnly(True)

        self.task_plot = Task_plot()
        self.data_logger = Data_logger(print_func=self.print_to_log,
                                       data_consumers=[self.task_plot])

        # Main layout

        self.vertical_layout     = QtGui.QVBoxLayout()
        self.horizontal_layout_1 = QtGui.QHBoxLayout()
        self.horizontal_layout_2 = QtGui.QHBoxLayout()
        self.horizontal_layout_3 = QtGui.QHBoxLayout()

        self.horizontal_layout_1.addWidget(self.status_groupbox)
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

        # Create timers

        self.update_timer = QtCore.QTimer() # Timer to regularly call update() during run.        
        self.update_timer.timeout.connect(self.update)

        # Keyboard Shortcuts

        shortcut_dict = {
                        't' : lambda: self.task_select.showMenu(),
                        'u' : lambda: self.setup_task(),
                        'Space' : (lambda: self.stop_task() if self.running 
                            else self.start_task() if self.uploaded else None)
                        }

        init_keyboard_shortcuts(self, shortcut_dict)

        # Initial setup.

        self.disconnect() # Set initial state as disconnected.

    # General methods

    def print_to_log(self, print_string, end='\n'):
        self.log_textbox.moveCursor(QtGui.QTextCursor.End)
        self.log_textbox.insertPlainText(print_string+end)
        self.log_textbox.moveCursor(QtGui.QTextCursor.End)
        self.GUI_main.app.processEvents() # To update gui during long operations that print progress.

    def test_data_path(self):
        # Checks whether data dir and subject ID are valid.
        self.data_dir = self.data_dir_text.text()
        subject_ID = self.subject_text.text()
        if  os.path.isdir(self.data_dir) and subject_ID:
            self.start_button.setText('Record')
            self.start_button.setIcon(QtGui.QIcon("gui/icons/record.svg"))
            return True
        else:
            self.start_button.setText('Start')
            self.start_button.setIcon(QtGui.QIcon("gui/icons/play.svg"))
            return False

    def refresh(self):
        # Called regularly when framework not running.
        if self.GUI_main.setups_tab.available_setups_changed:
            self.board_select.clear()
            if self.GUI_main.setups_tab.setup_names:
                self.board_select.addItems(self.GUI_main.setups_tab.setup_names)
                if not self.connected:
                    self.connect_button.setEnabled(True)
            else: # No setups available to connect to.
                    self.connect_button.setEnabled(False)
        if self.GUI_main.available_tasks_changed:
            self.task_select.update_menu(dirs['tasks'])
        if self.GUI_main.data_dir_changed and not self.custom_dir:
            self.data_dir_text.setText(dirs['data'])
        if self.task:
            try:
                task_path = os.path.join(dirs['tasks'], self.task + '.py')
                if not self.task_hash == _djb2_file(task_path): # Task file modified.
                    self.task_changed()
            except FileNotFoundError:
                pass

    def open_config_dialog(self):
        '''Open the config dialog and update GUI as required by chosen config.'''
        self.GUI_main.config_dialog.exec_(self.board)
        self.task_changed()
        if self.GUI_main.config_dialog.disconnect:
            time.sleep(0.5)
            self.GUI_main.refresh()
            self.disconnect()
        if self.connected and self.board.status['framework']:
            self.task_groupbox.setEnabled(True)

    # Widget methods.

    def connect(self):
        # Connect to pyboard.
        try:
            self.status_text.setText('Connecting...')
            self.board_select.setEnabled(False)
            self.variables_button.setEnabled(False)
            self.connect_button.setEnabled(False)
            self.repaint()
            port = self.GUI_main.setups_tab.get_port(self.board_select.currentText())           
            self.board = Pycboard(port, print_func=self.print_to_log, data_logger=self.data_logger)
            self.connected = True
            self.config_button.setEnabled(True)
            self.connect_button.setEnabled(True)
            self.connect_button.setText('Disconnect')
            self.connect_button.setIcon(QtGui.QIcon("gui/icons/disconnect.svg"))
            self.status_text.setText('Connected')
            if self.board.status['framework']:
                self.task_groupbox.setEnabled(True)
            else:
                self.print_to_log(
                    "\nLoad pyControl framework using 'Config' button.")
        except SerialException:
            self.status_text.setText('Connection failed')
            self.print_to_log('Connection failed.')
            self.connect_button.setEnabled(True)
            self.board_select.setEnabled(True)


    def disconnect(self):
        # Disconnect from pyboard.
        if self.board: self.board.close()
        self.board = None
        self.task_groupbox.setEnabled(False)
        self.file_groupbox.setEnabled(False)
        self.session_groupbox.setEnabled(False)
        self.config_button.setEnabled(False)
        self.board_select.setEnabled(True)
        self.connect_button.setText('Connect')
        self.connect_button.setIcon(QtGui.QIcon("gui/icons/connect.svg"))
        self.status_text.setText('Not connected')
        self.task_changed()
        self.connected = False

    def task_changed(self,task=None):
        self.uploaded = False
        self.upload_button.setText('Upload')
        self.upload_button.setIcon(QtGui.QIcon("gui/icons/circle-arrow-up.svg"))
        self.start_button.setEnabled(False)

    def setup_task(self):
        task = self.task_select.text()
        if task == 'select task':
            return
        try:
            if self.uploaded:
                self.status_text.setText('Resetting task..')
            else:
                self.status_text.setText('Uploading..')
                self.task_hash = _djb2_file(os.path.join(dirs['tasks'], task + '.py'))
            self.start_button.setEnabled(False)
            self.variables_button.setEnabled(False)
            self.repaint()
            self.board.setup_state_machine(task, uploaded=self.uploaded)
            if self.variables_dialog:
                self.variables_button.clicked.disconnect()
                self.variables_dialog.deleteLater()
            self.variables_dialog = Variables_dialog(self, self.board)
            self.variables_button.clicked.connect(self.variables_dialog.exec_)
            self.variables_button.setEnabled(True)
            self.task_plot.set_state_machine(self.board.sm_info)
            self.file_groupbox.setEnabled(True)
            self.session_groupbox.setEnabled(True)
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.status_text.setText('Uploaded : ' + task)
            self.task = task
            self.fresh_task = True
            self.uploaded = True
            self.upload_button.setText('Reset')
            self.upload_button.setIcon(QtGui.QIcon("gui/icons/refresh.svg"))
        except PyboardError:
            self.status_text.setText('Error setting up state machine.')
     
    def select_data_dir(self):
        new_path = QtGui.QFileDialog.getExistingDirectory(self, 'Select data folder', dirs['data'])
        if new_path:
            self.data_dir_text.setText(new_path)
            self.custom_dir = True

    def start_task(self):
        recording = self.test_data_path()
        if recording:
            if not self.fresh_task:
                reset_task = QtGui.QMessageBox.question(self, 'Reset task', 
                    'Task has already been run, variables may not have default values.\n\nReset task?'
                    ,QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
                if reset_task == QtGui.QMessageBox.Yes:
                    self.setup_task()
                    return
            subject_ID = str(self.subject_text.text())
            setup_ID = str(self.board_select.currentText())
            self.data_logger.open_data_file(self.data_dir, 'run_task', setup_ID, subject_ID)
            self.data_logger.copy_task_file(self.data_dir, dirs['tasks'], 'run_task-task_files')
        self.fresh_task = False
        self.running = True
        self.board.start_framework()
        self.task_plot.run_start(recording)
        self.task_select.setEnabled(False)
        self.upload_button.setEnabled(False)
        self.file_groupbox.setEnabled(False)
        self.start_button.setEnabled(False)
        self.board_groupbox.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.print_to_log(
            '\nRun started at: {}\n'.format(
            datetime.now().strftime('%Y/%m/%d %H:%M:%S')))
        self.update_timer.start(update_interval)
        self.GUI_main.refresh_timer.stop()
        self.status_text.setText('Running: ' + self.task)
        self.GUI_main.tab_widget.setTabEnabled(1, False) # Disable experiments tab.
        self.GUI_main.tab_widget.setTabEnabled(2, False) # Disable setups tab.

    def stop_task(self, error=False, stopped_by_task=False):
        self.running = False
        self.update_timer.stop()
        self.GUI_main.refresh_timer.start(self.GUI_main.refresh_interval)
        if not (error or stopped_by_task): 
            self.board.stop_framework()
            time.sleep(0.05)
            self.board.process_data()
        self.data_logger.close_files()
        self.task_plot.run_stop()
        self.board_groupbox.setEnabled(True)
        self.file_groupbox.setEnabled(True)
        self.start_button.setEnabled(True)
        self.task_select.setEnabled(True)
        self.upload_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_text.setText('Uploaded : ' + self.task)
        self.GUI_main.tab_widget.setTabEnabled(1, True) # Enable setups tab.
        self.GUI_main.tab_widget.setTabEnabled(2, True) # Enable setups tab.

    # Timer updates

    def update(self):
        # Called regularly during run to process data from board and update plots.
        try:
            self.board.process_data()
            if not self.board.framework_running:
                self.stop_task(stopped_by_task=True)
        except PyboardError:
            self.print_to_log('\nError during framework run.')
            self.stop_task(error=True)
        self.task_plot.update()

    # Cleanup.

    def closeEvent(self, event):
        # Called when GUI window is closed.
        if self.board:
            self.board.stop_framework()
            self.board.close()
        event.accept()

    # Exception handling.

    def excepthook(self, ex_type, ex_value, ex_traceback):
        # Called whenever an uncaught exception occurs.
        if ex_type in (SerialException, SerialTimeoutException):
            self.print_to_log('\nError: Serial connection with board lost.')
        elif ex_type == PyboardError:
            self.print_to_log('\nError: Unable to execute command.')
        else:
            self.print_to_log('\nError: uncaught exception of type: {}'.format(ex_type))
        if self.running:
            self.stop_task(error=True)
        self.disconnect()
