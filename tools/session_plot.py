# Functions for visualising a pyControl session.
# (c) Thomas Akam 2018. Released under the GPL-3 open source licence.

import os
import numpy as np
import pylab as plt
from time import time
from matplotlib.animation import FuncAnimation

# session_plot -----------------------------------------------------------------------

def session_plot(file_path, fig_no=1, return_fig=False):
    '''Plot the states, events and analog data for a pyControl session.'''

    # Import data file.

    with open(file_path, 'r') as f:
        all_lines = [line.strip() for line in f.readlines() if line.strip()]

    # Import any analog files.

    file_dir  = os.path.dirname(file_path)
    file_name = os.path.split(file_path)[1]
    analog_files = [f for f in os.listdir(file_dir) if 
                    file_name.split('.')[0] in f and f != file_name]

    analog_data = {}

    for analog_file in analog_files:
        analog_name = analog_file[len(file_name.split('.')[0])+1:-4]
        with open(os.path.join(file_dir, analog_file), 'rb') as f:
            analog_data[analog_name] = np.fromfile(f, dtype='<i').reshape(-1,2)

    # Extract state entry and event times.

    states_dict = eval(next(line for line in all_lines if line[0]=='S')[2:])
    events_dict = eval(next(line for line in all_lines if line[0]=='E')[2:])

    ID2name = {v: k for k, v in {**states_dict, **events_dict}.items()}

    data_lines = [line[2:].split(' ') for line in all_lines if line[0]=='D']

    event_times = np.array([int(dl[0]) for dl in data_lines if int(dl[1]) in events_dict.values()])/1000 
    event_IDs   = np.array([int(dl[1]) for dl in data_lines if int(dl[1]) in events_dict.values()]) 

    state_times = np.array([int(dl[0]) for dl in data_lines if int(dl[1]) in states_dict.values()])/1000 
    state_IDs   = np.array([int(dl[1]) for dl in data_lines if int(dl[1]) in states_dict.values()]) 

    state_durations = np.diff(state_times)

    # Plotting

    fig = plt.figure(fig_no, figsize=[18,12])
    fig.clf()

    n_subplots = 3 if analog_data else 2

    # Plot states.

    ax1 = plt.subplot(n_subplots,1,1)
    plt.quiver(state_times[:-1], state_IDs[:-1], 
               state_durations, np.zeros(state_durations.shape), state_IDs[:-1], 
               cmap='gist_rainbow', headwidth=1, headlength=0, minlength=0, scale=1, 
               width=10, units='dots', scale_units='xy')
    ax1.set_yticks(sorted(states_dict.values()))
    ax1.set_yticklabels([ID2name[ID] for ID in sorted(states_dict.values())])
    ax1.set_ylim(min(states_dict.values())-0.5, max(states_dict.values())+0.5)
    ax1.set_facecolor('black')

    # Plot events.

    ax2 = plt.subplot(n_subplots,1,2, sharex=ax1)
    plt.scatter(event_times, event_IDs, c=event_IDs, s=6, cmap='gist_rainbow')
    ax2.set_yticks(sorted(events_dict.values()))
    ax2.set_yticklabels([ID2name[ID] for ID in sorted(events_dict.values())])
    ax2.set_ylim(min(events_dict.values())-0.5, max(events_dict.values())+0.5)
    ax2.set_facecolor('black')

    # Plot analog data

    if analog_data:
        ax3 = plt.subplot(n_subplots,1,3, sharex=ax1)
        for name, data in analog_data.items():
            plt.plot(data[:,0]/1000, data[:,1], label=name)
        ax3.set_facecolor('black')
        ax3.set_ylabel('Signal value')
        ax3.legend()

    ax1.set_xlim(0,state_times[-1])

    plt.xlabel('Time (seconds)')
    plt.tight_layout()

    if return_fig: # Return the figure and axes
        return fig, ax1

# play_session -----------------------------------------------------------------------

def play_session(file_path, start_time=0):
    '''Scrolling plot of states, events and analog data starting at start_time
    seconds after the session start.'''

    fig, ax1 = session_plot(file_path, return_fig=True)

    t_0 = time()

    def update(i):
        t = time() - t_0 + start_time
        #print('Frame rate: {:.2f}'.format(1/(t - ax1.get_xlim()[1])))
        ax1.set_xlim(t-10,t)
        return  ax1
 
    anim = FuncAnimation(fig, update, interval=5, repeat=False)
    
    plt.show()

    return anim