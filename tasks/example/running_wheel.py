# Example of using a rotary encoder to measure running speed and trigger events when
# running starts and stops. The subject must run for 10 seconds to trigger reward delivery,
# then stop running for 5 seconds to initiate the next trial.
# If while running the subject exceeds a bonus velocity threshold, they earn a bonus
# and the reward duration is extended by a bonus duration.

from pyControl.utility import *
from devices import *
from pyControl.hardware import Analog_threshold

# Variables.

v.run_time = 10 * second  # Time subject must run to obtain reward.
v.stop_time = 5 * second  # Time subject must stop running to intiate the next trial.
v.reward_duration = 100 * ms  # Time reward solenoid is open for.
v.velocity_threshold = 100  # Minimum encoder velocity treated as running (encoder counts/second).
v.bonus_velocity_threshold = 5000  # Encoder velocity that triggers bonus reward (encoder counts/second).
v.give_bonus = False  # Whether to give bonus reward.
v.bonus_reward_duration = 50 * ms  # Time to add to reward duration if bonus is earned.

running_trigger = Analog_threshold(
    threshold=v.velocity_threshold,
    rising_event="started_running",
    falling_event="stopped_running",
)

bonus_trigger = Analog_threshold(
    threshold=v.bonus_velocity_threshold,
    rising_event="bonus_earned",
)
# Instantiate hardware - would normally be in a seperate hardware definition file.

board = Breakout_1_2()  # Breakout board.


running_wheel = Rotary_encoder(
    name="running_wheel",
    sampling_rate=100,
    output="velocity",
    triggers=[running_trigger, bonus_trigger],
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
    "bonus_earned",
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
        v.give_bonus = False
        set_timer("run_timer", v.run_time)
    elif event == "stopped_running":
        disarm_timer("run_timer")
        goto_state("trial_start")
    elif event == "bonus_earned":
        v.give_bonus = True
    elif event == "run_timer":
        goto_state("reward")


def reward(event):
    # Deliver reward then go to inter trial interval.
    if event == "entry":
        timed_goto_state("inter_trial_interval", v.reward_duration + v.bonus_reward_duration * v.give_bonus)
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
