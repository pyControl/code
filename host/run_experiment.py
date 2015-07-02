from experiments import experiments
from boxes import Boxes
import datetime
from config import *

date = datetime.date.today().strftime('-%Y-%m-%d')

print('Experiments available:\n')

for i, exp in enumerate(experiments):
  print('\nExperiment number : {}  Name:  {}\n'.format(i, exp.name))
  for bx in exp.subjects:
    print('    Box : {}   '.format(bx) + exp.subjects[bx])

experiment = experiments[int(input('\n\nEnter which experiment to run: '))]

boxes_to_use = experiment.subjects.keys()

file_names = {box_n: experiment.subjects[box_n] + date + '.txt' for box_n in boxes_to_use}

boxes = Boxes(boxes_to_use, experiment.hardware)

if input('\nRun hardware test (y / n)\n') == 'y':
	print('Uploading hardware test.')
	# !! upload hardware test to boxes.
	boxes.start_framework(data_output = False)
	input('\nPress any key when finished with hardware test.\n')
	boxes.stop_framework()
else:
	print('Skipping hardware test.')

print('Uploading task.')

boxes.setup_state_machine(experiment.task)
# !! Set variables.
boxes.open_data_file(file_names)
# !! Print state and event info to data files.

input('\nHit enter to start experiment. To quit at any time, hit ctrl + c.\n\n')

boxes.start_framework(dur = None, verbose = True)

try:
    while True:  # Read data untill interupted by user.
        boxes.process_data()
    
except KeyboardInterrupt:
    boxes.stop_framework()
    boxes.close_data_file()
    boxes.close()
    # !! transfer files as necessary.
















