import os
import re
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets

from source.gui.settings import get_setting, user_folder
from source.gui.dialogs import (
    invalid_run_experiment_dialog,
    invalid_save_experiment_dialog,
    unrun_subjects_dialog,
    persistent_value_dialog,
)
from source.gui.utility import (
    TableCheckbox,
    cbox_update_options,
    cbox_set_item,
    null_resize,
    variable_constants,
    init_keyboard_shortcuts,
    NestedMenu,
)
from source.gui.hardware_variables_dialog import get_task_hw_vars, hw_vars_defined_in_setup

# --------------------------------------------------------------------------------
# Experiments_tab
# --------------------------------------------------------------------------------


@dataclass
class Experiment:
    name: str
    task: str
    hardware_test: str
    data_dir: str
    subjects: dict
    variables: list
    subset_warning: bool = None


class Configure_experiment_tab(QtWidgets.QWidget):
    """The configure experiment tab is used to specify an experiment, i.e. a
    set of subjects run on a given task on a set of setups."""

    def __init__(self, parent=None):
        super(QtWidgets.QWidget, self).__init__(parent)

        # Variables
        self.GUI_main = self.parent()
        self.custom_dir = False  # True if data_dir field has been manually edited.
        self.saved_exp_config = None  # Experiment object of last saved/loaded experiment.

        # Experiment Groupbox
        self.experiment_groupbox = QtWidgets.QGroupBox("Experiment")

        self.experiment_select = NestedMenu("select experiment", ".json")
        self.experiment_select.set_callback(self.experiment_changed)

        self.run_button = QtWidgets.QPushButton("Run")
        self.run_button.setIcon(QtGui.QIcon("source/gui/icons/run.svg"))
        new_button = QtWidgets.QPushButton("New")
        new_button.setIcon(QtGui.QIcon("source/gui/icons/add.svg"))
        self.delete_button = QtWidgets.QPushButton("Delete")
        self.delete_button.setIcon(QtGui.QIcon("source/gui/icons/delete.svg"))
        self.save_as_button = QtWidgets.QPushButton("Save as")
        self.save_as_button.setIcon(QtGui.QIcon("source/gui/icons/save_as.svg"))
        self.save_button = QtWidgets.QPushButton("Save")
        self.save_button.setIcon(QtGui.QIcon("source/gui/icons/save.svg"))
        self.save_button.setEnabled(False)
        self.name_text = ""

        experiment_actions_layout = QtWidgets.QHBoxLayout()
        experiment_actions_layout.addWidget(self.experiment_select)
        experiment_actions_layout.setStretchFactor(self.experiment_select, 2)
        experiment_actions_layout.addWidget(new_button)
        experiment_actions_layout.addWidget(self.delete_button)
        experiment_actions_layout.addWidget(QtWidgets.QLabel(" "))
        experiment_actions_layout.addWidget(self.save_as_button)
        experiment_actions_layout.addWidget(self.save_button)
        experiment_actions_layout.addWidget(QtWidgets.QLabel(" "))
        experiment_actions_layout.addWidget(self.run_button)

        task_label = QtWidgets.QLabel("Task")
        self.task_select = NestedMenu("select task", ".py")
        hardware_test_label = QtWidgets.QLabel("Hardware test")
        self.hardware_test_select = NestedMenu("no hardware test", ".py", add_default=True)
        data_dir_label = QtWidgets.QLabel("Data directory")
        self.data_dir_text = QtWidgets.QLineEdit(get_setting("folders", "data"))
        data_dir_button = QtWidgets.QPushButton("")
        data_dir_button.setIcon(QtGui.QIcon("source/gui/icons/folder.svg"))
        data_dir_button.setFixedWidth(30)

        self.experiment_parameters_layout = QtWidgets.QGridLayout()
        self.experiment_parameters_layout.addWidget(task_label, 0, 0, QtCore.Qt.AlignmentFlag.AlignCenter)
        self.experiment_parameters_layout.addWidget(hardware_test_label, 0, 1, QtCore.Qt.AlignmentFlag.AlignCenter)
        self.experiment_parameters_layout.addWidget(data_dir_label, 0, 2, 1, 2, QtCore.Qt.AlignmentFlag.AlignCenter)
        self.experiment_parameters_layout.addWidget(self.task_select, 1, 0)
        self.experiment_parameters_layout.addWidget(self.hardware_test_select, 1, 1)
        self.experiment_parameters_layout.addWidget(self.data_dir_text, 1, 2)
        self.experiment_parameters_layout.addWidget(data_dir_button, 1, 3)

        expbox_Vlayout = QtWidgets.QVBoxLayout(self.experiment_groupbox)
        expbox_Vlayout.addLayout(experiment_actions_layout)
        expbox_Vlayout.addWidget(QtWidgets.QLabel("<hr>"))
        expbox_Vlayout.addLayout(self.experiment_parameters_layout)

        config_tabs = QtWidgets.QTabWidget()
        # Subjects Tab
        self.subjects_tab = QtWidgets.QWidget()
        subjectsbox_layout = QtWidgets.QGridLayout(self.subjects_tab)
        self.subset_warning_checkbox = QtWidgets.QCheckBox("Warn me if any subjects will not be run")
        self.subset_warning_checkbox.setChecked(True)
        subjectsbox_layout.addWidget(self.subset_warning_checkbox, 0, 0)
        self.subjects_table = SubjectsTable(self)
        subjectsbox_layout.addWidget(self.subjects_table, 1, 0, 1, 2)
        subjectsbox_layout.setColumnStretch(1, 1)

        # Variables Tab
        self.variables_tab = QtWidgets.QWidget()
        variablesbox_layout = QtWidgets.QVBoxLayout(self.variables_tab)
        self.variables_table = VariablesTable(self)
        self.task_select.set_callback(self.variables_table.task_changed)
        variablesbox_layout.addWidget(self.variables_table)

        config_tabs.addTab(self.subjects_tab, "Subjects")
        config_tabs.addTab(self.variables_tab, "Variables")

        # Connect signals.
        self.data_dir_text.textEdited.connect(lambda: setattr(self, "custom_dir", True))
        data_dir_button.clicked.connect(self.select_data_dir)
        new_button.clicked.connect(self.create_new_experiment)
        self.delete_button.clicked.connect(self.delete_experiment)
        self.save_button.clicked.connect(self.save_experiment)
        self.save_as_button.clicked.connect(lambda: self.create_new_experiment(from_existing=True))
        self.run_button.clicked.connect(self.run_experiment)

        # Keyboard shortcuts
        shortcut_dict = {"Ctrl+s": self.save_experiment}
        init_keyboard_shortcuts(self, shortcut_dict)

        # # Main layout
        configure_exp_layout = QtWidgets.QGridLayout()
        configure_exp_layout.addWidget(self.experiment_groupbox, 0, 0)
        configure_exp_layout.addWidget(config_tabs, 1, 0, 1, 2)
        self.setLayout(configure_exp_layout)

        # Initialise variables.
        self.saved_exp_config = self.get_exp_config()

        self.experiment_enable(False)

    def experiment_enable(self, do_enable=True):
        self.subjects_tab.setEnabled(do_enable)
        self.variables_tab.setEnabled(do_enable)
        self.experiment_parameters_layout.setEnabled(do_enable)
        self.run_button.setEnabled(do_enable)
        self.delete_button.setEnabled(do_enable)
        self.save_as_button.setEnabled(do_enable)

    def select_data_dir(self):
        new_path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select data folder", get_setting("folders", "data")
        )
        if new_path:
            self.data_dir_text.setText(new_path)
            self.custom_dir = True

    def experiment_changed(self, experiment_name):
        if experiment_name in self.GUI_main.available_experiments:
            if not self.save_changes_dialog():
                return
            self.load_experiment(experiment_name)

    def refresh(self):
        """Called periodically when not running to update available task, ports, experiments."""
        if self.GUI_main.available_tasks_changed:
            self.task_select.update_menu(user_folder("tasks"))
            self.hardware_test_select.update_menu(user_folder("tasks"))
            self.GUI_main.available_tasks_changed = False
        if self.GUI_main.available_experiments_changed:
            self.experiment_select.update_menu(user_folder("experiments"))
            self.GUI_main.available_experiments_changed = False
        if self.GUI_main.setups_tab.available_setups_changed:
            self.subjects_table.all_setups = set(self.GUI_main.setups_tab.setup_names)
            self.subjects_table.update_available_setups()
        if self.saved_exp_config != self.get_exp_config() and self.experiment_select.text() != "select experiment":
            self.save_button.setEnabled(True)
        else:
            self.save_button.setEnabled(False)
        if self.GUI_main.data_dir_changed:
            if (self.name_text == "") and not self.custom_dir:
                self.data_dir_text.setText(get_setting("folders", "data"))

    def get_exp_config(self, filtered=False):
        """Return the current state of the experiments tab as an Experiment object."""
        return Experiment(
            name=self.name_text,
            task=str(self.task_select.text()),
            hardware_test=str(self.hardware_test_select.text()),
            data_dir=self.data_dir_text.text(),
            subjects=self.subjects_table.get_subjects_dict(filtered),
            variables=self.variables_table.get_variables_list(),
            subset_warning=self.subset_warning_checkbox.isChecked(),
        )

    def reset(self):
        self.name_text = ""
        self.data_dir_text.setText(get_setting("folders", "data"))
        self.custom_dir = False
        self.subjects_table.reset()
        self.variables_table.reset()
        self.task_select.setText("select task")
        self.hardware_test_select.setText("no hardware test")
        self.subset_warning_checkbox.setChecked(True)
        self.saved_exp_config = self.get_exp_config()

    def create_new_experiment(self, from_existing=False):
        """Clear experiment configuration."""
        savefilename = QtWidgets.QFileDialog.getSaveFileName(
            self, "", user_folder("experiments"), ("JSON files (*.json)")
        )[0]
        if savefilename != "":
            if not from_existing:
                self.reset()
            new_path = Path(savefilename)
            if str(new_path).find(user_folder("experiments")) < 0:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Unable to create experiment",
                    f'New experiment files must be inside the "{user_folder("experiments")}" folder',
                    QtWidgets.QMessageBox.StandardButton.Ok,
                )
                return
            exp_name = str(new_path.parent / new_path.stem).split(user_folder("experiments"))[1][1:]
            self.name_text = exp_name
            self.experiment_select.setText(exp_name)
            new_data_dir = Path(get_setting("folders", "data")) / exp_name
            try:  # make new data dir if it doesn't exist
                os.makedirs(new_data_dir)
            except FileExistsError:
                pass
            self.data_dir_text.setText(str(new_data_dir))
            self.save_experiment()
            self.experiment_enable(True)

    def delete_experiment(self):
        """Delete an experiment file after dialog to confirm deletion."""
        exp_path = os.path.join(user_folder("experiments"), self.name_text + ".json")
        if os.path.exists(exp_path):
            reply = QtWidgets.QMessageBox.question(
                self,
                "Delete experiment",
                f"Delete experiment '{self.name_text}'",
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.Cancel,
            )
            if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                self.experiment_select.setText("select experiment")
                self.experiment_enable(False)
                self.reset()
                os.remove(exp_path)

    def save_experiment(self, from_dialog=False):
        """Check that experiment setup/subject combinations are valid and unique"""
        subjects_dict = {}
        for table_row in range(self.subjects_table.num_subjects):
            try:
                subject = str(self.subjects_table.item(table_row, 2).text())
                if len(subject) == 0:
                    invalid_save_experiment_dialog(self.subjects_table, "All subjects must have names.")
                    return False
            except AttributeError:
                invalid_save_experiment_dialog(self.subjects_table, "All subjects must have names.")
                return False
            if subject in subjects_dict:
                invalid_save_experiment_dialog(self.subjects_table, "Duplicate subjects.")
                return False
            setup = str(self.subjects_table.cellWidget(table_row, 1).currentText())
            run = self.subjects_table.cellWidget(table_row, 0).isChecked()
            subjects_dict[subject] = {"setup": setup, "run": run}  # add dict subject entry
        # Store the current state of the experiment tab as a JSON object
        # saved in the experiments folder as .json file.
        experiment = self.get_exp_config()
        file_name = self.name_text + ".json"
        exp_path = os.path.join(user_folder("experiments"), file_name)
        with open(exp_path, "w", encoding="utf-8") as exp_file:
            exp_file.write(json.dumps(asdict(experiment), sort_keys=True, indent=4))
        if not from_dialog:
            self.experiment_select.setText(experiment.name)
        self.saved_exp_config = experiment
        self.save_button.setEnabled(False)
        return True

    def load_experiment(self, experiment_name):
        """Load experiment  .json file and set fields of experiment tab."""
        exp_path = os.path.join(user_folder("experiments"), experiment_name + ".json")
        self.name_text = experiment_name
        with open(exp_path, "r", encoding="utf-8") as exp_file:
            exp_dict = json.loads(exp_file.read())
            experiment = Experiment(**exp_dict)
        if experiment.task in self.GUI_main.available_tasks:
            self.task_select.setText(experiment.task)
        else:
            self.task_select.setText("select task")
        if experiment.hardware_test in self.GUI_main.available_tasks:
            self.hardware_test_select.setText(experiment.hardware_test)
        else:
            self.hardware_test_select.setText("no hardware test")
        self.experiment_select.setText(experiment.name)
        if experiment.subset_warning is None:  # Experiment file created with GUI version <= 1.5.
            self.subset_warning_checkbox.setChecked(True)
            subjects_dict = {subject: {"run": True, "setup": setup} for setup, subject in experiment.subjects.items()}
            self.subjects_table.set_from_dict(subjects_dict)
        else:
            self.subset_warning_checkbox.setChecked(experiment.subset_warning)
            self.subjects_table.set_from_dict(experiment.subjects)

        self.variables_table.task_changed(experiment.task)
        self.data_dir_text.setText(experiment.data_dir)
        self.variables_table.set_from_list(experiment.variables)
        self.saved_exp_config = experiment
        self.save_button.setEnabled(False)
        self.experiment_enable(True)

    def run_experiment(self):
        """Check that the experiment is valid. Prompt user to save experiment if
        it is new or has been edited. Then run experiment."""
        experiment = self.get_exp_config(filtered=True)
        if not experiment.name:
            invalid_run_experiment_dialog(self, "Experiment must have a name.")
            return
        # Validate data path.
        if not (os.path.exists(experiment.data_dir) or os.path.exists(os.path.split(experiment.data_dir)[0])):
            invalid_run_experiment_dialog(self, "Data directory not available.")
            return
        # Validate task and hardware defintion.
        if experiment.task == "select task":
            invalid_run_experiment_dialog(self, "Task not selected.")
            return
        if experiment.task not in self.GUI_main.available_tasks:
            invalid_run_experiment_dialog(self, f"Task file '{experiment.task}.py' not found.")
            return
        if (
            experiment.hardware_test != "no hardware test"
            and experiment.hardware_test not in self.GUI_main.available_tasks
        ):
            invalid_run_experiment_dialog(self, f"Hardware test file '{experiment.hardware_test}.py' not found.")
            return
        # Validate setups and subjects.
        if not experiment.subjects:
            invalid_run_experiment_dialog(self, "No subjects selected to run")
            return
        setups = [experiment.subjects[subject]["setup"] for subject in experiment.subjects]
        subjects = experiment.subjects.keys()
        if len(setups) == 0:
            invalid_run_experiment_dialog(self, "No subjects specified.")
            return
        if min([len(subject) for subject in subjects]) == 0:
            invalid_run_experiment_dialog(self, "All subjects must have names.")
            return
        if len(set(setups)) < len(setups):
            invalid_run_experiment_dialog(self, "Repeated Setup. Cannot run two experiments on the same Setup.")
            return
        for setup in setups:
            if setup not in self.GUI_main.setups_tab.setup_names:
                invalid_run_experiment_dialog(self, f"Setup '{setup}' not available.")
                return
        # Validate variables.
        persistent_value_vars = []
        for v in experiment.variables:
            if v["value"]:
                try:
                    eval(v["value"], variable_constants)
                except:
                    invalid_run_experiment_dialog(self, f"Invalid value '{v['value']}' for variable '{v['name']}'.")
                    return
            if v["persistent"] and v["value"]:
                persistent_value_vars.append(v["name"])
        if persistent_value_vars:
            okay = persistent_value_dialog(self, persistent_value_vars)
            if not okay:
                return
        # Validate hw_variables
        task_file = Path(user_folder("tasks"), experiment.task + ".py")
        task_hw_vars = get_task_hw_vars(task_file)
        if task_hw_vars:
            for setup_name in setups:
                if not hw_vars_defined_in_setup(self, setup_name, task_hw_vars):
                    return

        if self.subset_warning_checkbox.isChecked():
            all_subjects = self.get_exp_config().subjects
            will_not_run = ""
            for subject in all_subjects.keys():
                if all_subjects[subject]["run"] is False:
                    will_not_run += f"{subject}\n"
            if will_not_run != "":
                okay = unrun_subjects_dialog(self, will_not_run)
                if not okay:
                    return
        if not self.save_changes_dialog():
            return
        self.GUI_main.run_experiment_tab.setup_experiment(experiment)

    def save_changes_dialog(self):
        """Dialog to save experiment if it has been edited.  Returns False if
        cancel is selected, True otherwise."""
        if self.experiment_select.text() == "select experiment":
            return True
        if self.saved_exp_config == self.get_exp_config():
            return True  # Experiment has not been edited.
        exp_path = os.path.join(user_folder("experiments"), self.name_text + ".json")
        dialog_text = None
        if not os.path.exists(exp_path):
            dialog_text = "Experiment not saved, save experiment?"
        else:
            dialog_text = "Experiment edited, save experiment?"
        reply = QtWidgets.QMessageBox.question(
            self,
            "Save experiment",
            dialog_text,
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No
            | QtWidgets.QMessageBox.StandardButton.Cancel,
        )
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            was_saved = self.save_experiment(from_dialog=True)
            if not was_saved:
                invalid_run_experiment_dialog(self, "Failed to save experiment")
                return False
        elif reply == QtWidgets.QMessageBox.StandardButton.Cancel:
            return False
        return True


