import os
import time
import json
from datetime import datetime

from pyqtgraph.Qt import QtGui, QtCore
from serial import SerialException

from config.gui_settings import  update_interval
from com.pycboard import Pycboard, PyboardError
from com.data_logger import Data_logger
from gui.plotting import Experiment_plot
from gui.dialogs import Variables_dialog, Summary_variables_dialog
from gui.utility import variable_constants

class Run_experiment_tab(QtGui.QWidget):
    '''The run experiment tab is responsible for setting up, running and stopping
    an experiment that has been defined using the configure experiments tab.'''

    def __init__(self, parent=None):
        super(QtGui.QWidget, self).__init__(parent)

        self.GUI_main = self.parent()
        self.experiment_plot = Experiment_plot(self)

        self.name_label = QtGui.QLabel('Experiment name:')
        self.name_text  = QtGui.QLineEdit()
        self.status_label = QtGui.QLabel('Status:')
        self.status_text = QtGui.QLineEdit()
        self.status_text.setFixedWidth(60)
        self.time_label = QtGui.QLabel('Time:')
        self.time_text = QtGui.QLineEdit()
        self.time_text.setFixedWidth(60)
        self.name_text.setReadOnly(True)
        self.plots_button =  QtGui.QPushButton('Plots')
        self.plots_button.clicked.connect(self.experiment_plot.show)
        self.logs_button = QtGui.QPushButton('Hide logs')
        self.logs_button.clicked.connect(self.show_hide_logs)    
        self.startstopclose_button = QtGui.QPushButton()
        self.startstopclose_button.clicked.connect(self.startstopclose)

        self.Hlayout = QtGui.QHBoxLayout()
        self.Hlayout.addWidget(self.name_label)
        self.Hlayout.addWidget(self.name_text)
        self.Hlayout.addWidget(self.status_label)
        self.Hlayout.addWidget(self.status_text)
        self.Hlayout.addWidget(self.time_label)
        self.Hlayout.addWidget(self.time_text)
        self.Hlayout.addWidget(self.logs_button)
        self.Hlayout.addWidget(self.plots_button)
        self.Hlayout.addWidget(self.startstopclose_button)

        self.scroll_area = QtGui.QScrollArea(parent=self)
        self.scroll_area.horizontalScrollBar().setEnabled(False)
        self.scroll_inner = QtGui.QFrame(self)
        self.boxes_layout = QtGui.QVBoxLayout(self.scroll_inner)
        self.scroll_area.setWidget(self.scroll_inner)
        self.scroll_area.setWidgetResizable(True)

        self.Vlayout = QtGui.QVBoxLayout(self)
        self.Vlayout.addLayout(self.Hlayout)
        self.Vlayout.addWidget(self.scroll_area)

        self.subjectboxes = []

        self.update_timer = QtCore.QTimer() # Timer to regularly call update() during run.        
        self.update_timer.timeout.connect(self.update)

    def setup_experiment(self, experiment):
        '''Called when an experiment is loaded.'''
        # Setup tabs.
        self.status_text.setText('Loading')
        self.experiment = experiment
        self.GUI_main.tab_widget.setTabEnabled(0, False)
        self.GUI_main.experiments_tab.setCurrentWidget(self)
        self.startstopclose_button.setText('Start')
        self.experiment_plot.setup_experiment(experiment)
        self.state = 'pre_run'
        self.logs_visible = True
        self.logs_button.setText('Hide logs')
        # Setup controls box.
        self.name_text.setText(experiment['name'])
        self.time_text.setText('')
        self.startstopclose_button.setEnabled(False)
        self.logs_button.setEnabled(False)
        self.plots_button.setEnabled(False)
        # Setup subjectboxes
        for setup in sorted(experiment['subjects'].keys()):
            self.subjectboxes.append(
                Subjectbox('{} : {}'.format(setup, experiment['subjects'][setup]), self))
            self.boxes_layout.addWidget(self.subjectboxes[-1])
        # Create data folder if needed.
        if not os.path.exists(self.experiment['data_dir']):
            os.mkdir(self.experiment['data_dir'])
        # Load persistent variables if they exist.
        self.pv_path = os.path.join(self.experiment['data_dir'], 'persistent_variables.json')
        if os.path.exists(self.pv_path):
            with open(self.pv_path, 'r') as pv_file:
                persistent_variables =  json.loads(pv_file.read())
        else:
            persistent_variables = {}
        # Setup boards.
        self.GUI_main.app.processEvents()
        self.boards = []
        for i, setup in enumerate(sorted(experiment['subjects'].keys())):
            print_func = self.subjectboxes[i].print_to_log
            serial_port = self.GUI_main.setups_tab.get_port(setup)
            # Connect to boards.
            print_func('Connecting to board.. ')
            try:
                self.boards.append(Pycboard(serial_port, print_func=print_func))
            except SerialException:
                print_func('Connection failed.')
                self.stop_experiment()
                return
            self.boards[i].subject = experiment['subjects'][setup]
        # Hardware test.
        if experiment['hardware_test'] != ' no hardware test':
            reply = QtGui.QMessageBox.question(self, 'Hardware test', 'Run hardware test?',
                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
            if reply == QtGui.QMessageBox.Yes:
                try:
                    for i, board in enumerate(self.boards):
                            board.setup_state_machine(experiment['hardware_test'])
                            board.print('\nStarting hardware test.')
                            board.start_framework(data_output=False)
                            time.sleep(0.01)
                            board.process_data()
                    QtGui.QMessageBox.question(self, 'Hardware test', 
                        'Press OK when finished with hardware test.', QtGui.QMessageBox.Ok)
                    for i, board in enumerate(self.boards):
                        board.stop_framework()
                        time.sleep(0.01)
                        board.process_data()
                except PyboardError:
                    self.subjectboxes[i].task_crashed()
                    self.stop_experiment(error=True)
                    return
        # Setup state machines.
        for i, board in enumerate(self.boards):
            try:
                board.data_logger = Data_logger(print_func=board.print, data_consumers=
                    [self.experiment_plot.subject_plots[i], self.subjectboxes[i]])
                board.setup_state_machine(experiment['task'])
            except PyboardError:
                self.stop_experiment()
                return
            # Set variables.
            board.subject_variables = [v for v in experiment['variables'] 
                                       if v['subject'] in ('all', board.subject)]
            if board.subject_variables:
                board.print('\nSetting variables.\n')
                board.variables_set_pre_run = []
                try:
                    
                    try:
                        subject_pv_dict = persistent_variables[board.subject]
                    except KeyError:
                        subject_pv_dict = {}
                    for v in board.subject_variables:
                        if v['persistent'] and v['name'] in subject_pv_dict.keys(): # Use stored value.
                            v_value =  subject_pv_dict[v['name']]
                            board.variables_set_pre_run.append(
                                (v['name'], str(v_value), '(persistent value)'))
                        else:
                            if v['value'] == '':
                                continue
                            v_value = eval(v['value'], variable_constants) # Use value from variables table.
                            board.variables_set_pre_run.append((v['name'], v['value'], ''))
                        board.set_variable(v['name'], v_value)
                    # Print set variables to log.    
                    name_len  = max([len(v[0]) for v in board.variables_set_pre_run])
                    value_len = max([len(v[1]) for v in board.variables_set_pre_run])
                    for v_name, v_value, pv_str in board.variables_set_pre_run:
                        self.subjectboxes[i].print_to_log(
                            v_name.ljust(name_len+4) + v_value.ljust(value_len+4) + pv_str)
                except PyboardError:
                    board.print('Setting variables failed')
                    self.stop_experiment()
                    return
        for i, board in enumerate(self.boards):
            self.subjectboxes[i].assign_board(board)
        self.experiment_plot.set_state_machine(board.sm_info)
        self.startstopclose_button.setEnabled(True)
        self.logs_button.setEnabled(True)
        self.plots_button.setEnabled(True)
        self.status_text.setText('Ready')

    def start_experiment(self):
        '''Open data files, write variables set pre run to file, start framework.'''
        self.status_text.setText('Running')
        self.startstopclose_button.setText('Stop')
        self.state = 'running'
        self.experiment_plot.start_experiment()
        self.start_time = datetime.now()
        ex = self.experiment
        for i, board in enumerate(self.boards):
            board.print('\nStarting experiment.\n')
            board.data_logger.open_data_file(ex['data_dir'], ex['name'], board.subject, self.start_time)
            if board.subject_variables: # Write variables set pre run to data file.
                for v_name, v_value, pv in board.variables_set_pre_run:
                    board.data_logger.data_file.write('V 0 {} {}\n'.format(v_name, v_value))
            board.data_logger.data_file.write('\n')
            board.start_framework()
        self.GUI_main.refresh_timer.stop()
        self.update_timer.start(update_interval)

    def stop_experiment(self, error=False):
        self.status_text.setText('Stopped')
        self.startstopclose_button.setText('Close')
        self.state = 'post_run'
        self.update_timer.stop()
        self.GUI_main.refresh_timer.start(self.GUI_main.refresh_interval)
        summary_variables = [v for v in self.experiment['variables'] if v['summary']]
        persistent_variables = {}
        if summary_variables: sv_dict = {}
        for i, board in enumerate(self.boards):
            # Stop running boards.
            if board.framework_running:
                board.stop_framework()
                time.sleep(0.01)
                board.process_data()
                self.subjectboxes[i].task_stopped()
        if error:
            self.startstopclose_button.setEnabled(True)
            return
        for i, board in enumerate(self.boards):
            # Store persistent variables.
            subject_pvs = [v for v in board.subject_variables if v['persistent']]
            if subject_pvs:
                board.print('\nStoring persistent variables.')
                persistent_variables[board.subject] = {
                    v['name']: board.get_variable(v['name']) for v in subject_pvs}
            # Read summary variables.
            if summary_variables:
                sv_dict[board.subject] = {v['name']: board.get_variable(v['name'])
                                          for v in summary_variables}
                for v_name, v_value in sv_dict[board.subject].items():
                    board.data_logger.data_file.write('\nV -1 {} {}'.format(v_name, v_value))
                    board.data_logger.data_file.flush()
        if persistent_variables:
            with open(self.pv_path, 'w') as pv_file:
                pv_file.write(json.dumps(persistent_variables, sort_keys=True, indent=4))
        if summary_variables:
            Summary_variables_dialog(self, sv_dict).show()

    def close_experiment(self):
        self.GUI_main.tab_widget.setTabEnabled(0, True)
        self.GUI_main.experiments_tab.setCurrentWidget(self.GUI_main.configure_experiment_tab)
        self.experiment_plot.close_experiment()
        # Close boards.
        for board in self.boards:
            if board.data_logger: board.data_logger.close_files()
            board.close()
        # Clear subjectboxes.
        while len(self.subjectboxes) > 0:
            subjectbox = self.subjectboxes.pop() 
            subjectbox.setParent(None)
            subjectbox.deleteLater()
        if not self.logs_visible:
            self.boxes_layout.takeAt(self.boxes_layout.count()-1) # Remove stretch.

    def startstopclose(self):
        if self.state == 'pre_run': 
            self.start_experiment()
        elif self.state == 'running':
            self.stop_experiment()
        elif self.state == 'post_run':
            self.close_experiment()

    def show_hide_logs(self):
        '''Show/hide the log textboxes in subjectboxes.'''
        if self.logs_visible:
            for subjectbox in self.subjectboxes:
                subjectbox.log_textbox.hide()
            self.boxes_layout.addStretch(100)
            self.logs_visible = False
            self.logs_button.setText('Show logs')
        else:
            for subjectbox in self.subjectboxes:
                subjectbox.log_textbox.show()
            self.boxes_layout.takeAt(self.boxes_layout.count()-1) # Remove stretch.
            self.logs_visible = True
            self.logs_button.setText('Hide logs')

    def update(self):
        '''Called regularly while experiment is running'''
        self.time_text.setText(str(datetime.now()-self.start_time).split('.')[0])
        boards_running = False
        for i, board in enumerate(self.boards):
            if board.framework_running:
                boards_running = True
                try:
                    board.process_data()
                    if not board.framework_running:
                        self.subjectboxes[i].task_stopped()
                except PyboardError:
                    self.subjectboxes[i].task_crashed()
        self.experiment_plot.update()
        if not boards_running:
            self.stop_experiment()

# -----------------------------------------------------------------------------

class Subjectbox(QtGui.QGroupBox):
    '''Groupbox for displaying data from a single subject.'''

    def __init__(self, name, parent=None):

        super(QtGui.QGroupBox, self).__init__(name, parent=parent)
        self.board = None # Overwritten with board once instantiated.
        self.GUI_main = self.parent().GUI_main
        self.run_exp_tab = self.parent()

        self.state_label = QtGui.QLabel('State:')
        self.state_text = QtGui.QLineEdit()
        self.state_text.setFixedWidth(140)
        self.state_text.setReadOnly(True)
        self.event_label = QtGui.QLabel('Event:')
        self.event_text = QtGui.QLineEdit()
        self.event_text.setReadOnly(True)
        self.event_text.setFixedWidth(140)
        self.print_label = QtGui.QLabel('Print:')
        self.print_text = QtGui.QLineEdit()
        self.print_text.setReadOnly(True)
        self.variables_button = QtGui.QPushButton('Variables')
        self.variables_button.setEnabled(False)
        self.log_textbox = QtGui.QTextEdit()
        self.log_textbox.setMinimumHeight(180)
        self.log_textbox.setFont(QtGui.QFont('Courier', 9))
        self.log_textbox.setReadOnly(True)

        self.Vlayout = QtGui.QVBoxLayout(self)
        self.Hlayout = QtGui.QHBoxLayout()
        self.Hlayout.addWidget(self.state_label)
        self.Hlayout.addWidget(self.state_text)
        self.Hlayout.addWidget(self.event_label)
        self.Hlayout.addWidget(self.event_text)
        self.Hlayout.addWidget(self.print_label)
        self.Hlayout.addWidget(self.print_text)
        self.Hlayout.setStretchFactor(self.print_text, 10)
        self.Hlayout.addWidget(self.variables_button)
        self.Vlayout.addLayout(self.Hlayout)
        self.Vlayout.addWidget(self.log_textbox)

    def print_to_log(self, print_string, end='\n'):
        self.log_textbox.moveCursor(QtGui.QTextCursor.End)
        self.log_textbox.insertPlainText(print_string+end)
        self.log_textbox.moveCursor(QtGui.QTextCursor.End)
        self.GUI_main.app.processEvents()

    def assign_board(self, board):
        self.board = board
        self.variables_dialog = Variables_dialog(self, board)
        self.variables_button.clicked.connect(self.variables_dialog.exec_)
        self.variables_button.setEnabled(True)

    def task_crashed(self):
        '''Called if task crashes during run.'''
        self.print_to_log('\nError during framework run.')
        self.state_text.setText('Error')
        self.state_text.setStyleSheet('color: red;')

    def task_stopped(self):
        '''Called when task stops running.'''
        self.state_text.setText('Stopped')
        self.state_text.setStyleSheet('color: grey;') 

    def process_data(self, new_data):
        '''Update the state, event and print line info.'''
        try:
            new_state = next(self.board.sm_info['ID2name'][nd[2]] for nd in reversed(new_data)
                if nd[0] == 'D' and nd[2] in self.board.sm_info['states'].values())
            self.state_text.setText(new_state)
            self.state_text.home(False)
        except StopIteration:
            pass
        try:
            new_event = next(self.board.sm_info['ID2name'][nd[2]] for nd in reversed(new_data)
                if nd[0] == 'D' and nd[2] in self.board.sm_info['events'].values())
            self.event_text.setText(new_event)
            self.event_text.home(False)
        except StopIteration:
            pass
        try:
            new_print = next(nd[2] for nd in reversed(new_data) if nd[0] == 'P')
            self.print_text.setText(new_print)
            self.print_text.home(False)
        except StopIteration:
            pass
            