# A probabilistic reversal learning task in which the subject must initiate
# the trial in the center poke, then chose left or right pokes for a
# probabilistic reward.  The reward probabilities on the left and right side
# reverse once a moving average of choices crosses a threshold fraction
# correct, with a random delay between the treshold crossing and reversal.

from pyControl.utility import *
import hardware_definition as hw

# States and events.

states = [
    "init_trial",
    "choice_state",
    "left_reward",
    "right_reward",
    "inter_trial_interval",
]

events = [
    "left_poke",
    "center_poke",
    "right_poke",
    "session_timer",
]

initial_state = "init_trial"

# Parameters.

v.session_duration = 1 * hour  # Session duration.
v.reward_durations = [100, 100]  # Reward delivery duration (ms) [left, right].
v.ITI_duration = 1 * second  # Inter trial interval duration.
v.threshold = 0.75  # Performance treshold used for triggering reversal.
v.tau = 8  # Time constant for moving average of choices (trials).
v.trials_post_threshold = [5, 15]  # Trials after threshold crossing before reversal occurs [min, max].
v.good_prob = 0.8  # Reward probabilities on the good side.
v.bad_prob = 0.2  # Reward probabilities on the bad side.

# Variables.

v.n_rewards = 0  # Number of rewards obtained.
v.n_trials = 0  # Number of trials received.
v.n_blocks = 0  # Number of reversals.
v.good_side = choice(["left", "right"])  # Which side is currently good.
v.correct_mov_ave = Exp_mov_ave(tau=v.tau, init_value=0.5)  # Moving average of correct/incorrect choices
v.threshold_crossed = False  # Whether performance threshold has been crossed.
v.trials_till_reversal = 0  # Used after threshold crossing to trigger reversal.


# Non-state machine code.


def get_trial_outcome(chosen_side):
    # Function called after choice is made which determines trial outcome,
    # controls when reversals happen, and prints trial information.

    # Determine trial outcome.
    if chosen_side == v.good_side:  # Subject choose good side.
        v.outcome = withprob(v.good_prob)
        v.correct_mov_ave.update(1)

    else:
        v.outcome = withprob(v.bad_prob)
        v.correct_mov_ave.update(0)

    # Determine when reversal occurs.
    if v.threshold_crossed:  # Subject has already crossed threshold.
        v.trials_till_reversal -= 1
        if v.trials_till_reversal == 0:  # Trigger reversal.
            v.good_side = "left" if (v.good_side == "right") else "right"
            v.correct_mov_ave.value = 1 - v.correct_mov_ave.value
            v.threshold_crossed = False
            v.n_blocks += 1
    else:  # Check for threshold crossing.
        if v.correct_mov_ave.value > v.threshold:
            v.threshold_crossed = True
            v.trials_till_reversal = randint(*v.trials_post_threshold)

    # Print trial information.
    v.n_trials += 1
    v.n_rewards += v.outcome
    v.choice = chosen_side
    v.ave_correct = v.correct_mov_ave.value
    print_variables(["n_trials", "n_rewards", "n_blocks", "good_side", "choice", "outcome", "ave_correct"])
    return v.outcome


# Run start and stop behaviour.


def run_start():
    # Set session timer and turn on houslight.
    set_timer("session_timer", v.session_duration)
    hw.houselight.on()


def run_end():
    # Turn off all hardware outputs.
    hw.off()


# State behaviour functions.


def init_trial(event):
    # Turn on center Poke LED and wait for center poke.
    if event == "entry":
        hw.center_poke.LED.on()
    elif event == "exit":
        hw.center_poke.LED.off()
    elif event == "center_poke":
        goto_state("choice_state")


def choice_state(event):
    # Wait for left or right choice, evaluate if reward is delivered using get_trial_outcome function.
    if event == "entry":
        hw.left_poke.LED.on()
        hw.right_poke.LED.on()
    elif event == "exit":
        hw.left_poke.LED.off()
        hw.right_poke.LED.off()
    elif event == "left_poke":
        if get_trial_outcome("left"):
            goto_state("left_reward")
        else:
            goto_state("inter_trial_interval")
    elif event == "right_poke":
        if get_trial_outcome("right"):
            goto_state("right_reward")
        else:
            goto_state("inter_trial_interval")


def left_reward(event):
    # Deliver reward to left poke.
    if event == "entry":
        timed_goto_state("inter_trial_interval", v.reward_durations[0])
        hw.left_poke.SOL.on()
    elif event == "exit":
        hw.left_poke.SOL.off()


def right_reward(event):
    # Deliver reward to right poke.
    if event == "entry":
        timed_goto_state("inter_trial_interval", v.reward_durations[1])
        hw.right_poke.SOL.on()
    elif event == "exit":
        hw.right_poke.SOL.off()


def inter_trial_interval(event):
    # Go to init trial after specified delay.
    if event == "entry":
        timed_goto_state("init_trial", v.ITI_duration)


# State independent behaviour.


def all_states(event):
    # When 'session_timer' event occurs stop framework to end session.
    if event == "session_timer":
        stop_framework()
