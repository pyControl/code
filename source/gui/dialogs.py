import os
import sys
import json
import logging
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
from source.gui.settings import get_setting, user_folder
from source.gui.utility import variable_constants


# Controls_dialog ---------------------------------------------------------------------


class Controls_dialog(QtWidgets.QDialog):
    """Dialog for setting and getting task variables."""

    def __init__(self, parent):
        super(QtWidgets.QDialog, self).__init__(parent)
        self.setWindowTitle("Controls")
        self.scroll_area = QtWidgets.QScrollArea(parent=self)
        self.scroll_area.setWidgetResizable(True)
        self.controls_grid = Controls_grid(self.scroll_area, parent.board)
        self.scroll_area.setWidget(self.controls_grid)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.scroll_area)
        self.setLayout(self.layout)

        self.close_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+W"), self)
        self.close_shortcut.activated.connect(self.close)

    def showEvent(self, event):
        """Called when dialog is opened."""
        super(Controls_dialog, self).showEvent(event)
        board = self.controls_grid.board
        self.controls_grid.variables_groupbox.setEnabled(
            bool(board.sm_info.variables) and (board.framework_running or (board.timestamp == 0))
        )
        self.controls_grid.events_groupbox.setEnabled(board.framework_running and bool(board.sm_info.events))


class Controls_grid(QtWidgets.QWidget):
    """Grid of controls displayed within scroll area of dialog"""

    def __init__(self, parent_widget, board):
        super(QtWidgets.QWidget, self).__init__(parent_widget)
        self.board = board

        # Events groupbox.
        self.events_groupbox = QtWidgets.QGroupBox("Event trigger")
        self.eventsbox_layout = QtWidgets.QHBoxLayout(self.events_groupbox)
        self.trigger_event_lbl = QtWidgets.QLabel("Event:")
        self.event_select_combo = QtWidgets.QComboBox()
        self.event_select_combo.addItems(self.board.sm_info.events)
        self.trigger_event_button = QtWidgets.QPushButton("Trigger")
        self.trigger_event_button.clicked.connect(self.trigger_event)
        self.trigger_event_button.setDefault(False)
        self.trigger_event_button.setAutoDefault(False)
        self.eventsbox_layout.addWidget(self.trigger_event_lbl)
        self.eventsbox_layout.addWidget(self.event_select_combo)
        self.eventsbox_layout.addWidget(self.trigger_event_button)
        self.eventsbox_layout.addStretch(1)

        # Notes groupbox
        self.notes_groupbox = QtWidgets.QGroupBox("Add note to log")
        self.notesbox_layout = QtWidgets.QGridLayout(self.notes_groupbox)
        self.notes_textbox = QtWidgets.QTextEdit()
        self.notes_textbox.setFixedHeight(get_setting("GUI", "log_font_size") * 4)
        self.notes_textbox.setFont(QtGui.QFont("Courier New", get_setting("GUI", "log_font_size")))
        self.note_button = QtWidgets.QPushButton("Add note")
        self.note_button.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.note_button.clicked.connect(self.add_note)
        self.notesbox_layout.addWidget(self.notes_textbox, 0, 0, 1, 2)
        self.notesbox_layout.addWidget(self.note_button, 1, 1)
        self.notesbox_layout.setColumnStretch(0, 1)

        # Variables groupbox.
        self.variables_groupbox = QtWidgets.QGroupBox("Variables")
        self.grid_layout = QtWidgets.QGridLayout(self.variables_groupbox)
        control_row = 0
        variables = board.sm_info.variables
        for v_name, v_value in sorted(variables.items()):
            if (
                not v_name.endswith("___")
                and v_name != "custom_controls_dialog"
                and not v_name.startswith("hw_")
                and v_name != "api_class"
            ):
                Variable_setter(v_name, v_value, control_row, self)
                control_row += 1

        # Main layout.
        self.vlayout = QtWidgets.QVBoxLayout(self)
        self.vlayout.addWidget(self.notes_groupbox)
        self.vlayout.addWidget(self.events_groupbox)
        self.vlayout.addWidget(self.variables_groupbox)
        self.vlayout.addStretch()

    def trigger_event(self):
        if self.board.framework_running:
            self.board.trigger_event(self.event_select_combo.currentText())

    def add_note(self):
        note_text = self.notes_textbox.toPlainText()
        self.notes_textbox.clear()
        self.board.data_logger.print_message(note_text, source="u")


