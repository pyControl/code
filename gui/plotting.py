import time
import numpy as np
from datetime import timedelta
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui

from config.gui_settings import event_history_len, state_history_len, analog_history_dur
from gui.detachableTabWidget import detachableTabWidget

# ----------------------------------------------------------------------------------------
# Task_plot 
# ----------------------------------------------------------------------------------------

class Task_plot(QtGui.QWidget):
    ''' Widget for plotting the states, events and analog inputs output by a state machine.'''

    def __init__(self, parent=None):
        super(QtGui.QWidget, self).__init__(parent)

        # Create widgets

        self.states_plot = States_plot(self, data_len=state_history_len)
        self.events_plot = Events_plot(self, data_len=event_history_len)
        self.analog_plot = Analog_plot(self, data_dur=analog_history_dur)
        self.run_clock   = Run_clock(self.states_plot.axis)

        # Setup plots

        self.events_plot.axis.setXLink(self.states_plot.axis)
        self.analog_plot.axis.setXLink(self.states_plot.axis)
        self.analog_plot.axis.setVisible(False)

        # create layout

        self.vertical_layout = QtGui.QVBoxLayout()
        self.vertical_layout.addWidget(self.states_plot.axis,1)
        self.vertical_layout.addWidget(self.events_plot.axis,1)
        self.vertical_layout.addWidget(self.analog_plot.axis,1)
        self.setLayout(self.vertical_layout)

    def set_state_machine(self, sm_info):
        # Initialise plots with state machine information.
        self.states_plot.set_state_machine(sm_info)
        self.events_plot.set_state_machine(sm_info)
        self.analog_plot.set_state_machine(sm_info)

        if sm_info['analog_inputs']:
            self.analog_plot.axis.setVisible(True)
            self.events_plot.axis.getAxis('bottom').setLabel('')
        else:
            self.analog_plot.axis.setVisible(False)
            self.events_plot.axis.getAxis('bottom').setLabel('Time (seconds)')

    def run_start(self, recording):
        self.start_time = time.time()
        self.states_plot.run_start()
        self.events_plot.run_start()
        self.analog_plot.run_start()
        if recording:
            self.run_clock.recording()

    def run_stop(self):
        self.run_clock.run_stop()

    def process_data(self, new_data):
        '''Store new data from board.'''
        self.states_plot.process_data(new_data)
        self.events_plot.process_data(new_data)
        self.analog_plot.process_data(new_data)

    def update(self):
        '''Update plots.'''
        run_time = time.time() - self.start_time
        self.states_plot.update(run_time)
        self.events_plot.update(run_time)
        self.analog_plot.update(run_time)
        self.run_clock.update(run_time)

# States_plot --------------------------------------------------------

class States_plot():

    def __init__(self, parent=None, data_len=100):
        self.data_len = data_len
        self.axis = pg.PlotWidget(title='States')
        self.axis.showAxis('right')
        self.axis.hideAxis('left')
        self.axis.setRange(xRange=[-10.2, 0], padding=0)
        self.axis.setMouseEnabled(x=True,y=False)
        self.axis.showGrid(x=True,alpha=0.75)
        self.axis.setLimits(xMax=0)

    def set_state_machine(self, sm_info):
        self.state_IDs = list(sm_info['states'].values())
        self.axis.clear()
        max_len = max([len(n) for n in list(sm_info['states'])+list(sm_info['events'])])
        self.axis.getAxis('right').setTicks([[(i, n) for (n, i) in sm_info['states'].items()]])
        self.axis.getAxis('right').setWidth(5*max_len)
        self.axis.setYRange(min(self.state_IDs), max(self.state_IDs), padding=0.1)
        self.n_colours = len(sm_info['states'])+len(sm_info['events'])
        self.plots = {ID: self.axis.plot(pen=pg.mkPen(pg.intColor(ID, self.n_colours), width=3))
                      for ID in self.state_IDs}

    def run_start(self):
        self.data = np.zeros([self.data_len*2, 2], int)
        for plot in self.plots.values():
            plot.clear()
        self.cs = self.state_IDs[0]
        self.updated_states = []

    def process_data(self, new_data):
        '''Store new data from board'''
        new_states = [nd for nd in new_data if nd[0] == 'D' and nd[2] in self.state_IDs]
        self.updated_states = [self.cs]
        if new_states:
            n_new =len(new_states)
            self.data = np.roll(self.data, -2*n_new, axis=0)
            for i, ns in enumerate(new_states): # Update data array.
                timestamp, ID = ns[1:]
                self.updated_states.append(ID)
                j = 2*(-n_new+i)  # Index of state entry in self.data
                self.data[j-1:,0] = timestamp
                self.data[j:  ,1] = ID  
            self.cs = ID

    def update(self, run_time):
        '''Update plots.'''
        self.data[-1,0] = 1000*run_time # Update exit time of current state to current time.
        for us in self.updated_states: # Set data for updated state plots.
            state_data = self.data[self.data[:,1]==us,:]
            timestamps, ID = (state_data[:,0]/1000, state_data[:,1])
            self.plots[us].setData(x=timestamps, y=ID, connect='pairs')
        # Shift all state plots.
        for plot in self.plots.values():
            plot.setPos(-run_time, 0)

