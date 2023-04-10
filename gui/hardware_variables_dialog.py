import json
import ast
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets


class Hardware_variables_editor(QtWidgets.QDialog):
    """Dialog for editing hadrware specific variables"""

    def __init__(self, setup):
        super(QtWidgets.QDialog, self).__init__(setup.setups_tab)
        layout = QtWidgets.QVBoxLayout(self)

        self.var_table = VariablesTable(setup, self)

        hlayout = QtWidgets.QHBoxLayout()
        save_btn = QtWidgets.QPushButton("Save variables")
        save_btn.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        save_btn.setIcon(QtGui.QIcon("gui/icons/save.svg"))
        hlayout.addStretch(1)
        hlayout.addWidget(save_btn)

        layout.addWidget(self.var_table)
        layout.addLayout(hlayout)

        close_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+W"), self)
        close_shortcut.activated.connect(self.close)

        self.setMinimumWidth(600)
        self.setMinimumHeight(400)

        save_btn.clicked.connect(self.var_table.save)

        self.setWindowTitle(f"{setup.name_item.text()} Variables")

    def closeEvent(self, event):
        if self.var_table.get_table_data(do_validation=False) != self.var_table.starting_table:
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


class Variable_row:
    def __init__(self, variable_table, task_var_val):
        self.variable_table = variable_table

        self.remove_button = QtWidgets.QPushButton("remove")
        self.remove_button.setIcon(QtGui.QIcon("gui/icons/remove.svg"))
        ind = QtCore.QPersistentModelIndex(self.variable_table.model().index(self.variable_table.n_variables, 1))
        self.remove_button.clicked.connect(lambda: self.variable_table.remove_row(ind.row()))

        self.variable_edit = QtWidgets.QLineEdit()
        completer = QtWidgets.QCompleter(self.get_existing_hardware_vars())
        self.variable_edit.setCompleter(completer)
        expression = QtCore.QRegularExpression("^[a-zA-Z_][a-zA-Z0-9_]*$")
        valid_python_variable_validator = QtGui.QRegularExpressionValidator(expression)
        self.variable_edit.setValidator(valid_python_variable_validator)
        self.value_edit = QtWidgets.QLineEdit()

        self.column_order = (
            self.variable_edit,
            self.value_edit,
            self.remove_button,
        )

        if task_var_val:  # Set cell values from provided dictionary.
            self.fill_row(task_var_val)

    def fill_row(self, var_val):
        var, val = var_val
        self.variable_edit.setText(str(var))
        self.value_edit.setText(str(val))

    def put_into_table(self, row_index):
        for column, widget in enumerate(self.column_order):
            self.variable_table.removeCellWidget(row_index, column)  # this removes add_button from underneath
            self.variable_table.setCellWidget(row_index, column, widget)

    def get_existing_hardware_vars(self):
        with open(self.variable_table.setups_tab.save_path, "r", encoding="utf-8") as f:
            setups_json = json.loads(f.read())

        existing_vars = []
        for setup_vals in setups_json.values():
            try:
                existing_vars.extend(list(setup_vals["variables"].keys()))
            except KeyError:
                pass
        return list(set(existing_vars))


class VariablesTable(QtWidgets.QTableWidget):
    def __init__(self, setup, setup_var_editor):
        super(QtWidgets.QTableWidget, self).__init__(1, 3)
        self.setup_var_editor = setup_var_editor
        self.setup = setup
        self.setups_tab = setup.setups_tab
        self.serial_port = setup.port_item.text()
        self.setHorizontalHeaderLabels(["Variable", "Value", ""])
        self.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.verticalHeader().setVisible(False)
        self.n_variables = 0

        with open(self.setups_tab.save_path, "r", encoding="utf-8") as f:
            setups_json = json.loads(f.read())
        try:
            setup_vars = setups_json[self.setup.port_item.text()]["variables"]
            if len(setup_vars.keys()):
                for variable, val in setup_vars.items():
                    self.add_row([variable, val])
        except KeyError:
            pass

        self.add_row()
        self.remove_row(self.n_variables - 1)

        self.starting_table = self.get_table_data(do_validation=False)

    def add_row(self, task_var_val=None):
        """Add a row to the table."""
        new_widgets = Variable_row(self, task_var_val)
        new_widgets.put_into_table(row_index=self.n_variables)
        self.insertRow(self.n_variables + 1)
        if not task_var_val:
            add_button = QtWidgets.QPushButton("   add   ")
            add_button.setIcon(QtGui.QIcon("gui/icons/add.svg"))
            add_button.clicked.connect(self.add_row)
            self.setCellWidget(self.n_variables + 1, 2, add_button)
            for i in range(2):  # disable the cells in the add_button row
                disabled_item = QtWidgets.QLineEdit()
                disabled_item.setEnabled(False)
                disabled_item.setStyleSheet("background:#dcdcdc;")
                self.setCellWidget(self.n_variables + 1, i, disabled_item)
        self.n_variables += 1

    def remove_row(self, variable_n):
        """remove a row to the table."""
        self.removeRow(variable_n)
        self.n_variables -= 1

    def get_table_data(self, do_validation):
        setup_variables = {}
        for table_row in range(self.n_variables):
            var_name = self.cellWidget(table_row, 0).text()
            var_text = self.cellWidget(table_row, 1).text()

            # validate that all tasks, variables and values are filled in
            if do_validation:
                if not var_name:
                    QtWidgets.QMessageBox.warning(self, "Error trying to save", f"row {table_row+1} needs a variable")
                    return False
                if not var_text:
                    QtWidgets.QMessageBox.warning(self, "Error trying to save", f"row {table_row+1} needs a value")
                    return False

            try:  # convert strings into types (int,boolean,float etc.) if possible
                value_edit = ast.literal_eval(var_text)
            except ValueError:
                value_edit = var_text
            except SyntaxError:
                value_edit = var_text

            # check that the variable isn't repeated
            if var_name not in setup_variables:
                setup_variables[var_name] = value_edit
            else:
                if do_validation:
                    QtWidgets.QMessageBox.warning(
                        self, "Error trying to save", f"A variable is repeated in row {table_row+1}"
                    )
                    return False
        return setup_variables

    def save(self):
        setup_variables = self.get_table_data(do_validation=True)
        if setup_variables is not False:
            if setup_variables != self.starting_table:
                self.setups_tab.saved_setups[self.serial_port]["variables"] = setup_variables
                with open(self.setups_tab.save_path, "w", encoding="utf-8") as f:
                    f.write(json.dumps(self.setups_tab.saved_setups, sort_keys=True, indent=4))
            self.starting_table = setup_variables
            self.setup_var_editor.close()


def set_hardware_variables(parent, hw_vars_in_task, pre_run_vars):
    """parent is either a run_task tab or an experiment subjectbox"""
    try:
        setups_dict = parent.GUI_main.setups_tab.saved_setups
        setup_hw_variables = setups_dict[parent.serial_port]["variables"]
        for hw_var in hw_vars_in_task:
            try:
                var_name = hw_var
                var_value = setup_hw_variables[hw_var.replace("hw_", "")]
                pre_run_vars.append((var_name, str(var_value), "(hardware variable)"))
                parent.board.set_variable(var_name, var_value)
            except KeyError:
                pass
    except KeyError:
        pass
        # A warning of some type should go here? A Qmessagebox would work for a run_task, but in run_experiment it breaks during a parallel call