class Variable_setter(QtWidgets.QWidget):
    """For setting and getting a single variable."""

    def __init__(self, v_name, v_value, i, parent_grid):
        super(QtWidgets.QWidget, self).__init__(parent_grid)
        self.board = parent_grid.board
        self.v_name = v_name
        self.label = QtWidgets.QLabel(v_name)
        self.get_button = QtWidgets.QPushButton("Get value")
        self.set_button = QtWidgets.QPushButton("Set value")
        self.value_str = QtWidgets.QLineEdit(repr(v_value))
        self.value_text_colour("gray")
        self.get_button.clicked.connect(self.get)
        self.set_button.clicked.connect(self.set)
        self.value_str.textChanged.connect(lambda x: self.value_text_colour("black"))
        self.value_str.returnPressed.connect(self.set)
        self.get_button.setDefault(False)
        self.get_button.setAutoDefault(False)
        self.set_button.setDefault(False)
        self.set_button.setAutoDefault(False)
        parent_grid.grid_layout.addWidget(self.label, i, 1)
        parent_grid.grid_layout.addWidget(self.value_str, i, 2)
        parent_grid.grid_layout.addWidget(self.get_button, i, 3)
        parent_grid.grid_layout.addWidget(self.set_button, i, 4)

    def value_text_colour(self, color="gray"):
        self.value_str.setStyleSheet(f"color: {color};")

    def get(self):
        if self.board.framework_running:  # Value returned later.
            self.board.get_variable(self.v_name)
            self.value_str.setText("getting..")
            QtCore.QTimer.singleShot(200, self.reload)
        else:  # Value returned immediately.
            self.value_text_colour("black")
            self.value_str.setText(repr(self.board.get_variable(self.v_name)))
            QtCore.QTimer.singleShot(1000, self.value_text_colour)

    def set(self):
        try:
            v_value = eval(self.value_str.text(), variable_constants)
        except Exception:
            self.value_str.setText("Invalid value")
            return
        if self.board.framework_running:  # Value returned later if set OK.
            self.board.set_variable(self.v_name, v_value)
            self.value_str.setText("setting..")
            QtCore.QTimer.singleShot(200, self.reload)
        else:  # Set OK returned immediately.
            if self.board.set_variable(self.v_name, v_value):
                self.value_text_colour("gray")
            else:
                self.value_str.setText("Set failed")

    def reload(self):
        """Reload value from sm_info.  sm_info is updated when variables are output
        during framework run due to get/set."""
        self.value_text_colour("black")
        self.value_str.setText(repr(self.board.sm_info.variables[self.v_name]))
        QtCore.QTimer.singleShot(1000, self.value_text_colour)


# Summary variables dialog -----------------------------------------------------------


class Summary_variables_dialog(QtWidgets.QDialog):
    """Dialog for displaying summary variables from an experiment as a table.
    The table is copied to the clipboard as a string that can be pasted into a
    spreadsheet."""

    def __init__(self, parent, sv_dict):
        super(QtWidgets.QDialog, self).__init__(parent)
        self.setWindowTitle("Summary variables")

        subjects = list(sv_dict.keys())
        v_names = sorted(sv_dict[subjects[0]].keys())

        self.label = QtWidgets.QLabel("Summary variables copied to clipboard.")
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.table = QtWidgets.QTableWidget(len(subjects), len(v_names), parent=self)
        self.table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setHorizontalHeaderLabels(v_names)
        self.table.setVerticalHeaderLabels(subjects)

        self.Vlayout = QtWidgets.QVBoxLayout(self)
        self.Vlayout.addWidget(self.label)
        self.Vlayout.addWidget(self.table)

        clip_string = "Subject\t" + "\t".join(v_names)

        for s, subject in enumerate(subjects):
            clip_string += "\n" + subject
            for v, v_name in enumerate(v_names):
                v_value_str = repr(sv_dict[subject][v_name])
                clip_string += "\t" + v_value_str
                item = QtWidgets.QTableWidgetItem()
                item.setText(v_value_str)
                self.table.setItem(s, v, item)

        self.table.resizeColumnsToContents()

        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(clip_string)


