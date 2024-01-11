import time
from datetime import timedelta
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtWidgets, QtCore
from source.gui.settings import get_setting
from source.gui.utility import detachableTabWidget
from source.communication.pycboard import MsgType

# ----------------------------------------------------------------------------------------
# Task_plot
# ----------------------------------------------------------------------------------------


class Task_plot(QtWidgets.QWidget):
    """Widget for plotting the states, events and analog inputs output by a state machine."""

    def __init__(self, parent=None):
        super(QtWidgets.QWidget, self).__init__(parent)

        # Create widgets
        self.states_plot = States_plot(self, data_len=get_setting("plotting", "state_history_len"))
        self.events_plot = Events_plot(self, data_len=get_setting("plotting", "event_history_len"))
        self.analog_plot = Analog_plot(self, data_dur=get_setting("plotting", "analog_history_dur"))
        self.run_clock = Run_clock(self.states_plot.axis)

        # Setup plots
        self.pause_button = QtWidgets.QPushButton()
        self.pause_button.setEnabled(False)
        self.pause_button.setCheckable(True)
        self.events_plot.axis.setXLink(self.states_plot.axis)
        self.analog_plot.axis.setXLink(self.states_plot.axis)
        self.analog_plot.axis.setVisible(False)

        # create layout

        self.layout = QtWidgets.QGridLayout()
        self.layout.addWidget(self.states_plot.axis, 0, 0, 1, 3)
        self.layout.addWidget(self.events_plot.axis, 1, 0, 1, 3)
        self.layout.addWidget(self.analog_plot.axis, 2, 0, 1, 3)
        self.layout.addWidget(self.pause_button, 3, 0, 1, 3, QtCore.Qt.AlignmentFlag.AlignCenter)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.pause_button.clicked.connect(self.update_pause_btn_text)
        self.update_pause_btn_text()

    def set_state_machine(self, sm_info):
        # Initialise plots with state machine information.
        self.axiswidth = 6 + 6 * max([len(n) for n in list(sm_info.states) + list(sm_info.events)])
        self.states_plot.set_state_machine(sm_info)
        self.events_plot.set_state_machine(sm_info)
        self.analog_plot.set_state_machine(sm_info)
        if self.analog_plot.inputs:
            self.analog_plot.axis.setVisible(True)
            self.events_plot.axis.getAxis("bottom").setLabel("")
            self.layout.setRowStretch(0, 1)
            self.layout.setRowStretch(1, 1)
            self.layout.setRowStretch(2, 1)
        else:
            self.analog_plot.axis.setVisible(False)
            self.events_plot.axis.getAxis("bottom").setLabel("Time (seconds)")
            self.layout.setRowStretch(0, 1)
            self.layout.setRowStretch(1, 1)
            self.layout.setRowStretch(2, 0)

    def run_start(self, recording):
        self.pause_button.setChecked(False)
        self.pause_button.setEnabled(True)
        self.update_pause_btn_text()
        self.start_time = time.time()
        self.states_plot.run_start()
        self.events_plot.run_start()
        self.analog_plot.run_start()
        if recording:
            self.run_clock.recording()

    def run_stop(self):
        self.pause_button.setEnabled(False)
        self.run_clock.run_stop()

    def process_data(self, new_data):
        """Store new data from board."""
        self.states_plot.process_data(new_data)
        self.events_plot.process_data(new_data)
        self.analog_plot.process_data(new_data)

    def update(self):
        """Update plots."""
        if not self.pause_button.isChecked():
            run_time = time.time() - self.start_time
            self.states_plot.update(run_time)
            self.events_plot.update(run_time)
            self.analog_plot.update(run_time)
            self.run_clock.update(run_time)

    def update_pause_btn_text(self):
        if self.pause_button.isChecked():
            self.pause_button.setText("Resume plotting")
            self.pause_button.setIcon(QtGui.QIcon("source/gui/icons/play.svg"))
        else:
            self.pause_button.setText("Pause plotting")
            self.pause_button.setIcon(QtGui.QIcon("source/gui/icons/pause.svg"))


# States_plot --------------------------------------------------------


