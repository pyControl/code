from pyqtgraph.Qt import QtGui, QtCore
from serial import SerialException

from config.gui_settings import  update_interval
from com.pycboard import Pycboard, PyboardError
from com.data_logger import Data_logger

class Run_experiment_tab(QtGui.QWidget):

    def __init__(self, parent=None):
        super(QtGui.QWidget, self).__init__(parent)

        self.GUI_main = self.parent()

        self.name_label = QtGui.QLabel('Experiment name:')
        self.name_text  = QtGui.QLineEdit()
        self.startstopclose_button = QtGui.QPushButton()
        self.startstopclose_button.clicked.connect(self.startstopclose)
        self.Hlayout = QtGui.QHBoxLayout()
        self.Hlayout.addWidget(self.name_label)
        self.Hlayout.addWidget(self.name_text)
        self.Hlayout.addWidget(self.startstopclose_button)

        self.Vlayout = QtGui.QVBoxLayout(self)
        self.Vlayout.addLayout(self.Hlayout)

        self.summaryboxes = []

        self.update_timer = QtCore.QTimer() # Timer to regularly call update() during run.        
        self.update_timer.timeout.connect(self.update)

    def setup_experiment(self, experiment):
        '''Called when an experiment is loaded.'''
        # Setup tabs.
        self.experiment = experiment
        self.GUI_main.tab_widget.setTabEnabled(0, False)
        self.GUI_main.experiments_tab.setCurrentWidget(self)
        self.startstopclose_button.setText('Start experiment')
        self.state = 'pre_run' 
        # Setup controls box.
        self.name_text.setText(experiment['name'])
        self.startstopclose_button.setEnabled(False)
        # Setup summaryboxes
        for setup in sorted(experiment['subjects'].keys()):
            self.summaryboxes.append(
                Summarybox('{} : {}'.format(setup, experiment['subjects'][setup]), self))
            self.Vlayout.addWidget(self.summaryboxes[-1])
        # Setup boards.
        self.GUI_main.app.processEvents()
        self.data_loggers = []
        self.boards = []
        self.print_funcs = []
        for i, setup in enumerate(sorted(experiment['subjects'].keys())):
            print_func = self.summaryboxes[i].print_to_log
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
            #self.plots_tab.subject_plot_tabs[i].task_plot.set_state_machine(self.sm_info)
        self.startstopclose_button.setEnabled(True)

    def start_experiment(self):
        self.startstopclose_button.setText('Stop experiment')
        self.state = 'running'
        #self.plots_tab.start_experiment()
        for i, board in enumerate(self.boards):
            self.print_funcs[i]('\nStarting experiment.\n')
            board.start_framework()
        self.GUI_main.refresh_timer.stop()
        self.update_timer.start(update_interval)

    def stop_experiment(self):
        self.startstopclose_button.setText('Close experiment')
        self.state = 'post_run'
        #self.plots_tab.stop_experiment()
        self.update_timer.stop()
        self.GUI_main.refresh_timer.start(self.GUI_main.refresh_interval)
        for i, board in enumerate(self.boards):
            board.stop_framework()
            board.close()

    def close_experiment(self):
        self.GUI_main.tab_widget.setTabEnabled(0, True)
        self.GUI_main.experiments_tab.setCurrentWidget(self.GUI_main.configure_experiment_tab) 
        # Clear summaryboxes.
        while len(self.summaryboxes) > 0:
            summarybox = self.summaryboxes.pop() 
            summarybox.setParent(None)
            summarybox.deleteLater()

    def startstopclose(self):
        if self.state == 'pre_run': 
            self.start_experiment()
        elif self.state == 'running':
            self.stop_experiment()
        elif self.state == 'post_run':
            self.close_experiment()

    def update(self):
        '''Called regularly while experiment is running'''
        for i, board in enumerate(self.boards):
            try:
                board.process_data()
                if not board.framework_running:
                    pass
            except PyboardError:
                self.print_funcs[i]('\nError during framework run.')


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
