import os
import json
import re

from pyqtgraph.Qt import QtGui, QtCore

from config.paths import dirs, update_paths
from gui.utility import variable_constants,null_resize,cbox_set_item,cbox_update_options

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
    '''Dialog for editing folder paths.'''
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


class Gui_generator_dialog(QtGui.QDialog):
    def __init__(self, parent):
        super(QtGui.QDialog, self).__init__(parent)
        self.setWindowTitle('GUI Generator')

        self.Vlayout = QtGui.QGridLayout(self)
        self.variable_generator_table = GUI_VariablesTable(self)
        self.dialog_name_lbl = QtGui.QLabel('Dialog Name')
        self.generate_btn = QtGui.QPushButton('Save GUI')
        self.generate_btn.setIcon(QtGui.QIcon("gui/icons/save.svg"))
        self.generate_btn.clicked.connect(self.variable_generator_table.save_gui_data)
        self.Vlayout.addWidget(self.variable_generator_table,0,0)
        self.Vlayout.addWidget(self.dialog_name_lbl,1,0)
        self.Vlayout.addWidget(self.generate_btn,1,0)
        self.setMinimumWidth(900)
        self.setMinimumHeight(450)

        self.close_shortcut = QtGui.QShortcut(QtGui.QKeySequence('Ctrl+W'), self)
        self.close_shortcut.activated.connect(self.close)

    def load_task(self,new_task):
        self.variable_generator_table.task_changed(new_task)

    def change_layout(self):
        self.setLayout(self.otherlayout)
    
    def closeEvent(self, event):
        self.deleteLater()
    
class Row_widgets():
    def __init__(self,parent,var_name = None, row_data = None):
        self.parent = parent
        #buttons
        self.up_button = QtGui.QPushButton('⬆️')
        self.down_button = QtGui.QPushButton('⬇️')
        self.remove_button = QtGui.QPushButton('remove')
        self.remove_button.setIcon(QtGui.QIcon("gui/icons/remove.svg"))
        # combo boxes
        self.variable_cbox = QtGui.QComboBox()
        self.variable_cbox.activated.connect(self.parent.update_available)
        self.variable_cbox.addItems(['     select variable     ']+self.parent.available_variables)
        self.input_type_combo = QtGui.QComboBox()
        self.input_type_combo.activated.connect(self.parent.update_available)
        self.input_type_combo.addItems(['line edit','checkbox','spinbox','slider'])
        # line edits
        self.display_name = QtGui.QLineEdit()
        self.spin_min = QtGui.QLineEdit()
        self.spin_min.setAlignment(QtCore.Qt.AlignCenter)
        self.spin_max = QtGui.QLineEdit()
        self.spin_max.setAlignment(QtCore.Qt.AlignCenter)
        self.spin_step = QtGui.QLineEdit()
        self.spin_step.setAlignment(QtCore.Qt.AlignCenter)
        self.suffix = QtGui.QLineEdit()
        self.suffix.setAlignment(QtCore.Qt.AlignCenter)
        self.hint = QtGui.QLineEdit()
        self.hint.setAlignment(QtCore.Qt.AlignCenter)
        
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
        if var_name:
            self.load_vals_from_dict(var_name,row_data)

    def copy_vals_from_row(self,row_index):
            var_name = str(self.parent.cellWidget(row_index, 2).currentText())
            self.variable_cbox.addItems([var_name])
            cbox_set_item(self.variable_cbox,var_name)

            self.display_name.setText(str(self.parent.cellWidget(row_index, 3).text()))
            cbox_set_item(self.input_type_combo,str(self.parent.cellWidget(row_index, 4).currentText()))

            self.spin_min.setText(str(self.parent.cellWidget(row_index, 5).text()))
            self.spin_max.setText(str(self.parent.cellWidget(row_index, 6).text()))
            self.spin_step.setText(str(self.parent.cellWidget(row_index, 7).text()))
            self.suffix.setText(str(self.parent.cellWidget(row_index, 8).text()))
            self.hint.setText(str(self.parent.cellWidget(row_index, 9).text()))
    
    def load_vals_from_dict(self,var_name,row_data):
        self.variable_cbox.addItems([var_name])
        cbox_set_item(self.variable_cbox,var_name)

        self.display_name.setText(row_data['label'])
        cbox_set_item(self.input_type_combo,row_data['widget'])
        self.spin_min.setText(str(row_data['min']))
        self.spin_max.setText(str(row_data['max']))
        self.spin_step.setText(str(row_data['step']))
        self.suffix.setText(row_data['suffix'])
        self.hint.setText(row_data['hint'])

    def put_into_table(self,row_index):
        for column,widget in enumerate(self.column_order):
            self.parent.setCellWidget(row_index, column, widget)
            
