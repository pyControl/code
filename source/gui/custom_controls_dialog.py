import os
import json
import re
from enum import Enum
from typing import Union
from copy import deepcopy
from dataclasses import dataclass, asdict
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
from source.gui.settings import user_folder
from source.gui.utility import variable_constants, null_resize, cbox_set_item, cbox_update_options


# input widgets ---------------------------------------------------------------
class Spin_var:
    def __init__(self, init_var_dict, label, spin_min, spin_max, step, varname):
        center = QtCore.Qt.AlignmentFlag.AlignCenter
        Vcenter = QtCore.Qt.AlignmentFlag.AlignVCenter
        right = QtCore.Qt.AlignmentFlag.AlignRight
        button_width = 65
        spin_width = 85
        self.label = QtWidgets.QLabel(label)
        self.label.setAlignment(right | Vcenter)
        self.varname = varname

        if isinstance(spin_min, float) or isinstance(spin_max, float) or isinstance(step, float):
            self.spn = QtWidgets.QDoubleSpinBox()
        else:
            self.spn = QtWidgets.QSpinBox()

        self.spn.setRange(spin_min, spin_max)
        self.spn.setValue(init_var_dict[self.varname])
        self.spn.setSingleStep(step)
        self.spn.setAlignment(center)
        self.spn.setMinimumWidth(spin_width)
        self.value_text_colour("gray")

        self.get_btn = QtWidgets.QPushButton("Get")
        self.get_btn.setMinimumWidth(button_width)
        self.get_btn.setMaximumWidth(button_width)
        self.get_btn.setAutoDefault(False)
        self.get_btn.clicked.connect(self.get)

        self.set_btn = QtWidgets.QPushButton("Set")
        self.set_btn.setMinimumWidth(button_width)
        self.set_btn.setMaximumWidth(button_width)
        self.set_btn.setAutoDefault(False)
        self.set_btn.clicked.connect(self.set)

    def add_to_grid(self, grid, row):
        grid.addWidget(self.label, row, 0)
        grid.addWidget(self.spn, row, 1)
        grid.addWidget(self.get_btn, row, 2)
        grid.addWidget(self.set_btn, row, 3)

    def setEnabled(self, doEnable):
        self.label.setEnabled(doEnable)
        self.spn.setEnabled(doEnable)
        self.get_btn.setEnabled(doEnable)
        self.set_btn.setEnabled(doEnable)

    def setBoard(self, board):
        self.board = board

    def get(self):
        if self.board.framework_running:  # Value returned later.
            self.board.get_variable(self.varname)
            QtCore.QTimer.singleShot(200, self.reload)
        else:  # Value returned immediately.
            self.spn.setValue(self.board.get_variable(self.varname))

    def set(self):
        self.board.set_variable(self.varname, round(self.spn.value(), 2))
        if self.board.framework_running:  # Value returned later.
            QtCore.QTimer.singleShot(200, self.reload)
        else:  # Value returned immediately.
            msg = QtWidgets.QMessageBox()
            msg.setText("Variable Changed")
            msg.exec()
            self.spn.setValue(self.board.get_variable(self.varname))

    def reload(self):
        """Reload value from sm_info.  sm_info is updated when variables are output
        during framework run due to get/set."""
        self.value_text_colour("black")
        self.spn.setValue(self.board.sm_info.variables[self.varname])
        QtCore.QTimer.singleShot(1000, self.value_text_colour)

    def setVisible(self, makeVisible):
        self.label.setVisible(makeVisible)
        self.spn.setVisible(makeVisible)
        self.get_btn.setVisible(makeVisible)
        self.set_btn.setVisible(makeVisible)

    def setHint(self, hint):
        self.label.setToolTip(hint)
        self.spn.setToolTip(hint)

    def value_text_colour(self, color="gray"):
        self.spn.setStyleSheet(f"color: {color};")

    def setSuffix(self, suffix):
        self.spn.setSuffix(suffix)


