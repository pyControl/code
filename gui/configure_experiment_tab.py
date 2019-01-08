import os
import re
import json
from pyqtgraph.Qt import QtGui, QtCore

from config.paths import data_dir, tasks_dir, experiments_dir
from gui.utility import TableCheckbox, cbox_update_options, cbox_set_item, null_resize

# --------------------------------------------------------------------------------
# Experiments_tab
# --------------------------------------------------------------------------------

class Configure_experiment_tab(QtGui.QWidget):

    def __init__(self, parent=None):
        super(QtGui.QWidget, self).__init__(parent)

        # Variables
        self.GUI_main = self.parent()
        self.custom_dir = False # True if data_dir field has been manually edited.

        # Experiment Groupbox
        self.experiment_groupbox = QtGui.QGroupBox('Experiment')
        self.expbox_Vlayout = QtGui.QVBoxLayout(self.experiment_groupbox)
        self.expbox_Hlayout_1 = QtGui.QHBoxLayout()
        self.expbox_Hlayout_2 = QtGui.QHBoxLayout()
        self.expbox_Hlayout_3 = QtGui.QHBoxLayout()
        self.expbox_Vlayout.addLayout(self.expbox_Hlayout_1)
        self.expbox_Vlayout.addLayout(self.expbox_Hlayout_2)
        self.expbox_Vlayout.addLayout(self.expbox_Hlayout_3)

        self.experiment_select = QtGui.QComboBox()

        self.run_button = QtGui.QPushButton('Run')
        self.new_button = QtGui.QPushButton('New')
        self.delete_button = QtGui.QPushButton('Delete')
        self.save_button = QtGui.QPushButton('Save')
        self.name_label = QtGui.QLabel('Experiment name:')
        self.name_text = QtGui.QLineEdit()
        self.task_label = QtGui.QLabel('Task:')
        self.task_select = QtGui.QComboBox()
        self.task_select.setFixedWidth(150)
        self.hardware_test_label = QtGui.QLabel('Hardware test:')
        self.hardware_test_select = QtGui.QComboBox()
        self.hardware_test_select.setFixedWidth(150)
        self.data_dir_label = QtGui.QLabel('Data dir:')
        self.data_dir_text = QtGui.QLineEdit(data_dir)
        self.data_dir_button = QtGui.QPushButton('...')
        self.data_dir_button.setFixedWidth(30)

        self.expbox_Hlayout_1.addWidget(self.experiment_select)
        self.expbox_Hlayout_1.setStretchFactor(self.experiment_select, 2)
        self.expbox_Hlayout_1.addWidget(self.new_button)
        self.expbox_Hlayout_1.addWidget(self.delete_button)
        self.expbox_Hlayout_1.addWidget(self.save_button)
        self.expbox_Hlayout_1.addWidget(self.run_button)
        self.expbox_Hlayout_2.addWidget(self.name_label)
        self.expbox_Hlayout_2.addWidget(self.name_text)
        self.expbox_Hlayout_2.addWidget(self.task_label)
        self.expbox_Hlayout_2.addWidget(self.task_select)
        self.expbox_Hlayout_2.addWidget(self.hardware_test_label)
        self.expbox_Hlayout_2.addWidget(self.hardware_test_select)
        self.expbox_Hlayout_3.addWidget(self.data_dir_label)
        self.expbox_Hlayout_3.addWidget(self.data_dir_text)
        self.expbox_Hlayout_3.addWidget(self.data_dir_button)

        # Subjects Groupbox
        self.subjects_groupbox = QtGui.QGroupBox('Subjects')
        self.subjectsbox_layout = QtGui.QHBoxLayout(self.subjects_groupbox)
        self.subjects_table = SubjectsTable(self)
        self.subjectsbox_layout.addWidget(self.subjects_table)

        # Variables Groupbox
        self.variables_groupbox = QtGui.QGroupBox('Variables')
        self.variablesbox_layout = QtGui.QHBoxLayout(self.variables_groupbox)
        self.variables_table = VariablesTable(self)
        self.variablesbox_layout.addWidget(self.variables_table)

        # Initialise widgets
        self.experiment_select.addItems(['select experiment'])
        self.task_select.addItems(['select task'])
        self.hardware_test_select.addItems(['none'])

        # Connect signals.
        self.name_text.textChanged.connect(self.name_edited)
        self.data_dir_text.textEdited.connect(lambda: setattr(self, 'custom_dir', True))
        self.data_dir_button.clicked.connect(self.select_data_dir)
        self.experiment_select.activated[str].connect(self.experiment_changed)
        self.task_select.currentIndexChanged[str].connect(self.task_changed)
        self.new_button.clicked.connect(self.new_experiment)
        self.delete_button.clicked.connect(self.delete_experiment)
        self.save_button.clicked.connect(self.save_experiment)
        self.run_button.clicked.connect(self.run_experiment)

        # Main layout
        self.vertical_layout = QtGui.QVBoxLayout(self)
        self.vertical_layout.addWidget(self.experiment_groupbox)
        self.vertical_layout.addWidget(self.subjects_groupbox)
        self.vertical_layout.addWidget(self.variables_groupbox)

    def name_edited(self):
        if not self.custom_dir:
            self.data_dir_text.setText(os.path.join(data_dir, self.name_text.text()))

    def select_data_dir(self):
        self.data_dir_text.setText(
            QtGui.QFileDialog.getExistingDirectory(self, 'Select data folder', data_dir))
        self.custom_dir = True

    def task_changed(self, task_name):
        if task_name in self.GUI_main.available_tasks:
            self.variables_table.task_changed(task_name)

    def experiment_changed(self, experiment_name):
        # if not self.save_dialog(): return
        if experiment_name in self.GUI_main.available_experiments:
            self.load_experiment(experiment_name)

    def refresh(self):
        '''Called periodically when not running to update available task, ports, experiments.'''
        if self.GUI_main.available_tasks_changed:
            cbox_update_options(self.task_select, self.GUI_main.available_tasks)
            cbox_update_options(self.hardware_test_select, ['none'] + self.GUI_main.available_tasks)
            self.GUI_main.available_tasks_changed = False
        if self.GUI_main.available_experiments_changed:
            cbox_update_options(self.experiment_select, self.GUI_main.available_experiments)
            self.GUI_main.available_experiments_changed = False
        if self.GUI_main.available_ports_changed:
            self.subjects_table.all_setups = set(self.GUI_main.available_ports)
            self.subjects_table.update_available_setups()

    def experiment_dict(self):
        '''Return the current state of the experiments tab as a dictionary.'''
        return {'name': self.name_text.text(),
                'task': str(self.task_select.currentText()),
                'hardware_test': str(self.hardware_test_select.currentText()),
                'data_dir': self.data_dir_text.text(),
                'subjects': self.subjects_table.subjects_dict(),
                'variables': self.variables_table.variables_list()}

    def new_experiment(self, dialog=True):
        '''Clear experiment configuration.'''
        if dialog and not self.save_dialog(): return
        self.name_text.setText('')
        self.data_dir_text.setText(data_dir)
        self.custom_dir = False
        self.subjects_table.reset()
        self.variables_table.reset()
        cbox_set_item(self.experiment_select, 'select experiment', insert=True)
        cbox_set_item(self.task_select, 'select task', insert=True)

    def delete_experiment(self):
        '''Delete an experiment file after dialog to confirm deletion.'''
        exp_path = os.path.join(experiments_dir, self.name_text.text()+'.pcx')
        if os.path.exists(exp_path):
            reply = QtGui.QMessageBox.question(self, 'Delete experiment', 
                "Delete experiment '{}'".format(self.name_text.text()),
                    QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel)
            if reply == QtGui.QMessageBox.Yes:
                self.new_experiment(dialog=False)
                os.remove(exp_path)

    def save_experiment(self):
        '''Store the current state of the experiment tab as a JSON object
        saved in the experiments folder as .pcx file.'''
        experiment = self.experiment_dict()
        exp_path = os.path.join(experiments_dir, self.name_text.text()+'.pcx')
        with open(exp_path,'w') as exp_file:
            exp_file.write(json.dumps(experiment, sort_keys=True, indent=4))
        cbox_set_item(self.experiment_select, experiment['name'], insert=True)

    def load_experiment(self, experiment_name):
        '''Load experiment  .pcx file and set fields of experiment tab.'''
        exp_path = os.path.join(experiments_dir, experiment_name +'.pcx')
        with open(exp_path,'r') as exp_file:
            experiment = json.loads(exp_file.read())
        self.name_text.setText(experiment['name'])
        cbox_set_item(self.task_select, experiment['task'])
        cbox_set_item(self.hardware_test_select, experiment['hardware_test'])
        self.variables_table.task_changed(experiment['task'])
        self.data_dir_text.setText(experiment['data_dir'])
        self.subjects_table.set_from_dict(experiment['subjects'])
        self.variables_table.set_from_list(experiment['variables'])

    def run_experiment(self):
        '''Run an experiment. Prompts user to save experiment if it is new or has been edited.'''
        if not self.save_dialog(): return
        self.GUI_main.run_experiment_tab.setup_experiment(self.experiment_dict())

    def save_dialog(self):
        '''Dialog to save experiment if it has been edited.  Returns False if
        cancel is selected, True otherwise.'''        
        experiment = self.experiment_dict()
        exp_path = os.path.join(experiments_dir, self.name_text.text()+'.pcx')
        dialog_text = None
        if not os.path.exists(exp_path):
            dialog_text = 'Experiment not saved, save experiment?'
        else:
            with open(exp_path,'r') as exp_file:
                saved_experiment = json.loads(exp_file.read())
            if experiment != saved_experiment:
                dialog_text = 'Experiment edited, save experiment?'
        if dialog_text:
            reply = QtGui.QMessageBox.question(self, 'Save experiment', dialog_text,
                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No | QtGui.QMessageBox.Cancel)
            if reply == QtGui.QMessageBox.Yes:
                self.save_experiment()
            elif reply == QtGui.QMessageBox.Cancel:
                return False
        return True

