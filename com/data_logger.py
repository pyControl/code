import os
import json
from datetime import datetime
from shutil import copyfile

class Data_logger():
    '''Class for logging data from a pyControl setup to disk'''

    def __init__(self, sm_info=None, print_func=None, data_consumers=[]):
        self.data_file = None
        self.analog_files = {}
        self.print_func = print_func
        self.data_consumers = data_consumers
        if sm_info:
            self.set_state_machine(sm_info)

    def set_state_machine(self, sm_info):
        self.sm_info = sm_info
        self.ID2name_fw = self.sm_info['ID2name']      # Dict mapping framework IDs to names.
        self.ID2name_hw = {ai['ID']: name for name, ai # Dict mapping hardware IDs to names.
                           in self.sm_info['analog_inputs'].items()}
        self.analog_files = {ai['ID']: None for ai in self.sm_info['analog_inputs'].values()}

    def open_data_file(self, data_dir, experiment_name, setup_ID, subject_ID, datetime_now=None):
        '''Open data file and write header information.'''
        self.file_type = 'tsv'
        self.data_dir = data_dir
        self.experiment_name = experiment_name
        self.subject_ID = subject_ID
        self.setup_ID = setup_ID
        if datetime_now is None: datetime_now = datetime.now()
        file_name = self.subject_ID + datetime_now.strftime('-%Y-%m-%d-%H%M%S') + '.' + self.file_type
        self.file_path = os.path.join(self.data_dir, file_name)
        self.data_file = open(self.file_path, 'w', newline = '\n')
        if self.file_type == 'tsv': # Write header.
            self.data_file.write(self.tsv_row_str(
                rtype='type', time='time', name='name', value='value'))
        self.write_info_line('Experiment name', self.experiment_name)
        self.write_info_line('Task name', self.sm_info['name'])
        self.write_info_line('Task file hash', self.sm_info['task_hash'])
        self.write_info_line('Setup ID', self.setup_ID)
        self.write_info_line('Framework version', self.sm_info['framework_version'])
        self.write_info_line('Micropython version', self.sm_info['micropython_version'])
        self.write_info_line('Subject ID', self.subject_ID)
        self.write_info_line('Start date', datetime_now.strftime('%Y/%m/%d %H:%M:%S'))
        if self.file_type == 'txt':
            self.data_file.write('\n')
            self.data_file.write('S {}\n\n'.format(json.dumps(self.sm_info['states'])))
            self.data_file.write('E {}\n\n'.format(json.dumps(self.sm_info['events'])))

    def write_info_line(self, name, value):
        if self.file_type == 'tsv':
            name = name.lower().replace(' ', '_')
            self.data_file.write(self.tsv_row_str('info', name=name, value=value))
        elif self.file_type == 'txt':
            self.data_file.write(f'I {name} : {value}\n')

    def tsv_row_str(self, rtype, time='', name='', value=''):
        return f'{rtype}\t{time}\t{name}\t{value}\n'

    def copy_task_file(self, data_dir, tasks_dir, dir_name='task_files'):
        '''If not already present, copy task file to data_dir/dir_name
        appending the files djb2 hash to the file name.'''
        exp_tasks_dir = os.path.join(data_dir, dir_name)
        if not os.path.exists(exp_tasks_dir):
            os.mkdir(exp_tasks_dir)
        task_file_path = os.path.join(tasks_dir, self.sm_info['name']+'.py')
        task_save_name = os.path.split(self.sm_info['name'])[1] +'_{}.py'.format(self.sm_info['task_hash'])
        if not task_save_name in os.listdir(exp_tasks_dir):
            copyfile(task_file_path, os.path.join(exp_tasks_dir, task_save_name))
            
    def close_files(self):
        if self.data_file:
            self.data_file.close()
            self.data_file = None
            self.file_path = None
        for analog_file in self.analog_files.values():
            if analog_file:
                analog_file.close()
                analog_file = None

    def process_data(self, new_data):
        '''If data _file is open new data is written to file.  If print_func is specified
        human readable data strings are passed to it.'''
        if self.data_file:
            self.write_to_file(new_data)
        if self.print_func:
            self.print_func(self.data_to_string(new_data, verbose=True), end='')
        if self.data_consumers:
            for data_consumer in self.data_consumers:
                data_consumer.process_data(new_data)

    def write_to_file(self, new_data):
        data_string = self.data_to_string(new_data)
        if data_string:
            self.data_file.write(data_string)
            self.data_file.flush()
        for nd in new_data:
            if nd[0] == 'A':
                self.save_analog_chunk(*nd[1:]) 

    def data_to_string(self, new_data, verbose=False):
        '''Convert list of data tuples into a string.  If verbose=True state and event names are used,
        if verbose=False state and event IDs are used.'''
        for nd in new_data:
            if self.file_type == 'txt' or verbose: 
                if nd[0] == 'D':  # State entry or event.
                        if verbose: # Print state or event name.
                            data_string = f'D {nd[1]} {self.ID2name_fw[nd[2]]}\n'
                        else:       # Print state or event ID.
                            data_string = f'D {nd[1]} {nd[2]}\n'
                elif nd[0] in ('P', 'V'): # User print output or set variable.
                    data_string = '{} {} {}\n'.format(*nd)
                elif nd[0] == '!': # Warning
                    data_string = f'! {nd[1]}\n'
                elif nd[0] == '!!': # Crash traceback.
                    error_string = nd[1]
                    if not verbose: # In data files multi-line tracebacks have ! prepended to all lines aid parsing data file.
                        error_string = '! ' + error_string.replace('\n', '\n! ')
                    data_string = '\n' + error_string + '\n'
            elif self.file_type == 'tsv':
                if nd[0] == 'D':  # State entry or event.
                    if nd[2] in self.sm_info['states'].keys():
                        data_string = self.tsv_row_str('state', time=nd[1], name=self.ID2name_fw[nd[2]])
                    else:
                        data_string = self.tsv_row_str('event', time=nd[1], name=self.ID2name_fw[nd[2]])
                elif nd[0] == 'P': # User print output.
                    data_string = self.tsv_row_str('print', time=nd[1], value=nd[2])
                elif nd[0] == 'V': # Variable.
                    data_string = self.tsv_row_str('variable', time=nd[1], value=nd[2])
                elif nd[0] == '!': # Warning
                    data_string = self.tsv_row_str('warning', value=nd[1])
                elif nd[0] == '!!': # Error
                    data_string = self.tsv_row_str('error', value=nd[1].replace('\n','|'))
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