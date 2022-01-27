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

# GUI editor dialog. ---------------------------------------------------------
class GUI_editor(QtGui.QDialog):
    def __init__(self, parent,task,gui_name,data_to_load=None):
        super(QtGui.QDialog, self).__init__(parent)
        self.gui_name = gui_name
        self.available_vars = []
        self.get_vars(task)
        self.tables = []

        self.setWindowTitle('Custom GUI Editor')
        self.layout = QtGui.QGridLayout(self)

        # main widgets
        self.tabs = QtGui.QTabWidget()
        self.add_tab_btn = QtGui.QPushButton('Add tab')
        self.add_tab_btn.setIcon(QtGui.QIcon("gui/icons/add.svg"))
        self.add_tab_btn.clicked.connect(self.add_tab)
        self.del_tab_btn = QtGui.QPushButton('Remove tab')
        self.del_tab_btn.setIcon(QtGui.QIcon("gui/icons/remove.svg"))
        self.del_tab_btn.clicked.connect(self.remove_tab)
        self.tab_title_lbl = QtGui.QLabel('Tab title:')
        self.tab_title_edit = QtGui.QLineEdit()
        self.tab_title_edit.setMinimumWidth(200)
        self.tab_title_btn = QtGui.QPushButton('set tab title')
        self.tab_title_btn.clicked.connect(self.set_tab_title)
        self.generate_btn = QtGui.QPushButton('Save GUI')
        self.generate_btn.setIcon(QtGui.QIcon("gui/icons/save.svg"))
        self.generate_btn.clicked.connect(self.save_gui_data)
        if data_to_load:
            self.load_gui_data(data_to_load)
        else:
            self.add_tab()
        self.tabs.currentChanged.connect(self.refresh_variable_options)
        self.refresh_variable_options()

        # layout
        self.layout.addWidget(self.add_tab_btn,0,0)
        self.layout.addWidget(self.del_tab_btn,0,1)
        self.layout.addWidget(self.tab_title_lbl,0,2)
        self.layout.addWidget(self.tab_title_edit,0,3)
        self.layout.addWidget(self.tab_title_btn,0,4)
        self.layout.addWidget(self.generate_btn,0,6)
        self.layout.addWidget(self.tabs,1,0,1,7)
        self.layout.setColumnStretch(5,1)

        self.setMinimumWidth(910)
        self.setMinimumHeight(450)

        self.close_shortcut = QtGui.QShortcut(QtGui.QKeySequence('Ctrl+W'), self)
        self.close_shortcut.activated.connect(self.close)

    def load_gui_data(self,gui_data):
        for tab_name in gui_data['ordered_tabs']:
            tab_data = gui_data[tab_name]
            self.add_tab(tab_data,tab_name)

    def save_gui_data(self):
        gui_dict = {}
        ordered_tabs = []
        for index,table in enumerate(self.tables):
            tab_title = self.tabs.tabText(index)
            ordered_tabs.append(tab_title) 
            gui_dict[tab_title] = table.save_gui_data()

        gui_dict['ordered_tabs'] = ordered_tabs
        with open(F'gui/user_variable_GUIs/{self.gui_name}.json', 'w') as generated_data_file:
            json.dump(gui_dict,generated_data_file,indent=4)
        self.accept()
        self.deleteLater()
    
    def refresh_variable_options(self):
        fully_asigned_variables = []
        for table in self.tables:
            # determine which variables are already being used
            for row in range(table.n_variables):
                assigned_var = table.cellWidget(row,2).currentText()
                if assigned_var != '     select variable     ':
                    fully_asigned_variables.append(assigned_var)
            self.available_vars = sorted(list( self.variable_names - set(fully_asigned_variables)), key=str.lower)

        for table in self.tables: # Update the available options in the variable comboboxes
            for row in range(table.n_variables):  
                cbox_update_options(table.cellWidget(row,2), self.available_vars)
        
        index = self.tabs.currentIndex()
        if index> -1:
            self.tab_title_edit.setText(self.tabs.tabText(index))

    def get_vars(self,task):
        '''Remove variables that are not defined in the new task.'''
        pattern = "[\n\r]v\.(?P<vname>\w+)\s*\="
        try:
            with open(os.path.join(dirs['tasks'], task+'.py'), "r") as file:
                file_content = file.read()
        except FileNotFoundError:
            return
        # get list of variables. ignore private variables and the variable_gui variable
        self.variable_names = set([v_name for v_name in re.findall(pattern, file_content) if not v_name[-3:] == '___' and v_name != 'variable_gui'])

    def add_tab(self,data = None, name = None):
        new_table = Variables_table(self,data)
        if name:
            tab_title = name
        else:
            tab_title = f"tab-{len(self.tables)+1}"
        self.tables.append(new_table)
        self.tabs.addTab(new_table,tab_title)
        if len(self.tables)<2:
            self.del_tab_btn.setEnabled(False)
        else:
            self.del_tab_btn.setEnabled(True)
    
    def remove_tab(self):
        if len(self.tables)>1:
            index = self.tabs.currentIndex()
            self.tabs.removeTab(index)
            del self.tables[index]
            if len(self.tables)<2:
                self.del_tab_btn.setEnabled(False)
            else:
                self.del_tab_btn.setEnabled(True)
            self.refresh_variable_options()

    def set_tab_title(self):
        index = self.tabs.currentIndex()
        self.tabs.setTabText(index,self.tab_title_edit.text())

    def closeEvent(self, event):
        self.deleteLater()
    
