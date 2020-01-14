import os

from pyqtgraph.Qt import QtGui, QtCore

from config.paths import config_dir
from gui.utility import variable_constants

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
        # Layout.
        self.vertical_layout = QtGui.QVBoxLayout()
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

    def exec_(self, board):
        self.board = board
        self.flashdrive_enabled = 'MSC' in self.board.status['usb_mode']
        self.flashdrive_button.setText('{} USB flash drive'
            .format('Disable' if self.flashdrive_enabled else 'Enable'))
        self.disconnect = False # Indicates whether board was disconnected by dialog.
        return QtGui.QDialog.exec_(self)

    def load_framework(self):
        self.accept()
        self.board.load_framework()

    def load_hardware_definition(self):
        hwd_path = QtGui.QFileDialog.getOpenFileName(self, 'Select hardware definition:',
                    os.path.join(config_dir, 'hardware_definition.py'), filter='*.py')[0]
        self.accept()
        self.board.load_hardware_definition(hwd_path)

    def DFU_mode(self):
        self.accept()
        self.board.DFU_mode()
        self.disconnect = True

    def flashdrive(self):
        self.accept()
        if self.flashdrive_enabled:
            self.board.disable_mass_storage()
        else:
            self.board.enable_mass_storage()
        self.disconnect = True

# Variables_dialog ---------------------------------------------------------------------

class Variables_dialog(QtGui.QDialog):
    # Dialog for setting and getting task variables.
    def __init__(self, parent, board):
        super(QtGui.QDialog, self).__init__(parent)
        self.setWindowTitle('Set variables')
        self.scroll_area = QtGui.QScrollArea(parent=self)
        self.scroll_area.setWidgetResizable(True)
        self.variables_grid = Variables_grid(self.scroll_area, board)
        self.scroll_area.setWidget(self.variables_grid)
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.addWidget(self.scroll_area)
        self.setLayout(self.layout)

class Variables_grid(QtGui.QWidget):
    # Grid of variables to set/get, displayed within scroll area of dialog.
    def __init__(self, parent, board):
        super(QtGui.QWidget, self).__init__(parent)
        variables = board.sm_info['variables']
        self.grid_layout = QtGui.QGridLayout()
        for i, (v_name, v_value_str) in enumerate(sorted(variables.items())):
            Variable_setter(v_name, v_value_str, self.grid_layout, i, self, board)
        self.setLayout(self.grid_layout)

class Variable_setter(QtGui.QWidget):
    # For setting and getting a single variable.
    def __init__(self, v_name, v_value_str, grid_layout, i, parent, board): # Should split into seperate init and provide info.
        super(QtGui.QWidget, self).__init__(parent)
        self.board = board
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
            self.value_text_colour('black')
            self.value_str.setText(repr(self.board.get_variable(self.v_name))) 
            QtCore.QTimer.singleShot(1000, self.value_text_colour)

    def set(self):
        try:
            v_value = eval(self.value_str.text(), variable_constants)
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
        self.value_str.setText(repr(self.board.sm_info['variables'][self.v_name]))
        QtCore.QTimer.singleShot(1000, self.value_text_colour)

# Summary variables dialog -----------------------------------------------------------

class Summary_variables_dialog(QtGui.QDialog):
    '''Dialog for displaying summary variables from an experiment as a table.
    The table is copied to the clipboard as a string that can be pasted into a
    spreadsheet.'''
    def __init__(self, parent, sv_dict):
        super(QtGui.QDialog, self).__init__(parent)
        self.setWindowTitle('Summary variables')

        subjects = list(sv_dict.keys())
        v_names  = sorted(sv_dict[subjects[0]].keys())

        self.label = QtGui.QLabel('Summary variables copied to clipboard.')
        self.label.setAlignment(QtCore.Qt.AlignCenter)

        self.table = QtGui.QTableWidget(len(subjects), len(v_names),  parent=self)
        self.table.setSizeAdjustPolicy(QtGui.QAbstractScrollArea.AdjustToContents)
        self.table.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.table.setHorizontalHeaderLabels(v_names)
        self.table.setVerticalHeaderLabels(subjects)

        self.Vlayout = QtGui.QVBoxLayout(self)
        self.Vlayout.addWidget(self.label)
        self.Vlayout.addWidget(self.table)

        clip_string = 'Subject\t' + '\t'.join(v_names)

        for s, subject in enumerate(subjects):
            clip_string += '\n' + subject
            for v, v_name in enumerate(v_names):
                v_value_str = repr(sv_dict[subject][v_name])
                clip_string += '\t' + v_value_str
                item = QtGui.QTableWidgetItem()
                item.setText(v_value_str)
                self.table.setItem(s, v, item)

        self.table.resizeColumnsToContents()

        clipboard = QtGui.QApplication.clipboard()
        clipboard.setText(clip_string)

# Invalid experiment dialog. ---------------------------------------------------------

def invalid_experiment_dialog(parent, message):
    QtGui.QMessageBox.question(parent, 'Invalid experiment', 
        message + '\n\nUnable to run experiment.', QtGui.QMessageBox.Ok)

# Keyboard shortcuts dialog. ---------------------------------------------------------

class Keyboard_shortcuts_dialog(QtGui.QDialog):
    '''Dialog for displaying summary variables from an experiment as a table.
    The table is copied to the clipboard as a string that can be pasted into a
    spreadsheet.'''
    def __init__(self, parent):
        super(QtGui.QDialog, self).__init__(parent)
        self.setWindowTitle('Keyboard shortcuts')

        self.Vlayout = QtGui.QVBoxLayout(self)

        self.textbox = QtGui.QTextEdit()
        self.textbox.setReadOnly(True)
        self.textbox.setFont(QtGui.QFont('Courier New', 9))
        self.textbox.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff);

        self.textbox.insertHtml('<p><b>Global:</b></p>\n')

        self.textbox.insertPlainText('\n'
            'Ctrl + t : Open tasks folder\n'
            'Ctrl + d : Open data folder\n')
        self.textbox.insertHtml('<p><b>Run task tab:</b></p>\n')
        self.textbox.insertPlainText('\n'
            '    t    : Select task\n'
            '    u    : Upload/reset task\n'
            'spacebar : Start/stop task\n')
        self.textbox.insertHtml('<p><b>Experiments tab:</b></p>\n')
        self.textbox.insertPlainText('\n'
            'Ctrl + s : save experiment\n')

        self.Vlayout.addWidget(self.textbox)
        self.resize(240, 270)
        self.textbox.moveCursor(QtGui.QTextCursor.Start)
        self.textbox.ensureCursorVisible()

