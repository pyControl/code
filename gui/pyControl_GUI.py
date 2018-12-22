import os
import sys
from serial.tools import list_ports
from pyqtgraph.Qt import QtGui, QtCore
from serial import SerialException

# Add parent directory to path to allow imports.
top_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not top_dir in sys.path: sys.path.insert(0, top_dir)

from run_task_tab import Run_task_tab
from config.paths import tasks_dir, experiments_dir
from config.gui_settings import update_interval, VERSION
from gui.plotting import Task_plotter
from gui.experiments_tab import Experiments_tab

from com.pycboard import Pycboard, PyboardError
from com.data_logger import Data_logger

# --------------------------------------------------------------------------------
# GUI_main
# --------------------------------------------------------------------------------

class GUI_main(QtGui.QMainWindow):
 
    def __init__(self):
        super().__init__()
        self.setWindowTitle('pyControl v{}'.format(VERSION))
        self.setGeometry(20, 30, 700, 800) # Left, top, width, height.

        # Variables
        self.refresh_interval = 1000 # How often refresh method is called when not running (ms).
        self.available_tasks = None  # List of task file names in tasks folder.
        self.available_ports = None  # List of available serial ports.
        self.available_experiments = None # List of experiment in experiments folder.
        self.available_tasks_changed = False
        self.available_experiments_changed = False
        self.available_ports_changed = False
        self.current_tab_ind = 0 # Which tab is currently selected.
        self.experiment = None # Overwritten by experiment dict on run.
        self.app = None # Overwritten with QtGui.QApplication instance in main.

        # Widgets.
        self.tab_widget = QtGui.QTabWidget(self)
        self.setCentralWidget(self.tab_widget)

        self.run_task_tab = Run_task_tab(self)  
        self.experiments_tab = Experiments_tab(self)
        self.summary_tab = Summary_tab(self) 
        self.plots_tab = Plots_tab(self)

        self.tab_widget.addTab(self.run_task_tab,'Run task')
        self.tab_widget.addTab(self.experiments_tab,'Experiments')
        self.tab_widget.addTab(self.summary_tab,'Summary')
        self.tab_widget.addTab(self.plots_tab,'Plots')    

        self.tab_widget.currentChanged.connect(self.tab_changed) 

        # Timers

        self.refresh_timer = QtCore.QTimer() # Timer to regularly call refresh() when not running.
        self.process_timer = QtCore.QTimer() # Timer to regularly call process_data() during run.        
        
        self.process_timer.timeout.connect(self.process_data)
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(self.refresh_interval)

        # Initial setup.
        self.refresh()    # Refresh tasks and ports lists.
        self.tab_widget.setTabEnabled(2,False)
        self.tab_widget.setTabEnabled(3,False)

        self.show()

    def refresh(self):
        '''Called regularly when framework not running.'''
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
        self.run_task_tab.refresh()
        self.experiments_tab.refresh()

    def tab_changed(self, new_tab_ind):
        '''Called whenever the active tab is changed.'''
        if self.current_tab_ind == 0: 
            if self.run_task_tab.connected:
                self.run_task_tab.disconnect()
        self.current_tab_ind = new_tab_ind

    # Experiment functions

    def run_experiment(self, experiment):
        '''Called when an experiment is loaded.'''
        # Setup tabs.
        self.experiment = experiment
        self.tab_widget.setTabEnabled(0, False)
        self.tab_widget.setTabEnabled(1, False)
        self.tab_widget.setTabEnabled(2, True)
        self.tab_widget.setTabEnabled(3, True)
        self.summary_tab.run_experiment(experiment)
        self.plots_tab.run_experiment(experiment)
        self.experiment_running = False
        # Setup boards.
        self.app.processEvents()
        self.data_loggers = []
        self.boards = []
        self.print_funcs = []
        for i, setup in enumerate(sorted(experiment['subjects'].keys())):
            print_func = self.summary_tab.summaryboxes[i].print_to_log
            data_logger = Data_logger(print_func=print_func)
            # Connect to board.
            print_func('Connecting to board.. ')
            try:
                board = Pycboard(setup, print_func=print_func, data_logger=data_logger)
            except SerialException:
                print_func('Connection failed.')
                self.stop_experiment()
                return
            # Setup state machine.
            try:
                self.sm_info = board.setup_state_machine(experiment['task'])
            except PyboardError:
                self.stop_experiment()
                return
            # Set variables.
            print_func('\nSetting variables. ', end='')
            try:
                subject_variables = [v for v in experiment['variables'] 
                                 if v['subject'] in ('all', experiment['subjects'][setup])]
                for v in subject_variables:
                    board.set_variable(v['variable'], eval(v['value']))
                print_func('OK')
            except PyboardError:
                print_func('Failed')
                self.stop_experiment()
                return
            self.boards.append(board)
            self.data_loggers.append(data_logger)
            self.print_funcs.append(print_func)
            self.plots_tab.subject_plot_tabs[i].task_plot.set_state_machine(self.sm_info)
        self.summary_tab.startstop_button.setEnabled(True)
        self.plots_tab.startstop_button.setEnabled(True)

    def startstop_experiment(self):
        if not self.experiment_running:
            self.start_experiment()
        else:
            self.stop_experiment()

    def start_experiment(self):
        self.experiment_running = True
        self.summary_tab.start_experiment()
        self.plots_tab.start_experiment()
        for i, board in enumerate(self.boards):
            self.print_funcs[i]('\nStarting experiment.\n')
            board.start_framework()
        self.refresh_timer.stop()
        self.process_timer.start(update_interval)

    def stop_experiment(self):
        self.experiment_running = False
        self.tab_widget.setTabEnabled(0, True)
        self.tab_widget.setTabEnabled(1, True)
        self.summary_tab.stop_experiment()
        self.plots_tab.stop_experiment()
        self.process_timer.stop()
        self.refresh_timer.start(self.refresh_interval)
        for i, board in enumerate(self.boards):
            board.stop_framework()
            board.close()

    def process_data(self):
        '''Called regularly while experiment is running'''
        for i, board in enumerate(self.boards):
            try:
                new_data = board.process_data()
                self.plots_tab.subject_plot_tabs[i].process_data(new_data)
                if not board.framework_running:
                    pass
            except PyboardError:
                self.print_funcs[i]('\nError during framework run.')

    # Exception handling.

    def excepthook(self, ex_type, ex_value, ex_traceback):
        '''Called whenever an uncaught exception occurs.'''
        if hasattr(self.tab_widget.currentWidget(), 'excepthook'):
           self.tab_widget.currentWidget().excepthook(ex_type, ex_value, ex_traceback)
        else:
            print(str(ex_value))
            ex_traceback.print_tb()

