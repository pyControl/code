import os
import json

from pyqtgraph.Qt import QtGui, QtCore

from config.paths import dirs, update_paths
from gui.utility import variable_constants

# Board_config_dialog -------------------------------------------------

flashdrive_message = (
    'It is recommended to disable the pyboard filesystem from acting as a '
    'USB flash drive before loading the framework, as this helps prevent the '
    'filesystem getting corrupted. Do you want to disable the flashdrive?')

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
        if self.flashdrive_enabled:
            reply = QtGui.QMessageBox.question(self, 'Disable flashdrive', 
                flashdrive_message, QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
            if reply == QtGui.QMessageBox.Yes:
                self.board.disable_mass_storage()
                self.disconnect = True
                return
        self.board.load_framework()

    def load_hardware_definition(self):
        hwd_path = QtGui.QFileDialog.getOpenFileName(self, 'Select hardware definition:',
                    os.path.join(dirs['config'], 'hardware_definition.py'), filter='*.py')[0]
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
            if not v_name[-3:] == '___':
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

def invalid_run_experiment_dialog(parent, message):
    QtGui.QMessageBox.warning(parent, 'Invalid experiment', 
        message + '\n\nUnable to run experiment.', QtGui.QMessageBox.Ok)

def invalid_save_experiment_dialog(parent, message):
    QtGui.QMessageBox.warning(parent, 'Invalid experiment', 
        message + '\n\nUnable to save experiment.', QtGui.QMessageBox.Ok)

# Unrun subjects warning     ---------------------------------------------------------

def unrun_subjects_dialog(parent,message):
    reply = QtGui.QMessageBox.warning(parent, 'Unrun Subjects', 
        'The following Subjects will not be run:\n\n{}'.format(message), (QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel))
    if reply == QtGui.QMessageBox.Ok:
        return True
    else:
        return False
        
# Keyboard shortcuts dialog. ---------------------------------------------------------

class Keyboard_shortcuts_dialog(QtGui.QDialog):
    '''Dialog for displaying information about keyboard shortcuts.'''
    def __init__(self, parent):
        super(QtGui.QDialog, self).__init__(parent)
        self.setWindowTitle('Shortcuts')

        self.Vlayout = QtGui.QVBoxLayout(self)

        label = QtGui.QLabel('<center><b>Keyboard Shortcuts</b></center<br></br>')
        label.setFont(QtGui.QFont('Helvetica', 12))
        self.Vlayout.addWidget(label)

        label_strings = [
            '<b><u>Global:</u></b>',
            '<b style="color:#0220e0;">Ctrl + t</b> : Open tasks folder',
            '<b style="color:#0220e0;">Ctrl + d</b> : Open data folder',
        
            '<br></br><b><u>Run task tab:</u></b>',
            '<b style="color:#0220e0;">    t    </b> : Select task',
            '<b style="color:#0220e0;">    u    </b> : Upload/reset task',
            '<b style="color:#0220e0;">spacebar </b> : Start/stop task',

            '<br></br><b><u>Experiments tab:</u></b>',
            '<b style="color:#0220e0;">Ctrl + s</b> : Save experiment ']

        for ls in label_strings:
            label = QtGui.QLabel(ls)
            label.setFont(QtGui.QFont('Helvetica', 10))
            self.Vlayout.addWidget(label)

        self.setFixedSize(self.sizeHint())

# Paths dialog. ---------------------------------------------------------

class Path_setter():
    def __init__(self, name, path, edited, dialog):
        self.name = name
        self.path = os.path.normpath(path)
        self.edited = edited
        self.dialog = dialog
        # Instantiate widgets
        self.name_label = QtGui.QLabel(name +' folder:')
        self.path_text = QtGui.QLineEdit(self.path)
        self.path_text.setReadOnly(True)
        self.path_text.setFixedWidth(400)
        self.change_button = QtGui.QPushButton('Change')
        self.change_button.clicked.connect(self.select_path)
        # Layout
        self.hlayout = QtGui.QHBoxLayout()
        self.hlayout.addWidget(self.name_label)
        self.hlayout.addWidget(self.path_text)
        self.hlayout.addWidget(self.change_button)
        self.dialog.Vlayout.addLayout(self.hlayout)

        self.dialog.setters.append(self)

    def select_path(self):
        new_path = QtGui.QFileDialog.getExistingDirectory(
            self.dialog, 'Select {} folder'.format(self.name), self.path)
        if new_path:
            new_path = os.path.normpath(new_path)
            if new_path != self.path:
                self.path = new_path
                self.edited = True
                self.path_text.setText(new_path)

class Paths_dialog(QtGui.QDialog):
    '''Dialog for displaying information about keyboard shortcuts.'''
    def __init__(self, parent):
        super(QtGui.QDialog, self).__init__(parent)
        self.setWindowTitle('Paths')

        self.Vlayout = QtGui.QVBoxLayout(self)
        self.setters = []

        # Instantiate setters
        self.tasks_setter = Path_setter('tasks', dirs['tasks'], False, self)
        self.data_setter  = Path_setter('data' , dirs['data'] , False, self)

        self.setFixedSize(self.sizeHint())

    def closeEvent(self, event):
        '''Save any user edited paths as json in config folder.'''
        edited_paths = {s.name: s.path for s in self.setters if s.edited}
        if edited_paths:
            # Store newly edited paths.
            json_path = os.path.join(dirs['config'],'user_paths.json')
            if os.path.exists(json_path):
                with open(json_path,'r') as f:
                    user_paths = json.loads(f.read())
            else:
                user_paths = {}
            user_paths.update(edited_paths)
            with open(json_path, 'w') as f:
                f.write(json.dumps(user_paths))
            self.parent().data_dir_changed = True
            update_paths(user_paths)