# Invalid experiment dialog. ---------------------------------------------------------


def invalid_run_experiment_dialog(parent, message):
    QtWidgets.QMessageBox.warning(
        parent,
        "Invalid experiment",
        message + "\n\nUnable to run experiment.",
        QtWidgets.QMessageBox.StandardButton.Ok,
    )


def invalid_save_experiment_dialog(parent, message):
    QtWidgets.QMessageBox.warning(
        parent,
        "Invalid experiment",
        message + "\n\nUnable to save experiment.",
        QtWidgets.QMessageBox.StandardButton.Ok,
    )


# Unrun subjects warning     ---------------------------------------------------------


def unrun_subjects_dialog(parent, message):
    reply = QtWidgets.QMessageBox.warning(
        parent,
        "Unrun Subjects",
        f"The following Subjects will not be run:\n\n{message}",
        (QtWidgets.QMessageBox.StandardButton.Ok | QtWidgets.QMessageBox.StandardButton.Cancel),
    )
    if reply == QtWidgets.QMessageBox.StandardButton.Ok:
        return True
    else:
        return False


# Persistent variabe value warning ------------------------------------------------------


def persistent_value_dialog(parent, var_names):
    reply = QtWidgets.QMessageBox.warning(
        parent,
        "Persistent variables value",
        f"Values entered in variables table will take precedence over stored persistent values for variables:\n\n{var_names}",
        (QtWidgets.QMessageBox.StandardButton.Ok | QtWidgets.QMessageBox.StandardButton.Cancel),
    )
    if reply == QtWidgets.QMessageBox.StandardButton.Ok:
        return True
    else:
        return False


# Keyboard shortcuts dialog. ---------------------------------------------------------


class Keyboard_shortcuts_dialog(QtWidgets.QDialog):
    """Dialog for displaying information about keyboard shortcuts."""

    def __init__(self, parent):
        super(QtWidgets.QDialog, self).__init__(parent)
        self.setWindowTitle("Shortcuts")

        self.Vlayout = QtWidgets.QVBoxLayout(self)

        label = QtWidgets.QLabel("<center><b>Keyboard Shortcuts</b></center<br></br>")
        label.setFont(QtGui.QFont("Helvetica", 12))
        self.Vlayout.addWidget(label)

        if sys.platform == "darwin":  # shortcuts for mac
            modifier_key = "Cmd"
        else:
            modifier_key = "Ctrl"

        label_strings = [
            "<b><u>Global:</u></b>",
            f'<b style="color:#0220e0;">{modifier_key} + t</b> : Open tasks folder',
            f'<b style="color:#0220e0;">{modifier_key} + d</b> : Open data folder',
            f'<b style="color:#0220e0;">{modifier_key} + e</b> : Open error log',
            f'<b style="color:#0220e0;">{modifier_key} + ,</b> : Open settings',
            "<br></br><b><u>Run task tab:</u></b>",
            '<b style="color:#0220e0;">    t    </b> : Select task',
            '<b style="color:#0220e0;">    u    </b> : Upload/reset task',
            '<b style="color:#0220e0;">spacebar </b> : Start/stop task',
            "<br></br><b><u>Experiments tab:</u></b>",
            f'<b style="color:#0220e0;">{modifier_key} + s</b> : Save experiment ',
        ]

        for ls in label_strings:
            label = QtWidgets.QLabel(ls)
            label.setFont(QtGui.QFont("Helvetica", 10))
            self.Vlayout.addWidget(label)

        self.setFixedSize(self.sizeHint())


# Settings dialog. ---------------------------------------------------------