# Events_plot--------------------------------------------------------

class Events_plot():

    def __init__(self, parent=None, data_len=100):
        self.axis = pg.PlotWidget(title='Events')
        self.axis.showAxis('right')
        self.axis.hideAxis('left')
        self.axis.setRange(xRange=[-10.2, 0], padding=0)
        self.axis.setMouseEnabled(x=True,y=False)
        self.axis.showGrid(x=True,alpha=0.75)
        self.axis.setLimits(xMax=0)
        self.data_len = data_len

    def set_state_machine(self, sm_info):
        self.event_IDs = list(sm_info['events'].values())
        self.axis.clear()
        if not self.event_IDs: return # State machine can have no events.
        max_len = max([len(n) for n in list(sm_info['states'])+list(sm_info['events'])])
        self.axis.getAxis('right').setTicks([[(i, n) for (n, i) in sm_info['events'].items()]])
        self.axis.getAxis('right').setWidth(5*max_len)
        self.axis.setYRange(min(self.event_IDs), max(self.event_IDs), padding=0.1)
        self.n_colours = len(sm_info['states'])+len(sm_info['events'])
        self.plot = self.axis.plot(pen=None, symbol='o', symbolSize=6, symbolPen=None)

    def run_start(self):
        if not self.event_IDs: return # State machine can have no events.
        self.plot.clear()
        self.data = np.zeros([self.data_len, 2])

    def process_data(self, new_data):
        '''Store new data from board.'''
        if not self.event_IDs: return # State machine can have no events.
        new_events = [nd for nd in new_data if nd[0] == 'D' and nd[2] in self.event_IDs]
        if new_events:
            n_new = len(new_events)
            self.data = np.roll(self.data, -n_new, axis=0)
            for i, ne in enumerate(new_events):
                timestamp, ID = ne[1:]
                self.data[-n_new+i,0] = timestamp / 1000
                self.data[-n_new+i,1] = ID

    def update(self, run_time):
        '''Update plots'''
        # Should not need to setData but setPos does not cause redraw otherwise.
        if not self.event_IDs: return
        self.plot.setData(self.data, symbolBrush=[pg.intColor(ID) for ID in self.data[:,1]])
        self.plot.setPos(-run_time, 0)

# ------------------------------------------------------------------------------------------