# ---------------------------------------------------------------------------------


class SubjectsTable(QtWidgets.QTableWidget):
    """Table for specifying the setups and subjects used in experiment."""

    def __init__(self, config_experiment_tab):
        super(QtWidgets.QTableWidget, self).__init__(1, 4, parent=config_experiment_tab)
        self.setHorizontalHeaderLabels(["Run", "Setup", "Subject", ""])
        self.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.verticalHeader().setVisible(False)
        self.cellChanged.connect(self.cell_changed)
        self.all_setups = set([])
        self.available_setups = []
        self.unallocated_setups = []
        self.subjects = []
        self.num_subjects = 0
        self.add_subject()
        self.config_experiment_tab = config_experiment_tab

    def reset(self):
        """Clear all rows of table."""
        for i in reversed(range(self.num_subjects)):
            self.removeRow(i)
        self.available_setups = sorted(list(self.all_setups))
        self.subjects = []
        self.num_subjects = 0

    def cell_changed(self, row, column):
        """If cell in subject row is changed, update subjects list and variables table."""
        if column == 2:
            self.update_subjects()
            self.config_experiment_tab.variables_table.update_available()

    def add_subject(self, setup=None, subject=None, do_run=None):
        """Add row to table allowing extra subject to be specified."""
        setup_cbox = QtWidgets.QComboBox()
        setup_cbox.addItems(self.available_setups if self.available_setups else ["select setup"])
        if self.unallocated_setups:
            setup_cbox.setCurrentIndex(self.available_setups.index(self.unallocated_setups[0]))
        setup_cbox.activated.connect(self.update_available_setups)
        remove_button = QtWidgets.QPushButton("remove")
        remove_button.setIcon(QtGui.QIcon("source/gui/icons/remove.svg"))
        ind = QtCore.QPersistentModelIndex(self.model().index(self.num_subjects, 2))
        remove_button.clicked.connect(lambda: self.remove_subject(ind.row()))
        add_button = QtWidgets.QPushButton("   add   ")
        add_button.setIcon(QtGui.QIcon("source/gui/icons/add.svg"))
        add_button.clicked.connect(self.add_subject)
        run_checkbox = TableCheckbox()
        if do_run is None:
            run_checkbox.setChecked(True)  # new subjects are set to "Run" by default
        else:
            run_checkbox.setChecked(do_run)
        self.setCellWidget(self.num_subjects, 0, run_checkbox)
        self.setCellWidget(self.num_subjects, 1, setup_cbox)
        self.setCellWidget(self.num_subjects, 3, remove_button)
        self.insertRow(self.num_subjects + 1)
        self.setCellWidget(self.num_subjects + 1, 3, add_button)
        if setup:
            cbox_set_item(setup_cbox, setup)
        if subject:
            subject_item = QtWidgets.QTableWidgetItem()
            subject_item.setText(subject)
            self.setItem(self.num_subjects, 2, subject_item)
        self.num_subjects += 1
        self.update_available_setups()
        null_resize(self)

    def remove_subject(self, subject_n):
        """Remove specified row from table"""
        if self.item(subject_n, 2):
            s_name = self.item(subject_n, 2).text()
            self.config_experiment_tab.variables_table.remove_subject(s_name)
        self.removeRow(subject_n)
        self.num_subjects -= 1
        self.update_available_setups()
        self.update_subjects()
        null_resize(self)

    def update_available_setups(self, i=None):
        """Update which setups are available for selection in dropdown menus."""
        selected_setups = set([str(self.cellWidget(s, 1).currentText()) for s in range(self.num_subjects)])
        self.available_setups = sorted(list(self.all_setups))
        self.unallocated_setups = sorted(list(self.all_setups - selected_setups))
        for s in range(self.num_subjects):
            cbox_update_options(self.cellWidget(s, 1), self.available_setups)

    def update_subjects(self):
        """Update the subjects list"""
        self.subjects = [str(self.item(s, 2).text()) for s in range(self.num_subjects) if self.item(s, 2)]

    def get_subjects_dict(self, filtered=False):
        """Return setups and subjects as a dictionary {subject:{'setup':setup,'run':run}}"""
        subjects_dict = {}
        for s in range(self.num_subjects):
            try:
                subject = str(self.item(s, 2).text())
            except AttributeError:
                return
            setup = str(self.cellWidget(s, 1).currentText())
            run = self.cellWidget(s, 0).isChecked()
            if filtered:
                if run:
                    subjects_dict[subject] = {"setup": setup, "run": run}  # add dict subject entry
            else:
                subjects_dict[subject] = {"setup": setup, "run": run}  # add dict subject entry
        return subjects_dict

    def set_from_dict(self, subjects_dict):
        """Fill table with subjects and setups from subjects_dict"""
        self.reset()
        for subject in subjects_dict:
            setup = subjects_dict[subject]["setup"]
            do_run = subjects_dict[subject]["run"]
            self.add_subject(setup, subject, do_run)
        self.update_available_setups()
        self.update_subjects()