class Text_var:
    def __init__(self, init_var_dict, label, varname, text_width=80):
        center = QtCore.Qt.AlignmentFlag.AlignCenter
        Vcenter = QtCore.Qt.AlignmentFlag.AlignVCenter
        right = QtCore.Qt.AlignmentFlag.AlignRight
        button_width = 65
        self.label = QtWidgets.QLabel(label)
        self.label.setAlignment(right | Vcenter)
        self.varname = varname

        self.line_edit = QtWidgets.QLineEdit()
        self.line_edit.setAlignment(center)
        self.line_edit.setMinimumWidth(text_width)
        self.line_edit.setMaximumWidth(text_width)
        self.line_edit.setText(str(init_var_dict[self.varname]))
        self.line_edit.textChanged.connect(lambda x: self.value_text_colour("black"))
        self.line_edit.returnPressed.connect(self.set)
        self.value_text_colour("gray")

        self.get_btn = QtWidgets.QPushButton("Get")
        self.get_btn.setMinimumWidth(button_width)
        self.get_btn.setMaximumWidth(button_width)
        self.get_btn.setAutoDefault(False)
        self.get_btn.clicked.connect(self.get)

        self.set_btn = QtWidgets.QPushButton("Set")
        self.set_btn.setMinimumWidth(button_width)
        self.set_btn.setMaximumWidth(button_width)
        self.set_btn.setAutoDefault(False)
        self.set_btn.clicked.connect(self.set)

    def add_to_grid(self, grid, row):
        grid.addWidget(self.label, row, 0)
        grid.addWidget(self.line_edit, row, 1)
        grid.addWidget(self.get_btn, row, 2)
        grid.addWidget(self.set_btn, row, 3)

    def setEnabled(self, doEnable):
        self.label.setEnabled(doEnable)
        self.line_edit.setEnabled(doEnable)
        self.get_btn.setEnabled(doEnable)
        self.set_btn.setEnabled(doEnable)

    def setBoard(self, board):
        self.board = board

    def get(self):
        if self.board.framework_running:  # Value returned later.
            self.board.get_variable(self.varname)
            QtCore.QTimer.singleShot(200, self.reload)
        else:  # Value returned immediately.
            self.line_edit.setText(str(self.board.get_variable(self.varname)))

    def set(self):
        try:
            v_value = eval(self.line_edit.text(), variable_constants)
        except Exception:
            self.line_edit.setText("Invalid value")
            return
        self.board.set_variable(self.varname, v_value)
        if self.board.framework_running:  # Value returned later.
            QtCore.QTimer.singleShot(200, self.reload)
        else:  # Value returned immediately.
            msg = QtWidgets.QMessageBox()
            msg.setText("Variable Changed")
            msg.exec()
            self.line_edit.setText(str(self.board.get_variable(self.varname)))

    def reload(self):
        """Reload value from sm_info.  sm_info is updated when variables are output
        during framework run due to get/set."""
        self.value_text_colour("black")
        self.line_edit.setText(str(self.board.sm_info.variables[self.varname]))
        QtCore.QTimer.singleShot(1000, self.value_text_colour)

    def setHint(self, hint):
        self.label.setToolTip(hint)
        self.line_edit.setToolTip(hint)

    def value_text_colour(self, color="gray"):
        self.line_edit.setStyleSheet(f"color: {color};")


class Checkbox_var:
    def __init__(self, init_var_dict, label, varname):
        self.varname = varname
        self.label = QtWidgets.QLabel(label)
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.checkbox = QtWidgets.QCheckBox()
        self.checkbox.setChecked(init_var_dict[self.varname])
        self.checkbox.clicked.connect(self.set)

    def setBoard(self, board):
        self.board = board

    def add_to_grid(self, grid, row):
        grid.addWidget(self.label, row, 0)
        grid.addWidget(self.checkbox, row, 1)

    def set(self):
        self.board.set_variable(self.varname, self.checkbox.isChecked())
        if not self.board.framework_running:  # Value returned later.
            msg = QtWidgets.QMessageBox()
            msg.setText("Variable Changed")
            msg.exec()

    def setHint(self, hint):
        self.label.setToolTip(hint)
        self.checkbox.setToolTip(hint)


class DoubleSlider(QtWidgets.QSlider):  # https://stackoverflow.com/questions/4827885/qslider-stepping
    def __init__(self, *args, **kargs):
        super(DoubleSlider, self).__init__(*args, **kargs)
        self._min = 0
        self._max = 99
        self.interval = 1
        # prevent tongue from moving if you click to the right or left of it, must actually click on tongue and drag
        self.setPageStep(0)

    def setValue(self, value):
        index = round((value - self._min) / self.interval)
        return super(DoubleSlider, self).setValue(index)

    def value(self):
        return round(self.index * self.interval + self._min, 4)

    @property
    def index(self):
        return super(DoubleSlider, self).sliderPosition()

    def setIndex(self, index):
        return super(DoubleSlider, self).setValue(index)

    def setRange(self, minval, maxval):
        self._min = minval
        self._max = maxval
        self._range_adjusted()

    def setMinimum(self, value):
        self._min = value
        self._range_adjusted()

    def setMaximum(self, value):
        self._max = value
        self._range_adjusted()

    def setInterval(self, value):
        # To avoid division by zero
        if not value:
            raise ValueError("Interval of zero specified")
        self.interval = value
        self._range_adjusted()

    def _range_adjusted(self):
        number_of_steps = int((self._max - self._min) / self.interval)
        super(DoubleSlider, self).setMaximum(number_of_steps)


class Slider_var:
    def __init__(self, init_var_dict, label, slide_min, slide_max, step, varname):
        self.varname = varname

        self.slider = DoubleSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)
        self.slider.setInterval(step)
        self.slider.setRange(slide_min, slide_max)
        self.slider.setValue(init_var_dict[self.varname])

        self.suffix = ""
        self.label = QtWidgets.QLabel(label)
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.val_label = QtWidgets.QLabel(str(self.slider.value()))

        self.slider.sliderMoved.connect(self.update_val_lbl)
        self.slider.sliderReleased.connect(self.set)

    def setBoard(self, board):
        self.board = board

    def add_to_grid(self, grid, row):
        grid.addWidget(self.label, row, 0)
        grid.addWidget(self.slider, row, 1, 1, 2)
        grid.addWidget(self.val_label, row, 3)

    def update_val_lbl(self):
        self.val_label.setText(f"{str(self.slider.value())}{self.suffix}")

    def set(self):
        self.board.set_variable(self.varname, self.slider.value())
        if not self.board.framework_running:  # Value returned later.
            msg = QtWidgets.QMessageBox()
            msg.setText("Variable Changed")
            msg.exec()

    def setHint(self, hint):
        self.label.setToolTip(hint)
        self.slider.setToolTip(hint)

    def setSuffix(self, suff):
        self.suffix = suff
        self.val_label.setText(f"{str(self.slider.value())}{self.suffix}")


