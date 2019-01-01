from pyqtgraph.Qt import QtGui, QtCore
from serial import SerialException

from config.gui_settings import  update_interval
from com.pycboard import Pycboard, PyboardError
from com.data_logger import Data_logger
from gui.plotting import Experiment_plot
from gui.dialogs import Variables_dialog

class Run_experiment_tab(QtGui.QWidget):

    def __init__(self, parent=None):
        super(QtGui.QWidget, self).__init__(parent)

        self.GUI_main = self.parent()
        self.experiment_plot = Experiment_plot(self)

        self.name_label = QtGui.QLabel('Experiment name:')
        self.name_text  = QtGui.QLineEdit()
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
        self.Hlayout.addWidget(self.logs_button)
        self.Hlayout.addWidget(self.plots_button)
        self.Hlayout.addWidget(self.startstopclose_button)

        self.scroll_area = QtGui.QScrollArea(parent=self)
        self.scroll_area.horizontalScrollBar().setEnabled(False)
        self.scroll_inner = QtGui.QFrame(self)
        # self.scroll_area.setStyleSheet('background-color:transparent;')
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
        self.startstopclose_button.setEnabled(False)
        self.logs_button.setEnabled(False)
        self.plots_button.setEnabled(False)
        # Setup subjectboxes
        for setup in sorted(experiment['subjects'].keys()):
            self.subjectboxes.append(
                Subjectbox('{} : {}'.format(setup, experiment['subjects'][setup]), self))
            self.boxes_layout.addWidget(self.subjectboxes[-1])
        # Setup boards.
        self.GUI_main.app.processEvents()
        self.boards = []
        for i, setup in enumerate(sorted(experiment['subjects'].keys())):
            print_func = self.subjectboxes[i].print_to_log
            data_logger = Data_logger(print_func=print_func, 
                data_consumers=[self.experiment_plot.subject_plots[i],
                                self.subjectboxes[i]])
            # Connect to boards.
            print_func('Connecting to board.. ')
            try:
                self.boards.append(Pycboard(setup, print_func=print_func, data_logger=data_logger))
            except SerialException:
                print_func('Connection failed.')
                self.stop_experiment()
                return
        # Setup state machines.
        for i, board in enumerate(self.boards):
            try:
                board.setup_state_machine(experiment['task'])
            except PyboardError:
                self.stop_experiment()
                return
            # Set variables.
            board.print('\nSetting variables. ', end='')
            try:
                subject_variables = [v for v in experiment['variables'] 
                                 if v['subject'] in ('all', experiment['subjects'][setup])]
                for v in subject_variables:
                    board.set_variable(v['variable'], eval(v['value']))
                board.print('OK')
            except PyboardError:
                board.print('Failed')
                self.stop_experiment()
                return
            self.subjectboxes[i].assign_board(board)
        self.experiment_plot.set_state_machine(board.sm_info)
        self.startstopclose_button.setEnabled(True)
        self.logs_button.setEnabled(True)
        self.plots_button.setEnabled(True)

    def start_experiment(self):
        self.startstopclose_button.setText('Stop')
        self.state = 'running'
        self.experiment_plot.start_experiment()
        for i, board in enumerate(self.boards):
            board.print('\nStarting experiment.\n')
            board.start_framework()
        self.GUI_main.refresh_timer.stop()
        self.update_timer.start(update_interval)

    def stop_experiment(self):
        self.startstopclose_button.setText('Close')
        self.state = 'post_run'
        self.update_timer.stop()
        self.GUI_main.refresh_timer.start(self.GUI_main.refresh_interval)
        for i, board in enumerate(self.boards):
            board.stop_framework()
            board.close()

    def close_experiment(self):
        self.GUI_main.tab_widget.setTabEnabled(0, True)
        self.GUI_main.experiments_tab.setCurrentWidget(self.GUI_main.configure_experiment_tab)
        self.experiment_plot.close_experiment()
        # Clear subjectboxes.
        while len(self.subjectboxes) > 0:
            subjectbox = self.subjectboxes.pop() 
            subjectbox.setParent(None)
            subjectbox.deleteLater()

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
            self.boxes_layout.addStretch()
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
        for i, board in enumerate(self.boards):
            try:
                board.process_data()
                if not board.framework_running:
                    pass
            except PyboardError:
                board.print('\nError during framework run.')
        self.experiment_plot.update()

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
        self.state_text.setReadOnly(True)
        self.event_label = QtGui.QLabel('Event:')
        self.event_text = QtGui.QLineEdit()
        self.event_text.setReadOnly(True)
        self.print_label = QtGui.QLabel('Print:')
        self.print_text = QtGui.QLineEdit()
        self.print_text.setReadOnly(True)
        self.variables_button = QtGui.QPushButton('Variables')
        self.variables_button.setEnabled(False)
        self.log_textbox = QtGui.QTextEdit()
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

    def process_data(self, new_data):
        '''Update the state, event and print line info.'''
        try:
            new_state = next(self.board.sm_info['ID2name'][nd[2]] for nd in reversed(new_data)
                if nd[0] == 'D' and nd[2] in self.board.sm_info['states'].values())
            self.state_text.setText(new_state)
        except StopIteration:
            pass
        try:
            new_event = next(self.board.sm_info['ID2name'][nd[2]] for nd in reversed(new_data)
                if nd[0] == 'D' and nd[2] in self.board.sm_info['events'].values())
            self.event_text.setText(new_event)
        except StopIteration:
            pass
        try:
            new_print = next(nd[2] for nd in reversed(new_data) if nd[0] == 'P')
            self.print_text.setText(new_print)
        except StopIteration:
            pass
            