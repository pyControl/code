import os
import time
import json
import importlib
from datetime import datetime
from collections import OrderedDict

from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
from serial import SerialException

from source.communication.pycboard import Pycboard, PyboardError
from source.gui.settings import get_setting, user_folder
from source.gui.plotting import Experiment_plot
from source.gui.dialogs import Controls_dialog, Summary_variables_dialog
from source.gui.utility import variable_constants, TaskInfo, parallel_call
from source.gui.custom_controls_dialog import Custom_controls_dialog, Custom_gui
from source.gui.hardware_variables_dialog import set_hardware_variables

# ----------------------------------------------------------------------------------------
#  Run_experiment_tab
# ----------------------------------------------------------------------------------------


class Run_experiment_tab(QtWidgets.QWidget):
    """The run experiment tab is responsible for setting up, running and stopping
    an experiment that has been defined using the configure experiments tab."""

    def __init__(self, parent=None):
        super(QtWidgets.QWidget, self).__init__(parent)

        self.GUI_main = self.parent()
        self.experiment_plot = Experiment_plot(self)

        self.name_label = QtWidgets.QLabel("Experiment name:")
        self.name_text = QtWidgets.QLineEdit()
        self.name_text.setReadOnly(True)
        self.plots_button = QtWidgets.QPushButton("Show plots")
        self.plots_button.setIcon(QtGui.QIcon("source/gui/icons/bar-graph.svg"))
        self.plots_button.clicked.connect(self.experiment_plot.show)
        self.logs_button = QtWidgets.QPushButton("Hide logs")
        self.logs_button.clicked.connect(self.show_hide_logs)
        self.startstopclose_all_button = QtWidgets.QPushButton()
        self.startstopclose_all_button.clicked.connect(self.startstopclose_all)

        self.Hlayout = QtWidgets.QHBoxLayout()
        self.Hlayout.addWidget(self.name_label)
        self.Hlayout.addWidget(self.name_text)
        self.Hlayout.addWidget(self.logs_button)
        self.Hlayout.addWidget(self.plots_button)
        self.Hlayout.addWidget(self.startstopclose_all_button)

        self.scroll_area = QtWidgets.QScrollArea(parent=self)
        self.scroll_area.horizontalScrollBar().setEnabled(False)
        self.scroll_inner = QtWidgets.QFrame(self)
        self.boxes_layout = QtWidgets.QVBoxLayout(self.scroll_inner)
        self.scroll_area.setWidget(self.scroll_inner)
        self.scroll_area.setWidgetResizable(True)

        self.Vlayout = QtWidgets.QVBoxLayout(self)
        self.Vlayout.addLayout(self.Hlayout)
        self.Vlayout.addWidget(self.scroll_area)

        self.subjectboxes = []

        self.plot_update_timer = QtCore.QTimer()  # Timer to regularly call update() during run.
        self.plot_update_timer.timeout.connect(self.plot_update)

    # Main setup experiment function.

    def setup_experiment(self, experiment):
        """Called when an experiment is loaded."""
        # Setup tabs.
        self.experiment = experiment
        self.GUI_main.settings_action.setEnabled(False)  # settings shouldn't be opened when experiment is running
        self.GUI_main.tab_widget.setTabEnabled(0, False)  # Disable run task tab.
        self.GUI_main.tab_widget.setTabEnabled(2, False)  # Disable setups tab.
        self.GUI_main.experiments_tab.setCurrentWidget(self)
        self.experiment_plot.setup_experiment(experiment)
        self.logs_visible = True
        self.logs_button.setText("Hide logs")
        self.startstopclose_all_button.setText("Start all")
        self.startstopclose_all_button.setIcon(QtGui.QIcon("source/gui/icons/play.svg"))
        self.startstopclose_all_button.setEnabled(False)
        # Setup controls box.
        self.name_text.setText(experiment.name)
        self.logs_button.setEnabled(False)
        self.plots_button.setEnabled(False)
        # Setup subjectboxes
        self.subjects = list(experiment.subjects.keys())
        self.num_subjects = len(self.subjects)
        self.subjects.sort(key=lambda s: experiment.subjects[s]["setup"])
        for subject in self.subjects:
            self.subjectboxes.append(Subjectbox(subject, experiment.subjects[subject]["setup"], self))
            self.boxes_layout.addWidget(self.subjectboxes[-1])
        # Create data folder if needed.
        if not os.path.exists(self.experiment.data_dir):
            os.mkdir(self.experiment.data_dir)
        # Load persistent variables if they exist.
        self.pv_path = os.path.join(self.experiment.data_dir, "persistent_variables.json")
        if os.path.exists(self.pv_path):
            with open(self.pv_path, "r") as pv_file:
                self.persistent_variables = json.loads(pv_file.read())
        else:
            self.persistent_variables = {}
        self.GUI_main.app.processEvents()
        # Setup boards.
        self.print_to_logs("Connecting to board.. ")
        parallel_call("connect_to_board", self.subjectboxes)
        if self.setup_has_failed():
            return
        # Hardware test.
        if experiment.hardware_test != "no hardware test":
            reply = QtWidgets.QMessageBox.question(
                self,
                "Hardware test",
                "Run hardware test?",
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            )
            if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                self.print_to_logs("\nStarting hardware test.")
                parallel_call("start_hardware_test", self.subjectboxes)
                if self.setup_has_failed():
                    return
                QtWidgets.QMessageBox.question(
                    self,
                    "Hardware test",
                    "Press OK when finished with hardware test.",
                    QtWidgets.QMessageBox.StandardButton.Ok,
                )
                for box in self.subjectboxes:
                    try:
                        box.board.stop_framework()
                        time.sleep(0.05)
                        box.board.process_data()
                    except PyboardError:
                        box.setup_failed = True
                        box.error()
                if self.setup_has_failed():
                    return
        # Setup task
        self.print_to_logs("\nSetting up task.")
        parallel_call("setup_task", self.subjectboxes)
        if self.setup_has_failed():
            return
        # Copy task file to experiments data folder.
        self.subjectboxes[0].board.data_logger.copy_task_file(self.experiment.data_dir, user_folder("tasks"))
        # Configure GUI ready to run.
        for box in self.subjectboxes:
            box.make_variables_dialog()  # Don't use parallel_call to avoid 'parent in a different thread error'.
            box.set_ready_to_start()
        self.experiment_plot.set_state_machine(self.subjectboxes[0].board.sm_info)
        self.startstopclose_all_button.setEnabled(True)
        self.logs_button.setEnabled(True)
        self.plots_button.setEnabled(True)
        self.setups_started = 0
        self.setups_finished = 0

    def startstopclose_all(self):
        """Called when startstopclose_all_button is clicked."""
        if self.startstopclose_all_button.text() == "Close exp.":
            self.close_experiment()
        elif self.startstopclose_all_button.text() == "Start all":
            for box in self.subjectboxes:
                if box.state == "pre_run":
                    box.start_task()
        elif self.startstopclose_all_button.text() == "Stop all":
            parallel_call("stop_task", [box for box in self.subjectboxes if box.state == "running"])

    def update_startstopclose_button(self):
        """Called when a setup is started or stopped to update the
        startstopclose_all button."""
        if self.setups_finished == self.num_subjects:
            self.startstopclose_all_button.setText("Close exp.")
            self.startstopclose_all_button.setIcon(QtGui.QIcon("source/gui/icons/close.svg"))
        elif self.setups_started == self.num_subjects:
            self.startstopclose_all_button.setText("Stop all")
            self.startstopclose_all_button.setIcon(QtGui.QIcon("source/gui/icons/stop.svg"))

    def stop_experiment(self):
        """Called when all setups have stopped running. Configure GUI update
        timers, store persistent variables and display summary variables."""
        self.plot_update_timer.stop()
        self.GUI_main.refresh_timer.start(self.GUI_main.refresh_interval)
        # Store persistent variables.
        if os.path.exists(self.pv_path):
            with open(self.pv_path, "r") as pv_file:
                persistent_variables = json.loads(pv_file.read())
        else:
            persistent_variables = {}
        for box in self.subjectboxes:
            if box.subject_pers_vars:
                persistent_variables[box.subject] = box.subject_pers_vars
        if persistent_variables:
            with open(self.pv_path, "w") as pv_file:
                pv_file.write(json.dumps(persistent_variables, sort_keys=True, indent=4))
        # Display summary variables.
        summary_variables = [v for v in self.experiment.variables if v["summary"]]
        if summary_variables:
            sv_dict = OrderedDict()
            for box in self.subjectboxes:
                sv_dict[box.subject] = box.subject_sumr_vars
            Summary_variables_dialog(self, sv_dict).show()
        self.startstopclose_all_button.setEnabled(True)

    def setup_has_failed(self):
        """Check if setup has failed on any subjectbox and if so abort experiment."""
        if any([box.setup_failed for box in self.subjectboxes]):
            # Setup has failed abort experiment setup.
            self.plot_update_timer.stop()
            self.GUI_main.refresh_timer.start(self.GUI_main.refresh_interval)
            for box in self.subjectboxes:
                # Stop running boards and close serial connections.
                if box.board:
                    if box.board.framework_running:
                        box.stop_task()
                    box.board.close()
            msg = QtWidgets.QMessageBox()
            msg.setWindowTitle("Error")
            msg.setText("An error occured while setting up experiment")
            msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
            msg.exec()
            self.startstopclose_all_button.setText("Close exp.")
            self.startstopclose_all_button.setEnabled(True)
            return True
        else:
            return False

    def close_experiment(self):
        """Close the Run_experiment_tab and return to Setup_experiment_tab."""
        self.GUI_main.settings_action.setEnabled(True)
        self.GUI_main.tab_widget.setTabEnabled(0, True)  # Enable run task tab.
        self.GUI_main.tab_widget.setTabEnabled(2, True)  # Enable setups tab.
        self.GUI_main.experiments_tab.setCurrentWidget(self.GUI_main.configure_experiment_tab)
        self.experiment_plot.close_experiment()
        # Clear subjectboxes.
        while len(self.subjectboxes) > 0:
            box = self.subjectboxes.pop()
            box.setParent(None)
            box.deleteLater()
        if not self.logs_visible:
            self.boxes_layout.takeAt(self.boxes_layout.count() - 1)  # Remove stretch.

    def show_hide_logs(self):
        """Show/hide the log textboxes in subjectboxes."""
        if self.logs_visible:
            for box in self.subjectboxes:
                box.log_textbox.hide()
            self.boxes_layout.addStretch(100)
            self.logs_visible = False
            self.logs_button.setText("Show logs")
        else:
            for box in self.subjectboxes:
                box.log_textbox.show()
            self.boxes_layout.takeAt(self.boxes_layout.count() - 1)  # Remove stretch.
            self.logs_visible = True
            self.logs_button.setText("Hide logs")

    def plot_update(self):
        """Called every plotting update interval (default=10ms)
        while experiment is running"""
        for box in self.subjectboxes:
            box.update()
        self.experiment_plot.update()
        if self.setups_finished == self.num_subjects:
            self.stop_experiment()

    def print_to_logs(self, print_str):
        """Print to all subjectbox logs."""
        for box in self.subjectboxes:
            box.print_to_log(print_str)


