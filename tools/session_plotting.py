# Functions for visualising a pyControl session.
# (c) Thomas Akam 2018. Released under the GPL-3 open source licence.

import numpy as np
import pylab as plt
from time import time
from matplotlib.animation import FuncAnimation

# session_plot -----------------------------------------------------------------------

def session_plot(file_path, fig_no=1, return_fig=False):
    '''Plot the state and event times for a pyControl session.'''

    # Import data

    with open(file_path, 'r') as f:
        all_lines = [line.strip() for line in f.readlines() if line.strip()]

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

    # Plot states.

    ax1 = plt.subplot(2,1,2)
    plt.quiver(state_times[:-1], state_IDs[:-1], 
               state_durations, np.zeros(state_durations.shape), state_IDs[:-1], 
               cmap='gist_rainbow', headwidth=1, headlength=0, minlength=0, scale=1, 
               width=10, units='dots', scale_units='xy')
    ax1.set_yticks(sorted(states_dict.values()))
    ax1.set_yticklabels([ID2name[ID] for ID in sorted(states_dict.values())])
    ax1.set_ylim(min(states_dict.values())-0.5, max(states_dict.values())+0.5)
    ax1.set_facecolor('black')

    # Plot events.

    ax2 = plt.subplot(2,1,1, sharex = ax1)
    plt.scatter(event_times, event_IDs, c=event_IDs, s=6, cmap='gist_rainbow')
    ax2.set_yticks(sorted(events_dict.values()))
    ax2.set_yticklabels([ID2name[ID] for ID in sorted(events_dict.values())])
    ax2.set_ylim(min(events_dict.values())-0.5, max(events_dict.values())+0.5)
    ax2.set_facecolor('black')
    ax2.set_xlabel('Time (seconds)')

    plt.tight_layout()

    if return_fig: # Return the figure and axes
        return fig, ax1, ax2

# play_session -----------------------------------------------------------------------

def play_session(file_path, start_time=0):
    '''Scrolling plot of states and events starting at start_time seconds after 
    the session start.'''

    fig, ax1, ax2 = session_plot(file_path, return_fig=True)

    t_0 = time()

    def update(i):
        t = time() - t_0 + start_time
        ax1.set_xlim(t-10,t)
        return  ax1

    anim = FuncAnimation(fig, update, interval=50, repeat=False)
    
    plt.show()

    return anim