class States_plot:
    def __init__(self, parent=None, data_len=100):
        self.task_plot = parent
        self.data_len = data_len
        self.axis = pg.PlotWidget(title="States")
        self.axis.showAxis("right")
        self.axis.hideAxis("left")
        self.axis.setRange(xRange=[-10.2, 0], padding=0)
        self.axis.setMouseEnabled(x=True, y=False)
        self.axis.showGrid(x=True, alpha=0.75)
        self.axis.setLimits(xMax=0)

    def set_state_machine(self, sm_info):
        self.state_IDs = list(sm_info.states.values())
        self.axis.clear()
        self.axis.getAxis("right").setTicks([[(i, n) for (n, i) in sm_info.states.items()]])
        self.axis.setYRange(min(self.state_IDs), max(self.state_IDs), padding=0.1)
        self.n_colours = len(sm_info.states) + len(sm_info.events)
        self.plots = {
            ID: self.axis.plot(pen=pg.mkPen(pg.intColor(ID, self.n_colours), width=3)) for ID in self.state_IDs
        }
        self.axis.getAxis("right").setWidth(self.task_plot.axiswidth)
        self.axis.getAxis("right").setStyle(hideOverlappingLabels=False)

    def run_start(self):
        self.data = np.zeros([self.data_len * 2, 2], int)
        for plot in self.plots.values():
            plot.setData(x=[], y=[])

    def process_data(self, new_data):
        """Store new data from board"""
        new_states = [nd for nd in new_data if nd.type == MsgType.STATE]
        if new_states:
            n_new = len(new_states)
            self.data = np.roll(self.data, -2 * n_new, axis=0)
            for i, nd in enumerate(new_states):  # Update data array.
                j = 2 * (-n_new + i)  # Index of state entry in self.data
                self.data[j - 1 :, 0] = nd.time
                self.data[j:, 1] = nd.content

    def update(self, run_time):
        """Update plots."""
        self.data[-1, 0] = run_time * 1000  # Update exit time of current state to current time.
        for ID in self.state_IDs:
            state_data = self.data[self.data[:, 1] == ID, :]
            timestamps, IDs = (state_data[:, 0] / 1000 - run_time, state_data[:, 1])
            if timestamps.size > 0:
                self.plots[ID].setData(x=timestamps, y=IDs, connect="pairs")


# Events_plot--------------------------------------------------------


class Events_plot:
    def __init__(self, parent=None, data_len=100):
        self.task_plot = parent
        self.axis = pg.PlotWidget(title="Events")
        self.axis.showAxis("right")
        self.axis.hideAxis("left")
        self.axis.setRange(xRange=[-10.2, 0], padding=0)
        self.axis.setMouseEnabled(x=True, y=False)
        self.axis.showGrid(x=True, alpha=0.75)
        self.axis.setLimits(xMax=0)
        self.event_IDs = []
        self.data_len = data_len

    def set_state_machine(self, sm_info):
        self.event_IDs = list(sm_info.events.values())
        self.axis.clear()
        self.axis.getAxis("right").setTicks([[(i, n) for (n, i) in sm_info.events.items()]])
        self.axis.getAxis("right").setStyle(hideOverlappingLabels=False)
        self.axis.getAxis("right").setWidth(self.task_plot.axiswidth)
        if self.event_IDs:  # Task has events.
            self.axis.setYRange(min(self.event_IDs), max(self.event_IDs), padding=0.1)
            self.n_colours = len(sm_info.states) + len(sm_info.events)
            self.plot = self.axis.plot(pen=None, symbol="o", symbolSize=6, symbolPen=None)

    def run_start(self):
        if not self.event_IDs:
            return  # State machine can have no events.
        self.plot.clear()
        self.data = np.zeros([self.data_len, 2])

    def process_data(self, new_data):
        """Store new data from board."""
        if not self.event_IDs:
            return  # State machine can have no events.
        new_events = [nd for nd in new_data if nd.type == MsgType.EVENT]
        if new_events:
            n_new = len(new_events)
            self.data = np.roll(self.data, -n_new, axis=0)
            for i, nd in enumerate(new_events):
                self.data[-n_new + i, 0] = nd.time / 1000
                self.data[-n_new + i, 1] = nd.content

    def update(self, run_time):
        """Update plots"""
        if not self.event_IDs:
            return
        self.plot.setData(
            x=self.data[:, 0] - run_time,
            y=self.data[:, 1],
            symbolBrush=[pg.intColor(ID) for ID in self.data[:, 1]],
        )


# ------------------------------------------------------------------------------------------


