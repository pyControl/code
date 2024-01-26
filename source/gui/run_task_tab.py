import os
import time
import importlib
from datetime import datetime
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
from serial import SerialException, SerialTimeoutException
from source.communication.pycboard import Pycboard, PyboardError, _djb2_file
from source.gui.settings import get_setting, user_folder
from source.gui.dialogs import Controls_dialog
from source.gui.custom_controls_dialog import Custom_controls_dialog, Custom_gui
from source.gui.plotting import Task_plot
from source.gui.utility import init_keyboard_shortcuts, NestedMenu, TaskInfo
from source.gui.hardware_variables_dialog import set_hardware_variables, hw_vars_defined_in_setup


# Run_task_gui ------------------------------------------------------------------------

## Create widgets.


class Run_task_tab(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(QtWidgets.QWidget, self).__init__(parent)

        # Variables.
        self.GUI_main = self.parent()
        self.board = None  # Pycboard class instance.
        self.task = None  # Task currently uploaded on pyboard.
        self.task_hash = None  # Used to check if file has changed.
        self.data_dir = None  # Folder to save data files.
        self.custom_dir = False  # True if data_dir field has been changed from default.
        self.connected = False  # Whether gui is connected to pyboard.
        self.uploaded = False  # Whether selected task file is on board.
        self.fresh_task = None  # Whether task has been run or variables edited.
        self.user_API = None  # Overwritten by user API class.
        self.running = False
        self.controls_dialog = None

        pad = 3  # Spacing round GUI elements in groupboxes.

        # Setup groupbox

        self.board_groupbox = QtWidgets.QGroupBox("Setup")

        self.board_select = QtWidgets.QComboBox()
        self.board_select.addItems(["No setups found"])
        self.board_select.setSizeAdjustPolicy(QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.connect_button = QtWidgets.QPushButton("Connect")
        self.connect_button.setIcon(QtGui.QIcon("source/gui/icons/connect.svg"))
        self.connect_button.setEnabled(False)
        self.config_dropdown = QtWidgets.QComboBox()
        self.config_dropdown.addItem(QtGui.QIcon("source/gui/icons/settings.svg"), "Config")
        self.config_dropdown.setFixedWidth(self.config_dropdown.minimumSizeHint().width())
        self.config_dropdown.addItem(QtGui.QIcon("source/gui/icons/upload.svg"), "Load framework")
        self.config_dropdown.addItem(QtGui.QIcon("source/gui/icons/upload.svg"), "Load hardware definition")
        self.config_dropdown.addItem(QtGui.QIcon("source/gui/icons/wrench.svg"), "DFU mode")
        self.config_dropdown.addItem(QtGui.QIcon("source/gui/icons/enable.svg"), "Enable flashdrive")
        self.config_dropdown.addItem(QtGui.QIcon("source/gui/icons/disable.svg"), "Disable flashdrive")
        self.config_dropdown.view().setRowHidden(0, True)

        boardgroup_layout = QtWidgets.QGridLayout(self.board_groupbox)
        boardgroup_layout.addWidget(self.board_select, 0, 0, 1, 2)
        boardgroup_layout.addWidget(self.connect_button, 1, 0)
        boardgroup_layout.addWidget(self.config_dropdown, 1, 1)
        boardgroup_layout.setContentsMargins(pad, pad, pad, pad)

        self.connect_button.clicked.connect(lambda: self.disconnect() if self.connected else self.connect())
        self.config_dropdown.currentIndexChanged.connect(self.configure_board)

        # File groupbox

        self.file_groupbox = QtWidgets.QGroupBox("Data file")

        data_dir_label = QtWidgets.QLabel("Data dir:")
        data_dir_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.data_dir_text = QtWidgets.QLineEdit(get_setting("folders", "data"))
        data_dir_button = QtWidgets.QPushButton()
        data_dir_button.setIcon(QtGui.QIcon("source/gui/icons/folder.svg"))
        data_dir_button.setFixedWidth(30)
        subject_label = QtWidgets.QLabel("Subject ID:")
        self.subject_text = QtWidgets.QLineEdit()

        filegroup_layout = QtWidgets.QGridLayout()
        filegroup_layout.addWidget(data_dir_label, 0, 0)
        filegroup_layout.addWidget(self.data_dir_text, 0, 1)
        filegroup_layout.addWidget(data_dir_button, 0, 2)
        filegroup_layout.addWidget(subject_label, 1, 0)
        filegroup_layout.addWidget(self.subject_text, 1, 1)
        filegroup_layout.setContentsMargins(pad, pad, pad, pad)
        self.file_groupbox.setLayout(filegroup_layout)

        self.data_dir_text.textChanged.connect(self.test_data_path)
        self.data_dir_text.textEdited.connect(lambda: setattr(self, "custom_dir", True))
        data_dir_button.clicked.connect(self.select_data_dir)
        self.subject_text.textChanged.connect(self.test_data_path)

        # Task groupbox

        self.task_groupbox = QtWidgets.QGroupBox("Task")

        self.task_select = NestedMenu("select task", ".py")
        self.task_select.set_callback(self.task_changed)
        self.upload_button = QtWidgets.QPushButton("Upload")
        self.upload_button.setIcon(QtGui.QIcon("source/gui/icons/circle-arrow-up.svg"))
        self.controls_button = QtWidgets.QPushButton("Controls")
        self.controls_button.setIcon(QtGui.QIcon("source/gui/icons/filter.svg"))

        taskgroup_layout = QtWidgets.QGridLayout(self.task_groupbox)
        taskgroup_layout.addWidget(self.task_select, 0, 0, 1, 2)
        taskgroup_layout.addWidget(self.upload_button, 1, 0)
        taskgroup_layout.addWidget(self.controls_button, 1, 1)
        taskgroup_layout.setContentsMargins(pad, pad, pad, pad)

        self.upload_button.clicked.connect(self.setup_task)

        # Session groupbox.

        self.session_groupbox = QtWidgets.QGroupBox("Session")

        self.start_button = QtWidgets.QPushButton("Start")
        self.start_button.setIcon(QtGui.QIcon("source/gui/icons/play.svg"))
        self.stop_button = QtWidgets.QPushButton("Stop")
        self.stop_button.setIcon(QtGui.QIcon("source/gui/icons/stop.svg"))

        self.task_info = TaskInfo()

        sessiongroup_layout = QtWidgets.QGridLayout()
        sessiongroup_layout.addWidget(self.task_info.print_label, 0, 1)
        sessiongroup_layout.addWidget(self.task_info.print_text, 0, 2, 1, 3)
        sessiongroup_layout.addWidget(self.task_info.state_label, 1, 1)
        sessiongroup_layout.addWidget(self.task_info.state_text, 1, 2)
        sessiongroup_layout.addWidget(self.task_info.event_label, 1, 3)
        sessiongroup_layout.addWidget(self.task_info.event_text, 1, 4)
        sessiongroup_layout.addWidget(self.start_button, 0, 0)
        sessiongroup_layout.addWidget(self.stop_button, 1, 0)
        sessiongroup_layout.setContentsMargins(pad, pad, pad, pad)
        self.session_groupbox.setLayout(sessiongroup_layout)

        self.start_button.clicked.connect(self.start_task)
        self.stop_button.clicked.connect(self.stop_task)

        # Log text and task plots.

        self.log_textbox = QtWidgets.QTextEdit()
        self.log_textbox.setFont(QtGui.QFont("Courier New", get_setting("GUI", "log_font_size")))
        self.log_textbox.setReadOnly(True)

        self.task_plot = Task_plot()

        self.top_section = QtWidgets.QWidget()
        top_layout = QtWidgets.QHBoxLayout(self.top_section)
        top_layout.addWidget(self.board_groupbox)
        top_layout.addWidget(self.task_groupbox)
        top_layout.addWidget(self.file_groupbox)
        top_layout.setContentsMargins(0, 0, 0, 0)

        # Resizable log and plots layout.
        self.vsplitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
        self.vsplitter.addWidget(self.log_textbox)
        self.vsplitter.addWidget(self.task_plot)
        self.vsplitter.setSizes([1, 2])

        # Main layout
        self.run_layout = QtWidgets.QGridLayout()
        self.run_layout.addWidget(self.top_section, 0, 0)
        self.run_layout.addWidget(self.session_groupbox, 1, 0)
        self.run_layout.addWidget(self.vsplitter, 2, 0)
        self.run_layout.setRowStretch(2, 1)

        self.setLayout(self.run_layout)

        # Create timers
        self.plot_update_timer = QtCore.QTimer()  # Timer to regularly call update() during run.
        self.plot_update_timer.timeout.connect(self.plot_update)

        # Keyboard Shortcuts
        shortcut_dict = {
            "t": self.task_select.showMenu,
            "u": self.setup_task,
            "Space": (lambda: self.stop_task() if self.running else self.start_task() if self.uploaded else None),
        }

        init_keyboard_shortcuts(self, shortcut_dict)

        # Initial setup.
        self.disconnect()  # Set initial state as disconnected.

    # General methods
    def print_to_log(self, print_string, end="\n"):
        self.log_textbox.moveCursor(QtGui.QTextCursor.MoveOperation.End)
        self.log_textbox.insertPlainText(print_string + end)
        self.log_textbox.moveCursor(QtGui.QTextCursor.MoveOperation.End)
        self.GUI_main.app.processEvents()  # To update gui during long operations that print progress.

    def test_data_path(self):
        # Checks whether data dir and subject ID are valid.
        self.data_dir = self.data_dir_text.text()
        subject_ID = self.subject_text.text()
        if os.path.isdir(self.data_dir) and subject_ID:
            self.start_button.setText("Record")
            self.start_button.setIcon(QtGui.QIcon("source/gui/icons/record.svg"))
            return True
        else:
            self.start_button.setText("Start")
            self.start_button.setIcon(QtGui.QIcon("source/gui/icons/play.svg"))
            return False

    def refresh(self):
        # Called regularly when framework not running.
        if self.GUI_main.setups_tab.available_setups_changed:
            self.board_select.clear()
            if self.GUI_main.setups_tab.setup_names:
                self.board_select.addItems(self.GUI_main.setups_tab.setup_names)
                if not self.connected:
                    self.connect_button.setEnabled(True)
            else:  # No setups available to connect to.
                self.board_select.addItems(["No setups found"])
                self.connect_button.setEnabled(False)
        if self.GUI_main.available_tasks_changed:
            self.task_select.update_menu(user_folder("tasks"))
        if self.GUI_main.data_dir_changed and not self.custom_dir:
            self.data_dir_text.setText(get_setting("folders", "data"))
        if self.task:
            try:
                # gets called frequently, so not using get_setting()
                task_path = os.path.join(self.GUI_main.task_directory, self.task + ".py")
                if not self.task_hash == _djb2_file(task_path):  # Task file modified.
                    self.task_changed()
            except FileNotFoundError:
                pass

    def configure_board(self, index):
        if index:
            disconnect = False  # Indicates whether board was disconnected by dialog.
            if index == 1:
                self.config_dropdown.setCurrentIndex(0)
                flashdrive_enabled = "MSC" in self.board.status["usb_mode"]
                if flashdrive_enabled:
                    flashdrive_message = (
                        "It is recommended to disable the pyboard filesystem from acting as a "
                        "USB flash drive before loading the framework, as this helps prevent the "
                        "filesystem getting corrupted. Do you want to disable the flashdrive?"
                    )
                    reply = QtWidgets.QMessageBox.question(
                        self,
                        "Disable flashdrive",
                        flashdrive_message,
                        QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
                    )
                    if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                        self.board.disable_mass_storage()
                        disconnect = True
                    else:
                        self.board.load_framework()
                else:
                    self.board.load_framework()
            elif index == 2:
                self.config_dropdown.setCurrentIndex(0)
                hwd_path = QtWidgets.QFileDialog.getOpenFileName(
                    self,
                    "Select hardware definition:",
                    user_folder("hardware_definitions"),
                    filter="*.py",
                )[0]
                if hwd_path:
                    self.board.load_hardware_definition(hwd_path)
            elif index == 3:
                self.config_dropdown.setCurrentIndex(0)
                self.board.DFU_mode()
                disconnect = True
            elif index == 4:
                self.config_dropdown.setCurrentIndex(0)
                self.board.enable_mass_storage()
                disconnect = True
            elif index == 5:
                self.config_dropdown.setCurrentIndex(0)
                self.board.disable_mass_storage()
                disconnect = True

            self.task_changed()
            if disconnect:
                time.sleep(0.5)
                self.GUI_main.refresh()
                self.disconnect()
            if self.connected and self.board.status["framework"]:
                self.task_groupbox.setEnabled(True)

    # Widget methods.

    def connect(self):
        # Connect to pyboard.
        self.print_to_log(f"\nConnecting to board {self.board_select.currentText()}")
        try:
            self.board_select.setEnabled(False)
            self.controls_button.setEnabled(False)
            self.connect_button.setEnabled(False)
            self.repaint()
            self.serial_port = self.GUI_main.setups_tab.get_port(self.board_select.currentText())
            self.board = Pycboard(
                self.serial_port, print_func=self.print_to_log, data_consumers=[self.task_plot, self.task_info]
            )
            self.connected = True
            self.config_dropdown.setEnabled(True)
            flashdrive_enabled = "MSC" in self.board.status["usb_mode"]
            if flashdrive_enabled:
                self.config_dropdown.view().setRowHidden(4, True)
                self.config_dropdown.view().setRowHidden(5, False)
            else:
                self.config_dropdown.view().setRowHidden(4, False)
                self.config_dropdown.view().setRowHidden(5, True)
            self.connect_button.setEnabled(True)
            self.connect_button.setText("Disconnect")
            self.connect_button.setIcon(QtGui.QIcon("source/gui/icons/disconnect.svg"))
            if self.board.status["framework"]:
                self.task_groupbox.setEnabled(True)
            else:
                self.print_to_log("\nLoad pyControl framework using 'Config' button.")
        except (SerialException, PyboardError):
            self.print_to_log("Connection failed.")
            self.connect_button.setEnabled(True)
            self.board_select.setEnabled(True)

    def disconnect(self):
        # Disconnect from pyboard.
        if self.board:
            self.board.close()
            self.print_to_log("\nDisconnected from board.")
        self.board = None
        self.task_groupbox.setEnabled(False)
        self.file_groupbox.setEnabled(False)
        self.session_groupbox.setEnabled(False)
        self.config_dropdown.setEnabled(False)
        self.board_select.setEnabled(True)
        self.connect_button.setText("Connect")
        self.connect_button.setIcon(QtGui.QIcon("source/gui/icons/connect.svg"))
        self.task_changed()
        self.connected = False

    def task_changed(self, *args):
        self.uploaded = False
        self.upload_button.setText("Upload")
        self.upload_button.setIcon(QtGui.QIcon("source/gui/icons/circle-arrow-up.svg"))
        self.start_button.setEnabled(False)
        self.controls_button.setEnabled(False)

    def setup_task(self):
        """Upload task, set any hardware variables, ready gui to run task."""
        # Upload task to board.
        task = self.task_select.text()
        if task == "select task":
            return
        try:
            if not self.uploaded:
                self.task_hash = _djb2_file(os.path.join(self.GUI_main.task_directory, task + ".py"))
            self.start_button.setEnabled(False)
            self.controls_button.setEnabled(False)
            self.repaint()
            self.board.setup_state_machine(task, uploaded=self.uploaded)
            self.initialise_API()
            self.task = task
            # Set values for any hardware variables.
            task_hw_vars = [task_var for task_var in self.board.sm_info.variables if task_var.startswith("hw_")]
            if task_hw_vars:
                if not hw_vars_defined_in_setup(self, self.board_select.currentText(), task_hw_vars):
                    return
                else:
                    hw_vars_set = set_hardware_variables(self, task_hw_vars)
                    name_len = max([len(v[0]) for v in hw_vars_set])
                    value_len = max([len(v[1]) for v in hw_vars_set])
                    for v_name, v_value, pv_str in hw_vars_set:
                        self.print_to_log(v_name.ljust(name_len + 4) + v_value.ljust(value_len + 4) + pv_str)
            # Configure GUI ready to run.
            if self.controls_dialog:
                self.controls_button.clicked.disconnect()
                self.controls_dialog.deleteLater()
            self.controls_dialog = Controls_dialog(self)
            self.using_json_gui = False
            if "custom_controls_dialog" in self.board.sm_info.variables:
                custom_variables_name = self.board.sm_info.variables["custom_controls_dialog"]
                potential_dialog = Custom_controls_dialog(self, custom_variables_name)
                if potential_dialog.custom_gui == Custom_gui.JSON:
                    self.controls_dialog = potential_dialog
                    self.using_json_gui = True
                elif potential_dialog.custom_gui == Custom_gui.PYFILE:
                    py_gui_file = importlib.import_module(f"controls_dialogs.{custom_variables_name}")
                    importlib.reload(py_gui_file)
                    self.controls_dialog = py_gui_file.Custom_controls_dialog(self, self.board)
            self.controls_button.clicked.connect(self.controls_dialog.exec)
            self.controls_button.setEnabled(True)
            self.task_plot.set_state_machine(self.board.sm_info)
            self.task_info.set_state_machine(self.board.sm_info)
            self.file_groupbox.setEnabled(True)
            self.session_groupbox.setEnabled(True)
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.fresh_task = True
            self.uploaded = True
            self.upload_button.setText("Reset")
            self.upload_button.setIcon(QtGui.QIcon("source/gui/icons/refresh.svg"))
        except PyboardError:
            self.print_to_log("Error setting up state machine.")

    def initialise_API(self):
        # If task file specifies a user API attempt to initialise it.
        self.user_API = None  # Remove previous API.
        # Remove previous API from data consumers.
        self.board.data_consumers = [self.task_plot, self.task_info]
        if "api_class" not in self.board.sm_info.variables:
            return  # Task does not use API.
        API_name = self.board.sm_info.variables["api_class"]
        # Try to import and instantiate the user API.
        try:
            user_module_name = f"api_classes.{API_name}"
            user_module = importlib.import_module(user_module_name)
            importlib.reload(user_module)
        except ModuleNotFoundError:
            self.print_to_log(f"\nCould not find user API module: {user_module_name}")
            return
        if not hasattr(user_module, API_name):
            self.print_to_log(f'\nCould not find user API class "{API_name}" in {user_module_name}')
            return
        try:
            user_API_class = getattr(user_module, API_name)
            self.user_API = user_API_class()
            self.user_API.interface(self.board, self.print_to_log)
            self.board.data_consumers.insert(0, self.user_API)
            self.print_to_log(f"\nInitialised API: {API_name}")
        except Exception as e:
            self.print_to_log(f"Unable to intialise API: {API_name}\nTraceback: {e}")
            raise (PyboardError)

    def select_data_dir(self):
        new_path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select data folder", get_setting("folders", "data")
        )
        if new_path:
            self.data_dir_text.setText(new_path)
            self.custom_dir = True

    def start_task(self):
        recording = self.test_data_path()
        if recording:
            if not self.fresh_task:
                reset_task = QtWidgets.QMessageBox.question(
                    self,
                    "Reset task",
                    "Task has already been run, variables may not have default values.\n\nReset task?",
                    QtWidgets.QMessageBox.StandardButton.Yes,
                    QtWidgets.QMessageBox.StandardButton.No,
                )
                if reset_task == QtWidgets.QMessageBox.StandardButton.Yes:
                    self.setup_task()
                    return
            subject_ID = self.subject_text.text()
            setup_ID = self.board_select.currentText()
            self.board.data_logger.open_data_file(self.data_dir, "run_task", setup_ID, subject_ID)
            self.board.data_logger.copy_task_file(self.data_dir, self.GUI_main.task_directory, "run_task-task_files")
        self.fresh_task = False
        self.running = True
        self.board.start_framework()
        self.task_plot.run_start(recording)
        if self.user_API:
            self.user_API.run_start()
        self.task_select.setEnabled(False)
        self.upload_button.setEnabled(False)
        self.file_groupbox.setEnabled(False)
        self.start_button.setEnabled(False)
        self.board_groupbox.setEnabled(False)
        self.stop_button.setEnabled(True)
        if self.using_json_gui:
            self.controls_dialog.edit_action.setEnabled(False)
        self.print_to_log(f"\nRun started at: {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}\n")
        self.plot_update_timer.start(get_setting("plotting", "update_interval"))
        self.GUI_main.refresh_timer.stop()
        self.GUI_main.settings_action.setEnabled(False)  # settings shouldn't be opened when task is running
        self.GUI_main.tab_widget.setTabEnabled(1, False)  # Disable experiments tab.
        self.GUI_main.tab_widget.setTabEnabled(2, False)  # Disable setups tab.

    def stop_task(self, error=False, stopped_by_task=False):
        self.running = False
        self.plot_update_timer.stop()
        self.GUI_main.refresh_timer.start(self.GUI_main.refresh_interval)
        if not (error or stopped_by_task):
            self.board.stop_framework()
            time.sleep(0.05)
            try:
                self.board.process_data()
                self.print_to_log(f"\nRun stopped at: {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}")
            except PyboardError:
                self.print_to_log("\nError while stopping framework run.")
        self.board.data_logger.close_files()
        self.task_plot.run_stop()
        if self.user_API:
            self.user_API.run_stop()
        self.board_groupbox.setEnabled(True)
        self.file_groupbox.setEnabled(True)
        self.start_button.setEnabled(True)
        self.task_select.setEnabled(True)
        self.upload_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        if self.using_json_gui:
            self.controls_dialog.edit_action.setEnabled(True)
        self.GUI_main.settings_action.setEnabled(True)  # settings shouldn't be opened when task is running
        self.GUI_main.tab_widget.setTabEnabled(1, True)  # Enable setups tab.
        self.GUI_main.tab_widget.setTabEnabled(2, True)  # Enable setups tab.

    # Timer updates

    def plot_update(self):
        """Called every plotting update interval (default=10ms)
        while experiment is running"""
        try:
            self.board.process_data()
            if not self.board.framework_running:
                self.stop_task(stopped_by_task=True)
        except PyboardError:
            self.print_to_log("\nError during framework run.")
            self.stop_task(error=True)
        self.task_plot.update()
        if self.user_API:
            self.user_API.plot_update()

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
            self.print_to_log("\nError: Serial connection with board lost.")
        elif ex_type == PyboardError:
            self.print_to_log("\nError: Unable to execute command.")
        else:
            self.print_to_log(f"\nError: uncaught exception of type: {ex_type}")
        if self.running:
            self.stop_task(error=True)
        self.disconnect()