class GUI_VariablesTable(QtGui.QTableWidget):
    def __init__(self, parent=None):
        super(QtGui.QTableWidget, self).__init__(1,11, parent=parent)
        self.parent = parent
        self.setHorizontalHeaderLabels(['','','Variable', 'Label', 'Input type','Min','Max','Step','Suffix','Hint',''])
        self.verticalHeader().setVisible(False)
        self.setColumnWidth(0, 30)
        self.setColumnWidth(1, 30)
        self.setColumnWidth(2, 150)
        self.setColumnWidth(3, 175)
        self.setColumnWidth(4, 100)
        self.setColumnWidth(5, 40)
        self.setColumnWidth(6, 40)
        self.setColumnWidth(7, 40)
        self.setColumnWidth(8, 50)

        self.n_variables = 0
        self.variable_names = []
        self.available_variables = []
        self.assigned = {v_name:[] for v_name in self.variable_names} # Which subjects have values assigned for each variable.
        self.add_variable()

    def add_variable(self, varname = None, row_dict= None):
        # populate row with widgets
        new_widgets = Row_widgets(self,varname, row_dict)

        new_widgets.put_into_table(row_index=self.n_variables)

        # connect buttons to functions
        self.connect_buttons(self.n_variables)

        # insert another row witha an "add" button
        self.insertRow(self.n_variables+1)
        add_button = QtGui.QPushButton('   add   ')
        add_button.setIcon(QtGui.QIcon("gui/icons/add.svg"))
        add_button.clicked.connect(self.add_variable)
        self.setCellWidget(self.n_variables+1,10, add_button)

        self.n_variables += 1
        self.update_available()
        null_resize(self)

    def remove_variable(self, variable_n):
        self.removeRow(variable_n)
        self.n_variables -= 1
        self.update_available()
        null_resize(self)
    
    def swap_with_above(self, row):
        if self.n_variables > row > 0:
            new_widgets = Row_widgets(self)
            new_widgets.copy_vals_from_row(row)
            self.removeRow(row) # delete old row
            above_row = row -1
            self.insertRow(above_row) # insert new row
            new_widgets.put_into_table(row_index=above_row) # populate new row with widgets
            self.connect_buttons(above_row) # connect new buttons to functions
            self.reconnect_buttons(row) # disconnect swapped row buttons and reconnect to its new row index
            self.update_available()
            null_resize(self)

    def swap_with_below(self, row):
        self.swap_with_above(row+1)

    def connect_buttons(self,row):
        ind = QtCore.QPersistentModelIndex(self.model().index(row, 2))
        self.cellWidget(row,0).clicked.connect(lambda :self.swap_with_above(ind.row())) # up arrow connection
        self.cellWidget(row,1).clicked.connect(lambda :self.swap_with_below(ind.row())) # down arrow connection
        self.cellWidget(row,10).clicked.connect(lambda :self.remove_variable(ind.row())) # remove button connection

    def reconnect_buttons(self,row):
        ind = QtCore.QPersistentModelIndex(self.model().index(row, 2))
        self.cellWidget(row,0).clicked.disconnect() # up arrow
        self.cellWidget(row,0).clicked.connect(lambda : self.swap_with_above(ind.row()))
        self.cellWidget(row,1).clicked.disconnect() # down arrow
        self.cellWidget(row,1).clicked.connect(lambda :self.swap_with_below(ind.row()))
        self.cellWidget(row,10).clicked.disconnect() # remove button
        self.cellWidget(row,10).clicked.connect(lambda :self.remove_variable(ind.row()))

    def update_available(self, i=None):
        # enable/disable cells depending on input_type type
        for v in range(self.n_variables):
            v_name = self.cellWidget(v,2).currentText()
            input_type = self.cellWidget(v,4).currentText()
            if v_name == '     select variable     ':
                for i in (3,5,6,7,8,9): # disable inputs until a variable as been selected
                    self.cellWidget(v,i).setEnabled(False)
                    self.cellWidget(v,i).setStyleSheet("background: #dcdcdc;")
            else:
                self.cellWidget(v,3).setStyleSheet("background: #ffffff;")
                self.cellWidget(v,9).setStyleSheet("background: #ffffff;")
                self.cellWidget(v,9).setEnabled(True)
                if self.cellWidget(v,3).text() == "":
                    self.cellWidget(v,3).setText(v_name.replace('_',' '))
                self.cellWidget(v,3).setEnabled(True)
                self.cellWidget(v,4).setEnabled(True)
                self.cellWidget(v,8).setEnabled(True)
                if input_type == 'spinbox' or input_type == 'slider':
                    for i in (5,6,7,8):
                        self.cellWidget(v,i).setEnabled(True)
                        self.cellWidget(v,i).setStyleSheet("background: #ffffff;")
                else:
                    for i in (5,6,7,8): 
                        self.cellWidget(v,i).setEnabled(False)
                        self.cellWidget(v,i).setText('')
                        self.cellWidget(v,i).setStyleSheet("background: #dcdcdc;")
                    
        # Update the variables available:
        fully_asigned_variables = []
        for row in range(self.n_variables):
            assigned_var = self.cellWidget(row,2).currentText()
            if assigned_var != '     select variable     ':
                fully_asigned_variables.append(assigned_var)
        self.available_variables = sorted(list( set(self.variable_names) - set(fully_asigned_variables)), key=str.lower)

        # Update the available options in the variable comboboxes.
        for v in range(self.n_variables):  
            v_name = self.cellWidget(v,2).currentText()
            cbox_update_options(self.cellWidget(v,2), self.available_variables)

    def task_changed(self, task):
        '''Remove variables that are not defined in the new task.'''
        pattern = "[\n\r]v\.(?P<vname>\w+)\s*\="
        try:
            with open(os.path.join(dirs['tasks'], task+'.py'), "r") as file:
                file_content = file.read()
        except FileNotFoundError:
            return
        # get list of variables. ignore private variables and the variable_gui variable
        self.variable_names = list(set([v_name for v_name in 
            re.findall(pattern, file_content) if not v_name[-3:] == '___' and v_name != 'variable_gui']))
        # Remove variables that are not in new task.
        for i in reversed(range(self.n_variables)):
            if not self.cellWidget(i,2).currentText() in self.variable_names:
                self.removeRow(i)
                self.n_variables -= 1
        null_resize(self)
        self.update_available()

    def set_dialog_name(self,new_dialog_name):
        self.new_dialog_name = new_dialog_name

    def save_gui_data(self):
        gui_dictionary = {}
        ordered_elements = []
        for row in range(self.n_variables):  
            element_specs = {}
            varname = self.cellWidget(row,2).currentText()
            if varname != '     select variable     ':
                ordered_elements.append(varname) 
                element_specs['label'] = self.cellWidget(row,3).text()
                element_specs['widget'] = self.cellWidget(row,4).currentText()
                element_specs['min'] = ""
                element_specs['max'] = ""
                element_specs['step'] = ""
                element_specs['suffix'] = ""
                element_specs['hint'] = self.cellWidget(row,9).text()

                if element_specs['widget'] == 'spinbox' or element_specs['widget'] == 'slider':
                    try: # store the value as an integer or float. if the string is empty or not a number, an error message will be shown 
                        value = self.cellWidget(row,5).text()
                        element_specs['min'] =  float(value) if value.find('.')>-1 else int(value)
                        value = self.cellWidget(row,6).text()
                        element_specs['max'] = float(value) if value.find('.')>-1 else int(value)
                        value = self.cellWidget(row,7).text()
                        element_specs['step'] = float(value) if value.find('.')>-1 else int(value)
                    except:
                        msg = QtGui.QMessageBox()
                        msg.setText("Numbers for min, max, and step are required for spinboxes and sliders")
                        msg.exec()
                        return
                    element_specs['suffix'] = self.cellWidget(row,8).text()

                gui_dictionary[varname] = element_specs
        gui_dictionary['ordered_elements'] = ordered_elements # after Python 3.6, dictionaries became ordered, but to be backwards compatible we add ordering here
        gui_dictionary['title'] = self.new_dialog_name

        # self.create_custom_gui_file(gui_dictionary)
        with open(F'gui/user_variable_GUIs/{self.new_dialog_name}.json', 'w') as generated_data_file:
            json.dump(gui_dictionary,generated_data_file,indent=4)
        self.parent.accept()
        self.deleteLater()
    
    def load_gui_data(self,gui_dict):
        for row,element in enumerate(gui_dict['ordered_elements']):
            self.add_variable(element,gui_dict[element])
    

class Custom_var_not_found_dialog(QtGui.QDialog):
    def __init__(self,missing_file,parent):
        super(QtGui.QDialog, self).__init__(parent)
        self.setWindowTitle('Custom Variable GUI not found')

        message = QtGui.QLabel(F"The custom variable GUI <b>\"{missing_file}\"</b> was not found.<br><br>Would you like to generate a new custom variable GUI, or continue with the default variable GUI?")
        continue_button = QtGui.QPushButton('Continue with default variable GUI')
        generate_button = QtGui.QPushButton('Create new custom variable GUI')
        continue_button.setDefault(True)
        continue_button.setFocus()
        self.layout = QtGui.QGridLayout(self)
        self.layout.addWidget(message,0,0,1,2)
        self.layout.addWidget(continue_button,1,0)
        self.layout.addWidget(generate_button,1,1)

        generate_button.clicked.connect(self.accept)
        continue_button.clicked.connect(self.close)

        self.setFixedSize(self.sizeHint())