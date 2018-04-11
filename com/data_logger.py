import os
from datetime import datetime

class Data_logger():
    '''Class for logging data from a pyControl setup to disk'''

    def __init__(self, data_dir, experiment_name, task_name, sm_info):
        self.data_dir = data_dir
        self.experiment_name = experiment_name
        self.task_name = task_name
        self.sm_info = sm_info
        self.ID2name_fw = {ID: name for name, ID       # Dict mapping framework IDs to names.
                           in {**self.sm_info['states'], **self.sm_info['events']}.items()}
        self.ID2name_hw = {ai['ID']: name for name, ai # Dict mapping hardware IDs to names.
                           in self.sm_info['analog_inputs'].items()}
        self.data_file = None
        self.analog_files = {ai['ID']: None for ai in self.sm_info['analog_inputs'].values()}

    def open_data_file(self, subject_ID,  datetime_now=None):
        '''Open data file and write header information.'''
        if datetime_now is None: datetime_now = datetime.now()
        self.subject_ID = subject_ID
        file_name = os.path.join(self.subject_ID + datetime_now.strftime('-%Y-%m-%d-%H%M%S') + '.txt')
        self.file_path = os.path.join(self.data_dir, file_name)
        self.data_file = open(self.file_path, 'w', newline = '\n')
        self.data_file.write('I Experiment name  : {}\n'.format(self.experiment_name))
        self.data_file.write('I Task name : {}\n'.format(self.task_name))
        self.data_file.write('I Subject ID : {}\n'.format(self.subject_ID))
        self.data_file.write('I Start date : ' + datetime_now.strftime('%Y/%m/%d %H:%M:%S') + '\n\n')
        self.data_file.write('S {}\n\n'.format(self.sm_info['states'] ))
        self.data_file.write('E {}\n\n'.format(self.sm_info['events'] ))

    def close_files(self):
        if self.data_file:
            self.data_file.close()
            self.data_file = None
            self.file_path = None
        for analog_file in self.analog_files.values():
            if analog_file:
                analog_file.close()
                analog_file = None

    def write_to_file(self, new_data):
        data_string = self.data_to_string(new_data)
        if data_string:
            self.data_file.write(data_string)
        for nd in new_data:
            if nd[0] == 'A':
                self.save_analog_chunk(*nd[1:]) 

    def data_to_string(self, new_data, verbose=False):
        data_string = ''
        for nd in new_data:
            if nd[0] == 'D':  # State entry or event.
                    if verbose: # Print state or event name.
                        data_string += 'D {} {}\n'.format(nd[1], self.ID2name_fw[nd[2]])
                    else:       # Print state or event ID.
                        data_string += 'D {} {}\n'.format(nd[1], nd[2])
            elif nd[0] in ('P', 'V'): # User print output or set variable.
                data_string += '{} {} {}\n'.format(*nd)
            elif nd[0] == '!': # Error
                error_string = nd[1]
                data_string += '! ' + error_string.replace('\n', '\n! ') + '\n'
        return data_string

    def save_analog_chunk(self, ID, sampling_rate, timestamp, data_array):
        '''Save a chunk of analog data to .pca data file.  File is created if not 
        already open for that analog input.'''
        if not self.analog_files[ID]:
            file_name = os.path.splitext(self.file_path)[0] + '_' + \
                            self.ID2name_hw[ID] + '.pca'
            self.analog_files[ID] = open(file_name, 'wb')
        ms_per_sample = 1000 / sampling_rate
        for i, x in enumerate(data_array):
            t = int(timestamp + i*ms_per_sample)
            self.analog_files[ID].write(t.to_bytes(4,'little', signed=True))
            self.analog_files[ID].write(x.to_bytes(4,'little', signed=True))
        self.analog_files[ID].flush()