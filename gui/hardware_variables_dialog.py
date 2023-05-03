import json
import ast
import re
import os
from pathlib import Path
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets


class Hardware_variables_editor(QtWidgets.QDialog):
    """Dialog for editing hadrware specific variables"""

    def __init__(self, setups_tab):
        super(QtWidgets.QDialog, self).__init__(setups_tab)
        layout = QtWidgets.QVBoxLayout(self)
        self.setups_tab = setups_tab

        hlayout = QtWidgets.QHBoxLayout()
        self.variable_cbox = QtWidgets.QComboBox()
        self.variable_cbox.addItems(self.get_hw_vars_from_task_files())
        self.variable_cbox.currentTextChanged.connect(self.update_var_table)
        hlayout.addWidget(QtWidgets.QLabel("Hardware variable:"))
        hlayout.addWidget(self.variable_cbox)
        hlayout.addStretch(1)

        self.var_table = VariablesTable(self)

        hlayout_2 = QtWidgets.QHBoxLayout()
        self.save_button = QtWidgets.QPushButton("")
        self.save_button.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.save_button.setIcon(QtGui.QIcon("gui/icons/save.svg"))
        self.save_button.setEnabled(False)
        hlayout_2.addStretch(1)
        hlayout_2.addWidget(self.save_button)

        layout.addLayout(hlayout)
        layout.addWidget(self.var_table)
        layout.addLayout(hlayout_2)

        close_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+W"), self)
        close_shortcut.activated.connect(self.close)

        self.setMinimumWidth(400)
        self.setMinimumHeight(400)

        self.save_button.clicked.connect(self.var_table.save)

        self.setWindowTitle("Edit Hardware Variables")
        self.update_var_table()

    def update_var_table(self):
        self.var_table.fill_table(self.variable_cbox.currentText())
        self.save_button.setText(f"Save {self.variable_cbox.currentText()} values")
        self.save_button.setEnabled(False)

    def get_hw_vars_from_task_files(self):
        # scan all task files and gather any v.hw_ variables
        hw_vars_from_all_tasks = []
        for dirName, _, fileList in os.walk("tasks"):
            # Loop through all the files in the current directory
            for file_name in fileList:
                if file_name.endswith(".py"):
                    task_path = Path(dirName, file_name)
                    hw_vars_from_all_tasks = hw_vars_from_all_tasks + get_task_hw_vars(task_path)

        return sorted(list(set(hw_vars_from_all_tasks)))

    def closeEvent(self, event):
        if self.var_table.get_table_data() != self.var_table.starting_table:
            reply = QtWidgets.QMessageBox.question(
                self,
                "Changes not saved",
                "Are you sure you want to exit without saving changes?",
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.Cancel,
            )
            if reply == QtWidgets.QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
        self.deleteLater()


class VariablesTable(QtWidgets.QTableWidget):
    """Table of setups and values for the hardware variable that is chosed from the dropdown"""

    def __init__(self, setup_var_editor):
        super(QtWidgets.QTableWidget, self).__init__(1, 2)
        self.setup_var_editor = setup_var_editor
        self.num_selected = len(self.setup_var_editor.setups_tab.get_selected_setups())
        for i in range(self.num_selected - 1):
            self.insertRow(i)
        self.setHorizontalHeaderLabels(["Setup", "Value"])
        self.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setVisible(False)

    def fill_table(self, hw_variable):
        with open(self.setup_var_editor.setups_tab.save_path, "r", encoding="utf-8") as f:
            setups_json = json.loads(f.read())
        selected_setups = self.setup_var_editor.setups_tab.get_selected_setups()

        for row, setup in enumerate(selected_setups):
            setup_name = QtWidgets.QLabel(setup.name)
            value_edit = QtWidgets.QLineEdit()
            value_edit.textChanged.connect(self.refresh_save_button)
            if setups_json[setup.port].get("variables"):
                value = setups_json[setup.port]["variables"].get(hw_variable)
                if value:
                    value_edit.setText(str(value))
            self.setCellWidget(row, 0, setup_name)
            self.setCellWidget(row, 1, value_edit)

        self.starting_table = self.get_table_data()

    def refresh_save_button(self):
        if self.get_table_data() != self.starting_table:
            self.setup_var_editor.save_button.setEnabled(True)
        else:
            self.setup_var_editor.save_button.setEnabled(False)

    def get_table_data(self):
        setup_variables = {}
        for table_row in range(self.num_selected):
            setup_name = self.cellWidget(table_row, 0).text()
            var_text = self.cellWidget(table_row, 1).text()

            try:  # convert strings into types (int,boolean,float etc.) if possible
                value_edit = ast.literal_eval(var_text)
            except (ValueError, SyntaxError):
                value_edit = var_text

            setup_variables[setup_name] = value_edit
        setup_variables["hw_var"] = self.setup_var_editor.variable_cbox.currentText()

        return setup_variables

    def save(self):
        setup_variables = self.get_table_data()
        if setup_variables is not False:
            if setup_variables != self.starting_table:
                hw_var_name = setup_variables["hw_var"]
                for setup_name, hw_val in setup_variables.items():
                    if setup_name != "hw_var":
                        serial_port = self.setup_var_editor.setups_tab.get_port(setup_name)
                        saved_setups = self.setup_var_editor.setups_tab.saved_setups
                        if hw_val:
                            saved_setups[serial_port]["variables"][hw_var_name] = hw_val
                        else:  # if value is left blank, delete it from the "variables" dictionary if it was there previously
                            saved_setups[serial_port]["variables"].pop(hw_var_name, None)

                with open(self.setup_var_editor.setups_tab.save_path, "w", encoding="utf-8") as f:
                    f.write(json.dumps(self.setup_var_editor.setups_tab.saved_setups, sort_keys=True, indent=4))
            self.starting_table = setup_variables
            # self.setup_var_editor.close()
            self.refresh_save_button()


def get_task_hw_vars(task_file_path):
    task_file_content = task_file_path.read_text(encoding="utf-8")
    pattern = "^v\.hw_(?P<vname>\w+)\s*\="
    return list(set(["hw_" + v_name for v_name in re.findall(pattern, task_file_content, flags=re.MULTILINE)]))


def set_hardware_variables(parent, hw_vars_in_task, pre_run_vars):
    # parent is either a run_task tab or an experiment subjectbox
    setups_dict = parent.GUI_main.setups_tab.get_setups_from_json()
    setup_hw_variables = setups_dict[parent.serial_port].get("variables")
    for hw_var in hw_vars_in_task:
        var_name = hw_var
        var_value = setup_hw_variables.get(hw_var)
        pre_run_vars.append((var_name, str(var_value), "(hardware variable)"))
        parent.board.set_variable(var_name, var_value)


def hw_vars_defined_in_setup(parent, setup_name, task_name, task_hw_vars):
    """Check if the setup has all of the task's hardware variables fully defined"""
    serial_port = parent.GUI_main.setups_tab.get_port(setup_name)
    saved_setups = parent.GUI_main.setups_tab.get_setups_from_json()
    setup_hw_variables = saved_setups[serial_port].get("variables")

    for hw_var in task_hw_vars:
        if setup_hw_variables.get(hw_var) is None:
            warning_msg = f"""
"{hw_var}" is not defined for the {setup_name} setup


Either remove "{hw_var}" from the "{task_name}.py" task, or assign a value to "{hw_var}" by editing {setup_name}'s variables.

            """
            QtWidgets.QMessageBox.warning(
                parent,
                "Undefined hardware variable",
                warning_msg,
                QtWidgets.QMessageBox.StandardButton.Ok,
            )
            return False
    return True