# ---------------------------------------------------------------------------------

class SubjectsTable(QtGui.QTableWidget):
    '''Table for specifying the setups and subjects used in experiment. '''

    def __init__(self, parent=None):
        super(QtGui.QTableWidget, self).__init__(1,3, parent=parent)
        self.setHorizontalHeaderLabels(['Setup', 'Subject', ''])
        self.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.Stretch)
        self.horizontalHeader().setResizeMode(1, QtGui.QHeaderView.Stretch)
        self.horizontalHeader().setResizeMode(2, QtGui.QHeaderView.ResizeToContents)
        self.verticalHeader().setVisible(False)
        self.cellChanged.connect(self.cell_changed)
        self.all_setups = set([])
        self.available_setups = []
        self.subjects = []
        self.n_subjects = 0
        add_button = QtGui.QPushButton('add')
        add_button.clicked.connect(self.add_subject)  
        self.setCellWidget(0,2, add_button)

    def reset(self):
        '''Clear all rows of table.'''
        for i in reversed(range(self.n_subjects)):
            self.removeRow(i)
        self.available_setups = sorted(list(self.all_setups))
        self.subjects = []
        self.n_subjects = 0

    def cell_changed(self, row, column):
        if column == 1:
            self.update_subjects()

    def add_subject(self, setup=None, subject=None):
        '''Add row to table allowing extra subject to be specified.'''
        setup_cbox = QtGui.QComboBox()
        setup_cbox.setEditable(True)
        setup_cbox.addItems(self.available_setups)
        setup_cbox.activated.connect(self.update_available_setups)
        remove_button = QtGui.QPushButton('remove')
        ind = QtCore.QPersistentModelIndex(self.model().index(self.n_subjects, 2))
        remove_button.clicked.connect(lambda :self.remove_subject(ind.row()))
        add_button = QtGui.QPushButton('add')
        add_button.clicked.connect(self.add_subject)        
        self.setCellWidget(self.n_subjects,0, setup_cbox)
        self.setCellWidget(self.n_subjects,2, remove_button)
        self.insertRow(self.n_subjects+1)
        self.setCellWidget(self.n_subjects+1,2, add_button)
        if setup:
            cbox_set_item(setup_cbox, setup)
        if subject:
            subject_item = QtGui.QTableWidgetItem()
            subject_item.setText(subject)
            self.setItem(self.n_subjects, 1, subject_item)
        self.n_subjects += 1
        self.update_available_setups()
        null_resize(self)

    def remove_subject(self, subject_n):
        '''Remove specified row from table'''
        if self.item(subject_n, 1): 
            s_name = self.item(subject_n, 1).text()
            self.parent().parent().variables_table.remove_subject(s_name)
        self.removeRow(subject_n)
        self.n_subjects -= 1
        self.update_available_setups()
        self.update_subjects()

    def update_available_setups(self, i=None):
        '''Update which setups are available for selection in dropdown menus.'''
        selected_setups = set([str(self.cellWidget(s,0).currentText())
                               for s in range(self.n_subjects)])
        self.available_setups = sorted(list(self.all_setups - selected_setups))
        for s in range(self.n_subjects):
            cbox_update_options(self.cellWidget(s,0), self.available_setups)

    def update_subjects(self):
        '''Update the subjects list'''
        self.subjects = [str(self.item(s, 1).text()) 
                         for s in range(self.n_subjects) if self.item(s, 1)]

    def subjects_dict(self):
        '''Return setups and subjects as a dictionary {setup:subject}'''
        return {str(self.cellWidget(s,0).currentText()): 
                str(self.item(s, 1).text()) if self.item(s, 1) else ''
                for s in range(self.n_subjects)}

    def set_from_dict(self, subjects_dict):
        '''Fill table with subjects and setups from subjects_dict'''
        self.reset()
        for s, setup in enumerate(sorted(subjects_dict.keys())):
            self.add_subject(setup, subjects_dict[setup])
        self.update_available_setups()
        self.update_subjects()