# --------------------------------------------------------------------------------
# Summary tab
# --------------------------------------------------------------------------------

class Summary_tab(QtGui.QWidget):

    def __init__(self, parent=None):
        super(QtGui.QWidget, self).__init__(parent)

        self.GUI_main = self.parent()

        self.name_label = QtGui.QLabel('Experiment name:')
        self.name_text  = QtGui.QLineEdit()
        self.startstop_button = QtGui.QPushButton('Start experiment')
        self.startstop_button.clicked.connect(self.GUI_main.startstop_experiment)

        self.Hlayout = QtGui.QHBoxLayout()
        self.Hlayout.addWidget(self.name_label)
        self.Hlayout.addWidget(self.name_text)
        self.Hlayout.addWidget(self.startstop_button)

        self.Vlayout = QtGui.QVBoxLayout(self)
        self.Vlayout.addLayout(self.Hlayout)

        self.summaryboxes = []

    def reset(self):
        '''Remove and delete all subject summary boxes.'''
        while len(self.summaryboxes) > 0:
            summarybox = self.summaryboxes.pop() 
            summarybox.setParent(None)
            summarybox.deleteLater()

    def run_experiment(self, experiment):
        '''Called when experiment is run to setup tab.'''
        self.reset()
        self.name_text.setText(experiment['name'])
        self.startstop_button.setEnabled(False)
        for setup in sorted(experiment['subjects'].keys()):
            self.summaryboxes.append(
                Summarybox('{} : {}'.format(setup, experiment['subjects'][setup]), self))
            self.Vlayout.addWidget(self.summaryboxes[-1])

    def start_experiment(self):
        self.startstop_button.setText('Stop experiment')

    def stop_experiment(self):
        '''Called when experiment stops.'''
        self.startstop_button.setText('Start experiment')
        self.startstop_button.setEnabled(False)

