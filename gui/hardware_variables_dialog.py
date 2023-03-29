import os
import re
import json
import ast
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
from gui.settings import get_setting
from gui.utility import cbox_update_options, NestedMenu, cbox_set_item

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

        self.setMinimumWidth(700)
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

        self.task_select = NestedMenu("select task", ".py")
        self.task_select.update_menu(get_setting("folders", "tasks"))
        self.task_select.set_callback(self.variable_table.task_changed)

        self.remove_button = QtWidgets.QPushButton("remove")
        self.remove_button.setIcon(QtGui.QIcon("gui/icons/remove.svg"))
        ind = QtCore.QPersistentModelIndex(self.variable_table.model().index(self.variable_table.n_variables, 1))
        self.remove_button.clicked.connect(lambda: self.variable_table.remove_row(ind.row()))

        self.variable_cbox = QtWidgets.QComboBox()

        self.var_value = QtWidgets.QLineEdit()

        self.column_order = (
            self.task_select,
            self.variable_cbox,
            self.var_value,
            self.remove_button,
        )

        if task_var_val:  # Set cell values from provided dictionary.
            self.fill_row(task_var_val)

    def fill_row(self, task_var_val):
        task, var, val = task_var_val
        self.task_select.setText(task)
        cbox_update_options(self.variable_cbox, list(self.variable_table.get_vars(task)))
        cbox_set_item(self.variable_cbox, var)
        self.var_value.setText(str(val))

    def put_into_table(self, row_index):
        for column, widget in enumerate(self.column_order):
            self.variable_table.removeCellWidget(row_index, column)  # this removes add_button from underneath
            self.variable_table.setCellWidget(row_index, column, widget)


class VariablesTable(QtWidgets.QTableWidget):
    def __init__(self, setup, setup_var_editor):
        super(QtWidgets.QTableWidget, self).__init__(1, 4)
        self.setup_var_editor = setup_var_editor
        self.setup = setup
        self.setups_tab = setup.setups_tab
        self.serial_port = setup.port_item.text()
        self.setHorizontalHeaderLabels(["Task", "Variable", "Value", ""])
        self.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.verticalHeader().setVisible(False)
        self.n_variables = 0

        with open(self.setups_tab.save_path, "r", encoding="utf-8") as f:
            setups_json = json.loads(f.read())

        try:
            setup_vars = setups_json[self.setup.port_item.text()]["variables"]
            if len(setup_vars.keys()):
                for task in setup_vars.keys():
                    for variable, val in setup_vars[task].items():
                        self.add_row([task, variable, val])
            self.add_row()
        except KeyError:
            self.add_row()

        self.remove_row(self.n_variables - 1)

        for i in range(3):
            disabled_item = QtWidgets.QTableWidgetItem("")
            disabled_item.setFlags(disabled_item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            self.setItem(self.n_variables, i, disabled_item)

        self.starting_table = self.get_table_data(do_validation=False)

    def task_changed(self, task):
        variables_box = self.cellWidget(self.currentRow(), 1)
        variables_box.clear()
        cbox_update_options(variables_box, list(self.get_vars(task)))

        var_value = self.cellWidget(self.currentRow(), 2)
        var_value.setText("")

    def get_vars(self, task):
        pattern = "[\n\r]v\.(?P<vname>\w+)\s*\="
        try:
            with open(os.path.join(get_setting("folders", "tasks"), task + ".py"), "r", encoding="utf-8") as file:
                file_content = file.read()
        except FileNotFoundError:
            return
        # get list of variables. ignore private variables and the custom_variables_dialog variable
        return set(
            [
                v_name
                for v_name in re.findall(pattern, file_content)
                if not v_name[-3:] == "___" and v_name != "custom_variables_dialog"
            ]
        )

    def add_row(self, task_var_val=None):
        """Add a row to the table."""
        new_widgets = Variable_row(self, task_var_val)
        new_widgets.put_into_table(row_index=self.n_variables)
        try:
            # try using the same task for the new row as was chosen in the last row
            # (saves time from having to repeatedly choose the same task)
            last_added_task = self.cellWidget(self.currentRow() - 1, 0).text()
            if last_added_task != "select task":
                new_widgets.fill_row([last_added_task, "", ""])
        except AttributeError:
            pass
        self.insertRow(self.n_variables + 1)
        if not task_var_val:
            add_button = QtWidgets.QPushButton("   add   ")
            add_button.setIcon(QtGui.QIcon("gui/icons/add.svg"))
            add_button.clicked.connect(self.add_row)
            self.setCellWidget(self.n_variables + 1, 3, add_button)
            for i in range(3):  # disable the cells on the add_button row
                disabled_item = QtWidgets.QTableWidgetItem("")
                disabled_item.setFlags(disabled_item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
                self.setItem(self.n_variables + 1, i, disabled_item)
        self.n_variables += 1

    def remove_row(self, variable_n):
        """remove a row to the table."""
        self.removeRow(variable_n)
        self.n_variables -= 1

    def get_table_data(self, do_validation):
        setup_variables = {}
        for table_row in range(self.n_variables):
            task_name = self.cellWidget(table_row, 0).text()
            var_name = self.cellWidget(table_row, 1).currentText()
            var_text = self.cellWidget(table_row, 2).text()

            # validate that all tasks, variables and values are filled in
            if do_validation:
                if task_name == "select task":
                    QtWidgets.QMessageBox.warning(
                        self, "Error trying to save", f"row {table_row} needs a task selection"
                    )
                    return False
                if not var_name:
                    QtWidgets.QMessageBox.warning(
                        self, "Error trying to save", f"row {table_row} needs a variable selection"
                    )
                    return False
                if not var_text:
                    QtWidgets.QMessageBox.warning(self, "Error trying to save", f"row {table_row} needs a value")
                    return False

            try:  # convert strings into types (int,boolean,float etc.) if possible
                var_value = ast.literal_eval(var_text)
            except ValueError:
                var_value = var_text

            # add task key into variables dictionary if it doesn't already exist
            if task_name not in setup_variables:
                setup_variables[task_name] = {}

            # check that the variable isn't repeated
            if var_name not in setup_variables[task_name]:
                setup_variables[task_name][var_name] = var_value
            else:
                if do_validation:
                    QtWidgets.QMessageBox.warning(
                        self, "Error trying to save", f"A task-variable combination is repeated in row {table_row}"
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