class Settings_dialog(QtWidgets.QDialog):
    """Dialog for editing user settings"""

    def __init__(self, parent):
        super(QtWidgets.QDialog, self).__init__(parent)
        self.setWindowTitle("Settings")
        self.num_edited_setters = 0

        settings_grid_layout = QtWidgets.QGridLayout(self)
        paths_box = QtWidgets.QGroupBox("Folder paths")
        paths_layout = QtWidgets.QGridLayout()

        self.discard_changes_btn = QtWidgets.QPushButton("Discard changes")
        self.discard_changes_btn.setEnabled(False)
        self.discard_changes_btn.setIcon(QtGui.QIcon("source/gui/icons/delete.svg"))
        self.discard_changes_btn.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.discard_changes_btn.clicked.connect(self.reset)

        self.save_settings_btn = QtWidgets.QPushButton("Save settings and restart")
        self.save_settings_btn.setEnabled(False)
        self.save_settings_btn.setIcon(QtGui.QIcon("source/gui/icons/save.svg"))
        self.save_settings_btn.clicked.connect(self.saveChanges)

        # Instantiate setters
        self.api_classes_setter = Path_setter(self, "Api classes", ("folders", "api_classes"))
        self.controls_dialogs_setter = Path_setter(self, "Controls dialogs", ("folders", "controls_dialogs"))
        self.data_setter = Path_setter(self, "Data", ("folders", "data"))
        self.devices_setter = Path_setter(self, "Devices", ("folders", "devices"))
        self.experiments_setter = Path_setter(self, "Experiments", ("folders", "experiments"))
        self.hardware_definition_setter = Path_setter(self, "Hardware definitions", ("folders", "hardware_definitions"))
        self.task_settter = Path_setter(self, "Tasks", ("folders", "tasks"))
        self.path_setters = [
            self.api_classes_setter,
            self.controls_dialogs_setter,
            self.data_setter,
            self.devices_setter,
            self.experiments_setter,
            self.hardware_definition_setter,
            self.task_settter,
        ]
        for i, setter in enumerate(self.path_setters):
            setter.add_to_grid(paths_layout, i)
        paths_box.setLayout(paths_layout)

        plotting_box = QtWidgets.QGroupBox("Plotting")
        plotting_layout = QtWidgets.QGridLayout()
        self.update_interval = Spin_setter(
            self,
            "Update interval",
            ("plotting", "update_interval"),
            " ms",
        )
        self.event_history_len = Spin_setter(
            self,
            "Event history length",
            ("plotting", "event_history_len"),
            " events",
        )
        self.state_history_len = Spin_setter(
            self,
            "State history length",
            ("plotting", "state_history_len"),
            " states",
        )
        self.analog_history_dur = Spin_setter(
            self,
            "Analog history duration",
            ("plotting", "analog_history_dur"),
            " s",
        )

        self.plotting_spins = [
            self.update_interval,
            self.event_history_len,
            self.state_history_len,
            self.analog_history_dur,
        ]
        for i, variable in enumerate(self.plotting_spins):
            variable.add_to_grid(plotting_layout, i)
        plotting_layout.setColumnStretch(2, 1)
        plotting_layout.setRowStretch(i + 1, 1)
        plotting_box.setLayout(plotting_layout)

        gui_box = QtWidgets.QGroupBox("GUI")
        gui_layout = QtWidgets.QGridLayout()
        self.ui_font_size = Spin_setter(self, "UI font size", ("GUI", "ui_font_size"), " pt")
        self.log_font_size = Spin_setter(self, "Log font size", ("GUI", "log_font_size"), " pt")

        self.gui_spins = [self.ui_font_size, self.log_font_size]
        for i, variable in enumerate(self.gui_spins):
            variable.add_to_grid(gui_layout, i)
        gui_layout.setColumnStretch(2, 1)
        gui_layout.setRowStretch(i + 1, 1)
        gui_box.setLayout(gui_layout)

        self.fill_with_defaults_btn = QtWidgets.QPushButton("Use defaults")
        self.fill_with_defaults_btn.clicked.connect(self.fill_with_defaults)
        self.fill_with_defaults_btn.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)

        btns_layout = QtWidgets.QHBoxLayout()
        btns_layout.addStretch(1)
        btns_layout.addWidget(self.fill_with_defaults_btn)
        btns_layout.addWidget(self.discard_changes_btn)
        btns_layout.addWidget(self.save_settings_btn)

        settings_grid_layout.addWidget(paths_box, 0, 0, 1, 3)
        settings_grid_layout.addWidget(plotting_box, 1, 0)
        settings_grid_layout.addWidget(gui_box, 1, 1)
        settings_grid_layout.addLayout(btns_layout, 2, 0, 1, 3)
        settings_grid_layout.setColumnStretch(2, 1)

        self.setFixedSize(self.sizeHint())
        self.close_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+W"), self)
        self.close_shortcut.activated.connect(self.close)
        self.save_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+S"), self)
        self.save_shortcut.activated.connect(self.saveChanges)

    def reset(self):
        """
        Resets values to whatever is saved in settings.json,
        or to default_user_settings if no settings.json exists
        """
        for variable in self.path_setters + self.plotting_spins + self.gui_spins:
            variable.reset()
        self.num_edited_setters = 0
        self.save_settings_btn.setEnabled(False)
        self.save_settings_btn.setFocus()

    def fill_with_defaults(self):
        "Populates inputs with default_user_settings dictionary values from settings.py"

        for variable in self.plotting_spins + self.gui_spins:
            variable.fill_with_default()

    def saveChanges(self):
        user_setting_dict_new = {"folders": {}, "plotting": {}, "GUI": {}}
        for variable in self.path_setters + self.plotting_spins + self.gui_spins:
            top_key, sub_key = variable.key
            user_setting_dict_new[top_key][sub_key] = variable.get()
        # Store newly edited paths.
        json_path = os.path.join("config", "settings.json")
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                user_settings = json.loads(f.read())
        else:
            user_settings = {}
        user_settings.update(user_setting_dict_new)
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(user_settings, indent=4))
        self.parent().data_dir_changed = True
        self.parent().task_directory = user_folder("tasks")

        self.save_settings_btn.setEnabled(False)
        QtCore.QCoreApplication.quit()
        QtCore.QProcess.startDetached(sys.executable, sys.argv)

    def showEvent(self, event):
        self.reset()

    def closeEvent(self, event):
        if self.save_settings_btn.isEnabled():
            reply = QtWidgets.QMessageBox.question(
                self,
                "Changes not saved",
                "Are you sure you want to exit without saving your settings?",
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.Cancel,
            )
            if reply == QtWidgets.QMessageBox.StandardButton.Cancel:
                event.ignore()


