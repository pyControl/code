# Example of using a rotary encoder to measure running speed and trigger events when
# running starts and stops. The subject must run for 10 seconds to trigger reward delivery,
# then stop running for 5 seconds to initiate the next trial.

from pyControl.utility import *
from devices import *

# Variables.

v.run_time = 10 * second  # Time subject must run to obtain reward.
v.stop_time = 5 * second  # Time subject must stop running to intiate the next trial.
v.reward_duration = 100 * ms  # Time reward solenoid is open for.
v.velocity_threshold = 100  # Minimum encoder velocity treated as running (encoder counts/second).

# Instantiate hardware - would normally be in a seperate hardware definition file.

board = Breakout_1_2()  # Breakout board.


running_wheel = Rotary_encoder(
    name="running_wheel",
    sampling_rate=100,
    output="velocity",
    threshold=v.velocity_threshold,
    rising_event="started_running",
    falling_event="stopped_running",
)  # Running wheel must be plugged into port 1 of breakout board.

solenoid = Digital_output(board.port_2.POW_A)  # Reward delivery solenoid.

# States and events.

states = [
    "trial_start",
    "running_for_reward",
    "reward",
    "inter_trial_interval",
]

events = [
    "started_running",
    "stopped_running",
    "run_timer",
    "stopped_timer",
    "reward_timer",
]

initial_state = "trial_start"

# Run start behaviour.


def run_start():
    running_wheel.record()  # Start streaming wheel velocity to computer.


# State behaviour functions.


def trial_start(event):
    # Go to 'running_for_reward' state when subject starts running.
    if event == "entry" and (running_wheel.velocity > v.velocity_threshold):
        # Subject already running when state entered.
        goto_state("running_for_reward")
    elif event == "started_running":
        goto_state("running_for_reward")


def running_for_reward(event):
    # If subject runs for long enough go to reward state.
    # If subject stops go back to trial start.
    if event == "entry":
        set_timer("run_timer", v.run_time)
    elif event == "stopped_running":
        disarm_timer("run_timer")
        goto_state("trial_start")
    elif event == "run_timer":
        goto_state("reward")


def reward(event):
    # Deliver reward then go to inter trial interval.
    if event == "entry":
        timed_goto_state("inter_trial_interval", v.reward_duration)
        solenoid.on()
    elif event == "exit":
        solenoid.off()


def inter_trial_interval(event):
    # Go to trial start after subject stops running for stop_time seconds.
    if event == "entry" and (running_wheel.velocity < v.velocity_threshold):
        set_timer("stopped_timer", v.stop_time)
    elif event == "started_running":
        disarm_timer("stopped_timer")
    elif event == "stopped_running":
        set_timer("stopped_timer", v.stop_time)
    elif event == "stopped_timer":
        goto_state("trial_start")