class Event_button:
    def __init__(self, event_name, button_text):
        self.event_name = event_name
        self.event_btn = QtWidgets.QPushButton(button_text)
        self.event_btn.clicked.connect(self.trigger)
        self.event_btn.setAutoDefault(False)

    def trigger(self):
        if self.board.framework_running:  # Value returned later.
            self.board.trigger_event(self.event_name)

    def setHint(self, hint):
        self.event_btn.setToolTip(hint)

    def setBoard(self, board):
        self.board = board

    def add_to_grid(self, grid, row):
        grid.addWidget(self.event_btn, row, 1)


class Custom_gui(Enum):
    JSON = 1
    PYFILE = 2


# GUI created from dictionary describing custom widgets and layout ------------
class Custom_controls_dialog(QtWidgets.QDialog):
    def __init__(self, parent_tab, gui_name, is_experiment=False):
        super(QtWidgets.QDialog, self).__init__(parent_tab)
        self.parent_tab = parent_tab
        self.gui_name = gui_name
        self.custom_gui = False
        self.generator_data = None
        self.generator_data = self.get_custom_gui_data(is_experiment)
        if self.generator_data:
            self.parent_tab.print_to_log(f'\nLoading "{gui_name}" custom variable dialog')
            self.setWindowTitle("Controls")
            self.layout = QtWidgets.QVBoxLayout(self)
            toolBar = QtWidgets.QToolBar()
            toolBar.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            toolBar.setIconSize(QtCore.QSize(15, 15))
            self.layout.addWidget(toolBar)
            self.edit_action = QtGui.QAction(QtGui.QIcon("source/gui/icons/edit.svg"), "&edit", self)
            self.edit_action.setEnabled(True)
            if not is_experiment:
                toolBar.addAction(self.edit_action)
                self.edit_action.triggered.connect(self.open_gui_editor)
            self.scroll_area = QtWidgets.QScrollArea(parent=self)
            self.scroll_area.setWidgetResizable(True)
            self.controls_grid = Custom_controls_grid(self)
            self.scroll_area.setWidget(self.controls_grid)
            self.layout.addWidget(self.scroll_area)
            self.layout.setContentsMargins(0, 0, 0, 0)
            self.setLayout(self.layout)

            self.close_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+W"), self)
            self.close_shortcut.activated.connect(self.close)
            self.custom_gui = Custom_gui.JSON

    def updated_json_dict(self, json_dict):
        """This will update old (pyControl < v2.0) custom variables json files to a new format"""
        if "ordered_tabs" in json_dict:
            del json_dict["ordered_tabs"]
        for tab_name, tab in json_dict.copy().items():
            try:
                for control in tab.copy().keys():
                    if control.find("sep") > -1:
                        json_dict[tab_name][control]["widget"] = "separator"
                    elif control == "ordered_inputs":
                        del json_dict[tab_name][control]
            except AttributeError:
                pass
        return json_dict

    def get_custom_gui_data(self, is_experiment):
        custom_variables_dict = None
        try:  # Try to import and instantiate the user custom variable dialog
            json_file = os.path.join(user_folder("controls_dialogs"), f"{self.gui_name}.json")
            with open(json_file, "r") as j:
                custom_variables_dict = json.loads(j.read())
            # update json content if old version
            if deepcopy(custom_variables_dict) != self.updated_json_dict(custom_variables_dict):
                with open(json_file, "w", encoding="utf-8") as updated_json:
                    json.dump(custom_variables_dict, updated_json, indent=4)
        except FileNotFoundError:  # couldn't find the json data
            py_file = os.path.join(user_folder("controls_dialogs"), f"{self.gui_name}.py")
            if os.path.exists(py_file):
                self.custom_gui = Custom_gui.PYFILE
            else:
                self.parent_tab.print_to_log(f"\nCould not find custom variable dialog data: {json_file}")
                if not is_experiment:
                    # ask if they want to create a new custom gui
                    not_found_dialog = Custom_variables_not_found_dialog(
                        missing_file=self.gui_name, parent=self.parent_tab
                    )
                    do_create_custom = not_found_dialog.exec()
                    if do_create_custom:
                        gui_created = self.open_gui_editor()
                        if gui_created:
                            with open(json_file, "r", encoding="utf-8") as j:
                                custom_variables_dict = json.loads(j.read())
        return custom_variables_dict

    def open_gui_editor(self):
        gui_editor = Controls_dialog_editor(self)
        was_saved = gui_editor.exec()
        if was_saved:
            if self.parent_tab.controls_dialog:
                self.parent_tab.controls_dialog.close()
            self.parent_tab.task_changed()
            return True
        return False

    def process_data(self, new_data):
        pass


@dataclass
class Control_specs:
    widget: str
    label: str = ""
    hint: str = ""
    min: Union[int, float, None] = None
    max: Union[int, float, None] = None
    step: Union[int, float, None] = None
    suffix: str = ""


