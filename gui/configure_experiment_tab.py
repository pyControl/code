import os
import re
import json
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets

from config.paths import dirs
from gui.dialogs import invalid_run_experiment_dialog, invalid_save_experiment_dialog,unrun_subjects_dialog
from gui.utility import TableCheckbox, cbox_update_options, cbox_set_item, null_resize, variable_constants, init_keyboard_shortcuts,TaskSelectMenu

# --------------------------------------------------------------------------------
# Experiments_tab
# --------------------------------------------------------------------------------

class Configure_experiment_tab(QtGui.QWidget):
    '''The configure experiment tab is used to specify an experiment, i.e. a 
    set of subjects run on a given task on a set of setups.'''

    def __init__(self, parent=None):
        super(QtGui.QWidget, self).__init__(parent)

        # Variables
        self.GUI_main = self.parent()
        self.custom_dir = False    # True if data_dir field has been manually edited.
        self.saved_exp_path = None # Path of last saved/loaded experiment file.
        self.saved_exp_dict = {}   # Dict of last saved/loaded experiment.

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
        self.new_button.setIcon(QtGui.QIcon("gui/icons/add.svg"))
        self.delete_button = QtGui.QPushButton('Delete')
        self.delete_button.setIcon(QtGui.QIcon("gui/icons/delete.svg"))
        self.save_button = QtGui.QPushButton('Save')
        self.save_button.setEnabled(False)
        self.name_label = QtGui.QLabel('Experiment name:')
        self.name_text = QtGui.QLineEdit()
        self.task_label = QtGui.QLabel('Task:')
        self.task_select = TaskSelectMenu('select task')
        self.hardware_test_label = QtGui.QLabel('Hardware test:')
        self.hardware_test_select = TaskSelectMenu('no hardware test',add_default=True)
        self.data_dir_label = QtGui.QLabel('Data dir:')
        self.data_dir_text = QtGui.QLineEdit(dirs['data'])
        self.data_dir_button = QtGui.QPushButton('')
        self.data_dir_button.setIcon(QtGui.QIcon("gui/icons/folder.svg"))
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
        self.subjectsbox_layout = QtGui.QGridLayout(self.subjects_groupbox)
        self.subset_warning_checkbox = QtWidgets.QCheckBox('Warn me if any subjects will not be run')
        self.subset_warning_checkbox.setChecked(True)
        self.subjectsbox_layout.addWidget(self.subset_warning_checkbox,0,0)
        self.subjects_table = SubjectsTable(self)
        self.subjectsbox_layout.addWidget(self.subjects_table,1,0,1,2)
        self.subjectsbox_layout.setColumnStretch(1,1)

        # Variables Groupbox
        self.variables_groupbox = QtGui.QGroupBox('Variables')
        self.variablesbox_layout = QtGui.QHBoxLayout(self.variables_groupbox)
        self.variables_table = VariablesTable(self)
        self.task_select.set_callback(self.variables_table.task_changed)
        self.variablesbox_layout.addWidget(self.variables_table)

        # Initialise widgets
        self.experiment_select.addItems(['select experiment'])

        # Connect signals.
        self.name_text.textChanged.connect(self.name_edited)
        self.data_dir_text.textEdited.connect(lambda: setattr(self, 'custom_dir', True))
        self.data_dir_button.clicked.connect(self.select_data_dir)
        self.experiment_select.activated[str].connect(self.experiment_changed)
        self.new_button.clicked.connect(lambda: self.new_experiment(dialog=True))
        self.delete_button.clicked.connect(self.delete_experiment)
        self.save_button.clicked.connect(self.save_experiment)
        self.run_button.clicked.connect(self.run_experiment)

        # Keyboard shortcuts
        shortcut_dict = {
                        'Ctrl+s' : lambda: self.save_experiment(),
                        }
        init_keyboard_shortcuts(self, shortcut_dict)

        # Main layout
        self.vertical_layout = QtGui.QVBoxLayout(self)
        self.vertical_layout.addWidget(self.experiment_groupbox)
        self.vertical_layout.addWidget(self.subjects_groupbox)
        self.vertical_layout.addWidget(self.variables_groupbox)

        # Initialise variables.
        self.saved_exp_dict = self.experiment_dict()

    def name_edited(self):
        if not self.custom_dir:
            self.data_dir_text.setText(os.path.join(dirs['data'], self.name_text.text()))

    def select_data_dir(self):
        new_path = QtGui.QFileDialog.getExistingDirectory(self, 'Select data folder', dirs['data'])
        if new_path:
            self.data_dir_text.setText(new_path)
            self.custom_dir = True

    def experiment_changed(self, experiment_name):
        if experiment_name in self.GUI_main.available_experiments:
            cbox_set_item(self.experiment_select, 'select experiment', insert=True)
            if not self.save_dialog():
                return
            self.load_experiment(experiment_name)

    def refresh(self):
        '''Called periodically when not running to update available task, ports, experiments.'''
        if self.GUI_main.available_tasks_changed:
            self.task_select.update_menu(dirs['tasks'])
            self.hardware_test_select.update_menu(dirs['tasks'])
            self.GUI_main.available_tasks_changed = False
        if self.GUI_main.available_experiments_changed:
            cbox_update_options(self.experiment_select, self.GUI_main.available_experiments)
            self.GUI_main.available_experiments_changed = False
        if self.GUI_main.setups_tab.available_setups_changed:
            self.subjects_table.all_setups = set(self.GUI_main.setups_tab.setup_names)
            self.subjects_table.update_available_setups()
        if self.saved_exp_dict != self.experiment_dict():
            self.save_button.setEnabled(True)
        else:
            self.save_button.setEnabled(False)
        if self.GUI_main.data_dir_changed:
            if (str(self.name_text.text()) == '') and not self.custom_dir:
                self.data_dir_text.setText(dirs['data'])

    def experiment_dict(self, filtered=False):
        '''Return the current state of the experiments tab as a dictionary.'''
        return {'name': self.name_text.text(),
                'task': str(self.task_select.text()),
                'hardware_test': str(self.hardware_test_select.text()),
                'data_dir': self.data_dir_text.text(),
                'subjects': self.subjects_table.subjects_dict(filtered),
                'variables': self.variables_table.variables_list(),
                'subset_warning':self.subset_warning_checkbox.isChecked()}

    def new_experiment(self, dialog=True):
        '''Clear experiment configuration.'''
        if dialog:
            if not self.save_dialog(): return
        self.name_text.setText('')
        self.data_dir_text.setText(dirs['data'])
        self.custom_dir = False
        self.subjects_table.reset()
        self.variables_table.reset()
        cbox_set_item(self.experiment_select, 'select experiment', insert=True)
        self.task_select.setText('select task')
        self.hardware_test_select.setText('no hardware test')
        self.subset_warning_checkbox.setChecked(True)
        self.saved_exp_dict = self.experiment_dict()
        self.saved_exp_path = None

    def delete_experiment(self):
        '''Delete an experiment file after dialog to confirm deletion.'''
        exp_path = os.path.join(dirs['experiments'], self.name_text.text()+'.pcx')
        if os.path.exists(exp_path):
            reply = QtGui.QMessageBox.question(self, 'Delete experiment', 
                "Delete experiment '{}'".format(self.name_text.text()),
                    QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel)
            if reply == QtGui.QMessageBox.Yes:
                self.new_experiment(dialog=False)
                os.remove(exp_path)

    def save_experiment(self, from_dialog=False):
        '''Check that experiment setup/subject combinations are valid and unique'''
        d = {}
        for s in range(self.subjects_table.n_subjects):
            try:
                subject = str(self.subjects_table.item(s, 2).text())
                if len(subject) == 0:
                    invalid_save_experiment_dialog(self.subjects_table, 'All subjects must have names.')
                    return False
            except:
                invalid_save_experiment_dialog(self.subjects_table, 'All subjects must have names.')
                return False
            if subject in d:
                invalid_save_experiment_dialog(self.subjects_table, 'Duplicate subjects.')
                return False
            setup = str(self.subjects_table.cellWidget(s,1).currentText())
            run = self.subjects_table.cellWidget(s,0).isChecked()
            d[subject] =  {'setup':setup,'run':run} # add dict subject entry
        '''Store the current state of the experiment tab as a JSON object
        saved in the experiments folder as .pcx file.'''
        experiment = self.experiment_dict()
        file_name = self.name_text.text()+'.pcx'
        exp_path = os.path.join(dirs['experiments'], file_name)
        if os.path.exists(exp_path) and (exp_path != self.saved_exp_path):
            reply = QtGui.QMessageBox.question(self, 'Replace file', 
                "File '{}' already exists, do you want to replace it?".format(file_name),
                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
            if reply == QtGui.QMessageBox.No:
                return False
        with open(exp_path,'w') as exp_file:
            exp_file.write(json.dumps(experiment, sort_keys=True, indent=4))
        if not from_dialog:
            cbox_set_item(self.experiment_select, experiment['name'], insert=True)
        self.saved_exp_dict = experiment
        self.saved_exp_path = exp_path
        self.save_button.setEnabled(False)
        return True

    def load_experiment(self, experiment_name):
        '''Load experiment  .pcx file and set fields of experiment tab.'''
        exp_path = os.path.join(dirs['experiments'], experiment_name +'.pcx')
        with open(exp_path,'r') as exp_file:
            experiment = json.loads(exp_file.read())
        self.name_text.setText(experiment['name'])
        if experiment['task'] in self.GUI_main.available_tasks:
            self.task_select.setText(experiment['task'])
        else:
            self.task_select.setText('select task')
        if experiment['hardware_test'] in self.GUI_main.available_tasks:
            self.hardware_test_select.setText(experiment['hardware_test'])
        else:
            self.hardware_test_select.setText('no hardware test')
        cbox_set_item(self.experiment_select, experiment['name'])
        if 'subset_warning' in experiment.keys(): # New style experiment file.
            self.subset_warning_checkbox.setChecked(experiment['subset_warning'])
            self.subjects_table.set_from_dict(experiment['subjects'])
        else: # Experiment file created with GUI version <= 1.5.
            self.subset_warning_checkbox.setChecked(True)
            subjects_dict = {subject: {'run':True, 'setup':setup}
                for setup, subject in experiment['subjects'].items()}
            self.subjects_table.set_from_dict(subjects_dict)
        self.variables_table.task_changed(experiment['task'])
        self.data_dir_text.setText(experiment['data_dir'])
        self.variables_table.set_from_list(experiment['variables'])
        self.saved_exp_dict = experiment
        self.saved_exp_path = exp_path
        self.save_button.setEnabled(False)

    def run_experiment(self):
        '''Check that the experiment is valid. Prompt user to save experiment if
        it is new or has been edited. Then run experiment.'''
        experiment = self.experiment_dict(filtered=True)
        if not experiment['name']:
            invalid_run_experiment_dialog(self, 'Experiment must have a name.')
            return
        # Validate data path.
        if not (os.path.exists(experiment['data_dir']) or
                os.path.exists(os.path.split(experiment['data_dir'])[0])):
            invalid_run_experiment_dialog(self, "Data directory not available.")
            return
        # Validate task and hardware defintion.
        if experiment['task'] == 'select task':
            invalid_run_experiment_dialog(self, "Task not selected.")
            return
        if not experiment['task'] in self.GUI_main.available_tasks:
            invalid_run_experiment_dialog(self, 
                "Task file '{}.py' not found.".format(experiment['task']))
            return
        if (experiment['hardware_test'] != 'no hardware test' and
            experiment['hardware_test'] not in self.GUI_main.available_tasks):
            invalid_run_experiment_dialog(self, 
                "Hardware test file '{}.py' not found.".format(experiment['hardware_test']))
            return
        # Validate setups and subjects.
        if not experiment['subjects']:
            invalid_run_experiment_dialog(self, 'No subjects selected to run')
            return
        setups = [experiment['subjects'][subject]['setup'] for subject in experiment['subjects']]
        subjects = experiment['subjects'].keys()
        if len(setups) == 0:
                invalid_run_experiment_dialog(self, 'No subjects specified.')
                return
        if min([len(subject) for subject in subjects]) == 0:
                invalid_run_experiment_dialog(self,'All subjects must have names.')
                return
        if len(set(setups)) < len(setups):
                invalid_run_experiment_dialog(self,'Repeated Setup. Cannot run two experiments on the same Setup.')
                return
        for setup in setups:
            if not setup in self.GUI_main.setups_tab.setup_names:
                invalid_run_experiment_dialog(self, 
                    "Setup '{}' not available.".format(setup))
                return
        # Validate variables.
        for v in experiment['variables']:
            if v['value']:
                try:
                    eval(v['value'], variable_constants)
                except:
                    invalid_run_experiment_dialog(self, "Invalid value '{}' for variable '{}'."
                        .format(v['value'], v['name']))
                    return
        if self.subset_warning_checkbox.isChecked():
            all_subjects = self.experiment_dict()['subjects']
            will_not_run = ''
            for subject in all_subjects.keys():
                if all_subjects[subject]['run'] == False:
                    will_not_run += ('{}\n'.format(subject))
            if will_not_run != '':
                okay = unrun_subjects_dialog(self.subjects_groupbox,will_not_run)
                if not okay :return
        if not self.save_dialog(): return
        self.GUI_main.run_experiment_tab.setup_experiment(experiment)

    def save_dialog(self):
        '''Dialog to save experiment if it has been edited.  Returns False if
        cancel is selected, True otherwise.'''
        if self.saved_exp_dict == self.experiment_dict():
            return True # Experiment has not been edited.  
        exp_path = os.path.join(dirs['experiments'], self.name_text.text()+'.pcx')
        dialog_text = None
        if not os.path.exists(exp_path):
            dialog_text = 'Experiment not saved, save experiment?'
        else:
            dialog_text = 'Experiment edited, save experiment?'
        reply = QtGui.QMessageBox.question(self, 'Save experiment', dialog_text,
            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No | QtGui.QMessageBox.Cancel)
        if reply == QtGui.QMessageBox.Yes:
            was_saved = self.save_experiment(from_dialog=True)
            if not was_saved:
                invalid_run_experiment_dialog(self, "Failed to save experiment")
                return False
        elif reply == QtGui.QMessageBox.Cancel:
            return False
        return True

# ---------------------------------------------------------------------------------

class SubjectsTable(QtGui.QTableWidget):
    '''Table for specifying the setups and subjects used in experiment. '''

    def __init__(self, parent=None):
        super(QtGui.QTableWidget, self).__init__(1,4, parent=parent)
        self.setHorizontalHeaderLabels(['Run','Setup', 'Subject', ''])
        self.horizontalHeader().setResizeMode(1, QtGui.QHeaderView.Stretch)
        self.horizontalHeader().setResizeMode(2, QtGui.QHeaderView.Stretch)
        self.horizontalHeader().setResizeMode(3, QtGui.QHeaderView.ResizeToContents)
        self.verticalHeader().setVisible(False)
        self.cellChanged.connect(self.cell_changed)
        self.all_setups = set([])
        self.available_setups = []
        self.unallocated_setups = []
        self.subjects = []
        self.n_subjects = 0
        self.add_subject()

    def reset(self):
        '''Clear all rows of table.'''
        for i in reversed(range(self.n_subjects)):
            self.removeRow(i)
        self.available_setups = sorted(list(self.all_setups))
        self.subjects = []
        self.n_subjects = 0

    def cell_changed(self, row, column):
        '''If cell in subject row is changed, update subjects list and variables table.'''
        if column == 1:
            self.update_subjects()
            self.parent().parent().variables_table.update_available()

    def add_subject(self, setup=None, subject=None, do_run=None):
        '''Add row to table allowing extra subject to be specified.'''
        setup_cbox = QtGui.QComboBox()
        setup_cbox.addItems(self.available_setups if self.available_setups
                            else ['select setup'])
        if self.unallocated_setups:
            setup_cbox.setCurrentIndex(self.available_setups.index(
                                       self.unallocated_setups[0]))
        setup_cbox.activated.connect(self.update_available_setups)
        remove_button = QtGui.QPushButton('remove')
        remove_button.setIcon(QtGui.QIcon("gui/icons/remove.svg"))
        ind = QtCore.QPersistentModelIndex(self.model().index(self.n_subjects, 2))
        remove_button.clicked.connect(lambda :self.remove_subject(ind.row()))
        add_button = QtGui.QPushButton('add')
        add_button.setIcon(QtGui.QIcon("gui/icons/add.svg"))
        add_button.clicked.connect(self.add_subject)
        run_checkbox = TableCheckbox()
        if do_run ==None:
            run_checkbox.setChecked(True) #new subjects are set to "Run" by default
        else:
            run_checkbox.setChecked(do_run)
        self.setCellWidget(self.n_subjects,0,run_checkbox)  
        self.setCellWidget(self.n_subjects,1, setup_cbox)
        self.setCellWidget(self.n_subjects,3, remove_button)
        self.insertRow(self.n_subjects+1)
        self.setCellWidget(self.n_subjects+1,3, add_button)
        if setup:
            cbox_set_item(setup_cbox, setup)
        if subject:
            subject_item = QtGui.QTableWidgetItem()
            subject_item.setText(subject)
            self.setItem(self.n_subjects, 2, subject_item)
        self.n_subjects += 1
        self.update_available_setups()
        null_resize(self)

    def remove_subject(self, subject_n):
        '''Remove specified row from table'''
        if self.item(subject_n, 2): 
            s_name = self.item(subject_n, 2).text()
            self.parent().parent().variables_table.remove_subject(s_name)
        self.removeRow(subject_n)
        self.n_subjects -= 1
        self.update_available_setups()
        self.update_subjects()
        null_resize(self)

    def update_available_setups(self, i=None):
        '''Update which setups are available for selection in dropdown menus.'''
        selected_setups = set([str(self.cellWidget(s,1).currentText())
                               for s in range(self.n_subjects)])
        self.available_setups = sorted(list(self.all_setups))
        self.unallocated_setups = sorted(list(self.all_setups - selected_setups))
        for s in range(self.n_subjects):
            cbox_update_options(self.cellWidget(s,1), self.available_setups)

    def update_subjects(self):
        '''Update the subjects list'''
        self.subjects = [str(self.item(s, 2).text()) 
                         for s in range(self.n_subjects) if self.item(s, 2)]

    def subjects_dict(self,filtered=False):
        '''Return setups and subjects as a dictionary {subject:{'setup':setup,'run':run}}'''
        d = {}
        for s in range(self.n_subjects):
            try:
                subject = str(self.item(s, 2).text())
            except:
                return 
            setup = str(self.cellWidget(s,1).currentText())
            run = self.cellWidget(s,0).isChecked()
            if filtered:
                if run: 
                    d[subject] =  {'setup':setup,'run':run} # add dict subject entry
            else:
                d[subject] =  {'setup':setup,'run':run} # add dict subject entry
        return d

    def set_from_dict(self, subjects_dict):
        '''Fill table with subjects and setups from subjects_dict'''
        self.reset()
        for subject in subjects_dict:
            setup = subjects_dict[subject]['setup']
            do_run = subjects_dict[subject]['run']
            self.add_subject(setup,subject,do_run)
        self.update_available_setups()
        self.update_subjects()

# -------------------------------------------------------------------------------

class VariablesTable(QtGui.QTableWidget):
    '''Class for specifying task variables that are set to non-default values.'''

    def __init__(self, parent=None):
        super(QtGui.QTableWidget, self).__init__(1,6, parent=parent)
        self.subjects_table = self.parent().subjects_table
        self.setHorizontalHeaderLabels(['Variable', 'Subject', 'Value', 'Persistent','Summary',''])
        self.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.Stretch)
        self.horizontalHeader().setResizeMode(2, QtGui.QHeaderView.Stretch)
        self.horizontalHeader().setResizeMode(5, QtGui.QHeaderView.ResizeToContents)
        self.verticalHeader().setVisible(False)
        add_button = QtGui.QPushButton('   add   ')
        add_button.setIcon(QtGui.QIcon("gui/icons/add.svg"))
        add_button.clicked.connect(self.add_variable)
        self.setCellWidget(0,5, add_button)
        self.n_variables = 0
        self.variable_names = []
        self.available_variables = []
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
        remove_button.setIcon(QtGui.QIcon("gui/icons/remove.svg"))
        add_button = QtGui.QPushButton('   add   ')
        add_button.setIcon(QtGui.QIcon("gui/icons/add.svg"))
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
            if self.n_variables > 0: # Set variable to previous variable if available.
                v_name = str(self.cellWidget(self.n_variables-1, 0).currentText())
                if v_name in self.available_variables:
                    cbox_set_item(variable_cbox, v_name)
                    subject_cbox.addItems(self.available_subjects(v_name))
        self.n_variables += 1
        self.update_available()
        null_resize(self)

    def remove_variable(self, variable_n):
        self.removeRow(variable_n)
        self.n_variables -= 1
        self.update_available()
        null_resize(self)

    def remove_subject(self, subject):
        for i in reversed(range(self.n_variables)):
            if self.cellWidget(i,1).currentText() == subject:
                self.removeRow(i)
                self.n_variables -= 1
        self.update_available()
        null_resize(self)

    def update_available(self, i=None):
        # Find out what variable-subject combinations already assigned.
        self.assigned = {v_name:[] for v_name in self.variable_names}
        for v in range(self.n_variables):
            v_name = self.cellWidget(v,0).currentText()
            s_name = self.cellWidget(v,1).currentText()
            if s_name and s_name not in self.subjects_table.subjects + ['all']:
                cbox_set_item(self.cellWidget(v,1),'', insert=True)
                continue
            if v_name != 'select variable' and s_name:
                self.assigned[v_name].append(s_name)
        # Update the variables available:
        fully_asigned_variables = [v_n for v_n in self.assigned.keys()
                                   if 'all' in self.assigned[v_n]]
        if self.subjects_table.subjects:
            fully_asigned_variables += [v_n for v_n in self.assigned.keys()
                if set(self.assigned[v_n]) == set(self.subjects_table.subjects)]
        self.available_variables = sorted(list(
            set(self.variable_names) - set(fully_asigned_variables)), key=str.lower)
        # Update the available options in the variable and subject comboboxes.
        for v in range(self.n_variables):  
            v_name = self.cellWidget(v,0).currentText()
            s_name = self.cellWidget(v,1).currentText()
            cbox_update_options(self.cellWidget(v,0), self.available_variables)
            if v_name != 'select variable':
                # If variable has no subjects assigned, set subjects to 'all'.
                if not self.assigned[v_name]:
                    self.cellWidget(v,1).addItems(['all'])
                    self.assigned[v_name] = ['all']
                    self.available_variables.remove(v_name)
                cbox_update_options(self.cellWidget(v,1), self.available_subjects(v_name, s_name))

    def available_subjects(self, v_name, s_name=None):
        '''Return sorted list of the subjects that are available for selection 
        for the specified variable v_name given that subject s_name is already
        selected.'''
        if (not self.assigned[v_name]) or self.assigned[v_name] == [s_name]:
            available_subjects = ['all']+ sorted(self.subjects_table.subjects)
        else:
            available_subjects = sorted(list(set(self.subjects_table.subjects)-
                                             set(self.assigned[v_name])))
        return available_subjects

    def task_changed(self, task):
        '''Remove variables that are not defined in the new task.'''
        pattern = "[\n\r]v\.(?P<vname>\w+)\s*\="
        try:
            with open(os.path.join(dirs['tasks'], task+'.py'), "r") as file:
                file_content = file.read()
        except FileNotFoundError:
            return
        self.variable_names = list(set([v_name for v_name in 
            re.findall(pattern, file_content) if not v_name[-3:] == '___']))
        # Remove variables that are not in new task.
        for i in reversed(range(self.n_variables)):
            if not self.cellWidget(i,0).currentText() in self.variable_names:
                self.removeRow(i)
                self.n_variables -= 1
        null_resize(self)
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
        for var_dict in variables_list:
            self.add_variable(var_dict)
        self.update_available()
