import os
import json
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
from gui.settings import dirs, get_setting
from gui.utility import TableCheckbox
from com.pycboard import Pycboard, PyboardError

class Setups_tab(QtWidgets.QWidget):
    '''The setups tab is used to name and configure setups, where one setup is one
    pyboard and connected hardware.'''

    def __init__(self, parent=None):
        super(QtWidgets.QWidget, self).__init__(parent)

        # Variables
        self.GUI_main = self.parent()
        self.setups = {} # Dictionary {serial_port:Setup}
        self.setup_names = []
        self.available_setups_changed = False

        # Load saved setup names.
        self.save_path = os.path.join(dirs['config'], 'setup_names.json')
        if os.path.exists(self.save_path):
            with open(self.save_path, 'r') as f:
                self.saved_names = json.loads(f.read())
        else:
            self.saved_names = {} # {setup.port:setup.name}

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
        load_fw_button.setIcon(QtGui.QIcon("gui/icons/upload.svg"))
        load_hw_button = QtWidgets.QPushButton("Load hardware definition")
        load_hw_button.setIcon(QtGui.QIcon("gui/icons/upload.svg"))
        enable_flashdrive_button = QtWidgets.QPushButton("Enable flashdrive")
        enable_flashdrive_button.setIcon(QtGui.QIcon("gui/icons/enable.svg"))
        disable_flashdrive_button = QtWidgets.QPushButton("Disable flashdrive")
        disable_flashdrive_button.setIcon(QtGui.QIcon("gui/icons/disable.svg"))
        load_fw_button.clicked.connect(self.load_framework)
        load_hw_button.clicked.connect(self.load_hardware_definition)
        enable_flashdrive_button.clicked.connect(self.enable_flashdrive)
        disable_flashdrive_button.clicked.connect(self.disable_flashdrive)
        self.dfu_btn = QtWidgets.QPushButton("DFU mode")
        self.dfu_btn.setIcon(QtGui.QIcon("gui/icons/wrench.svg"))
        self.dfu_btn.clicked.connect(self.DFU_mode)

        config_layout = QtWidgets.QHBoxLayout()
        config_layout.addWidget(load_fw_button)
        config_layout.addWidget(load_hw_button)
        config_layout.addWidget(enable_flashdrive_button)
        config_layout.addWidget(disable_flashdrive_button)
        config_layout.addWidget(self.dfu_btn)
        self.configure_group.setLayout(config_layout)
        self.configure_group.setEnabled(False)

        select_layout = QtWidgets.QGridLayout()
        select_layout.addWidget(self.select_all_checkbox, 0, 0)
        select_layout.addWidget(self.setups_table, 1, 0, 1, 6)
        self.setup_groupbox.setLayout(select_layout)

        # Log textbox.
        self.log_textbox = QtWidgets.QTextEdit()
        self.log_textbox.setMinimumHeight(180)
        self.log_textbox.setFont(QtGui.QFont("Courier", get_setting("GUI", "log_font_size")))
        self.log_textbox.setReadOnly(True)
        self.log_textbox.setPlaceholderText("pyControl output")

        # Clear log
        self.clear_output_btn = QtWidgets.QPushButton("Clear output")
        self.clear_output_btn.clicked.connect(self.log_textbox.clear)

        # # Main layout.
        self.setups_layout = QtWidgets.QGridLayout()
        self.setups_layout.addWidget(self.setup_groupbox,0,0)
        self.setups_layout.addWidget(self.configure_group,1,0)
        self.setups_layout.addWidget(self.log_textbox,2,0)
        self.setups_layout.addWidget(self.clear_output_btn,3,0,QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setups_layout.setRowStretch(0,1)
        self.setups_layout.setRowStretch(2,1)
        self.setLayout(self.setups_layout)


    def adjust_to_small(self):
        max_width = get_setting("GUI","ui_max_width")
        for widget in [self.setup_groupbox,self.configure_group,self.log_textbox]:
            widget.setMaximumWidth(max_width)
            widget.setMinimumWidth(0)

        self.setups_layout.addWidget(self.setup_groupbox,0,0)
        self.setups_layout.addWidget(self.configure_group,1,0)
        self.setups_layout.addWidget(self.log_textbox,2,0)
        self.setups_layout.addWidget(self.clear_output_btn,3,0,QtCore.Qt.AlignmentFlag.AlignCenter)

        self.setups_layout.setColumnStretch(0,1)
        self.setups_layout.setColumnStretch(1,0)
        self.setups_layout.setColumnStretch(2,0)

        self.setups_layout.setRowStretch(0,1)
        self.setups_layout.setRowStretch(2,1)


    def adjust_to_med(self):
        for widget in [self.setup_groupbox,self.configure_group,self.log_textbox]:
            widget.setMinimumWidth(get_setting("GUI","ui_max_width"))

        self.setups_layout.addWidget(self.setup_groupbox,0,0)
        self.setups_layout.addWidget(self.configure_group,1,0)
        self.setups_layout.addWidget(self.log_textbox,2,0)
        self.setups_layout.addWidget(self.clear_output_btn,3,0,QtCore.Qt.AlignmentFlag.AlignCenter)

        self.setups_layout.setColumnStretch(1,1)
        self.setups_layout.setColumnStretch(2,0)

        self.setups_layout.setRowStretch(0,1)
        self.setups_layout.setRowStretch(2,1)

    def adjust_to_large(self):
        self.setups_layout.addWidget(self.setup_groupbox,0,0,4,1)
        self.setups_layout.addWidget(self.configure_group,0,1)
        self.setups_layout.addWidget(self.log_textbox,1,1,2,1)
        self.setups_layout.addWidget(self.clear_output_btn,3,1,QtCore.Qt.AlignmentFlag.AlignCenter)

        self.setups_layout.setColumnStretch(2,1)

        self.setups_layout.setRowStretch(0,0)
        self.setups_layout.setRowStretch(2,1)

    def print_to_log(self, print_string, end="\n"):
        self.log_textbox.moveCursor(QtGui.QTextCursor.MoveOperation.End)
        self.log_textbox.insertPlainText(print_string + end)
        self.log_textbox.moveCursor(QtGui.QTextCursor.MoveOperation.End)
        self.GUI_main.app.processEvents()

    def select_all_setups(self):
        if self.select_all_checkbox.isChecked():
            for setup in self.setups.values():
                setup.signal_from_rowcheck = False
                setup.select_checkbox.setChecked(True)
                setup.signal_from_rowcheck = True
        else:
            for setup in self.setups.values():
                setup.signal_from_rowcheck = False
                setup.select_checkbox.setChecked(False)
                setup.signal_from_rowcheck = True
        self.multi_config_enable()

    def multi_config_enable(self):
        self.select_all_checkbox.blockSignals(True)
        num_checked = 0
        for setup in self.setups.values():
            if setup.select_checkbox.isChecked():
                num_checked += 1
        if num_checked == 1:
            self.dfu_btn.setEnabled(True)
        else:
            self.dfu_btn.setEnabled(False)
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
        '''Update the save setup names when a setup name is edited.'''
        if setup.name == setup.port:
            if setup.port in self.saved_names.keys():
                del self.saved_names[setup.port]
            else:
                return
        else:
            self.saved_names[setup.port] = setup.name
        with open(self.save_path, 'w') as f:
            f.write(json.dumps(self.saved_names, sort_keys=True))

    def get_port(self, setup_name):
        '''Return a setups serial port given the setups name.'''
        return next(setup.port for setup in self.setups.values() if setup.name == setup_name)

    def get_selected_setups(self):
        '''Return sorted list of setups whose select checkboxes are ticked.'''
        return sorted([setup for setup in self.setups.values()
            if setup.select_checkbox.isChecked()], key=lambda setup: setup.port)

    def connect(self, setups):
        for setup in setups:
            setup.connect()

    def disconnect(self):
        '''Disconect from all pyboards.'''
        for setup in self.setups.values():
            setup.disconnect()

    def load_framework(self):
        for setup in self.get_selected_setups():
            setup.load_framework()

    def enable_flashdrive(self):
        for setup in self.get_selected_setups():
            setup.enable_flashdrive()

    def disable_flashdrive(self):
        for setup in self.get_selected_setups():
            setup.disable_flashdrive()

    def DFU_mode(self):
        for setup in self.get_selected_setups():
            setup.DFU_mode()

    def load_hardware_definition(self):
        hwd_path = QtWidgets.QFileDialog.getOpenFileName(self,
            'Select hardware definition:', dirs['hardware_definitions'], filter='*.py')[0]
        for setup in self.get_selected_setups():
            setup.load_hardware_definition(hwd_path)

    def refresh(self):
        '''Called regularly when no task running to update tab with currently 
        connected boards.'''
        if self.GUI_main.available_ports_changed:
            # Add any newly connected setups.
            for serial_port in self.GUI_main.available_ports:
                if not serial_port in self.setups.keys():
                    self.setups[serial_port] = Setup(serial_port, self)
            # Remove any unplugged setups.
            for serial_port in list(self.setups.keys()):
                if serial_port not in self.GUI_main.available_ports:
                    self.setups[serial_port].unplugged()
            self.setups_table.sortItems(0)
        self.update_available_setups()

# setup class --------------------------------------------------------------------

class Setup():
    '''Class representing one setup in the setups table.'''

    def __init__(self, serial_port, setups_tab):
        '''Setup is intilised when board is plugged into computer.'''

        try:
            self.name = setups_tab.saved_names[serial_port]
        except KeyError:
            self.name = serial_port

        self.port = serial_port
        self.setups_tab = setups_tab
        self.board = None

        self.port_item = QtWidgets.QTableWidgetItem()
        self.port_item.setText(serial_port)
        self.port_item.setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled)

        self.name_item = QtWidgets.QTableWidgetItem()
        self.name_item.changed = self.name_edited
        if self.name != self.port:
            self.name_item.setText(self.name)

        self.select_checkbox = TableCheckbox()
        self.setups_tab.setups_table.insertRow(0)
        self.setups_tab.setups_table.setCellWidget(0, 0, self.select_checkbox)
        self.setups_tab.setups_table.setItem(0, 1, self.port_item)
        self.setups_tab.setups_table.setItem(0, 2, self.name_item)
        self.select_checkbox.checkbox.stateChanged.connect(self.checkbox_handler)
        self.signal_from_rowcheck = True

    def checkbox_handler(self):
        if self.signal_from_rowcheck:
            self.setups_tab.multi_config_enable()

    def name_edited(self):
        '''If name entry in table is blank setup name is set to serial port.'''
        name = str(self.name_item.text())
        self.name = name if name else self.port
        self.setups_tab.update_available_setups()
        self.setups_tab.update_saved_setups(self)

    def print(self, print_string):
        ''' Print a string to the log prepended with the setup name.'''
        self.setups_tab.print_to_log('\n{}: '.format(self.name) + print_string)

    def connect(self):
        '''Instantiate pyboard object, opening serial connection to board.'''
        self.print('Connecting to board.')
        try:
            self.board = Pycboard(self.port, print_func=self.setups_tab.print_to_log)
        except PyboardError:
            self.print('Unable to connect.')

    def disconnect(self):
        if self.board:
            self.board.close()
            self.board = None

    def unplugged(self):
        '''Called when a board is physically unplugged from computer. 
        Closes serial connection and removes row from setups table.'''
        if self.board: self.board.close()
        self.setups_tab.setups_table.removeRow(self.port_item.row())
        del self.setups_tab.setups[self.port]

    def load_framework(self):
        if not self.board: self.connect()
        if self.board:
            self.print('Loading framework.')
            self.board.load_framework()

    def load_hardware_definition(self, hwd_path):
        if not self.board: self.connect()
        if self.board:
            self.print('Loading hardware definition.')
            self.board.load_hardware_definition(hwd_path)

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
        if not self.board: self.connect()
        if self.board:
            self.print('Enabling flashdrive.')
            self.board.enable_mass_storage()
            self.board.close()
            self.board = None

    def disable_flashdrive(self):
        self.select_checkbox.setChecked(False)
        if not self.board: self.connect()
        if self.board:
            self.print('Disabling flashdrive.')
            self.board.disable_mass_storage()
            self.board.close()
            self.board = None
