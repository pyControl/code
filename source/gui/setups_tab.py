import json
from pathlib import Path
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
from source.gui.settings import get_setting, user_folder
from source.gui.utility import TableCheckbox, parallel_call
from source.gui.hardware_variables_dialog import Hardware_variables_editor
from source.communication.pycboard import Pycboard, PyboardError


class Setups_tab(QtWidgets.QWidget):
    """The setups tab is used to name and configure setups, where one setup is one
    pyboard and connected hardware."""

    def __init__(self, parent=None):
        super(QtWidgets.QWidget, self).__init__(parent)

        # Variables
        self.GUI_main = self.parent()
        self.setups = {}  # Dictionary {serial_port:Setup}
        self.setup_names = []
        self.available_setups_changed = False

        # rename old file from setup_names.json to setups.json
        # and change format so that names are a key within a serial port dictionary
        setup_names = Path("config", "setup_names.json")
        try:
            new_path = Path("config", "setups.json")
            setup_names.rename(new_path)
            with open(new_path, "r", encoding="utf-8") as names_json:
                names_dict = json.loads(names_json.read())
                new_format = {}
                for k, v in names_dict.items():
                    new_format[k] = {"name": v, "variables": {}}
                with open(new_path, "w", encoding="utf-8") as f:
                    f.write(json.dumps(new_format, sort_keys=True, indent=4))
        except FileNotFoundError:
            pass

        # Load saved setup names.
        self.saved_setups = self.get_setups_from_json()

        # Select setups group box.
        self.setup_groupbox = QtWidgets.QGroupBox("Setups")

        self.select_all_checkbox = QtWidgets.QCheckBox("Select all")
        self.select_all_checkbox.stateChanged.connect(self.select_all_setups)

        self.setups_table = QtWidgets.QTableWidget(0, 3, parent=self)
        self.setups_table.setHorizontalHeaderLabels(["Select", "Serial port", "Name"])
        self.setups_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.setups_table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.setups_table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.setups_table.verticalHeader().setVisible(False)
        self.setups_table.itemChanged.connect(lambda item: item.changed() if hasattr(item, "changed") else None)

        # Configuration buttons
        self.configure_group = QtWidgets.QGroupBox("Configure selected")
        load_fw_button = QtWidgets.QPushButton("Load framework")
        load_fw_button.setIcon(QtGui.QIcon("source/gui/icons/upload.svg"))
        load_hw_button = QtWidgets.QPushButton("Load hardware definition")
        load_hw_button.setIcon(QtGui.QIcon("source/gui/icons/upload.svg"))
        enable_flashdrive_button = QtWidgets.QPushButton("Enable flashdrive")
        enable_flashdrive_button.setIcon(QtGui.QIcon("source/gui/icons/enable.svg"))
        disable_flashdrive_button = QtWidgets.QPushButton("Disable flashdrive")
        disable_flashdrive_button.setIcon(QtGui.QIcon("source/gui/icons/disable.svg"))
        load_fw_button.clicked.connect(self.load_framework)
        load_hw_button.clicked.connect(self.load_hardware_definition)
        enable_flashdrive_button.clicked.connect(self.enable_flashdrive)
        disable_flashdrive_button.clicked.connect(self.disable_flashdrive)
        self.variables_btn = QtWidgets.QPushButton("Variables")
        self.variables_btn.setIcon(QtGui.QIcon("source/gui/icons/filter.svg"))
        self.variables_btn.clicked.connect(self.edit_hardware_vars)

        self.dfu_btn = QtWidgets.QPushButton("DFU mode")
        self.dfu_btn.setIcon(QtGui.QIcon("source/gui/icons/wrench.svg"))
        self.dfu_btn.clicked.connect(self.DFU_mode)

        config_layout = QtWidgets.QGridLayout()
        config_layout.addWidget(load_fw_button, 0, 0)
        config_layout.addWidget(load_hw_button, 1, 0)
        config_layout.addWidget(self.variables_btn, 0, 1)
        config_layout.addWidget(self.dfu_btn, 1, 1)
        config_layout.addWidget(enable_flashdrive_button, 0, 2)
        config_layout.addWidget(disable_flashdrive_button, 1, 2)
        self.configure_group.setLayout(config_layout)
        self.configure_group.setEnabled(False)

        select_layout = QtWidgets.QGridLayout()
        select_layout.addWidget(self.select_all_checkbox, 0, 0)
        select_layout.addWidget(self.setups_table, 1, 0, 1, 6)
        self.setup_groupbox.setLayout(select_layout)

        # Log textbox.
        self.log_textbox = QtWidgets.QTextEdit()
        self.log_textbox.setMinimumHeight(180)
        self.log_textbox.setFont(QtGui.QFont("Courier New", get_setting("GUI", "log_font_size")))
        self.log_textbox.setReadOnly(True)
        self.log_textbox.setPlaceholderText("pyControl output")

        # Clear log
        self.clear_output_btn = QtWidgets.QPushButton("Clear output")
        self.clear_output_btn.clicked.connect(self.log_textbox.clear)

        # # Main layout.
        self.setups_layout = QtWidgets.QGridLayout()
        self.setups_layout.addWidget(self.setup_groupbox, 0, 0)
        self.setups_layout.addWidget(self.configure_group, 1, 0)
        self.setups_layout.addWidget(self.log_textbox, 2, 0)
        self.setups_layout.addWidget(self.clear_output_btn, 3, 0, QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setups_layout.setRowStretch(0, 1)
        self.setups_layout.setRowStretch(2, 1)
        self.setLayout(self.setups_layout)

    def get_setups_from_json(self):
        self.save_path = Path("config", "setups.json")
        if self.save_path.exists():
            with open(self.save_path, "r", encoding="utf-8") as f:
                setups_from_json = json.loads(f.read())
        else:
            setups_from_json = {}  # {setup.port:setup.name}
        return setups_from_json

    def print_to_log(self, print_string, end="\n"):
        self.log_textbox.moveCursor(QtGui.QTextCursor.MoveOperation.End)
        self.log_textbox.insertPlainText(print_string + end)
        self.log_textbox.moveCursor(QtGui.QTextCursor.MoveOperation.End)
        self.GUI_main.app.processEvents()

    def select_all_setups(self):
        if self.select_all_checkbox.isChecked():
            for setup in self.setups.values():
                if setup.select_checkbox.isEnabled():
                    setup.signal_from_rowcheck = False
                    setup.select_checkbox.setChecked(True)
                    setup.signal_from_rowcheck = True
        else:
            for setup in self.setups.values():
                if setup.select_checkbox.isEnabled():
                    setup.signal_from_rowcheck = False
                    setup.select_checkbox.setChecked(False)
                    setup.signal_from_rowcheck = True
        self.multi_config_enable()

    def multi_config_enable(self):
        """Configure which GUI buttons are active as a function of the setups selected."""
        self.select_all_checkbox.blockSignals(True)
        num_checked = 0
        for setup in self.setups.values():
            if setup.select_checkbox.isChecked():
                num_checked += 1
        if num_checked == 1:
            self.dfu_btn.setEnabled(True)
        else:
            self.dfu_btn.setEnabled(False)
        if len(self.get_selected_setups(has_name_filter=True)):
            self.variables_btn.setEnabled(True)
        else:
            self.variables_btn.setEnabled(False)
        if num_checked > 0:
            self.configure_group.setEnabled(True)
            if num_checked < len(self.setups.values()):  # some selected
                self.select_all_checkbox.setChecked(False)
            else:  # all selected
                self.select_all_checkbox.setChecked(True)
        else:  # none selected
            self.select_all_checkbox.setChecked(False)
            self.configure_group.setEnabled(False)
        self.select_all_checkbox.blockSignals(False)

    def update_available_setups(self):
        """Called when boards are plugged, unplugged or renamed."""
        setup_names = sorted([setup.name for setup in self.setups.values() if setup.name != "_hidden_"])
        if setup_names != self.setup_names:
            self.available_setups_changed = True
            self.setup_names = setup_names
            self.multi_config_enable()
        else:
            self.available_setups_changed = False

    def update_saved_setups(self, setup):
        """Update the save setup names when a setup name is edited."""
        if setup.name == setup.port:
            if setup.port not in self.saved_setups.keys():
                return
            else:
                del self.saved_setups[setup.port]
        else:
            if setup.port not in self.saved_setups:
                # create a new setup
                self.saved_setups[setup.port] = {}
                self.saved_setups[setup.port]["name"] = setup.name
                self.saved_setups[setup.port]["variables"] = {}
            else:
                # edit existing setup name
                self.saved_setups[setup.port]["name"] = setup.name
                if "variables" not in self.saved_setups[setup.port].keys():
                    self.saved_setups[setup.port]["variables"] = {}

        with open(self.save_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(self.saved_setups, sort_keys=True, indent=4))

    def get_port(self, setup_name):
        """Return a setups serial port given the setups name."""
        return next(setup.port for setup in self.setups.values() if setup.name == setup_name)

    def get_selected_setups(self, has_name_filter=False):
        """Return sorted list of setups whose select checkboxes are ticked."""
        if has_name_filter:
            return sorted(
                [
                    setup
                    for setup in self.setups.values()
                    if setup.select_checkbox.isChecked() and setup.name != setup.port and setup.name != "_hidden_"
                ],
                key=lambda setup: setup.port,
            )
        else:
            return sorted(
                [setup for setup in self.setups.values() if setup.select_checkbox.isChecked()],
                key=lambda setup: setup.port,
            )

    def disconnect(self):
        """Disconect from all pyboards, called on tab change."""
        if self.setups.values():
            parallel_call("disconnect", self.setups.values())

    def edit_hardware_vars(self):
        hardware_var_editor = Hardware_variables_editor(self)
        if not hardware_var_editor.get_hw_vars_from_task_files():
            warning_msg = (
                "There were no hardware variables found in your task files. "
                "To use a hardware variable, add a variable beginning with "
                "'hw_' to a task file for example 'v.hw_solenoid_dur = None'."
            )
            QtWidgets.QMessageBox.warning(
                self,
                "No hardware variables found",
                warning_msg,
                QtWidgets.QMessageBox.StandardButton.Ok,
            )
            return
        hardware_var_editor.exec()

    def load_framework(self):
        self.print_to_log("Loading framework...\n")
        parallel_call("load_framework", self.get_selected_setups())

    def enable_flashdrive(self):
        self.print_to_log("Enabling flashdrive...\n")
        parallel_call("enable_flashdrive", self.get_selected_setups())

    def disable_flashdrive(self):
        self.print_to_log("Disabling flashdrive...\n")
        parallel_call("disable_flashdrive", self.get_selected_setups())

    def DFU_mode(self):
        self.print_to_log("Enabling DFU mode...\n")
        parallel_call("DFU_mode", self.get_selected_setups())

    def load_hardware_definition(self):
        self.hwd_path = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select hardware definition:", user_folder("hardware_definitions"), filter="*.py"
        )[0]
        if self.hwd_path:
            self.print_to_log("Loading hardware definition...\n")
            parallel_call("load_hardware_definition", self.get_selected_setups())

    def refresh(self):
        """Called regularly when no task running to update tab with currently
        connected boards."""
        if self.GUI_main.available_ports_changed:
            # Add any newly connected setups.
            for serial_port in self.GUI_main.available_ports:
                if serial_port not in self.setups.keys():
                    self.setups[serial_port] = Setup(serial_port, self)
            # Remove any unplugged setups.
            for serial_port in list(self.setups.keys()):
                if serial_port not in self.GUI_main.available_ports:
                    self.setups[serial_port].unplugged()
            self.setups_table.sortItems(1)
        self.update_available_setups()


