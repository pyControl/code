import os
import sys
from pyqtgraph.Qt import QtGui, QtCore

from run_task_gui import Run_task_gui
from config.paths import data_dir, tasks_dir

# --------------------------------------------------------------------------------

class GUI_main(QtGui.QMainWindow):
 
    def __init__(self):
        super().__init__()
        self.setWindowTitle('pyControl')
        self.setGeometry(20, 30, 600, 800) # Left, top, width, height.

        # Variables
        self.refresh_interval = 1000
        self.available_tasks = None
        self.available_tasks_changed = False
 
        self.main_tabs = MainTabs(self)
        self.setCentralWidget(self.main_tabs)
 
        self.show()

        self.refresh_timer = QtCore.QTimer() # Timer to regularly call refresh() when not running.
        self.refresh_timer.timeout.connect(self.refresh)

        # Initial setup.

        self.refresh()    # Refresh tasks and ports lists.
        self.refresh_timer.start(self.refresh_interval)

    def refresh(self):
        # Called regularly when not running to update tasks and ports.
        self.scan_tasks()
        self.main_tabs.refresh()
        # self.scan_ports()

    def scan_tasks(self):
        # Scan task folder for available tasks and update tasks list if changed.     
        tasks =  set([t.split('.')[0] for t in os.listdir(tasks_dir)
                  if t[-3:] == '.py'])
        if not tasks == self.available_tasks:    
            self.available_tasks = tasks
            self.available_tasks_changed = True

# ------------------------------------------------------------------------------

class MainTabs(QtGui.QTabWidget):        
 
    def __init__(self, parent):   
        super(QtGui.QWidget, self).__init__(parent)
 
        # Initialize tab widgets.
        self.run_task_tab = Run_task_gui(self)	
        self.experiments_tab = Experiments_tab(self)
        self.summary_tab = QtGui.QWidget(self)	
        self.plot_tab = QtGui.QWidget(self)

        # Add tabs
        self.addTab(self.run_task_tab,'Run task')
        self.addTab(self.experiments_tab,'Experiments')
        self.addTab(self.summary_tab,'Summary')
        self.addTab(self.plot_tab,'Plots')     

        # Set initial state.
        self.setTabEnabled(2,False)
        self.setTabEnabled(3,False)

    def refresh(self):
        '''Call refresh method of active tab.'''
        if self.currentWidget() == self.experiments_tab:
            self.currentWidget().refresh()


# --------------------------------------------------------------------------------

class Experiments_tab(QtGui.QWidget):

    def __init__(self, parent=None):
        super(QtGui.QWidget, self).__init__(parent)

        # State variables
        self.GUI_main = self.parent().parent()
        self.custom_dir = False

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
        self.save_button = QtGui.QPushButton('Save')
        self.name_label = QtGui.QLabel('Experiment name:')
        self.name_text = QtGui.QLineEdit()
        self.task_select = QtGui.QComboBox()
        self.task_select.setFixedWidth(180)
        self.data_dir_label = QtGui.QLabel('Data dir:')
        self.data_dir_text = QtGui.QLineEdit(data_dir)
        self.data_dir_button = QtGui.QPushButton('...')
        self.data_dir_button.setFixedWidth(30)

        self.name_text.textChanged.connect(self.name_edited)
        self.data_dir_text.textEdited.connect(lambda: setattr(self, 'custom_dir', True))
        self.data_dir_button.clicked.connect(self.select_data_dir)

        self.expbox_Hlayout_1.addWidget(self.experiment_select)
        self.expbox_Hlayout_1.setStretchFactor(self.experiment_select, 2)
        self.expbox_Hlayout_1.addWidget(self.run_button)
        self.expbox_Hlayout_1.addWidget(self.new_button)
        self.expbox_Hlayout_1.addWidget(self.save_button)
        self.expbox_Hlayout_2.addWidget(self.name_label)
        self.expbox_Hlayout_2.addWidget(self.name_text)
        self.expbox_Hlayout_2.addWidget(self.task_select)
        self.expbox_Hlayout_3.addWidget(self.data_dir_label)
        self.expbox_Hlayout_3.addWidget(self.data_dir_text)
        self.expbox_Hlayout_3.addWidget(self.data_dir_button)

        # Subjects Groupbox
        self.subjects_groupbox = QtGui.QGroupBox('Subjects')
        self.subjectsbox_layout = QtGui.QHBoxLayout(self.subjects_groupbox)
        self.subjects_table = SubjectsTable()
        self.subjectsbox_layout.addWidget(self.subjects_table)

        # Variables Groupbox
        self.variables_groupbox = QtGui.QGroupBox('Variables')
        self.variablesbox_layout = QtGui.QHBoxLayout(self.variables_groupbox)
        self.variables_table = VariablesTable()
        self.variablesbox_layout.addWidget(self.variables_table)

        # Initialise widgets
        self.experiment_select.addItems(['select experiment'])

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

    def refresh(self):
        if self.GUI_main.available_tasks_changed == True:
            self.task_select.clear()
            self.task_select.addItems(self.GUI_main.available_tasks)