class Custom_controls_grid(QtWidgets.QWidget):
    def __init__(self, parent_controls_dialog):
        super(QtWidgets.QWidget, self).__init__(parent_controls_dialog)
        grid_layout = QtWidgets.QGridLayout()
        variables = parent_controls_dialog.parent_tab.board.sm_info.variables
        init_vars = dict(sorted(variables.items()))
        variable_tabs = QtWidgets.QTabWidget()
        used_vars = []
        self.widget_dict = {}
        for tab in parent_controls_dialog.generator_data:  # create widgets
            widget = QtWidgets.QWidget()
            layout = QtWidgets.QGridLayout()
            tab_data = parent_controls_dialog.generator_data[tab]
            used_vars.extend(list(tab_data.keys()))
            for row, (control_name, specs_dict) in enumerate(tab_data.items()):
                try:
                    control = Control_specs(**specs_dict)
                    if control.widget == "separator":
                        layout.addWidget(QtWidgets.QLabel("<hr>"), row, 0, 1, 4)
                    else:
                        if control.widget == "button":
                            self.widget_dict[control_name] = Event_button(control_name, control.label)
                        elif control.widget == "slider":
                            self.widget_dict[control_name] = Slider_var(
                                init_vars, control.label, control.min, control.max, control.step, control_name
                            )
                            self.widget_dict[control_name].setSuffix(" " + control.suffix)
                        elif control.widget == "spinbox":
                            self.widget_dict[control_name] = Spin_var(
                                init_vars, control.label, control.min, control.max, control.step, control_name
                            )
                            self.widget_dict[control_name].setSuffix(" " + control.suffix)
                        elif control.widget == "checkbox":
                            self.widget_dict[control_name] = Checkbox_var(init_vars, control.label, control_name)
                        elif control.widget == "line edit":
                            self.widget_dict[control_name] = Text_var(init_vars, control.label, control_name)

                        self.widget_dict[control_name].setHint(control.hint)
                        self.widget_dict[control_name].setBoard(parent_controls_dialog.parent_tab.board)
                        self.widget_dict[control_name].add_to_grid(layout, row)
                except KeyError:
                    parent_controls_dialog.parent_tab.print_to_log(
                        (
                            f'- Loading error: could not find "{control_name}" variable in the task file. '
                            "The variable name has been changed or no longer exists."
                        )
                    )

            layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
            widget.setLayout(layout)
            variable_tabs.addTab(widget, tab)

        leftover_widget = QtWidgets.QWidget()
        leftover_layout = QtWidgets.QGridLayout()
        leftover_vars = sorted(list(set(variables) - set(used_vars)), key=str.lower)
        leftover_vars = [
            v_name
            for v_name in leftover_vars
            if not v_name.endswith("___")
            and v_name != "custom_controls_dialog"
            and not v_name.startswith("hw_")
            and v_name != "api_class"
        ]
        if len(leftover_vars) > 0:
            for row, var in enumerate(leftover_vars):
                self.widget_dict[var] = Text_var(init_vars, var, var)
                self.widget_dict[var].setBoard(parent_controls_dialog.parent_tab.board)
                self.widget_dict[var].add_to_grid(leftover_layout, row + 1)
            leftover_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
            leftover_widget.setLayout(leftover_layout)
            variable_tabs.addTab(leftover_widget, "...")

        grid_layout.addWidget(variable_tabs, 0, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        grid_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.setLayout(grid_layout)


# GUI editor dialog. ---------------------------------------------------------


class Controls_dialog_editor(QtWidgets.QDialog):
    def __init__(self, parent_controls_dialog):
        super(QtWidgets.QDialog, self).__init__(parent_controls_dialog)
        self.parent_controls_dialog = parent_controls_dialog
        self.available_vars = []
        self.get_vars()
        self.events = list(parent_controls_dialog.parent_tab.board.sm_info.events.keys())
        self.tables = {}

        self.setWindowTitle("Custom Controls Dialog Editor")
        # main widgets
        self.tabs = QtWidgets.QTabWidget()
        self.add_tab_btn = QtWidgets.QPushButton("add tab")
        self.add_tab_btn.setIcon(QtGui.QIcon("source/gui/icons/add.svg"))
        self.add_tab_btn.clicked.connect(self.add_tab)
        self.add_tab_btn.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)

        self.del_tab_btn = QtWidgets.QPushButton("remove tab")
        self.del_tab_btn.setIcon(QtGui.QIcon("source/gui/icons/remove.svg"))
        self.del_tab_btn.clicked.connect(self.remove_tab)
        self.del_tab_btn.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)

        self.tab_title_lbl = QtWidgets.QLabel("Tab title:")
        self.tab_title_edit = QtWidgets.QLineEdit()
        self.tab_title_edit.setMinimumWidth(200)
        self.tab_title_edit.returnPressed.connect(self.set_tab_title)
        self.tab_title_btn = QtWidgets.QPushButton("set title")
        self.tab_title_btn.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.tab_title_btn.clicked.connect(self.set_tab_title)

        self.tab_shift_left_btn = QtWidgets.QPushButton("shift tab")
        self.tab_shift_left_btn.setIcon(QtGui.QIcon("source/gui/icons/left.svg"))
        self.tab_shift_left_btn.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.tab_shift_left_btn.clicked.connect(self.shift_tab_left)

        self.tab_shift_right_btn = QtWidgets.QPushButton("shift tab")
        self.tab_shift_right_btn.setIcon(QtGui.QIcon("source/gui/icons/right.svg"))
        self.tab_shift_right_btn.setLayoutDirection(QtCore.Qt.LayoutDirection.RightToLeft)
        self.tab_shift_right_btn.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.tab_shift_right_btn.clicked.connect(self.shift_tab_right)

        self.save_gui_btn = QtWidgets.QPushButton("Save GUI")
        self.save_gui_btn.setIcon(QtGui.QIcon("source/gui/icons/save.svg"))
        self.save_gui_btn.clicked.connect(self.save_gui_data)
        self.save_gui_btn.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        if self.parent_controls_dialog.generator_data:
            self.load_gui_data()
        else:
            self.add_tab()
        self.tabs.currentChanged.connect(self.refresh_variable_options)
        self.refresh_variable_options()

        # layout
        tab_box = QtWidgets.QGroupBox("")
        tab_box_layout = QtWidgets.QGridLayout(self)
        tab_box_layout.addWidget(self.add_tab_btn, 0, 0)
        tab_box_layout.addWidget(self.del_tab_btn, 0, 1)
        tab_box_layout.addWidget(self.tab_title_lbl, 0, 2)
        tab_box_layout.addWidget(self.tab_title_edit, 0, 3)
        tab_box_layout.addWidget(self.tab_title_btn, 0, 4)
        tab_box_layout.addWidget(self.tab_shift_left_btn, 0, 5)
        tab_box_layout.addWidget(self.tab_shift_right_btn, 0, 6)
        tab_box.setLayout(tab_box_layout)

        self.layout = QtWidgets.QGridLayout(self)
        self.layout.addWidget(tab_box, 0, 0)
        self.layout.addWidget(self.save_gui_btn, 0, 7)
        self.layout.addWidget(self.tabs, 1, 0, 1, 8)
        self.layout.setColumnStretch(5, 1)

        self.setMinimumWidth(910)
        self.setMinimumHeight(450)

        self.close_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+W"), self)
        self.close_shortcut.activated.connect(self.close)

    def load_gui_data(self):
        gui_data = self.parent_controls_dialog.generator_data
        for tab_name in gui_data:
            tab_data = gui_data[tab_name]
            self.add_tab(tab_data, tab_name)

    def save_gui_data(self):
        gui_dict = {}
        for tab_index in range(self.tabs.count()):
            tab_title = self.tabs.tabText(tab_index)
            data = self.tables[tab_title].get_tab_data_dict()
            if data:
                gui_dict[tab_title] = data
            else:  # there was an error
                return

        savename = os.path.join(user_folder("controls_dialogs"), f"{self.parent_controls_dialog.gui_name}.json")
        with open(savename, "w", encoding="utf-8") as generated_data_file:
            json.dump(gui_dict, generated_data_file, indent=4)
        self.accept()
        self.deleteLater()

    def refresh_variable_options(self):
        fully_asigned_variables = []
        for _, table in self.tables.items():
            # determine which variables are already being used
            for row in range(table.n_variables):
                assigned_var = table.cellWidget(row, Clm.CONTROL).currentText()
                if assigned_var not in ("     select control      ", "--- separator ---"):
                    fully_asigned_variables.append(assigned_var[4:])
            available_vars = sorted(list(self.variable_names - set(fully_asigned_variables)), key=str.lower)
            self.available_vars = ["[V] " + var for var in available_vars]
            self.available_vars.insert(0, "--- separator ---")
            available_events = reversed(sorted(list(set(self.events) - set(fully_asigned_variables))))
            available_events = ["[E] " + event for event in available_events]

            for event in available_events:
                self.available_vars.insert(1, event)

        for _, table in self.tables.items():
            for row in range(table.n_variables):
                cbox_update_options(table.cellWidget(row, Clm.CONTROL), self.available_vars)

        index = self.tabs.currentIndex()
        if index > -1:
            self.tab_title_edit.setText(self.tabs.tabText(index))

    def get_vars(self):
        task = self.parent_controls_dialog.parent_tab.task
        pattern = "[\n\r]v\.(?P<vname>\w+)\s*\="
        try:
            with open(os.path.join(user_folder("tasks"), task + ".py"), "r", encoding="utf-8") as file:
                file_content = file.read()
        except FileNotFoundError:
            return
        # get list of variables. ignore private variables and the custom_controls_dialog variable
        self.variable_names = set(
            [
                v_name
                for v_name in re.findall(pattern, file_content)
                if not v_name.endswith("___")
                and v_name != "custom_controls_dialog"
                and not v_name.startswith("hw_")
                and v_name != "api_class"
            ]
        )

    def add_tab(self, data=None, name=None):
        new_table = Variables_table(self, data)
        if name:
            tab_title = name
        else:
            tab_title = f"tab-{len(self.tables)+1}"
        self.tables[tab_title] = new_table
        self.tabs.addTab(new_table, tab_title)
        if len(self.tables) < 2:
            self.del_tab_btn.setEnabled(False)
        else:
            self.del_tab_btn.setEnabled(True)

    def remove_tab(self):
        if len(self.tables) > 1:
            reply = QtWidgets.QMessageBox.question(
                self,
                "Remove tab",
                f'Are you sure you want to remove "{self.tab_title_edit.text()}"?',
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.Cancel,
            )
            if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                index = self.tabs.currentIndex()
                table_key = self.tabs.tabText(index)
                self.tabs.removeTab(index)
                del self.tables[table_key]
                if len(self.tables) < 2:
                    self.del_tab_btn.setEnabled(False)
                else:
                    self.del_tab_btn.setEnabled(True)
                self.refresh_variable_options()

    def shift_tab_left(self):
        index = self.tabs.currentIndex()
        self.tabs.tabBar().moveTab(index, index - 1)

    def shift_tab_right(self):
        index = self.tabs.currentIndex()
        self.tabs.tabBar().moveTab(index, index + 1)

    def set_tab_title(self):
        new_title = self.tab_title_edit.text()
        if new_title in self.tables:
            QtWidgets.QMessageBox.warning(
                self,
                "Tab title already exists",
                "The new tab title must be different from existing tab titles.",
                QtWidgets.QMessageBox.StandardButton.Ok,
            )
            return
        index = self.tabs.currentIndex()
        old_key = self.tabs.tabText(index)
        self.tables[new_title] = self.tables.pop(old_key)
        self.tabs.setTabText(index, new_title)

    def closeEvent(self, event):
        self.deleteLater()


