# !/usr/bin/python3
# -*- coding: utf-8 -*-

""" pycontrol.__main__

"""

import datetime
from pprint import pformat
from sys import exit
import shutil
import os
import logging
import loggingbootstrap

import pycontrol

import pycontrol.settings as settings

try:
    import pycontrol.config
except:
    exit("Config package not found. You can create this by copying the example_config and rename it to config.")

from pycontrol.config import experiments as exps
from pycontrol.config import config as cf

from pycontrol.entities.experiment import Experiment
from pycontrol.entities.boxes import HandlerBoxes

__version__ = pycontrol.__version__
__author__ = pycontrol.__author__
__credits__ = pycontrol.__credits__
__license__ = pycontrol.__license__
__maintainer__ = pycontrol.__maintainer__
__email__ = pycontrol.__email__
__status__ = pycontrol.__status__

CLIPBOARD_FEATURE = False

try:
    import pyperclip

    CLIPBOARD_FEATURE = True
except:
    print("pyperclip module not installed")


# ----------------------------------------------------------------------------------------
# Helper functions.
# ----------------------------------------------------------------------------------------

def config_menu():
    """

    :return:
    """
    print('Loading boxes listed in config.py...')
    boxes_handler = HandlerBoxes(cf.box_serials.keys())
    selection = None
    while selection != 0:
        print('Config menu:' \
              '\n1. Print info.' \
              '\n2. Update framework (overrides current framework).' \
              '\n3. Update hardware definition (overrides current hw definition).' \
              '\n4. Save hardware IDs.' \
              '\n5. Hard reset boxes.' \
              '\n6. Reset filesystems.' \
              '\n7. Reconnect.' \
              '\n8. Close program.' \
              '\n0. Exit config menu.')

        selection = int(input('Select option: '))

        if selection == 1:
            boxes_handler.info()
        if selection == 2:
            boxes_handler.update_framework(override=True)
        elif selection == 3:
            boxes_handler.update_hardware_definition()
        elif selection == 4:
            boxes_handler.save_unique_IDs()
        elif selection == 5:
            boxes_handler.hard_reset()
        elif selection == 6:
            boxes_handler.reset_filesystem()
        elif selection == 7:
            boxes_handler.reconnect()
            print("List of boxes: {0}".format(
                [(box.number, "connected={0}".format(box.is_connected())) for box in boxes_handler.boxes]))

        elif selection == 8:
            boxes_handler.close()
            exit()

    boxes_handler.close()


def select_experiment():
    """
    Show a list of available experiments
    :return: the experiment object corresponding to the selected experiment id
    """

    if hasattr(exps, 'experiments'):
        experiments = exps.experiments  # List of experiments specified in experiments.py
    else:
        experiments = [e for e in [getattr(exps, c) for c in dir(exps)]
                       if isinstance(e, Experiment)]  # Construct list of available experiments.

    selection = 0
    while selection == 0:

        print('Experiments available:')

        for i, exp in enumerate(experiments):
            print('Experiment number : {} | Name:  {}'.format(i + 1, exp.name))
            for box_n, subject_ID in exp.subjects.items():
                print('      Box : {}   {}'.format(box_n, subject_ID))

        selection = int(input('Enter number of experiment to run, for config options enter 0: '))
        if selection == 0:
            config_menu()

    return experiments[selection - 1]  # The selected experiment.


def run_hardware_test(boxes_handler):
    """
    Upload and run hardware on a list of boxes
    :param boxes_handler: handler for a list of boxes
    :type boxes_handler: pycontrol.entities.boxes.HandlerBoxes
    """
    hw_test_path = os.path.join(cf.tasks_dir, cf.hardware_test + '.py')
    boxes_handler.upload_task(hw_test_path)
    if cf.hardware_test_display_output:
        print('Press CTRL + C when finished with hardware test.')
        boxes_handler.run_framework()
    else:
        boxes_handler.start_framework(data_output=False)
        input('Press any key when finished with hardware test.')
        boxes_handler.stop_framework()


def upload_task(exp, boxes_handler):
    """
    Upload task of an experiment to a list of boxes
    :param exp:
    :param boxes:
    """
    task_path = os.path.join(cf.tasks_dir, exp.task + '.py')
    if not os.path.exists(task_path):
        logger.critical("Task path not found: {0}. You can copy a task file example from 'example_tasks'.".format(
            os.path.realpath(task_path)))
        exit()

    boxes_handler.upload_task(task_path)


def set_persistent_variables(experiment, boxes_handler, data_dir):
    """

    :return:
    """

    pv_folder = os.path.join(data_dir, 'persistent_variables')
    set_pv = []  # Subjects whose persistant variables have been set.
    for box_n, subject_ID in experiment.subjects.items():
        subject_pv_path = os.path.join(pv_folder, '{}.txt'.format(subject_ID))
        if os.path.exists(subject_pv_path):
            with open(subject_pv_path, 'r') as pv_file:
                pv_dict = eval(pv_file.read())
            for v_name, v_value in pv_dict.items():
                box = next((box for box in boxes_handler.boxes if box.number == box_n), None)
                if box is None:
                    logger.warning("Box not found with number: %s", box_n)
                else:
                    box.set_variable(v_name, v_value, experiment.task)
            set_pv.append(subject_ID)
    if len(set_pv) == experiment.n_subjects:
        print('set OK.')
    elif len(set_pv) == 0:
        print('not set as none found.')
    else:
        print('not found for subjects: {}'.format(set(experiment.subjects.values()) - set(set_pv)))

    return pv_folder