class Analog_plot():

    def __init__(self, parent=None, data_dur=10):
        self.data_dur = data_dur
        self.axis = pg.PlotWidget(title='Analog')
        self.axis.showAxis('right')
        self.axis.hideAxis('left')
        self.axis.setRange(xRange=[-10.2, 0], padding=0)
        self.axis.setMouseEnabled(x=True,y=False)
        self.axis.showGrid(x=True,alpha=0.75)
        self.axis.setLimits(xMax=0)
        self.legend = None 

    def set_state_machine(self, sm_info):
        self.inputs = sm_info['analog_inputs']
        if not self.inputs: return # State machine may not have analog inputs.
        if self.legend:
            self.legend.close()
        self.legend = self.axis.addLegend(offset=(10, 10))
        self.axis.clear()
        self.plots = {ai['ID']: self.axis.plot(name=name, 
                      pen=pg.mkPen(pg.intColor(ai['ID'],len(self.inputs)))) for name, ai in sorted(self.inputs.items())}
        self.axis.getAxis('bottom').setLabel('Time (seconds)')
        max_len = max([len(n) for n in list(sm_info['states'])+list(sm_info['events'])])
        self.axis.getAxis('right').setWidth(5*max_len)
        
    def run_start(self):
        if not self.inputs: return # State machine may not have analog inputs.
        for plot in self.plots.values():
            plot.clear()
        self.data = {ai['ID']: np.zeros([ai['Fs']*self.data_dur, 2])
                     for ai in self.inputs.values()}
        self.updated_inputs = []

    def process_data(self, new_data):
        '''Store new data from board.'''
        if not self.inputs: return # State machine may not have analog inputs.
        new_analog = [nd for nd in new_data if nd[0] == 'A']
        self.updated_inputs = [na[1] for na in new_analog]
        for na in new_analog:
            ID, sampling_rate, timestamp, data_array = na[1:]
            new_len = len(data_array)
            t = timestamp/1000 + np.arange(new_len)/sampling_rate
            self.data[ID] = np.roll(self.data[ID], -new_len, axis=0)
            self.data[ID][-new_len:,:] = np.vstack([t,data_array]).T

    def update(self, run_time):
        '''Update plots.'''
        if not self.inputs: return # State machine may not have analog inputs.
        for ID in self.updated_inputs:
            self.plots[ID].setData(self.data[ID])
        for plot in self.plots.values():
            plot.setPos(-run_time, 0)   

# -----------------------------------------------------

class Run_clock():
    # Class for displaying the run time.

    def __init__(self, axis):
        self.clock_text = pg.TextItem(text='')
        self.clock_text.setFont(QtGui.QFont('arial',11, QtGui.QFont.Bold))
        axis.getViewBox().addItem(self.clock_text, ignoreBounds=True)
        self.clock_text.setParentItem(axis.getViewBox())
        self.clock_text.setPos(10,-5)
        self.recording_text = pg.TextItem(text='', color=(255,0,0))
        self.recording_text.setFont(QtGui.QFont('arial',12,QtGui.QFont.Bold))
        axis.getViewBox().addItem(self.recording_text, ignoreBounds=True)
        self.recording_text.setParentItem(axis.getViewBox())
        self.recording_text.setPos(80,-5)

    def update(self, run_time):
        self.clock_text.setText(str(timedelta(seconds=run_time))[:7])

    def recording(self):
        self.recording_text.setText('Recording')

    def run_stop(self):
        self.clock_text.setText('')
        self.recording_text.setText('')

# --------------------------------------------------------------------------------
# Experiment plotter
# --------------------------------------------------------------------------------

class Experiment_plot(QtGui.QMainWindow):
    '''Window for plotting data during experiment run where each subjects plots
    are displayed in a seperate tab.'''

    def __init__(self, parent=None):
        super(QtGui.QWidget, self).__init__(parent)
        self.setWindowTitle('Experiment plot')
        self.setGeometry(720, 30, 700, 800) # Left, top, width, height.       
        self.subject_tabs = detachableTabWidget(self)
        self.setCentralWidget(self.subject_tabs)
        self.subject_plots = []

    def setup_experiment(self, experiment):
        '''Create task plotters in seperate tabs for each subject.'''
        for setup in sorted(experiment['subjects'].keys()):
            self.subject_plots.append(Task_plot(self))
            self.subject_tabs.addTab(self.subject_plots[-1],
                '{} : {}'.format(setup, experiment['subjects'][setup]))

    def set_state_machine(self, sm_info):
        '''Provide the task plotters with the state machine info.'''
        for subject_plot in self.subject_plots:
            subject_plot.set_state_machine(sm_info)

    def start_experiment(self):
        for subject_plot in self.subject_plots:
            subject_plot.run_start(False)

    def close_experiment(self):
        '''Remove and delete all subject plot tabs.'''
        while len(self.subject_plots) > 0:
            subject_plot = self.subject_plots.pop() 
            subject_plot.setParent(None)
            subject_plot.deleteLater()

    def update(self):
        '''Update the plots of the active tab.'''
        for subject_plot in self.subject_plots:
            if not subject_plot.visibleRegion().isEmpty():
                subject_plot.update()