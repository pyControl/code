import os
from pyqtgraph.Qt import QtGui, QtCore
from config.paths import config_dir

# Settings_dialog -------------------------------------------------------

class Settings_dialog(QtGui.QDialog):

    def __init__(self, parent=None):
        super(QtGui.QDialog, self).__init__(parent)
        self.setWindowTitle('GUI settings')
        # Create widgets.
        self.s_len_label = QtGui.QLabel('State history length')
        self.s_len_text  = QtGui.QLineEdit(str(100))
        self.e_len_label = QtGui.QLabel('Event hisory length')
        self.e_len_text  = QtGui.QLineEdit(str(100))
        self.a_len_label = QtGui.QLabel('Analog history duration (s)')
        self.a_len_text  = QtGui.QLineEdit(str(5))
        # Layout
        self.grid_layout = QtGui.QGridLayout()
        self.grid_layout.addWidget(self.s_len_label, 1, 1)
        self.grid_layout.addWidget(self.s_len_text , 1, 2)
        self.grid_layout.addWidget(self.e_len_label, 2, 1)
        self.grid_layout.addWidget(self.e_len_text , 2, 2)
        self.grid_layout.addWidget(self.a_len_label, 3, 1)
        self.grid_layout.addWidget(self.a_len_text , 3, 2)
        self.setLayout(self.grid_layout)

# Board_config_dialog -------------------------------------------------

class Board_config_dialog(QtGui.QDialog):

    def __init__(self, parent=None):
        super(QtGui.QDialog, self).__init__(parent)
        self.setWindowTitle('Configure pyboard')
        # Create widgets.
        self.load_fw_button = QtGui.QPushButton('Load framework')
        self.load_hw_button = QtGui.QPushButton('Load hardware definition')
        self.DFU_button = QtGui.QPushButton('Device Firmware Update (DFU) mode')
        self.flashdrive_button = QtGui.QPushButton()
        self.vertical_layout = QtGui.QVBoxLayout()
        # Layout.
        self.setLayout(self.vertical_layout)
        self.vertical_layout.addWidget(self.load_fw_button)
        self.vertical_layout.addWidget(self.load_hw_button)
        self.vertical_layout.addWidget(self.DFU_button)
        self.vertical_layout.addWidget(self.flashdrive_button)
        # Connect widgets.
        self.load_fw_button.clicked.connect(self.load_framework)
        self.load_hw_button.clicked.connect(self.load_hardware_definition)
        self.DFU_button.clicked.connect(self.DFU_mode)
        self.flashdrive_button.clicked.connect(self.flashdrive)

    def exec_(self):
        self.flashdrive_enabled = 'MSC' in self.parent().board.status['usb_mode']
        self.flashdrive_button.setText('{} USB flash drive'
            .format('Disable' if self.flashdrive_enabled else 'Enable'))
        return QtGui.QDialog.exec_(self)

    def load_framework(self):
        self.accept()
        self.parent().board.load_framework()
        self.parent().task_changed()

    def load_hardware_definition(self):
        hwd_path = QtGui.QFileDialog.getOpenFileName(self, 'Select hardware definition:',
                    os.path.join(config_dir, 'hardware_definition.py'), filter='*.py')[0]
        self.accept()
        self.parent().board.load_hardware_definition(hwd_path)
        self.parent().task_changed()

    def DFU_mode(self):
        self.accept()
        self.parent().board.DFU_mode()
        self.parent().disconnect()
        QtCore.QTimer.singleShot(500, self.parent().refresh)

    def flashdrive(self):
        self.accept()
        if self.flashdrive_enabled:
            self.parent().board.disable_mass_storage()
        else:
            self.parent().board.enable_mass_storage()
        self.parent().disconnect()
        QtCore.QTimer.singleShot(500, self.parent().refresh)

# Variables_dialog ---------------------------------------------------------------------

class Variables_dialog(QtGui.QDialog):
    # Dialog for setting and getting task variables.
    def __init__(self, parent=None): # Should split into seperate init and provide info.
        super(QtGui.QDialog, self).__init__(parent)
        self.setWindowTitle('Set variables')
        variables = self.parent().sm_info['variables']
        self.grid_layout = QtGui.QGridLayout()
        for i, (v_name, v_value_str) in enumerate(variables.items()):
            Variable_setter(v_name, v_value_str, self.grid_layout, i, parent=self)
        self.setLayout(self.grid_layout)

class Variable_setter(QtGui.QWidget):
    # Widget for setting and getting a single variable.
    def __init__(self, v_name, v_value_str, grid_layout, i, parent=None): # Should split into seperate init and provide info.
        super(QtGui.QWidget, self).__init__(parent)
        self.board = self.parent().parent().board
        self.v_name = v_name
        self.label = QtGui.QLabel(v_name)
        self.get_button = QtGui.QPushButton('Get value')
        self.set_button = QtGui.QPushButton('Set value')
        self.value_str = QtGui.QLineEdit(v_value_str)
        if v_value_str[0] == '<': # Variable is a complex object that cannot be modifed.
            self.value_str.setText('<complex object>')
            self.set_button.setEnabled(False)
            self.get_button.setEnabled(False)
        self.value_text_colour('gray')
        self.get_button.clicked.connect(self.get)
        self.set_button.clicked.connect(self.set)
        self.value_str.textChanged.connect(lambda x: self.value_text_colour('black'))
        self.value_str.returnPressed.connect(self.set)
        self.get_button.setDefault(False)
        self.get_button.setAutoDefault(False)
        self.set_button.setDefault(False)
        self.set_button.setAutoDefault(False)
        grid_layout.addWidget(self.label     , i, 1)
        grid_layout.addWidget(self.value_str , i, 2)
        grid_layout.addWidget(self.get_button, i, 3)
        grid_layout.addWidget(self.set_button, i, 4)

    def value_text_colour(self, color='gray'):
        self.value_str.setStyleSheet("color: {};".format(color))

    def get(self):
        if self.board.framework_running: # Value returned later.
            self.board.get_variable(self.v_name)
            self.value_str.setText('getting..')
            QtCore.QTimer.singleShot(200, self.reload)
        else: # Value returned immediately.
            self.value_str.setText(str(self.board.get_variable(self.v_name))) 
            QtCore.QTimer.singleShot(1000, self.value_text_colour)

    def set(self):
        try:
            v_value = eval(self.value_str.text())
        except Exception:
            self.value_str.setText('Invalid value')
            return
        if self.board.framework_running: # Value returned later if set OK.
            self.board.set_variable(self.v_name, v_value)
            self.value_str.setText('setting..')
            QtCore.QTimer.singleShot(200, self.reload)
        else: # Set OK returned immediately.
            if self.board.set_variable(self.v_name, v_value):
                self.value_text_colour('gray')
            else:
                self.value_str.setText('Set failed')
                
    def reload(self):
        '''Reload value from sm_info.  sm_info is updated when variables are output
        during framework run due to get/set.'''
        self.value_text_colour('black')
        self.value_str.setText(str(self.board.sm_info['variables'][self.v_name]))
        QtCore.QTimer.singleShot(1000, self.value_text_colour)