@dataclass
class Clm:
    UP = 0
    DOWN = 1
    CONTROL = 2
    LABEL = 3
    TYPE = 4
    MIN = 5
    MAX = 6
    STEP = 7
    SUFFIX = 8
    HINT = 9
    ADD = 10


class Control_row:
    def __init__(self, parent_table):
        self.parent_table = parent_table
        # buttons
        self.up_button = QtWidgets.QPushButton("")
        self.up_button.setIcon(QtGui.QIcon("source/gui/icons/up.svg"))
        self.down_button = QtWidgets.QPushButton("")
        self.down_button.setIcon(QtGui.QIcon("source/gui/icons/down.svg"))
        self.remove_button = QtWidgets.QPushButton("remove")
        self.remove_button.setIcon(QtGui.QIcon("source/gui/icons/remove.svg"))
        # line edits
        self.display_name = QtWidgets.QLineEdit()
        self.spin_min = QtWidgets.QLineEdit()
        self.spin_min.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.spin_max = QtWidgets.QLineEdit()
        self.spin_max.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.spin_step = QtWidgets.QLineEdit()
        self.spin_step.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.suffix = QtWidgets.QLineEdit()
        self.suffix.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.hint = QtWidgets.QLineEdit()
        # combo boxes
        self.variable_cbox = QtWidgets.QComboBox()
        self.variable_cbox.activated.connect(lambda: self.parent_table.clear_label(self.display_name.text()))
        self.variable_cbox.addItems(["     select control      "] + self.parent_table.parent_editor.available_vars)
        self.input_type_combo = QtWidgets.QComboBox()
        self.input_type_combo.activated.connect(self.parent_table.update_available)
        self.input_type_combo.addItems(["line edit", "checkbox", "spinbox", "slider"])

        self.column_order = (
            self.up_button,
            self.down_button,
            self.variable_cbox,
            self.display_name,
            self.input_type_combo,
            self.spin_min,
            self.spin_max,
            self.spin_step,
            self.suffix,
            self.hint,
            self.remove_button,
        )

    def copy_vals_from_row(self, row_index):
        var_name = str(self.parent_table.cellWidget(row_index, Clm.CONTROL).currentText())
        self.variable_cbox.addItems([var_name])
        cbox_set_item(self.variable_cbox, var_name)
        self.display_name.setText(str(self.parent_table.cellWidget(row_index, Clm.LABEL).text()))
        cbox_set_item(self.input_type_combo, str(self.parent_table.cellWidget(row_index, Clm.TYPE).currentText()))
        self.spin_min.setText(self.parent_table.cellWidget(row_index, Clm.MIN).text())
        self.spin_max.setText(self.parent_table.cellWidget(row_index, Clm.MAX).text())
        self.spin_step.setText(self.parent_table.cellWidget(row_index, Clm.STEP).text())
        self.suffix.setText(self.parent_table.cellWidget(row_index, Clm.SUFFIX).text())
        self.hint.setText(self.parent_table.cellWidget(row_index, Clm.HINT).text())

    def load_vals_from_spec(self, var_name, specs):
        if var_name.startswith("sep_"):
            self.variable_cbox.addItems(["--- separator ---"])
            cbox_set_item(self.variable_cbox, "--- separator ---")
            cbox_set_item(self.input_type_combo, "bob")
        else:
            if specs.widget == "button":
                var_name = "[E] " + var_name
            else:
                var_name = "[V] " + var_name
            self.variable_cbox.addItems([var_name])
            cbox_set_item(self.variable_cbox, var_name)

        self.display_name.setText(specs.label)
        cbox_set_item(self.input_type_combo, specs.widget)
        self.spin_min.setText(str(specs.min))
        self.spin_max.setText(str(specs.max))
        self.spin_step.setText(str(specs.step))
        self.suffix.setText(specs.suffix)
        self.hint.setText(specs.hint)

    def put_into_table(self, row_index):
        for column, widget in enumerate(self.column_order):
            self.parent_table.setCellWidget(row_index, column, widget)