# -------------------------------------------------------------------------------


class VariablesTable(QtWidgets.QTableWidget):
    """Class for specifying task variables that are set to non-default values."""

    def __init__(self, config_experiment_tab):
        super(QtWidgets.QTableWidget, self).__init__(1, 6, parent=config_experiment_tab)
        self.subjects_table = config_experiment_tab.subjects_table
        self.setHorizontalHeaderLabels(["Variable", "Subject", "Value", "Persistent", "Summary", ""])
        self.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.verticalHeader().setVisible(False)
        add_button = QtWidgets.QPushButton("   add   ")
        add_button.setIcon(QtGui.QIcon("source/gui/icons/add.svg"))
        add_button.clicked.connect(self.add_variable)
        self.setCellWidget(0, 5, add_button)
        self.n_variables = 0
        self.variable_names = []
        self.available_variables = []
        # Which subjects have values assigned for each variable.
        self.assigned = {v_name: [] for v_name in self.variable_names}

    def reset(self):
        """Clear all rows of table."""
        for i in reversed(range(self.n_variables)):
            self.removeRow(i)
        self.n_variables = 0
        self.assigned = {v_name: [] for v_name in self.variable_names}

    def add_variable(self, var_dict=None):
        """Add a row to the variables table."""
        variable_cbox = QtWidgets.QComboBox()
        variable_cbox.activated.connect(self.update_available)
        subject_cbox = QtWidgets.QComboBox()
        subject_cbox.activated.connect(self.update_available)
        persistent = TableCheckbox()
        summary = TableCheckbox()
        remove_button = QtWidgets.QPushButton("remove")
        ind = QtCore.QPersistentModelIndex(self.model().index(self.n_variables, 2))
        remove_button.clicked.connect(lambda: self.remove_variable(ind.row()))
        remove_button.setIcon(QtGui.QIcon("source/gui/icons/remove.svg"))
        add_button = QtWidgets.QPushButton("   add   ")
        add_button.setIcon(QtGui.QIcon("source/gui/icons/add.svg"))
        add_button.clicked.connect(self.add_variable)
        self.insertRow(self.n_variables + 1)
        self.setCellWidget(self.n_variables, 0, variable_cbox)
        self.setCellWidget(self.n_variables, 1, subject_cbox)
        self.setCellWidget(self.n_variables, 3, persistent)
        self.setCellWidget(self.n_variables, 4, summary)
        self.setCellWidget(self.n_variables, 5, remove_button)
        self.setCellWidget(self.n_variables + 1, 5, add_button)
        if var_dict:  # Set cell values from provided dictionary.
            variable_cbox.addItems([var_dict["name"]])
            subject_cbox.addItems([var_dict["subject"]])
            value_item = QtWidgets.QTableWidgetItem()
            value_item.setText(var_dict["value"])
            self.setItem(self.n_variables, 2, value_item)
            persistent.setChecked(var_dict["persistent"])
            summary.setChecked(var_dict["summary"])
        else:
            variable_cbox.addItems(["select variable"] + self.available_variables)
            if self.n_variables > 0:  # Set variable to previous variable if available.
                v_name = str(self.cellWidget(self.n_variables - 1, 0).currentText())
                if v_name in self.available_variables:
                    cbox_set_item(variable_cbox, v_name)
                    subject_cbox.addItems(self.available_subjects(v_name))
        self.n_variables += 1
        self.update_available()
        null_resize(self)

    def remove_variable(self, variable_n):
        self.removeRow(variable_n)
        self.n_variables -= 1
        self.update_available()
        null_resize(self)

    def remove_subject(self, subject):
        for i in reversed(range(self.n_variables)):
            if self.cellWidget(i, 1).currentText() == subject:
                self.removeRow(i)
                self.n_variables -= 1
        self.update_available()
        null_resize(self)

    def update_available(self, i=None):
        # Find out what variable-subject combinations already assigned.
        self.assigned = {v_name: [] for v_name in self.variable_names}
        for v in range(self.n_variables):
            v_name = self.cellWidget(v, 0).currentText()
            s_name = self.cellWidget(v, 1).currentText()
            if s_name and s_name not in self.subjects_table.subjects + ["all", "all except"]:
                cbox_set_item(self.cellWidget(v, 1), "", insert=True)  # Remove subjects no longer in experiment.
                continue
            if v_name != "select variable" and s_name:
                self.assigned[v_name].append(s_name)
        # Update the variables available:
        fully_asigned_variables = [
            v_n for v_n in self.assigned.keys() if ({"all", "all except"} & set(self.assigned[v_n]))
        ]
        if self.subjects_table.subjects:
            fully_asigned_variables += [
                v_n for v_n in self.assigned.keys() if set(self.assigned[v_n]) == set(self.subjects_table.subjects)
            ]
        self.available_variables = sorted(list(set(self.variable_names) - set(fully_asigned_variables)), key=str.lower)
        # Update the available options in the variable and subject comboboxes.
        for v in range(self.n_variables):
            v_name = self.cellWidget(v, 0).currentText()
            s_name = self.cellWidget(v, 1).currentText()
            cbox_update_options(self.cellWidget(v, 0), self.available_variables)
            if v_name != "select variable":
                # If variable has no subjects assigned, set subjects to 'all'.
                if not self.assigned[v_name]:
                    self.cellWidget(v, 1).addItems(["all"])
                    self.assigned[v_name] = ["all"]
                    self.available_variables.remove(v_name)
                    s_name = "all"
                cbox_update_options(self.cellWidget(v, 1), self.available_subjects(v_name, s_name))

    def available_subjects(self, v_name, s_name=None):
        """Return sorted list of the subjects that are available for selection
        for the specified variable v_name given that subject s_name is already
        selected."""
        if (not self.assigned[v_name]) or self.assigned[v_name] == [s_name]:
            available_subjects = ["all"] + sorted(self.subjects_table.subjects)
        elif s_name == "all":
            sorted(self.subjects_table.subjects)
        else:
            available_subjects = sorted(list(set(self.subjects_table.subjects) - set(self.assigned[v_name])))
            if len(available_subjects) + int(s_name in self.subjects_table.subjects) > 1:
                available_subjects += ["all except"]
        return available_subjects

    def task_changed(self, task):
        """Remove variables that are not defined in the new task."""
        pattern = "[\n\r\.]v\.(?P<vname>\w+)\s*\="
        try:
            with open(os.path.join(user_folder("tasks"), task + ".py"), "r", encoding="utf-8") as file:
                file_content = file.read()
        except FileNotFoundError:
            return
        self.variable_names = list(
            set(
                [
                    v_name
                    for v_name in re.findall(pattern, file_content)
                    if not v_name.endswith("___")
                    and v_name != "custom_controls_dialog"
                    and not v_name.startswith("hw_")
                    and v_name != "api_class"
                ]
            )
        )
        # Remove variables that are not in new task.
        for i in reversed(range(self.n_variables)):
            if self.cellWidget(i, 0).currentText() not in self.variable_names:
                self.removeRow(i)
                self.n_variables -= 1
        null_resize(self)
        self.update_available()

    def get_variables_list(self):
        """Return the variables table contents as a list of dictionaries."""
        return [
            {
                "name": str(self.cellWidget(v, 0).currentText()),
                "subject": str(self.cellWidget(v, 1).currentText()),
                "value": str(self.item(v, 2).text()) if self.item(v, 2) else "",
                "persistent": self.cellWidget(v, 3).isChecked(),
                "summary": self.cellWidget(v, 4).isChecked(),
            }
            for v in range(self.n_variables)
        ]

    def set_from_list(self, variables_list):
        """Fill the variables table with values from variables_list"""
        self.reset()
        for var_dict in variables_list:
            self.add_variable(var_dict)
        self.update_available()
