import os
import json

from pyqtgraph.Qt import QtGui, QtCore

from config.paths import dirs
from com.pycboard import Pycboard, PyboardError
from gui.utility import TableCheckbox

class Setups_tab(QtGui.QWidget):
    '''The setups tab is used to name and configure setups, where one setup is one
    pyboard and connected hardware.'''

    def __init__(self, parent=None):
        super(QtGui.QWidget, self).__init__(parent)

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

        self.select_groupbox = QtGui.QGroupBox('Setups')

        self.select_all_button = QtGui.QPushButton('Select all')
        self.deselect_all_button = QtGui.QPushButton('Deselect all')

        self.select_all_button.clicked.connect(self.select_all_setups)
        self.deselect_all_button.clicked.connect(self.deselect_all_setups)

        self.setups_table = QtGui.QTableWidget(0, 4, parent=self)
        self.setups_table.setHorizontalHeaderLabels(['Serial port', 'Name', 'Select', 'Configure'])
        self.setups_table.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        self.setups_table.verticalHeader().setVisible(False)
        self.setups_table.itemChanged.connect(
            lambda item: item.changed() if hasattr(item, 'changed') else None)

        self.select_Hlayout = QtGui.QHBoxLayout()
        self.select_Hlayout.addWidget(self.select_all_button)
        self.select_Hlayout.addWidget(self.deselect_all_button)
        self.select_Vlayout = QtGui.QVBoxLayout(self.select_groupbox)

        self.select_Vlayout.addLayout(self.select_Hlayout)
        self.select_Vlayout.addWidget(self.setups_table)

        # Configure groupbox.

        self.configure_groupbox = QtGui.QGroupBox('Configure selected')

        self.load_fw_button = QtGui.QPushButton('Load framework')
        self.load_hw_button = QtGui.QPushButton('Load hardware definition')
        self.enable_flashdrive_button = QtGui.QPushButton('Enable flashdrive')
        self.disable_flashdrive_button = QtGui.QPushButton('Disable flashdrive')

        self.load_fw_button.clicked.connect(self.load_framework)
        self.load_hw_button.clicked.connect(self.load_hardware_definition)
        self.enable_flashdrive_button.clicked.connect(self.enable_flashdrive)
        self.disable_flashdrive_button.clicked.connect(self.disable_flashdrive)

        self.config_layout = QtGui.QHBoxLayout(self.configure_groupbox)
        self.config_layout.addWidget(self.load_fw_button)
        self.config_layout.addWidget(self.load_hw_button)
        self.config_layout.addWidget(self.enable_flashdrive_button)
        self.config_layout.addWidget(self.disable_flashdrive_button)

        # Log textbox.

        self.log_textbox = QtGui.QTextEdit()
        self.log_textbox.setMinimumHeight(180)
        self.log_textbox.setFont(QtGui.QFont('Courier', 9))
        self.log_textbox.setReadOnly(True)

        # Main layout.

        self.VLayout = QtGui.QVBoxLayout(self)
        self.VLayout.addWidget(self.select_groupbox)
        self.VLayout.addWidget(self.configure_groupbox)
        self.VLayout.addWidget(self.log_textbox)

    def print_to_log(self, print_string, end='\n'):
        self.log_textbox.moveCursor(QtGui.QTextCursor.End)
        self.log_textbox.insertPlainText(print_string+end)
        self.log_textbox.moveCursor(QtGui.QTextCursor.End)
        self.GUI_main.app.processEvents()

    def select_all_setups(self):
        for setup in self.setups.values():
            setup.select_checkbox.setChecked(True)

    def deselect_all_setups(self):
        for setup in self.setups.values():
            setup.select_checkbox.setChecked(False)

    def update_available_setups(self):
        '''Called when boards are plugged, unplugged or renamed.'''
        setup_names =  sorted([setup.name for setup in self.setups.values()])
        if setup_names != self.setup_names:
            self.available_setups_changed = True
            self.setup_names = setup_names
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

    def load_hardware_definition(self):
        hwd_path = QtGui.QFileDialog.getOpenFileName(self, 'Select hardware definition:',
            os.path.join(dirs['config'], 'hardware_definition.py'), filter='*.py')[0]
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

        self.port_item = QtGui.QTableWidgetItem()
        self.port_item.setText(serial_port)
        self.port_item.setFlags(QtCore.Qt.ItemIsEnabled)

        self.name_item = QtGui.QTableWidgetItem()
        self.name_item.changed = self.name_edited
        if self.name != self.port: 
            self.name_item.setText(self.name)

        self.select_checkbox = TableCheckbox()
        self.config_button = QtGui.QPushButton('Configure')
        self.config_button.setIcon(QtGui.QIcon("gui/icons/settings.svg"))
        self.config_button.clicked.connect(self.open_config_dialog)

        self.setups_tab.setups_table.insertRow(0)
        self.setups_tab.setups_table.setItem(0, 0, self.port_item)
        self.setups_tab.setups_table.setItem(0, 1, self.name_item)
        self.setups_tab.setups_table.setCellWidget(0, 2, self.select_checkbox)
        self.setups_tab.setups_table.setCellWidget(0, 3, self.config_button)

    def name_edited(self):
        '''If name entry in table is blank setup name is set to serial port.'''
        name = str(self.name_item.text())
        self.name = name if name else self.port
        self.setups_tab.update_available_setups()
        self.setups_tab.update_saved_setups(self)

    def open_config_dialog(self):
        '''Open the config dialog and update board status as required.'''
        if not self.board: self.connect()
        if self.board:
            self.setups_tab.GUI_main.config_dialog.exec_(self.board)
            if self.setups_tab.GUI_main.config_dialog.disconnect:
                self.disconnect()

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
        del(self.setups_tab.setups[self.port])

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

    def enable_flashdrive(self):
        if not self.board: self.connect()
        if self.board:
            self.print('Enabling flashdrive.')
            self.board.enable_mass_storage()
            self.board.close()
            self.board = None

    def disable_flashdrive(self):
        if not self.board: self.connect()
        if self.board:
            self.print('Disabling flashdrive.')
            self.board.disable_mass_storage()
            self.board.close()
            self.board = None
