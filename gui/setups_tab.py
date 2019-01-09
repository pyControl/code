import os

from pyqtgraph.Qt import QtGui, QtCore

from config.paths import config_dir
from gui.dialogs import Board_config_dialog
from com.pycboard import Pycboard, PyboardError
from gui.utility import TableCheckbox

class Setups_tab(QtGui.QWidget):
    '''The setups tab is used to name and configure setups.  A setup is one pyboard.'''

    def __init__(self, parent=None):
        super(QtGui.QWidget, self).__init__(parent)

        # Variables

        self.GUI_main = self.parent()
        self.setups = {} # Dictionary {serial_port:Setup}
        self.available_setups = [] # List of names of connected setups.
        self.portdict = {} # Dictionary {setup_name_or_port: setup_port}
        self.available_setups_changed = False
        self.board_config_dialog = Board_config_dialog(self)

        # Select setups group box.

        self.select_groupbox = QtGui.QGroupBox('Setups')

        self.select_all_button = QtGui.QPushButton('Select all')
        self.deselect_all_button = QtGui.QPushButton('Deselect all')

        self.select_all_button.clicked.connect(self.select_all_setups)
        self.deselect_all_button.clicked.connect(self.deselect_all_setups)

        self.setups_table = QtGui.QTableWidget(0, 3, parent=self)
        self.setups_table.setHorizontalHeaderLabels(['Serial port', 'Name', 'Select'])
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

    def disconnect(self):
        '''Disconect from all pyboards.'''
        for setup in self.setups.values():
            if setup.board:setup.board.close()

    def update_available_setups(self):
        available_setups =  sorted([setup.name if setup.name else setup.port
                             for setup in self.setups.values()])
        if available_setups != self.available_setups:
            self.available_setups_changed = True
            self.available_setups = available_setups
            self.portdict = {setup.name if setup.name else setup.port: setup.port
                             for setup in self.setups.values()}

    def get_selected_setups(self):
        return sorted([setup for setup in self.setups.values() 
                       if setup.select_checkbox.isChecked()], key=lambda setup: setup.port)

    def connect(self, setups):
        for setup in setups:
            setup.connect()

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
            os.path.join(config_dir, 'hardware_definition.py'), filter='*.py')[0]
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
            # Process any disconnections.
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

        self.name = None
        self.port = serial_port
        self.setups_tab = setups_tab
        self.board = None

        self.port_item = QtGui.QTableWidgetItem()
        self.port_item.setText(serial_port)
        self.port_item.setFlags(QtCore.Qt.ItemIsEnabled)

        self.name_item = QtGui.QTableWidgetItem()
        self.name_item.changed = self.name_edited

        self.select_checkbox = TableCheckbox()

        self.setups_tab.setups_table.insertRow(0)
        self.setups_tab.setups_table.setItem(0, 0, self.port_item)
        self.setups_tab.setups_table.setItem(0, 1, self.name_item)
        self.setups_tab.setups_table.setCellWidget(0, 2, self.select_checkbox)

    def name_edited(self):
        self.name = str(self.name_item.text())
        self.setups_tab.update_available_setups()

    def print(self, print_string):
        self.setups_tab.print_to_log('\n{}: '.format(self.name if self.name else self.port)
                                     + print_string)

    def connect(self):
        self.print('Connecting to board.')
        try: 
            self.board = Pycboard(self.port, print_func=self.setups_tab.print_to_log)
        except PyboardError:
            self.print('Unable to connect.')

    def unplugged(self):
        '''Called when a board is physically unplugged from computer.'''
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