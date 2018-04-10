import time
import pyqtgraph as pg
import numpy as np
from pyqtgraph.Qt import QtGui

# Task_plotter -----------------------------------------------------------------------

class Task_plotter(QtGui.QWidget):
    ''' Widget for plotting the states, events and analog inputs output by a state machine.'''

    def __init__(self, parent=None):
        super(QtGui.QWidget, self).__init__(parent)

        # Create widgets

        self.state_axis = pg.PlotWidget(title='States')
        self.event_axis = pg.PlotWidget(title='Events', labels={'bottom':'Time (seconds)'})
        self.analog_axis = pg.PlotWidget(title='Analog')

        # Setup plots

        self.event_plot = pg.ScatterPlotItem(size=6, pen=None)
        self.event_axis.addItem(self.event_plot)
        self.event_axis.setXLink(self.state_axis)
        self.analog_axis.setXLink(self.state_axis)
        self.analog_axis.addLegend(offset=(10, 10)) 
        self.analog_axis.setVisible(False)

        # create layout

        self.vertical_layout = QtGui.QVBoxLayout()
        self.vertical_layout.addWidget(self.state_axis,1)
        self.vertical_layout.addWidget(self.event_axis,1)
        self.vertical_layout.addWidget(self.analog_axis,1)

        self.setLayout(self.vertical_layout)

    def set_state_machine(self, sm_info):
        # Initialise plots with state machine information.
        self.events = sm_info['events'] # dict {event_name: ID}
        self.states = sm_info['states'] # dict {state_name: ID}
        self.analog_inputs = sm_info['analog_inputs']
        self.n_colours = len(self.events) + len(self.states)
        # Clear old data.
        self.state_axis.clear()
        self.event_plot.clear()
        self.analog_axis.clear()
        # Setup state axis
        self.state_axis.getAxis('left').setTicks([[(i, n) for (n, i) in self.states.items()]])
        self.state_axis.setYRange(min(self.states.values()), max(self.states.values()), padding=0.2)
        self.state_plots = {ID: self.state_axis.plot(pen=pg.mkPen(pg.intColor(ID, self.n_colours), width=3))
                            for ID in self.states.values()}
        self.state_data = {ID: State_history() for ID in self.states.values()}
        # Setup events axis.
        if self.events:
            self.event_axis.getAxis('left').setTicks([[(i, n) for (n, i) in self.events.items()]])
            self.event_axis.setYRange(min(self.events.values()), max(self.events.values()), padding=0.2)
        # Setup analog axis.
        if self.analog_inputs:
            self.analog_axis.setVisible(True)
            self.analog_plots = {ai['ID']: self.analog_axis.plot(name=name,
                                 pen=pg.mkPen(pg.intColor(ai['ID'], len(self.analog_inputs))))
                                 for name, ai in self.analog_inputs.items()}
            self.analog_axis.getAxis('bottom').setLabel('Time (seconds)')
            self.event_axis.getAxis('bottom').setLabel('')
        else:
            self.analog_axis.setVisible(False)
            self.event_axis.getAxis('bottom').setLabel('Time (seconds)')

    def run_start(self):
        self.start_time = time.time()
        self.event_plot.clear()
        for state_plot in self.state_plots.values():
            state_plot.clear()
        if self.analog_inputs:
            for analog_plot in self.analog_plots.values():
                analog_plot.clear()
            self.analog_data = {ai['ID']: Analog_history(history_length=ai['Fs']*12)
                                for name, ai in self.analog_inputs.items()}
        self.current_state = None
        self.current_state_data = np.zeros([1,2])

    def process_data(self, new_data):
        # Update plots.
        run_time = time.time() - self.start_time
        self.state_axis.setRange(xRange=[run_time-10.5, run_time-0.5])
        # Plot new states or events.
        for nd in new_data:
            if nd[0] == 'D': # State entry or event.
                if nd[2] in self.states.values(): # State entry.
                    self.current_state = nd[2]
                    self.state_data[nd[2]].put(nd[1], nd[2]) # New state entry.
                    self.state_data[nd[2]].put(nd[1], nd[2]) # New state exit, overwritten each update.
                    self.current_state_data = self.state_data[nd[2]].get()
                else: # Event
                    self.event_plot.addPoints([{'pos':(nd[1]/1000, nd[2]),
                        'brush':pg.intColor(nd[2], self.n_colours)}])
            elif nd[0] == 'A': # Analog data chunk.
                ID, sampling_rate, timestamp, data_array = nd[1:]
                t = timestamp/1000 + np.arange(len(data_array))/sampling_rate
                self.analog_data[ID].put(np.vstack([t,data_array]))
                self.analog_plots[ID].setData(*self.analog_data[ID].history)
        # Extend current state.
        self.current_state_data[-1,0] = run_time
        self.state_plots[self.current_state].setData(
            *self.current_state_data.T, connect='pairs')


class State_history():
    # Class used to store the entry and exit times for given state.

    def __init__(self):
        self.data = np.empty([1000,2])
        self.i = 0
        self.len = self.data.shape[0]

    def put(self,timestamp, ID, replace=False):
        # Put new data into array expanding if necessary,
        if replace: # Replace previous sample.
            self.i -= 1
        self.data[self.i,:] = (timestamp/1000, ID)
        self.i += 1
        if self.i >= self.len: # Double array size.
            temp = self.data
            self.data = np.empty([self.len*2,2])
            self.data[:self.len] = temp
            self.len =self.len*2

    def get(self):
        # Get all valid data from array
        return self.data[:self.i,:]


class Analog_history():
    # Class used to store the history of an analog signal.

    def __init__(self, history_length, dtype=float):
        self.history = np.zeros([2, history_length], dtype)

    def put(self, new_data):
        # Move old data along buffer, store new data samples.
        data_len = new_data.shape[1]
        self.history = np.roll(self.history, -data_len, axis=1)
        self.history[:,-data_len:] = new_data

