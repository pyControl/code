import os
import sys
from serial.tools import list_ports
from pyqtgraph.Qt import QtGui, QtCore

# Add parent directory to path to allow imports.
top_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not top_dir in sys.path: sys.path.insert(0, top_dir)

from run_task import Run_task
from config.paths import tasks_dir, experiments_dir
from gui.plotting import Task_plotter
from gui.experiments_tab import Experiments_tab

# --------------------------------------------------------------------------------
# GUI_main
# --------------------------------------------------------------------------------

class GUI_main(QtGui.QMainWindow):
 
    def __init__(self):
        super().__init__()
        self.setWindowTitle('pyControl')
        self.setGeometry(20, 30, 700, 800) # Left, top, width, height.

        # Variables
        self.refresh_interval = 1000 # How often refresh method is called when not running (ms).
        self.available_tasks = None  # List of task file names in tasks folder.
        self.available_ports = None  # List of available serial ports.
        self.available_experiments = None # List of experiment in experiments folder.
        self.available_tasks_changed = False
        self.available_experiments_changed = False
        self.available_ports_changed = False
        self.experiment = None # Overwritten by experiment dict on run.
        self.app = None # Overwritten with QtGui.QApplication instance in main.

        # Widgets and timers
        self.main_tabs = MainTabs(self)
        self.setCentralWidget(self.main_tabs)
        self.refresh_timer = QtCore.QTimer() # Timer to regularly call refresh() when not running.

        # Initial setup.
        self.refresh()    # Refresh tasks and ports lists.
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(self.refresh_interval)

        self.show()

    def refresh(self):
        # Called regularly when not running to update GUI.
        # Scan task folder.
        tasks =  [t.split('.')[0] for t in os.listdir(tasks_dir) if t[-3:] == '.py']
        self.available_tasks_changed = tasks != self.available_tasks
        if self.available_tasks_changed:    
            self.available_tasks = tasks
        # Scan experiments folder.
        experiments = [t.split('.')[0] for t in os.listdir(experiments_dir) if t[-4:] == '.pcx']
        self.available_experiments_changed = experiments != self.available_experiments
        if self.available_experiments_changed:    
            self.available_experiments = experiments
        # Scan serial ports.
        ports = set([c[0] for c in list_ports.comports()
                     if ('Pyboard' in c[1]) or ('USB Serial Device' in c[1])])
        self.available_ports_changed = ports != self.available_ports
        if self.available_ports_changed:    
            self.available_ports = ports
        # Refresh tabs.
        self.main_tabs.refresh()

    def run_experiment(self, experiment):
        self.experiment = experiment
        self.main_tabs.run_experiment(experiment)

    # Exception handling.

    def excepthook(self, ex_type, ex_value, ex_traceback):
        # Called whenever an uncaught exception occurs.
        if hasattr(self.main_tabs.currentWidget(), 'excepthook'):
           self.main_tabs.currentWidget().excepthook(ex_type, ex_value, ex_traceback)
        else:
            print(str(ex_value))
            print(str(ex_traceback))

# ------------------------------------------------------------------------------

class MainTabs(QtGui.QTabWidget):        
 
    def __init__(self, parent):   
        super(QtGui.QWidget, self).__init__(parent)
 
        # Initialize tab widgets.
        self.run_task_tab = Run_task(self)  
        self.experiments_tab = Experiments_tab(self)
        self.summary_tab = Summary_tab(self) 
        self.plots_tab = Plots_tab(self)

        # Add tabs
        self.addTab(self.run_task_tab,'Run task')
        self.addTab(self.experiments_tab,'Experiments')
        self.addTab(self.summary_tab,'Summary')
        self.addTab(self.plots_tab,'Plots')     

        # Set initial state.
        self.setTabEnabled(2,False)
        self.setTabEnabled(3,False)

    def refresh(self):
        '''Call refresh method of tabs.'''
        self.run_task_tab.refresh()
        self.experiments_tab.refresh()


    def run_experiment(self, experiment):
        self.setTabEnabled(0, False)
        self.setTabEnabled(1, False)
        self.setTabEnabled(2, True)
        self.setTabEnabled(3, True)
        self.summary_tab.run_experiment(experiment)
        self.plots_tab.run_experiment(experiment)