class Variables_table(QtWidgets.QTableWidget):
    def __init__(self, parent_editor=None, data=None):
        super(QtWidgets.QTableWidget, self).__init__(1, 11, parent=parent_editor)
        self.parent_editor = parent_editor
        self.setHorizontalHeaderLabels(
            ["", "", "Control", "Label", "Control type", "Min", "Max", "Step", "Suffix", "Hint", ""]
        )
        self.verticalHeader().setVisible(False)
        self.setColumnWidth(Clm.UP, 30)
        self.setColumnWidth(Clm.DOWN, 30)
        self.setColumnWidth(Clm.CONTROL, 150)
        self.setColumnWidth(Clm.LABEL, 175)
        self.setColumnWidth(Clm.TYPE, 80)
        self.setColumnWidth(Clm.MIN, 40)
        self.setColumnWidth(Clm.MAX, 40)
        self.setColumnWidth(Clm.STEP, 40)
        self.setColumnWidth(Clm.SUFFIX, 40)
        self.setColumnWidth(Clm.HINT, 150)

        self.n_variables = 0
        self.clear_label_flag = None
        if data:
            for control_name, cntrl_specs_dict in data.items():
                control_specs = Control_specs(**cntrl_specs_dict)
                self.add_row(control_name, control_specs)
            # after done loading control rows, insert another row with an "add" button
            add_button = QtWidgets.QPushButton("   add   ")
            add_button.setIcon(QtGui.QIcon("source/gui/icons/add.svg"))
            add_button.clicked.connect(self.add_row)
            self.setCellWidget(self.n_variables, Clm.ADD, add_button)
        else:
            self.add_row()

    def add_row(self, varname=False, row_dict=False):
        # populate row with widgets
        new_widgets = Control_row(self)
        if varname:
            new_widgets.load_vals_from_spec(varname, row_dict)
        new_widgets.put_into_table(row_index=self.n_variables)

        # connect buttons to functions
        self.connect_buttons(self.n_variables)

        # insert another row with an "add" button
        self.insertRow(self.n_variables + 1)
        if not varname:
            add_button = QtWidgets.QPushButton("   add   ")
            add_button.setIcon(QtGui.QIcon("source/gui/icons/add.svg"))
            add_button.clicked.connect(self.add_row)
            self.setCellWidget(self.n_variables + 1, Clm.ADD, add_button)

        self.n_variables += 1
        self.update_available()
        null_resize(self)

    def remove_row(self, variable_n):
        self.removeRow(variable_n)
        self.n_variables -= 1
        self.update_available()
        null_resize(self)

    def swap_with_above(self, row):
        if self.n_variables > row > 0:
            new_widgets = Control_row(self)
            new_widgets.copy_vals_from_row(row)
            self.removeRow(row)  # delete old row
            above_row = row - 1
            self.insertRow(above_row)  # insert new row
            new_widgets.put_into_table(row_index=above_row)  # populate new row with widgets
            self.connect_buttons(above_row)  # connect new buttons to functions
            self.reconnect_buttons(row)  # disconnect swapped row buttons and reconnect to its new row index
            self.update_available()
            null_resize(self)

    def swap_with_below(self, row):
        self.swap_with_above(row + 1)

    def connect_buttons(self, row):
        ind = QtCore.QPersistentModelIndex(self.model().index(row, Clm.CONTROL))
        self.cellWidget(row, Clm.UP).clicked.connect(lambda: self.swap_with_above(ind.row()))  # up arrow connection
        self.cellWidget(row, Clm.DOWN).clicked.connect(lambda: self.swap_with_below(ind.row()))  # down arrow connection
        self.cellWidget(row, Clm.ADD).clicked.connect(lambda: self.remove_row(ind.row()))  # remove button connection

    def reconnect_buttons(self, row):
        ind = QtCore.QPersistentModelIndex(self.model().index(row, Clm.CONTROL))
        self.cellWidget(row, Clm.UP).clicked.disconnect()  # up arrow
        self.cellWidget(row, Clm.UP).clicked.connect(lambda: self.swap_with_above(ind.row()))
        self.cellWidget(row, Clm.DOWN).clicked.disconnect()  # down arrow
        self.cellWidget(row, Clm.DOWN).clicked.connect(lambda: self.swap_with_below(ind.row()))
        self.cellWidget(row, Clm.ADD).clicked.disconnect()  # remove button
        self.cellWidget(row, Clm.ADD).clicked.connect(lambda: self.remove_row(ind.row()))

    def clear_label(self, val):
        self.clear_label_flag = val
        self.update_available()

    def update_available(self):
        def disable_inputs():
            for col in (Clm.LABEL, Clm.MIN, Clm.MAX, Clm.STEP, Clm.SUFFIX, Clm.HINT):
                self.cellWidget(row, col).setEnabled(False)
                self.cellWidget(row, col).setStyleSheet("background: #dcdcdc;")

        # enable/disable cells depending on input_type type
        for row in range(self.n_variables):
            v_name = self.cellWidget(row, Clm.CONTROL).currentText()
            input_type = self.cellWidget(row, Clm.TYPE).currentText()
            if v_name == "     select control      ":
                disable_inputs()
            elif v_name == "--- separator ---":
                disable_inputs()
                cbox_set_item(self.cellWidget(row, Clm.TYPE), "separator", insert=True)
                cbox_update_options(self.cellWidget(row, Clm.TYPE), ["separator"])
                for i in (Clm.LABEL, Clm.MIN, Clm.MAX, Clm.STEP, Clm.SUFFIX, Clm.HINT):
                    self.cellWidget(row, i).setText("")
            elif v_name.startswith("[E]"):
                disable_inputs()
                cbox_set_item(self.cellWidget(row, Clm.TYPE), "button", insert=True)
                cbox_update_options(self.cellWidget(row, Clm.TYPE), ["button"])
                if self.cellWidget(row, Clm.LABEL).text() == self.clear_label_flag:
                    self.cellWidget(row, Clm.LABEL).setText(v_name[4:].replace("_", " "))
                for col in (Clm.LABEL, Clm.HINT):  # disable inputs until a variable as been selected
                    self.cellWidget(row, col).setEnabled(True)
                    self.cellWidget(row, col).setStyleSheet("background: #ffffff;")
            elif v_name.startswith("[V]"):
                if self.cellWidget(row, Clm.TYPE).currentText() in ("separator", "button"):
                    cbox_set_item(self.cellWidget(row, Clm.TYPE), "line edit", insert=True)
                cbox_update_options(self.cellWidget(row, Clm.TYPE), ["line edit", "checkbox", "spinbox", "slider"])
                self.cellWidget(row, Clm.LABEL).setStyleSheet("background: #ffffff;")
                self.cellWidget(row, Clm.TYPE).setStyleSheet("color: black; background: none;")
                self.cellWidget(row, Clm.HINT).setStyleSheet("background: #ffffff;")
                self.cellWidget(row, Clm.HINT).setEnabled(True)
                if self.cellWidget(row, Clm.LABEL).text() == self.clear_label_flag:
                    self.cellWidget(row, Clm.LABEL).setText(v_name[4:].replace("_", " "))
                for col in (Clm.LABEL, Clm.TYPE, Clm.SUFFIX):
                    self.cellWidget(row, col).setEnabled(True)
                if input_type == "spinbox" or input_type == "slider":
                    for col in (Clm.MIN, Clm.MAX, Clm.STEP, Clm.SUFFIX):
                        self.cellWidget(row, col).setEnabled(True)
                        self.cellWidget(row, col).setStyleSheet("background: #ffffff;")
                else:
                    for col in (Clm.MIN, Clm.MAX, Clm.STEP, Clm.SUFFIX):
                        self.cellWidget(row, col).setEnabled(False)
                        self.cellWidget(row, col).setText("")
                        self.cellWidget(row, col).setStyleSheet("background: #dcdcdc;")
        self.parent_editor.refresh_variable_options()

    def get_tab_data_dict(self):
        tab_dictionary = {}
        num_separators = 0
        for row in range(self.n_variables):
            varname = self.cellWidget(row, Clm.CONTROL).currentText()
            if varname != "     select control      ":
                if varname == "--- separator ---":
                    varname = f"sep_{num_separators}"
                    num_separators += 1
                else:
                    varname = varname[4:]  # remove leading "[V] " or "[E] "
                control_specs = Control_specs(
                    label=self.cellWidget(row, Clm.LABEL).text(),
                    widget=self.cellWidget(row, Clm.TYPE).currentText(),
                    hint=self.cellWidget(row, Clm.HINT).text(),
                )

                if control_specs.widget in ("spinbox", "slider"):
                    # store the value as an integer or float.
                    try:
                        value = self.cellWidget(row, Clm.MIN).text()
                        control_specs.min = float(value) if value.find(".") > -1 else int(value)
                        value = self.cellWidget(row, Clm.MAX).text()
                        control_specs.max = float(value) if value.find(".") > -1 else int(value)
                        value = self.cellWidget(row, Clm.STEP).text()
                        control_specs.step = float(value) if value.find(".") > -1 else int(value)
                    # If the string is empty or not a number, an error message will be shown.
                    except ValueError:
                        msg = QtWidgets.QMessageBox()
                        msg.setText("Numbers for min, max, and step are required for spinboxes and sliders")
                        msg.exec()
                        return None
                    control_specs.suffix = self.cellWidget(row, Clm.SUFFIX).text()
                tab_dictionary[varname] = asdict(control_specs)
        return tab_dictionary


class Custom_variables_not_found_dialog(QtWidgets.QDialog):
    def __init__(self, missing_file, parent):
        super(QtWidgets.QDialog, self).__init__(parent)
        self.setWindowTitle("Custom controls dialog not found")

        message = QtWidgets.QLabel(f'The custom controls dialog <b>"{missing_file}"</b> was not found.<br><br>')
        continue_button = QtWidgets.QPushButton("Continue with\nstandard controls dialog")
        generate_button = QtWidgets.QPushButton("Create new\ncustom controls dialog")
        continue_button.setDefault(True)
        continue_button.setFocus()
        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(message, 0, 0, 1, 2)
        layout.addWidget(continue_button, 1, 0)
        layout.addWidget(generate_button, 1, 1)

        generate_button.clicked.connect(self.accept)
        continue_button.clicked.connect(self.close)

        self.setFixedSize(self.sizeHint())