class Summarybox(QtGui.QGroupBox):

    def __init__(self, name, parent=None):

        super(QtGui.QGroupBox, self).__init__(name, parent=parent)
        self.GUI_main = self.parent().GUI_main

        self.state_label = QtGui.QLabel('State:')
        self.state_text = QtGui.QLineEdit()
        self.state_text.setReadOnly(True)
        self.print_label = QtGui.QLabel('Print:')
        self.print_text = QtGui.QLineEdit()
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

    def print_to_log(self, print_string, end='\n'):
        self.log_textbox.moveCursor(QtGui.QTextCursor.End)
        self.log_textbox.insertPlainText(print_string+end)
        self.log_textbox.moveCursor(QtGui.QTextCursor.End)
        self.GUI_main.app.processEvents()

# --------------------------------------------------------------------------------
# Plots tab
# --------------------------------------------------------------------------------

class Plots_tab(QtGui.QWidget):

    def __init__(self, parent=None):
        super(QtGui.QWidget, self).__init__(parent)

        self.GUI_main = self.parent()

        self.name_label = QtGui.QLabel('Experiment name:')
        self.name_text  = QtGui.QLineEdit()
        self.startstop_button = QtGui.QPushButton('Start experiment')
        self.startstop_button.clicked.connect(self.GUI_main.startstop_experiment)
        self.subject_tabs = QtGui.QTabWidget(self)

        self.Hlayout = QtGui.QHBoxLayout()
        self.Hlayout.addWidget(self.name_label)
        self.Hlayout.addWidget(self.name_text)
        self.Hlayout.addWidget(self.startstop_button)

        self.Vlayout = QtGui.QVBoxLayout(self)
        self.Vlayout.addLayout(self.Hlayout)
        self.Vlayout.addWidget(self.subject_tabs)

        self.subject_plot_tabs = []

    def reset(self):
        '''Remove and delete all subject plot tabs.'''
        while len(self.subject_plot_tabs) > 0:
            subject_plot_tab = self.subject_plot_tabs.pop() 
            subject_plot_tab.setParent(None)
            subject_plot_tab.deleteLater()

    def run_experiment(self, experiment):
        '''Called when experiment is run to setup tab.'''
        self.reset()
        self.name_text.setText(experiment['name'])
        self.startstop_button.setEnabled(False)
        for setup in sorted(experiment['subjects'].keys()):
            self.subject_plot_tabs.append(Subject_plots_tab(self))
            self.subject_tabs.addTab(self.subject_plot_tabs[-1],
                '{} : {}'.format(setup, experiment['subjects'][setup]))

    def start_experiment(self):
        self.startstop_button.setText('Stop experiment')
        for subject_plot_tab in self.subject_plot_tabs:
            subject_plot_tab.task_plot.run_start(False)

    def stop_experiment(self):
        '''Called when experiment stops.'''
        self.startstop_button.setText('Start experiment')
        self.startstop_button.setEnabled(False)

class Subject_plots_tab(QtGui.QWidget):

    def __init__(self, parent=None):
        super(QtGui.QWidget, self).__init__(parent)
        self.log_textbox = QtGui.QTextEdit()
        self.log_textbox.setFont(QtGui.QFont('Courier', 9))
        self.log_textbox.setReadOnly(True)
        self.task_plot = Task_plotter()

        self.Vlayout = QtGui.QVBoxLayout()
        self.Vlayout.addWidget(self.log_textbox)#, stretch=10)
        self.Vlayout.addWidget(self.task_plot)
        self.setLayout(self.Vlayout)

    def process_data(self, new_data):
        self.task_plot.process_data(new_data)

# --------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    gui_main = GUI_main()
    gui_main.app = app # To allow app functions to be called from GUI.
    sys.excepthook = gui_main.excepthook
    sys.exit(app.exec_())