# setup class --------------------------------------------------------------------


class Setup:
    """Class representing one setup in the setups table."""

    def __init__(self, serial_port, setups_tab):
        """Setup is intilised when board is plugged into computer."""

        try:
            self.name = setups_tab.saved_setups[serial_port]["name"]
        except KeyError:
            # key error could be from the serial_port not being connected
            # or the serial port was never assigned a name before
            self.name = serial_port

        self.port = serial_port
        self.setups_tab = setups_tab
        self.board = None
        self.delay_printing = False

        self.port_item = QtWidgets.QTableWidgetItem()
        self.port_item.setText(serial_port)
        self.port_item.setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled)

        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.setPlaceholderText("name required if you want to edit setup variables")
        self.name_edit.textChanged.connect(self.name_changed)
        if self.name != self.port:
            self.name_edit.setText(self.name)

        self.select_checkbox = TableCheckbox()
        self.select_checkbox.checkbox.stateChanged.connect(self.checkbox_handler)

        self.setups_tab.setups_table.insertRow(0)
        self.setups_tab.setups_table.setCellWidget(0, 0, self.select_checkbox)
        self.setups_tab.setups_table.setItem(0, 1, self.port_item)
        self.setups_tab.setups_table.setCellWidget(0, 2, self.name_edit)
        self.signal_from_rowcheck = True

        self.name_changed()

    def checkbox_handler(self):
        if self.signal_from_rowcheck:
            self.setups_tab.multi_config_enable()

    def name_changed(self):
        """If name entry in table is blank setup name is set to serial port."""
        name = str(self.name_edit.text())
        self.name = name if name else self.port
        self.setups_tab.update_available_setups()
        self.setups_tab.update_saved_setups(self)

        if name == "":
            self.name_edit.setStyleSheet("color: red;")
        elif name == "_hidden_":
            self.name_edit.setStyleSheet("color: grey;")
        else:
            self.name_edit.setStyleSheet("color: black;")

    def print(self, print_string, end="\n"):
        """Print a string to the log prepended with the setup name."""
        if self.delay_printing:
            self.print_queue.append((print_string, end))
            return
        self.setups_tab.print_to_log(f"\n{self.name}: " + print_string)

    def start_delayed_print(self):
        """Store print output to display later to avoid error
        message when calling print from different thread."""
        self.print_queue = []
        self.delay_printing = True

    def end_delayed_print(self):
        """Print output stored in print queue to log with setup
        name and horisontal line above."""
        self.delay_printing = False
        if self.print_queue:
            self.setups_tab.print_to_log(f"{self.name} " + "-" * 70)
            for p in self.print_queue:
                self.setups_tab.print_to_log(*p)
            self.setups_tab.print_to_log("")  # Add blank line.

    def connect(self):
        """Instantiate pyboard object, opening serial connection to board."""
        self.print("\nConnecting to board.")
        try:
            self.board = Pycboard(self.port, print_func=self.print)
        except PyboardError:
            self.print("\nUnable to connect.")

    def disconnect(self):
        if self.board:
            self.board.close()
            self.board = None

    def unplugged(self):
        """Called when a board is physically unplugged from computer.
        Closes serial connection and removes row from setups table."""
        if self.board:
            self.board.close()
        self.setups_tab.setups_table.removeRow(self.port_item.row())
        del self.setups_tab.setups[self.port]

    def load_framework(self):
        if not self.board:
            self.connect()
        if self.board:
            self.board.load_framework()

    def load_hardware_definition(self):
        if not self.board:
            self.connect()
        if self.board:
            self.board.load_hardware_definition(self.setups_tab.hwd_path)

    def DFU_mode(self):
        """Enter DFU mode"""
        self.select_checkbox.setChecked(False)
        if not self.board:
            self.connect()
        if self.board:
            self.board.DFU_mode()
            self.board.close()

    def enable_flashdrive(self):
        self.select_checkbox.setChecked(False)
        if not self.board:
            self.connect()
        if self.board:
            self.board.enable_mass_storage()
            self.board.close()
            self.board = None

    def disable_flashdrive(self):
        self.select_checkbox.setChecked(False)
        if not self.board:
            self.connect()
        if self.board:
            self.board.disable_mass_storage()
            self.board.close()
            self.board = None