class Variable_row():
    def __init__(self,parent,var_name = None, row_data = None):
        self.parent = parent
        #buttons
        self.up_button = QtGui.QPushButton('⬆️')
        self.down_button = QtGui.QPushButton('⬇️')
        self.remove_button = QtGui.QPushButton('remove')
        self.remove_button.setIcon(QtGui.QIcon("gui/icons/remove.svg"))
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
        # combo boxes
        self.variable_cbox = QtGui.QComboBox()
        self.variable_cbox.activated.connect(lambda:self.parent.clear_label(self.display_name.text()))
        self.variable_cbox.addItems(['     select variable     ']+self.parent.parent.available_vars)
        self.input_type_combo = QtGui.QComboBox()
        self.input_type_combo.activated.connect(self.parent.update_available)
        self.input_type_combo.addItems(['line edit','checkbox','spinbox','slider'])

        
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
            
class Variables_table(QtGui.QTableWidget):
    def __init__(self, parent=None, data=None):
        super(QtGui.QTableWidget, self).__init__(1,11, parent=parent)
        self.parent = parent
        self.setHorizontalHeaderLabels(['','','Variable', 'Label', 'Input type','Min','Max','Step','Suffix','Hint',''])
        self.verticalHeader().setVisible(False)
        self.setColumnWidth(0, 30)
        self.setColumnWidth(1, 30)
        self.setColumnWidth(2, 150)
        self.setColumnWidth(3, 175)
        self.setColumnWidth(4, 80)
        self.setColumnWidth(5, 40)
        self.setColumnWidth(6, 40)
        self.setColumnWidth(7, 40)
        self.setColumnWidth(8, 40)
        self.setColumnWidth(9, 150)

        self.n_variables = 0
        self.clear_label_flag = None
        if data and data['ordered_inputs']:
            for row,element in enumerate(data['ordered_inputs']):
                self.add_row(element,data[element])
        else:
            self.add_row()

    def add_row(self, varname = None, row_dict= None):
        # populate row with widgets
        new_widgets = Variable_row(self,varname, row_dict)
        new_widgets.put_into_table(row_index=self.n_variables)

        # connect buttons to functions
        self.connect_buttons(self.n_variables)

        # insert another row with an "add" button
        self.insertRow(self.n_variables+1)
        add_button = QtGui.QPushButton('   add   ')
        add_button.setIcon(QtGui.QIcon("gui/icons/add.svg"))
        add_button.clicked.connect(self.add_row)
        self.setCellWidget(self.n_variables+1,10, add_button)

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
            new_widgets = Variable_row(self)
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
        self.cellWidget(row,10).clicked.connect(lambda :self.remove_row(ind.row())) # remove button connection

    def reconnect_buttons(self,row):
        ind = QtCore.QPersistentModelIndex(self.model().index(row, 2))
        self.cellWidget(row,0).clicked.disconnect() # up arrow
        self.cellWidget(row,0).clicked.connect(lambda : self.swap_with_above(ind.row()))
        self.cellWidget(row,1).clicked.disconnect() # down arrow
        self.cellWidget(row,1).clicked.connect(lambda :self.swap_with_below(ind.row()))
        self.cellWidget(row,10).clicked.disconnect() # remove button
        self.cellWidget(row,10).clicked.connect(lambda :self.remove_row(ind.row()))

    def clear_label(self,val):
        self.clear_label_flag = val
        self.update_available()
        
    def update_available(self, i=None):
        # enable/disable cells depending on input_type type
        for row in range(self.n_variables):
            v_name = self.cellWidget(row,2).currentText()
            input_type = self.cellWidget(row,4).currentText()
            if v_name == '     select variable     ':
                for i in (3,5,6,7,8,9): # disable inputs until a variable as been selected
                    self.cellWidget(row,i).setEnabled(False)
                    self.cellWidget(row,i).setStyleSheet("background: #dcdcdc;")
            else:
                self.cellWidget(row,3).setStyleSheet("background: #ffffff;")
                self.cellWidget(row,9).setStyleSheet("background: #ffffff;")
                self.cellWidget(row,9).setEnabled(True)
                if self.cellWidget(row,3).text() == self.clear_label_flag:
                    self.cellWidget(row,3).setText(v_name.replace('_',' '))
                self.cellWidget(row,3).setEnabled(True)
                self.cellWidget(row,4).setEnabled(True)
                self.cellWidget(row,8).setEnabled(True)
                if input_type == 'spinbox' or input_type == 'slider':
                    for i in (5,6,7,8):
                        self.cellWidget(row,i).setEnabled(True)
                        self.cellWidget(row,i).setStyleSheet("background: #ffffff;")
                else:
                    for i in (5,6,7,8): 
                        self.cellWidget(row,i).setEnabled(False)
                        self.cellWidget(row,i).setText('')
                        self.cellWidget(row,i).setStyleSheet("background: #dcdcdc;")
        
        self.parent.refresh_variable_options()
                    
    def save_gui_data(self):
        tab_dictionary = {}
        ordered_inputs = []
        for row in range(self.n_variables):  
            input_specs = {}
            varname = self.cellWidget(row,2).currentText()
            if varname != '     select variable     ':
                ordered_inputs.append(varname) 
                input_specs['label'] = self.cellWidget(row,3).text()
                input_specs['widget'] = self.cellWidget(row,4).currentText()
                input_specs['min'] = ""
                input_specs['max'] = ""
                input_specs['step'] = ""
                input_specs['suffix'] = ""
                input_specs['hint'] = self.cellWidget(row,9).text()

                if input_specs['widget'] == 'spinbox' or input_specs['widget'] == 'slider':
                    try: # store the value as an integer or float. if the string is empty or not a number, an error message will be shown 
                        value = self.cellWidget(row,5).text()
                        input_specs['min'] =  float(value) if value.find('.')>-1 else int(value)
                        value = self.cellWidget(row,6).text()
                        input_specs['max'] = float(value) if value.find('.')>-1 else int(value)
                        value = self.cellWidget(row,7).text()
                        input_specs['step'] = float(value) if value.find('.')>-1 else int(value)
                    except:
                        msg = QtGui.QMessageBox()
                        msg.setText("Numbers for min, max, and step are required for spinboxes and sliders")
                        msg.exec()
                        return
                    input_specs['suffix'] = self.cellWidget(row,8).text()

                tab_dictionary[varname] = input_specs
        tab_dictionary['ordered_inputs'] = ordered_inputs # after Python 3.6, dictionaries became ordered, but to be backwards compatible we add ordering here

        return tab_dictionary

class GUI_not_found(QtGui.QDialog):
    def __init__(self,missing_file,parent):
        super(QtGui.QDialog, self).__init__(parent)
        self.setWindowTitle('Custom variable GUI not found')

        message = QtGui.QLabel(F"The custom variable GUI <b>\"{missing_file}\"</b> was not found.<br><br>")
        continue_button = QtGui.QPushButton('Continue with standard variable GUI')
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