# ----------------------------------------------------------------------------------------
#  Subjectbox
# ----------------------------------------------------------------------------------------


class Subjectbox(QtWidgets.QGroupBox):
    """Groupbox for displaying data from a single subject."""

    def __init__(self, subject, setup_name, parent=None):
        super(QtWidgets.QGroupBox, self).__init__(f"{setup_name} : {subject}", parent=parent)
        self.subject = subject
        self.setup_name = setup_name
        self.GUI_main = self.parent().GUI_main
        self.run_exp_tab = self.parent()
        self.state = "pre_run"
        self.setup_failed = False
        self.print_queue = []
        self.delay_printing = False
        self.subject_pers_vars = {}
        self.subject_sumr_vars = {}

        self.start_stop_button = QtWidgets.QPushButton("Start")
        self.start_stop_button.setIcon(QtGui.QIcon("source/gui/icons/play.svg"))
        self.start_stop_button.setEnabled(False)
        self.start_stop_button.clicked.connect(self.start_stop_task)
        self.status_label = QtWidgets.QLabel("Status:")
        self.status_text = QtWidgets.QLineEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setFixedWidth(50)
        self.time_label = QtWidgets.QLabel("Time:")
        self.time_text = QtWidgets.QLineEdit()
        self.time_text.setReadOnly(True)
        self.time_text.setFixedWidth(50)
        self.task_info = TaskInfo()
        self.controls_button = QtWidgets.QPushButton("Controls")
        self.controls_button.setIcon(QtGui.QIcon("source/gui/icons/filter.svg"))
        self.controls_button.setEnabled(False)
        self.log_textbox = QtWidgets.QTextEdit()
        self.log_textbox.setMinimumHeight(180)
        self.log_textbox.setFont(QtGui.QFont("Courier New", get_setting("GUI", "log_font_size")))
        self.log_textbox.setReadOnly(True)

        self.Vlayout = QtWidgets.QVBoxLayout(self)
        self.Hlayout1 = QtWidgets.QHBoxLayout()
        self.Hlayout1.addWidget(self.start_stop_button)
        self.Hlayout1.addWidget(self.controls_button)
        self.Hlayout1.addWidget(self.status_label)
        self.Hlayout1.addWidget(self.status_text)
        self.Hlayout1.addWidget(self.time_label)
        self.Hlayout1.addWidget(self.time_text)
        self.Hlayout1.addWidget(self.task_info.state_label)
        self.Hlayout1.addWidget(self.task_info.state_text)
        self.Hlayout1.addWidget(self.task_info.event_label)
        self.Hlayout1.addWidget(self.task_info.event_text)
        self.Hlayout2 = QtWidgets.QHBoxLayout()
        self.Hlayout2.addWidget(self.task_info.print_label)
        self.Hlayout2.addWidget(self.task_info.print_text)
        self.Vlayout.addLayout(self.Hlayout1)
        self.Vlayout.addLayout(self.Hlayout2)
        self.Vlayout.addWidget(self.log_textbox)

    def print_to_log(self, print_string, end="\n"):
        if self.delay_printing:
            self.print_queue.append((print_string, end))
            return
        self.log_textbox.moveCursor(QtGui.QTextCursor.MoveOperation.End)
        self.log_textbox.insertPlainText(print_string + end)
        self.log_textbox.moveCursor(QtGui.QTextCursor.MoveOperation.End)
        self.GUI_main.app.processEvents()

    def start_delayed_print(self):
        """Store print output to display later to avoid error
        message when calling print_to_log from different thread."""
        self.print_queue = []
        self.delay_printing = True

    def end_delayed_print(self):
        """Print output stored in print queue to log."""
        self.delay_printing = False
        for p in self.print_queue:
            self.print_to_log(*p)

    def connect_to_board(self):
        """Connect to pyboard and instantiate Pycboard and Data_logger objects."""
        self.serial_port = self.GUI_main.setups_tab.get_port(self.setup_name)
        try:
            self.board = Pycboard(
                self.serial_port,
                print_func=self.print_to_log,
                data_consumers=[self.run_exp_tab.experiment_plot.subject_plots[self.subject], self.task_info],
            )
        except SerialException:
            self.print_to_log("\nConnection failed.")
            self.setup_failed = True
            self.error()
            return
        if not self.board.status["framework"]:
            self.print_to_log("\nInstall pyControl framework on board before running experiment.")
            self.setup_failed = True
            self.error()

    def start_hardware_test(self):
        """Transefer hardware test file to board and start framework running."""
        try:
            self.board.setup_state_machine(self.run_exp_tab.experiment.hardware_test)
            self.board.start_framework(data_output=False)
            time.sleep(0.01)
            self.board.process_data()
        except PyboardError:
            self.setup_failed = True
            self.error()

    def setup_task(self):
        """Load the task state machine and set variables"""
        # Setup task state machine.
        try:
            self.board.setup_state_machine(self.run_exp_tab.experiment.task)
            self.initialise_API()
        except PyboardError:
            self.setup_failed = True
            self.error()
            return
        # Set variables.
        subject_variables = [
            v for v in self.run_exp_tab.experiment.variables if v["subject"] in ("all", "all except", self.subject)
        ]
        self.subject_variables = [  # Remove variables with subject="all except" if value for subject is specified.
            v
            for v in subject_variables
            if not (
                (v["subject"] == "all except")
                and [u for u in subject_variables if u["name"] == v["name"] and u["subject"] == self.subject]
            )
        ]
        task_hw_vars = [task_var for task_var in self.board.sm_info.variables if task_var.startswith("hw_")]
        if self.subject_variables or task_hw_vars:
            self.print_to_log("\nSetting variables.\n")
            self.variables_set_pre_run = []
            try:
                # hardware specific variables
                if task_hw_vars:
                    hw_vars_set = set_hardware_variables(self, task_hw_vars)
                    self.variables_set_pre_run += hw_vars_set
                # persistent variables or value specified in variable table
                subject_pv_dict = self.run_exp_tab.persistent_variables.get(self.subject, {})
                for v in self.subject_variables:
                    if v["persistent"] and v["value"] == "" and v["name"] in subject_pv_dict.keys():  # Use stored value
                        v_value = subject_pv_dict[v["name"]]
                        self.variables_set_pre_run.append((v["name"], str(v_value), "(persistent value)"))
                    else:
                        if v["value"] == "":
                            continue
                        v_value = eval(v["value"], variable_constants)  # Use value from variables table.
                        self.variables_set_pre_run.append((v["name"], v["value"], ""))
                    self.board.set_variable(v["name"], v_value)
                # Print set variables to log.
                if self.variables_set_pre_run:
                    name_len = max([len(v[0]) for v in self.variables_set_pre_run])
                    value_len = max([len(v[1]) for v in self.variables_set_pre_run])
                    for v_name, v_value, pv_str in self.variables_set_pre_run:
                        self.print_to_log(v_name.ljust(name_len + 4) + v_value.ljust(value_len + 4) + pv_str)
            except PyboardError as e:
                self.print_to_log("Setting variable failed. " + str(e))
                self.setup_failed = True
        return

    def initialise_API(self):
        # If task file specifies a user API attempt to initialise it.
        self.user_API = None  # Remove previous API.
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

    def make_variables_dialog(self):
        """Configure variables dialog and ready subjectbox to start experiment."""
        if "custom_controls_dialog" in self.board.sm_info.variables:  # Task uses custon variables dialog
            custom_variables_name = self.board.sm_info.variables["custom_controls_dialog"]
            potential_dialog = Custom_controls_dialog(self, custom_variables_name, is_experiment=True)
            if potential_dialog.custom_gui == Custom_gui.JSON:
                self.controls_dialog = potential_dialog
            elif potential_dialog.custom_gui == Custom_gui.PYFILE:
                py_gui_file = importlib.import_module(f"controls_dialogs.{custom_variables_name}")
                importlib.reload(py_gui_file)
                self.controls_dialog = py_gui_file.Custom_controls_dialog(self, self.board)
        else:  # Board uses standard variables dialog.
            self.controls_dialog = Controls_dialog(self)
        self.controls_button.clicked.connect(self.controls_dialog.exec)

    def set_ready_to_start(self):
        """Set GUI elements ready to start run."""
        self.controls_button.setEnabled(True)
        self.start_stop_button.setEnabled(True)
        self.task_info.set_state_machine(self.board.sm_info)
        self.status_text.setText("Ready")

    def start_stop_task(self):
        """Called when start/stop button on Subjectbox pressed or
        startstopclose_all button is pressed."""
        if self.state == "pre_run":
            self.start_task()
        elif self.state == "running":
            self.stop_task()

    def start_task(self):
        """Start the task running on the Subjectbox's board."""
        self.status_text.setText("Running")
        self.state = "running"
        self.run_exp_tab.experiment_plot.run_start(self.subject)
        self.start_time = datetime.now()
        ex = self.run_exp_tab.experiment
        self.print_to_log("\nStarting experiment.\n")
        self.board.data_logger.open_data_file(ex.data_dir, ex.name, self.setup_name, self.subject, datetime.now())
        self.board.start_framework()
        if self.user_API:
            self.user_API.run_start()
        self.start_stop_button.setText("Stop")
        self.start_stop_button.setIcon(QtGui.QIcon("source/gui/icons/stop.svg"))
        self.run_exp_tab.setups_started += 1
        self.run_exp_tab.GUI_main.refresh_timer.stop()
        self.run_exp_tab.plot_update_timer.start(get_setting("plotting", "update_interval"))
        self.run_exp_tab.update_startstopclose_button()

    def error(self):
        """Set state text to error in red."""
        self.status_text.setText("Error")
        self.status_text.setStyleSheet("color: red;")

    def stop_task(self):
        """Called to stop task or if task stops automatically."""
        if self.board.framework_running:
            self.board.stop_framework()
            time.sleep(0.05)
            try:
                self.board.process_data()
            except PyboardError:
                self.print_to_log("\nError while stopping framework run.")
            if self.user_API:
                self.user_API.run_stop()
        # Read persistent variables.
        subject_pvs = [v for v in self.subject_variables if v["persistent"]]
        if subject_pvs:
            self.print_to_log("\nReading persistent variables.")
            self.subject_pers_vars = {v["name"]: self.board.get_variable(v["name"]) for v in subject_pvs}
        # Read summary variables.
        summary_variables = [v for v in self.run_exp_tab.experiment.variables if v["summary"]]
        if summary_variables:
            self.subject_sumr_vars = {v["name"]: self.board.get_variable(v["name"]) for v in summary_variables}
        # Close data files and disconnect from board.
        self.board.data_logger.close_files()
        self.board.close()
        # Update GUI elements.
        self.state = "post_run"
        self.task_info.state_text.setText("Stopped")
        self.task_info.state_text.setStyleSheet("color: grey;")
        self.status_text.setText("Stopped")
        self.start_stop_button.setEnabled(False)
        self.run_exp_tab.experiment_plot.run_stop(self.subject)
        self.run_exp_tab.setups_finished += 1
        self.run_exp_tab.update_startstopclose_button()

    def update(self):
        """Called regularly while experiment is running."""
        if self.board.framework_running:
            try:
                self.board.process_data()
                if not self.board.framework_running:
                    self.stop_task()
                self.time_text.setText(str(datetime.now() - self.start_time).split(".", maxsplit=1)[0])
            except PyboardError:
                self.stop_task()
                self.error()
            if self.user_API:
                self.user_API.plot_update()
