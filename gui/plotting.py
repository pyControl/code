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

        self.states_plot = States_plot(self)
        self.events_plot = Events_plot(self)
        self.analog_plot = Analog_plot(self)

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

    def run_start(self):
        self.start_time = time.time()
        self.states_plot.run_start()
        self.events_plot.run_start()
        self.analog_plot.run_start()

    def process_data(self, new_data):
        # Update plots.
        run_time = time.time() - self.start_time
        # Plot new states or events.
        self.states_plot.update(new_data, run_time)
        self.events_plot.update(new_data, run_time)
        self.analog_plot.update(new_data, run_time)


# States_plot --------------------------------------------------------

class States_plot():

    def __init__(self, parent=None, data_len=100):
        self.data_len = data_len
        self.axis = pg.PlotWidget(title='States')
        self.axis.setRange(xRange=[-10, 0])

    def set_state_machine(self, sm_info):
        self.state_IDs = list(sm_info['states'].values())
        self.axis.clear()
        self.axis.getAxis('left').setTicks([[(i, n) for (n, i) in sm_info['states'].items()]])
        self.axis.setYRange(min(self.state_IDs), max(self.state_IDs), padding=0.1)
        self.n_colours = len(sm_info['states'])+len(sm_info['events'])
        self.plots = {ID: self.axis.plot(pen=pg.mkPen(pg.intColor(ID, self.n_colours), width=3))
                      for ID in self.state_IDs}

    def run_start(self):
        self.data = np.zeros([self.data_len*2, 2], int)
        for plot in self.plots.values():
            plot.clear()
        self.cs = self.state_IDs[0]

    def update(self, new_data, run_time):
        new_states = [nd for nd in new_data if nd[0] == 'D' and nd[2] in self.state_IDs]
        # New state entries.
        updated_states = [self.cs]
        if new_states:
            n_new =len(new_states)
            self.data = np.roll(self.data, -2*n_new, axis=0)
            for i, ns in enumerate(new_states): # Update data array.
                timestamp, ID = ns[1:]
                updated_states.append(ID)
                j = 2*(-n_new+i)  # Index of state entry in self.data
                self.data[j-1:,0] = timestamp
                self.data[j:  ,1] = ID  
            self.cs = ID
        self.data[-1,0] = 1000*run_time # Update exit time of current state to current time.
        for us in updated_states: # Set data for updated state plots.
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
        self.data_len = data_len

    def set_state_machine(self, sm_info):
        self.event_IDs = list(sm_info['events'].values())
        self.axis.clear()
        if not self.event_IDs: return # State machine can have no events.
        self.axis.getAxis('left').setTicks([[(i, n) for (n, i) in sm_info['events'].items()]])
        self.axis.setYRange(min(self.event_IDs), max(self.event_IDs), padding=0.1)
        self.n_colours = len(sm_info['states'])+len(sm_info['events'])
        self.plot = self.axis.plot(pen=None, symbol='o', symbolSize=6, symbolPen=None)

    def run_start(self):
        if not self.event_IDs: return # State machine can have no events.
        self.plot.clear()
        self.data = np.zeros([self.data_len, 2])

    def update(self, new_data, run_time):
        if not self.event_IDs: return # State machine can have no events.
        new_events = [nd for nd in new_data if nd[0] == 'D' and nd[2] in self.event_IDs]
        # Add new events.
        if new_events:
            n_new = len(new_events)
            self.data = np.roll(self.data, -n_new, axis=0)
            for i, ne in enumerate(new_events):
                timestamp, ID = ne[1:]
                self.data[-n_new+i,0] = timestamp / 1000
                self.data[-n_new+i,1] = ID
        # Shift plot - should not need to setData but setPos does not cause redraw otherwise.
        self.plot.setData(self.data, symbolBrush=[pg.intColor(ID) for ID in self.data[:,1]])
        self.plot.setPos(-run_time, 0)

# ------------------------------------------------------------------------------------------

class Analog_plot():

    def __init__(self, parent=None, data_dur=10):
        self.data_dur = data_dur
        self.axis = pg.PlotWidget(title='Events')
        self.axis.addLegend(offset=(10, 10)) 

    def set_state_machine(self, sm_info):
        self.inputs = sm_info['analog_inputs']
        if not self.inputs: return # State machine may not have analog inputs.
        self.axis.clear()
        self.plots = {ai['ID']: self.axis.plot(name=name, 
                      pen=pg.mkPen(pg.intColor(ai['ID'],len(self.inputs)))) for name, ai in self.inputs.items()}
        self.axis.getAxis('bottom').setLabel('Time (seconds)')
        
    def run_start(self):
        if not self.inputs: return # State machine may not have analog inputs.
        for plot in self.plots.values():
            plot.clear()
        self.data = {ai['ID']: Analog_data(data_length=ai['Fs']*12) for name, ai in self.inputs.items()}

    def update(self, new_data, run_time):
        if not self.inputs: return # State machine may not have analog inputs.
        new_analog = [nd for nd in new_data if nd[0] == 'A']
        for na in new_analog:
            ID, sampling_rate, timestamp, data_array = na[1:]
            t = timestamp/1000 + np.arange(len(data_array))/sampling_rate
            self.data[ID].put(np.vstack([t,data_array]))
            self.plots[ID].setData(*self.data[ID].data)
        for plot in self.plots.values():
            plot.setPos(-run_time, 0)   

class Analog_data():
    # Class used to store data from an analog input.

    def __init__(self, data_length, dtype=float):
        self.data = np.zeros([2, data_length], dtype) # [timestamps, values]

    def put(self, new_data):
        # Move old data along buffer, store new data samples.
        data_len = new_data.shape[1]
        self.data = np.roll(self.data, -data_len, axis=1)
        self.data[:,-data_len:] = new_data