# -------------------------------------------------------------------------------

class VariablesTable(QtGui.QTableWidget):
    '''Class for specifying what variables are set to non-default values.'''

    def __init__(self, parent=None):
        super(QtGui.QTableWidget, self).__init__(1,6, parent=parent)
        self.subjects_table = self.parent().subjects_table
        self.setHorizontalHeaderLabels(['Variable', 'Subject', 'Value', 'Persistent','Summary',''])
        self.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.Stretch)
        self.horizontalHeader().setResizeMode(2, QtGui.QHeaderView.Stretch)
        self.horizontalHeader().setResizeMode(5, QtGui.QHeaderView.ResizeToContents)
        self.verticalHeader().setVisible(False)
        add_button = QtGui.QPushButton('add')
        add_button.clicked.connect(self.add_variable)
        self.setCellWidget(0,5, add_button)
        self.n_variables = 0
        self.variable_names = []
        self.assigned = {v_name:[] for v_name in self.variable_names} # Which subjects have values assigned for each variable.

    def reset(self):
        '''Clear all rows of table.'''
        for i in reversed(range(self.n_variables)):
            self.removeRow(i)
        self.n_variables = 0
        self.assigned = {v_name:[] for v_name in self.variable_names} 

    def add_variable(self, var_dict=None):
        '''Add a row to the variables table.'''
        variable_cbox = QtGui.QComboBox()
        variable_cbox.activated.connect(self.update_available)
        subject_cbox = QtGui.QComboBox()
        subject_cbox.activated.connect(self.update_available)
        persistent = TableCheckbox()
        summary    = TableCheckbox()
        remove_button = QtGui.QPushButton('remove')
        ind = QtCore.QPersistentModelIndex(self.model().index(self.n_variables, 2))
        remove_button.clicked.connect(lambda :self.remove_variable(ind.row()))
        add_button = QtGui.QPushButton('add')
        add_button.clicked.connect(self.add_variable)
        self.insertRow(self.n_variables+1)
        self.setCellWidget(self.n_variables  ,0, variable_cbox)
        self.setCellWidget(self.n_variables  ,1, subject_cbox)
        self.setCellWidget(self.n_variables  ,3, persistent)
        self.setCellWidget(self.n_variables  ,4, summary)
        self.setCellWidget(self.n_variables  ,5, remove_button)
        self.setCellWidget(self.n_variables+1,5, add_button)
        if var_dict: # Set cell values from provided dictionary.
            variable_cbox.addItems([var_dict['name']])
            subject_cbox.addItems([var_dict['subject']])
            value_item = QtGui.QTableWidgetItem()
            value_item.setText(var_dict['value'])
            self.setItem(self.n_variables, 2, value_item)
            persistent.setChecked(var_dict['persistent'])
            summary.setChecked(var_dict['summary'])
        else:
            variable_cbox.addItems(['select variable']+self.available_variables)
        self.n_variables += 1
        null_resize(self)


    def remove_variable(self, variable_n):
        self.removeRow(variable_n)
        self.n_variables -= 1
        self.update_available()

    def remove_subject(self, subject):
        for i in reversed(range(self.n_variables)):
            if self.cellWidget(i,1).currentText() == subject:
                self.removeRow(i)
                self.n_variables -= 1
        self.update_available()

    def update_available(self, i=None):
        # Find out what variable-subject combinations already assigned.
        self.assigned = {v_name:[] for v_name in self.variable_names}
        for v in range(self.n_variables):
            v_name = self.cellWidget(v,0).currentText()
            s_name = self.cellWidget(v,1).currentText()
            if v_name != 'select variable':
                self.assigned[v_name].append(s_name)
        # Update the variables available:
        self.available_variables = sorted(list(set(self.variable_names) - 
            set([v_n for v_n in self.assigned.keys() if 
                'all' in self.assigned[v_n] or
                set(self.assigned[v_n]) == set(self.subjects_table.subjects)])), key=str.lower)
        for v in range(self.n_variables):  
            v_name = str(self.cellWidget(v,0).currentText())
            s_name = self.cellWidget(v,1).currentText()
            # Update subjects combo box options.
            if v_name != 'select variable':
                if len(self.assigned[v_name]) <= 1:
                    available_subjects = ['all']+ sorted(self.subjects_table.subjects)
                else:
                    available_subjects = sorted(list(set(self.subjects_table.subjects)-
                                                     set(self.assigned[v_name])))
                # If variable has no subjects assigned, set subjects to 'all'.
                if self.assigned[v_name] == ['']:
                    self.cellWidget(v,1).addItems(['all'])
                    self.assigned[v_name] = ['all']
                    self.available_variables.remove(v_name)
                cbox_update_options(self.cellWidget(v,1), available_subjects)
            # Update variable combo box options.
            cbox_update_options(self.cellWidget(v,0), self.available_variables)  

    def task_changed(self, task):
        '''Remove variables that are not defined in the new task.'''
        pattern = "v\.(?P<vname>\w+)\s*\="
        try:
            with open(os.path.join(tasks_dir, task+'.py'), "r") as file:
                file_content = file.read()
        except FileNotFoundError:
            return
        self.variable_names = []
        for v_name in re.findall(pattern, file_content):
            if not v_name in [var_name for var_name in self.variable_names]:
                self.variable_names.append(v_name)
        self.available_variables = sorted(self.variable_names, key=str.lower)
        # Remove variables that are not in new task.
        for i in reversed(range(self.n_variables)):
            if not self.cellWidget(i,0).currentText() in self.available_variables:
                self.removeRow(i)
                self.n_variables -= 1
        self.update_available()

    def variables_list(self):
        '''Return the variables table contents as a list of dictionaries.'''
        return [{'name'  : str(self.cellWidget(v,0).currentText()),
                 'subject'   : str(self.cellWidget(v,1).currentText()),
                 'value'     : str(self.item(v, 2).text()) if self.item(v,2) else '',
                 'persistent': self.cellWidget(v,3).isChecked(),
                 'summary'   : self.cellWidget(v,4).isChecked()}
                 for v in range(self.n_variables)]

    def set_from_list(self, variables_list):
        '''Fill the variables table with values from variables_list'''
        self.reset()
        #self.update_available() # To update available subjects.
        for var_dict in variables_list:
            self.add_variable(var_dict)
        self.update_available()