class SubjectsTable(QtGui.QTableWidget):
    '''Table for specifying the setups and subjects used in experiment. '''

    def __init__(self, parent=None):
        super(QtGui.QTableWidget, self).__init__(1,3, parent=parent)
        self.setHorizontalHeaderLabels(['Setup', 'Subject', ''])
        self.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.Stretch)
        self.horizontalHeader().setResizeMode(1, QtGui.QHeaderView.Stretch)
        self.horizontalHeader().setResizeMode(2, QtGui.QHeaderView.ResizeToContents)
        self.verticalHeader().setVisible(False)
        self.n_subjects = 0
        self.all_setups = {'COM1', 'COM2', 'COM3', 'COM4'}
        self.available_setups = sorted(list(self.all_setups))
        self.add_subject()

    def add_subject(self):
        '''Add row to table allowing extra subject to be specified.'''
        setup_cbox = QtGui.QComboBox()
        setup_cbox.addItems(self.available_setups)
        setup_cbox.activated.connect(lambda: self.update_available())
        remove_button = QtGui.QPushButton('remove')
        ind = QtCore.QPersistentModelIndex(self.model().index(self.n_subjects, 2))
        remove_button.clicked.connect(lambda :self.remove_subject(ind.row()))
        add_button = QtGui.QPushButton('add')
        add_button.clicked.connect(self.add_subject)        
        self.setCellWidget(self.n_subjects,0, setup_cbox)
        self.setCellWidget(self.n_subjects,2, remove_button)
        self.insertRow(self.n_subjects+1)
        self.setCellWidget(self.n_subjects+1,2, add_button)
        self.n_subjects += 1
        self.update_available()
        
    def remove_subject(self, subject_n):
        '''Remove specified row from table'''
        self.removeRow(subject_n)
        self.n_subjects -= 1
        self.update_available()

    def update_available(self):
        '''Update which setups are available for selection in dropdown menus.'''
        selected_setups = set([str(self.cellWidget(s,0).currentText())
                               for s in range(self.n_subjects)])
        self.available_setups = list(self.all_setups - selected_setups)
        for s in range(self.n_subjects):
            current_setup = str(self.cellWidget(s,0).currentText())
            available = sorted([current_setup]+self.available_setups)
            i = available.index(current_setup)
            self.cellWidget(s,0).clear()
            self.cellWidget(s,0).addItems(available)
            self.cellWidget(s,0).setCurrentIndex(i)

class VariablesTable(QtGui.QTableWidget):
    '''Class for specifying what variables are set to non-default values.'''

    def __init__(self, parent=None):
        super(QtGui.QTableWidget, self).__init__(1,5, parent=parent)
        self.setHorizontalHeaderLabels(['Variable', 'Subject', 'Value', 'Persistent',''])
        self.horizontalHeader().setResizeMode(2, QtGui.QHeaderView.Stretch)
        self.horizontalHeader().setResizeMode(4, QtGui.QHeaderView.ResizeToContents)
        self.verticalHeader().setVisible(False)
        self.n_variables = 0
        add_button = QtGui.QPushButton('add')
        add_button.clicked.connect(self.add_variable)
        self.setCellWidget(0,4, add_button)

    def add_variable(self):
        variable_cbox = QtGui.QComboBox()
        variable_cbox.addItems(['select variable'])
        subject_cbox = QtGui.QComboBox()
        subject_cbox.addItems(['all'])
        persistent = TableCheckbox()
        remove_button = QtGui.QPushButton('remove')
        ind = QtCore.QPersistentModelIndex(self.model().index(self.n_variables, 2))
        remove_button.clicked.connect(lambda :self.remove_variable(ind.row()))
        add_button = QtGui.QPushButton('add')
        add_button.clicked.connect(self.add_variable)
        self.insertRow(self.n_variables+1)
        self.setCellWidget(self.n_variables  ,0, variable_cbox)
        self.setCellWidget(self.n_variables  ,1, subject_cbox)
        self.setCellWidget(self.n_variables  ,3, persistent)
        self.setCellWidget(self.n_variables  ,4, remove_button)
        self.setCellWidget(self.n_variables+1,4, add_button)
        self.n_variables += 1

    def remove_variable(self, variable_n):
        self.removeRow(variable_n)
        self.n_variables -= 1

# -------------------------------------------------------------------------

class TableCheckbox(QtGui.QWidget):
    '''Checkbox that is centered in cell when placed in table.'''

    def __init__(self, parent=None):
        super(QtGui.QWidget, self).__init__(parent)
        self.checkbox = QtGui.QCheckBox(parent=parent)
        self.layout = QtGui.QHBoxLayout(self)
        self.layout.addWidget(self.checkbox)
        self.layout.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.setContentsMargins(0,0,0,0)

# --------------------------------------------------------------------------------

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    ex = GUI_main()
    sys.exit(app.exec_())