class Path_setter(QtWidgets.QHBoxLayout):
    """Dialog for editing folder paths."""

    def __init__(self, parent, label, key):
        super(QtWidgets.QHBoxLayout, self).__init__()
        self.name = label
        self.key = key
        self.parent = parent
        self.edited = False
        # Instantiate widgets
        Vcenter = QtCore.Qt.AlignmentFlag.AlignVCenter
        right = QtCore.Qt.AlignmentFlag.AlignRight
        self.path = ""
        self.name_label = QtWidgets.QLabel(label)
        self.name_label.setAlignment(right | Vcenter)
        self.name_label.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.path_text = QtWidgets.QLineEdit()
        self.path_text.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.path_text.setReadOnly(True)
        self.path_text.setFixedWidth(500)
        self.change_button = QtWidgets.QPushButton("Change")
        self.change_button.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.path_text.setReadOnly(True)
        self.change_button.clicked.connect(self.select_path)
        # Layout
        self.addWidget(self.name_label)
        self.addWidget(self.path_text)
        self.addWidget(self.change_button)
        self.setContentsMargins(0, 0, 0, 0)

    def add_to_grid(self, groupbox_grid, row):
        groupbox_grid.addWidget(self.name_label, row, 0)
        groupbox_grid.addWidget(self.path_text, row, 1)
        groupbox_grid.addWidget(self.change_button, row, 2)

    def select_path(self):
        new_path = QtWidgets.QFileDialog.getExistingDirectory(
            self.parent, f"Select {self.name} folder", self.path_text.text()
        )
        if new_path:
            new_path = os.path.normpath(new_path)
            self.path_text.setText(new_path)
            self.show_edit()

    def show_edit(self):
        if self.get() != self.path:
            if self.edited is False:
                self.edited = True
                self.name_label.setStyleSheet("color:red;")
                self.parent.num_edited_setters += 1
                self.parent.save_settings_btn.setEnabled(True)
                self.parent.discard_changes_btn.setEnabled(True)
        else:
            if self.edited is True:
                self.edited = False
                self.name_label.setStyleSheet("color:black;")
                self.parent.num_edited_setters -= 1
                if self.parent.num_edited_setters < 1:
                    self.parent.save_settings_btn.setEnabled(False)
                    self.parent.discard_changes_btn.setEnabled(False)

    def reset(self):
        self.path = os.path.normpath(get_setting(*self.key))
        self.path_text.setText(self.path)
        self.show_edit()

    def get(self):
        return self.path_text.text()