def store_persistent_variables(experiment, boxes_handler, pv_folder):
    """

    :return:
    """

    if not os.path.exists(pv_folder):
        os.mkdir(pv_folder)
    for box_n, subject_ID in experiment.subjects.items():
        pv_dict = {}
        for v_name in experiment.persistent_variables:
            box = next((box for box in boxes_handler.boxes if box.number == box_n), None)
            if box is None:
                logger.warning("Box not found with number: %s", box_n)
            else:
                pv_dict[v_name] = box.get_variable(v_name, experiment.task)
        subject_pv_path = os.path.join(pv_folder, '{}.txt'.format(subject_ID))
        with open(subject_pv_path, 'w') as pv_file:
            pv_file.write(pformat(pv_dict))


def collect_summary_data(experiment, boxes_handler):
    """

    :return:
    """

    spacing = 1  # Number of lines between summary data lines.
    if type(experiment.summary_data[-1]) == int:  # Use user defined spacing.
        spacing = experiment.summary_data[-1]
        experiment.summary_data = experiment.summary_data[:-1]
    summary_string = ''
    for v_name in experiment.summary_data:
        v_values = [str(box.get_variable(v_name, experiment.task)) + '\n' for box in boxes_handler.boxes]
        v_values[0] = v_values[0].replace('\n', '\t{}\n'.format(v_name.split('.')[-1]))
        v_values.append('\n' * spacing)  # Add empty lines between variables.
        summary_string += ''.join(v_values)

    return summary_string.strip()


def run_framework(boxes_handler, dur=None, verbose=False):
    """

    :param boxes_handler:
    :param dur:
    :param verbose:
    :return:
    """
    boxes_handler.open_data_file()
    boxes_handler.print_IDs()  # Print state and event information to file.
    boxes_handler.write_to_file('Run started at: ' + datetime.datetime.now().strftime('%H:%M:%S') + '\n\n')

    boxes_handler.start_framework(dur, verbose)
    try:
        while boxes_handler.process_data():
            pass

    except KeyboardInterrupt:
        boxes_handler.stop_framework()
        boxes_handler.process_data()  # process one last time

    except Exception as err:
        print(str(err))

    boxes_handler.close_data_file()


def check_config():
    """
    Ensure that paths on config file are valid
    :return:
    """
    tasks_path = cf.tasks_dir
    if not os.path.exists(tasks_path):
        logger.critical("Tasks path not found: {0}. Check your config file.".format(os.path.realpath(tasks_path)))
        exit()

    framework_path = cf.framework_dir
    if not os.path.exists(framework_path):
        logger.critical(
            "Framework path not found: {0}. Check your config file.".format(os.path.realpath(framework_path)))
        exit()

    hwdef_path = cf.hwd_path
    if not os.path.exists(hwdef_path):
        logger.critical(
            "HW definition path not found: {0}. Check your config file.".format(os.path.realpath(hwdef_path)))
        exit()

    data_dir_path = cf.data_dir
    if not os.path.exists(data_dir_path):
        logger.critical(
            "Data dir path not found: {0}. Check your config file.".format(os.path.realpath(data_dir_path)))
        exit()


def start():
    """
    Starts host console routine
    """

    date = datetime.date.today().strftime('-%Y-%m-%d')

    exp = select_experiment()

    data_dir = os.path.join(cf.data_dir, exp.folder)

    boxes_handler = HandlerBoxes(sorted(list(exp.subjects.keys())), exp, data_dir, date)
    boxes_handler.update_framework()

    if not boxes_handler.check_unique_IDs():
        input('Hardware ID check failed, press any key to close program.')
        boxes_handler.close()
        exit()

    if input('Run hardware test? (y / n)') == 'y':
        print('Uploading hardware test...')
        run_hardware_test(boxes_handler)
    else:
        print('Skipping hardware test.')

    print('Uploading task...')
    upload_task(exp, boxes_handler)

    if exp.set_variables:  # Set state machine variables from experiment specification.
        print('Setting state machine variables...')
        for v_name in exp.set_variables:
            boxes_handler.set_variable(v_name, exp.set_variables[v_name], exp.task)

    if exp.persistent_variables:
        print('Persistent variables ', end='')
        pv_folder = set_persistent_variables(exp, boxes_handler, data_dir)

    print("Showing events...")
    boxes_handler.print_events()

    print("Showing states...")
    boxes_handler.print_states()

    input('Hit enter to start exp. To quit at any time, hit ctrl + c.')
    run_framework(boxes_handler)

    # while loop until user cancels or timeout

    if exp.persistent_variables:
        print('Storing persistent variables...')
        store_persistent_variables(exp, boxes_handler, pv_folder)

    summary_data = None
    if exp.summary_data:
        summary_data = collect_summary_data(exp, boxes_handler)

    boxes_handler.close()

    if CLIPBOARD_FEATURE:
        if summary_data:
            input('Press any key to copy summary data to clipboard.')
            pyperclip.copy(summary_data)  # Copy to clipboard.
    else:
        print('Summary data not copied to clipboad as pyperclip not installed')

    if exp.transfer_folder:
        transfer_folder = exp.transfer_folder
    else:
        transfer_folder = cf.transfer_dir
    if transfer_folder:
        print('\nCopying files to transfer folder.')
        if not os.path.exists(transfer_folder):
            os.mkdir(transfer_folder)
        for file_path in boxes_handler.file_paths.values():
            shutil.copy2(file_path, transfer_folder)

    input('\nHit any key to close program.')


if __name__ == '__main__':
    loggingbootstrap.create_double_logger("pycontrol", settings.LOG_HANDLER_CONSOLE_LEVEL,
                                          settings.LOG_FILENAME, settings.LOG_HANDLER_FILE_LEVEL)

    logger = logging.getLogger("pycontrol")
    check_config()
    start()
