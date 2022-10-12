from . import framework as fw

# Timer variables

active_timers = [] # list of event tuples: (trigger_time, event_type, data)

paused_timers = [] # list of event tuples: (trigger_time, event_type, data)

elapsed = False # Whether any timers have elapsed and need processing.

# Timer functions.

def reset():
    # Reset timer variables.
    global active_timers, paused_timers, elapsed
    active_timers = []
    paused_timers = []
    elapsed = False

def set(interval, event_type, event_data):
    # Set a timer to trigger specified event after 'interval' ms has elapsed.
    active_timers.append((fw.current_time+int(interval), event_type, event_data))
    active_timers.sort(reverse=True)

def check():
    #Check whether timers have triggered.
    global elapsed
    elapsed = bool(active_timers) and (active_timers[-1][0] <= fw.current_time)
    fw.check_timers = False

def get():
    # Get first timer event.
    global elapsed
    event_tuple = active_timers.pop()
    elapsed = bool(active_timers) and (active_timers[-1][0] <= fw.current_time)
    return event_tuple

def disarm(event_ID):
    # Remove all user timers with specified event_ID.
    global active_timers, paused_timers
    active_timers = [t for t in active_timers if not (t[2] == event_ID and (t[1] in (fw.event_typ, fw.timer_typ)))]
    paused_timers = [t for t in paused_timers if not  t[2] == event_ID]

def pause(event_ID):
    # Pause all user timers with specified event_ID.
    global active_timers, paused_timers
    paused_timers += [(t[0]-fw.current_time,t[1], t[2]) for t in active_timers
                      if (t[2] == event_ID and (t[1] in (fw.event_typ, fw.timer_typ)))]
    active_timers = [t for t in active_timers if not (t[2] == event_ID and (t[1] in (fw.event_typ, fw.timer_typ)))]

def unpause(event_ID):
    # Unpause user timers with specified event.
    global active_timers, paused_timers
    active_timers += [(t[0]+fw.current_time,t[1], t[2]) for t in paused_timers if t[2] == event_ID]
    paused_timers = [t for t in paused_timers if not t[2] == event_ID]
    active_timers.sort(reverse=True)

def remaining(event_ID):
    # Return time until timer for specified event elapses, returns 0 if no timer set for event.
    try:
        return next(
            t[0] - fw.current_time for t in reversed(active_timers) if (t[1] == fw.event_typ and t[2] == event_ID)
        )
    except StopIteration:
        return 0

def disarm_type(event_type):
    # Disarm all active timers of a particular type.
    global active_timers
    active_timers = [t for t in active_timers if not t[1] == event_type]