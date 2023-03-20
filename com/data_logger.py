import os
import json
import numpy as np
from datetime import datetime
from shutil import copyfile

class Data_logger():
    '''Class for logging data from a pyControl setup to disk'''

    def __init__(self, sm_info=None, print_func=None, data_consumers=[]):
        self.data_file = None
        self.analog_writers = {}
        self.print_func = print_func
        self.data_consumers = data_consumers
        if sm_info:
            self.set_state_machine(sm_info)

    def set_state_machine(self, sm_info):
        self.sm_info = sm_info
        self.ID2name_fw = self.sm_info['ID2name'] # Dict mapping framework IDs to names.
        
    def open_data_file(self, data_dir, experiment_name, setup_ID, subject_ID,
                       file_type, datetime_now=None):
        '''Open file tsv/txt file for event data and write header information.
        If state machine uses analog inputs instantiate analog data writers.'''
        self.data_dir = data_dir
        self.experiment_name = experiment_name
        self.subject_ID = subject_ID
        self.setup_ID = setup_ID
        self.file_type = file_type
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
        self.analog_writers = {ID: 
            Analog_writer(ai['name'], ai['fs'], ai['dtype'], self.file_path)
            for ID, ai in self.sm_info['analog_inputs'].items()}

    def write_info_line(self, name, value):
        if self.file_type == 'tsv':
            name = name.lower().replace(' ', '_')
            self.data_file.write(self.tsv_row_str('info', name=name, value=value))
        elif self.file_type == 'txt':
            self.data_file.write(f'I {name} : {value}\n')

    def tsv_row_str(self, rtype, time='', name='', value=''):
        time_str = f'{time/1000:.3f}' if type(time) == int else time
        return f'{time_str}\t{rtype}\t{name}\t{value}\n'

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
        for analog_writer in self.analog_writers.values():
            analog_writer.close_files()
        self.analog_writers = {}

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
            if nd.type == 'A':
                self.analog_writers[nd.ID].save_analog_chunk(timestamp=nd.time, data_array=nd.data)

    def data_to_string(self, new_data, verbose=False):
        '''Convert list of data tuples into a string.  If verbose=True state and event names are used,
        if verbose=False state and event IDs are used.'''
        data_string = ''
        for nd in new_data:
            if verbose or self.file_type == 'txt': 
                if nd.type == 'D':  # State entry or event.
                        if verbose: # Print state or event name.
                            data_string += f'D {nd[1]} {self.ID2name_fw[nd[2]]}\n'
                        else:       # Print state or event ID.
                            data_string += f'D {nd[1]} {nd[2]}\n'
                elif nd.type in ('P', 'V'): # User print output or set variable.
                    data_string += f'{nd.type} {nd.time} {nd.data}\n'
                elif nd.type == '!': # Warning
                    data_string += f'! {nd.data}\n'
                elif nd.type == '!!': # Crash traceback.
                    error_string = nd.data
                    if not verbose: # In data files multi-line tracebacks have ! prepended to all lines aid parsing data file.
                        error_string = '! ' + error_string.replace('\n', '\n! ')
                    data_string += '\n' + error_string + '\n'
            elif self.file_type == 'tsv':
                if nd.type == 'D':  # State entry or event.
                    if nd.ID in self.sm_info['states'].values():
                        data_string += self.tsv_row_str('state', time=nd.time, name=self.ID2name_fw[nd.ID])
                    else:
                        data_string += self.tsv_row_str('event', time=nd.time, name=self.ID2name_fw[nd.ID])
                elif nd.type == 'P': # User print output.
                    data_string += self.tsv_row_str('print', time=nd.time, value=nd.data)
                elif nd.type == 'V': # Variable.
                    v_name, v_value = nd.data.split(' ')
                    data_string += self.tsv_row_str('var', time=nd.time, name=v_name, value=v_value)
                elif nd.type == '!': # Warning
                    data_string += self.tsv_row_str('warn', value=nd.data)
                elif nd.type == '!!': # Error
                    data_string += self.tsv_row_str('error', value=nd.data.replace('\n','|'))
        return data_string


class Analog_writer():
    '''Class for writing data from one analog input to disk.'''

    def __init__(self, name, sampling_rate, data_type, session_filepath):
        self.name = name
        self.sampling_rate = sampling_rate
        self.data_type = data_type
        self.open_data_files(session_filepath)

    def open_data_files(self, session_filepath):
        ses_path_stem, file_ext = os.path.splitext(session_filepath)
        self.path_stem = ses_path_stem + f'_{self.name}'
        self.file_type = 'npy' if file_ext[-3:] == 'tsv' else 'pca'
        if self.file_type == 'pca':
            file_path = self.path_stem + '.pca'
            self.pca_file = open(file_path, 'wb')
        elif self.file_type == 'npy':
            self.t_tempfile_path = self.path_stem + '.time.temp'
            self.d_tempfile_path = self.path_stem + f'.data.1{self.data_type}.temp'
            self.time_tempfile  = open(self.t_tempfile_path, 'wb')
            self.data_tempfile = open(self.d_tempfile_path, 'wb')

    def close_files(self):
        '''Close data files. Convert temp files to numpy.'''
        if self.file_type == 'pca':
            self.pca_file.close()
        elif self.file_type == 'npy':
            self.time_tempfile.close()
            self.data_tempfile.close()
            with open(self.t_tempfile_path, 'rb') as f:
                times = np.frombuffer(f.read(), dtype='float64')
                np.save(self.path_stem + '.time.npy', times)
            with open(self.d_tempfile_path, 'rb') as f:
                data = np.frombuffer(f.read(), dtype=self.data_type)
                np.save(self.path_stem + '.data.npy', data)
            os.remove(self.t_tempfile_path)
            os.remove(self.d_tempfile_path)

    def save_analog_chunk(self, timestamp, data_array):
        '''Save a chunk of analog data to .pca data file.  File is created if not 
        already open for that analog input.'''
        if self.file_type == 'pca':
            ms_per_sample = 1000 / self.sampling_rate
            for i, x in enumerate(data_array):
                t = int(timestamp + i*ms_per_sample)
                self.pca_file.write(t.to_bytes(4,'little', signed=True))
                self.pca_file.write(x.to_bytes(4,'little', signed=True))
            self.pca_file.flush()
        elif self.file_type == 'npy':
            times = (np.arange(len(data_array), dtype='float64') 
                     / self.sampling_rate) + timestamp/1000 # Seconds
            self.time_tempfile.write(times.tobytes())
            self.data_tempfile.write(data_array.tobytes())
            self.time_tempfile.flush()
            self.data_tempfile.flush()