class Analog_plot:
    def __init__(self, parent=None, data_dur=10):
        self.task_plot = parent
        self.data_dur = data_dur
        self.axis = pg.PlotWidget(title="Analog")
        self.axis.showAxis("right")
        self.axis.hideAxis("left")
        self.axis.setRange(xRange=[-10.2, 0], padding=0)
        self.axis.setMouseEnabled(x=True, y=False)
        self.axis.showGrid(x=True, alpha=0.75)
        self.axis.setLimits(xMax=0)
        self.inputs = {}

    def set_state_machine(self, sm_info):
        self.inputs = {ID: ai for ID, ai in sm_info.analog_inputs.items() if ai["plot"]}
        if not self.inputs:
            return  # State machine may not have analog inputs.
        self.axis.clear()
        self.legend = self.axis.addLegend(offset=(10, 10))
        self.plots = {
            ID: self.axis.plot(name=ai["name"], pen=pg.mkPen(pg.intColor(i, len(self.inputs))))
            for i, (ID, ai) in enumerate(sorted(self.inputs.items()))
        }
        self.axis.getAxis("bottom").setLabel("Time (seconds)")
        self.axis.getAxis("right").setWidth(self.task_plot.axiswidth)

    def run_start(self):
        if not self.inputs:
            return  # State machine may not have analog inputs.
        for plot in self.plots.values():
            plot.clear()
        self.data = {ID: np.zeros([ai["fs"] * self.data_dur, 2]) for ID, ai in self.inputs.items()}
        self.updated_inputs = []

    def process_data(self, new_data):
        """Store new data from board."""
        if not self.inputs:
            return  # State machine may not have analog inputs.
        new_analog = [nd for nd in new_data if nd.type == MsgType.ANLOG]
        for na in new_analog:
            ID, data = na.content
            if ID in self.plots.keys():
                new_len = len(data)
                t = na.time / 1000 + np.arange(new_len) / self.inputs[ID]["fs"]
                self.data[ID] = np.roll(self.data[ID], -new_len, axis=0)
                self.data[ID][-new_len:, :] = np.vstack([t, data]).T

    def update(self, run_time):
        """Update plots."""
        if not self.inputs:
            return  # State machine may not have analog inputs.
        for ID in self.inputs.keys():
            self.plots[ID].setData(x=self.data[ID][:, 0] - run_time, y=self.data[ID][:, 1])


# -----------------------------------------------------


class Run_clock:
    # Class for displaying the run time.

    def __init__(self, axis):
        self.clock_text = pg.TextItem(text="")
        self.clock_text.setFont(QtGui.QFont("arial", 11, QtGui.QFont.Weight.Bold))
        axis.getViewBox().addItem(self.clock_text, ignoreBounds=True)
        self.clock_text.setParentItem(axis.getViewBox())
        self.clock_text.setPos(10, -5)
        self.recording_text = pg.TextItem(text="", color=(255, 0, 0))
        self.recording_text.setFont(QtGui.QFont("arial", 12, QtGui.QFont.Weight.Bold))
        axis.getViewBox().addItem(self.recording_text, ignoreBounds=True)
        self.recording_text.setParentItem(axis.getViewBox())
        self.recording_text.setPos(80, -5)

    def update(self, run_time):
        self.clock_text.setText(str(timedelta(seconds=run_time))[:7])

    def recording(self):
        self.recording_text.setText("Recording")

    def run_stop(self):
        self.clock_text.setText("")
        self.recording_text.setText("")


# --------------------------------------------------------------------------------
# Experiment plotter
# --------------------------------------------------------------------------------


class Experiment_plot(QtWidgets.QMainWindow):
    """Window for plotting data during experiment run where each subjects plots
    are displayed in a seperate tab."""

    def __init__(self, parent=None):
        super(QtWidgets.QWidget, self).__init__(parent)
        self.setWindowTitle("Experiment plot")
        self.setGeometry(720, 30, 700, 800)  # Left, top, width, height.
        self.subject_tabs = detachableTabWidget(self)
        self.setCentralWidget(self.subject_tabs)
        self.subject_plots = {}
        self.running_subjects = []

    def setup_experiment(self, experiment):
        """Create task plotters in seperate tabs for each subject."""
        subject_dict = experiment.subjects
        subjects = list(experiment.subjects.keys())
        subjects.sort(key=lambda s: experiment.subjects[s]["setup"])
        for subject in subjects:
            self.subject_plots[subject] = Task_plot(self)
            self.subject_tabs.addTab(self.subject_plots[subject], f"{subject_dict[subject]['setup']} : {subject}")

    def set_state_machine(self, sm_info):
        """Provide the task plotters with the state machine info."""
        for subject_plot in self.subject_plots.values():
            subject_plot.set_state_machine(sm_info)

    def run_start(self, subject):
        self.subject_plots[subject].run_start(False)
        self.running_subjects.append(subject)

    def run_stop(self, subject):
        self.running_subjects.remove(subject)

    def close_experiment(self):
        """Remove and delete all subject plot tabs."""
        for subject_plot in self.subject_plots.values():
            subject_plot.setParent(None)
            subject_plot.deleteLater()
        self.subject_tabs.closeDetachedTabs()
        self.subject_plots.clear()
        self.close()

    def update(self):
        """Update the plots of the active tab."""
        for subject in self.running_subjects:
            if not self.subject_plots[subject].visibleRegion().isEmpty():
                self.subject_plots[subject].update()