class Spin_setter:
    """Spinbox input for changing user settings"""

    def __init__(self, parent, label, key, suffix=None):
        center = QtCore.Qt.AlignmentFlag.AlignCenter
        Vcenter = QtCore.Qt.AlignmentFlag.AlignVCenter
        right = QtCore.Qt.AlignmentFlag.AlignRight
        spin_width = 85
        self.parent = parent
        self.key = key
        self.edited = False
        self.label = QtWidgets.QLabel(label)
        self.label.setAlignment(right | Vcenter)

        self.spn = QtWidgets.QSpinBox()
        self.spn.setMaximum(10000)
        self.spn.setAlignment(center)
        self.spn.setMinimumWidth(spin_width)
        if suffix:
            self.spn.setSuffix(suffix)
        self.spn.valueChanged.connect(self.show_edit)

    def add_to_grid(self, groupbox_grid, row):
        groupbox_grid.addWidget(self.label, row, 0)
        groupbox_grid.addWidget(self.spn, row, 1)

    def show_edit(self):
        """
        checks whether the settings has been edited, and changes label color accordingly
        also keeps a running tally of how many settings have been edited
        and enables/disables the "Save settings" button accordingly
        """
        if self.get() != self.start_value:
            if self.edited is False:
                self.edited = True
                self.label.setStyleSheet("color:red;")
                self.parent.num_edited_setters += 1
                self.parent.save_settings_btn.setEnabled(True)
                self.parent.discard_changes_btn.setEnabled(True)
        else:
            if self.edited is True:
                self.edited = False
                self.label.setStyleSheet("color:black;")
                self.parent.num_edited_setters -= 1
                if self.parent.num_edited_setters < 1:
                    self.parent.save_settings_btn.setEnabled(False)
                    self.parent.discard_changes_btn.setEnabled(False)

        self.spn.lineEdit().deselect()

    def fill_with_default(self):
        top_key, sub_key = self.key
        self.spn.setValue(get_setting(top_key, sub_key, want_default=True))

    def reset(self):
        self.start_value = get_setting(*self.key)
        self.spn.setValue(self.start_value)
        self.show_edit()

    def get(self):
        return self.spn.value()


# Error log dialog. ---------------------------------------------------------
class Error_log_dialog(QtWidgets.QDialog):
    def __init__(self, parent):
        super(QtWidgets.QDialog, self).__init__(parent)
        self.setWindowTitle("Error Log")

        log_layout = QtWidgets.QGridLayout(self)
        self.log_viewer = QtWidgets.QTextEdit()
        self.log_viewer.setMinimumWidth(800)
        self.log_viewer.setMinimumHeight(800)
        self.log_viewer.setReadOnly(True)

        clear_log_btn = QtWidgets.QPushButton("Clear log")
        clear_log_btn.clicked.connect(self.clear_log)

        log_layout.addWidget(self.log_viewer, 0, 0, 1, 3)
        log_layout.addWidget(clear_log_btn, 1, 1)
        log_layout.setColumnStretch(0, 1)
        log_layout.setColumnStretch(2, 1)

        self.close_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+W"), self)
        self.close_shortcut.activated.connect(self.close)

    def showEvent(self, event):
        self.log_viewer.moveCursor(QtGui.QTextCursor.MoveOperation.End)

    def clear_log(self):
        reply = QtWidgets.QMessageBox.question(
            self,
            "Clear error log",
            "Are you sure you want to clear the error log?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.Cancel,
        )
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            self.log_viewer.clear()
            logging.shutdown()
            os.remove(r"ErrorLog.txt")
            self.close()