# --------------------------------------------------------------------------------
# Summary tab
# --------------------------------------------------------------------------------

class Summary_tab(QtGui.QWidget):

    def __init__(self, parent=None):
        super(QtGui.QWidget, self).__init__(parent)

        self.GUI_main = self.parent().parent()
        self.Vlayout = QtGui.QVBoxLayout(self)

    def run_experiment(self, experiment):
        '''Called when experiment is run to setup tab.'''
        self.subject_summaryboxes = []
        for setup in sorted(experiment['subjects'].keys()):
            self.subject_summaryboxes.append(
                Subject_summarybox('{} : {}'.format(setup, experiment['subjects'][setup])))
            self.Vlayout.addWidget(self.subject_summaryboxes[-1])

class Subject_summarybox(QtGui.QGroupBox):

    def __init__(self, name, parent=None):
        super(QtGui.QGroupBox, self).__init__(name, parent=parent)

        self.state_label = QtGui.QLabel('State:')
        self.state_text = QtGui.QLineEdit('Current state')
        self.state_text.setReadOnly(True)
        self.print_label = QtGui.QLabel('Print:')
        self.print_text = QtGui.QLineEdit('Last print line')
        self.print_text.setReadOnly(True)
        self.variables_button = QtGui.QPushButton('Variables')
        self.log_textbox = QtGui.QTextEdit()
        self.log_textbox.setFont(QtGui.QFont('Courier', 9))
        self.log_textbox.setReadOnly(True)

        self.Vlayout = QtGui.QVBoxLayout(self)
        self.Hlayout = QtGui.QHBoxLayout()
        self.Hlayout.addWidget(self.state_label)
        self.Hlayout.addWidget(self.state_text)
        self.Hlayout.addWidget(self.print_label)
        self.Hlayout.addWidget(self.print_text)
        self.Hlayout.setStretchFactor(self.print_text, 3)
        self.Hlayout.addWidget(self.variables_button)
        self.Vlayout.addLayout(self.Hlayout)
        self.Vlayout.addWidget(self.log_textbox)

# --------------------------------------------------------------------------------
# Plots tab
# --------------------------------------------------------------------------------

class Plots_tab(QtGui.QTabWidget):

    def __init__(self, parent=None):
        super(QtGui.QWidget, self).__init__(parent)

        self.GUI_main = self.parent().parent()
        self.Vlayout = QtGui.QVBoxLayout(self)

    def run_experiment(self, experiment):
        '''Called when experiment is run to setup tab.'''
        self.subject_plottabs = []
        for setup in sorted(experiment['subjects'].keys()):
            self.subject_plottabs.append(Subject_plots_tab(self))
            self.addTab(self.subject_plottabs[-1],
                '{} : {}'.format(setup, experiment['subjects'][setup]))


class Subject_plots_tab(QtGui.QWidget):

    def __init__(self, parent=None):
        super(QtGui.QWidget, self).__init__(parent)
        self.log_textbox = QtGui.QTextEdit()
        self.log_textbox.setFont(QtGui.QFont('Courier', 9))
        self.log_textbox.setReadOnly(True)
        self.task_plot = Task_plotter()

        self.Vlayout = QtGui.QVBoxLayout()
        self.Vlayout.addWidget(self.log_textbox)
        self.Vlayout.addWidget(self.task_plot)
        self.setLayout(self.Vlayout)

# --------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    gui_main = GUI_main()
    gui_main.app = app # To allow app functions to be called from GUI.
    sys.excepthook = gui_main.excepthook
    sys.exit(app.exec_())