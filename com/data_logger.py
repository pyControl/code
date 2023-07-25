import os
import numpy as np
from datetime import datetime
from shutil import copyfile


class Data_logger:
    """Class for logging data from a pyControl setup to disk"""

    def __init__(self, sm_info=None, print_func=None, data_consumers=[]):
        self.data_file = None
        self.analog_writers = {}
        self.print_func = print_func
        self.data_consumers = data_consumers
        if sm_info:
            self.set_state_machine(sm_info)

    def set_state_machine(self, sm_info):
        self.sm_info = sm_info
        self.ID2name_fw = self.sm_info.ID2name  # Dict mapping framework IDs to names.

    def open_data_file(self, data_dir, experiment_name, setup_ID, subject_ID, datetime_now=None):
        """Open file tsv/txt file for event data and write header information.
        If state machine uses analog inputs instantiate analog data writers."""
        self.data_dir = data_dir
        self.experiment_name = experiment_name
        self.subject_ID = subject_ID
        self.setup_ID = setup_ID
        if datetime_now is None:
            datetime_now = datetime.now()
        self.end_timestamp = -1
        file_name = self.subject_ID + datetime_now.strftime("-%Y-%m-%d-%H%M%S") + ".tsv"
        self.file_path = os.path.join(self.data_dir, file_name)
        self.data_file = open(self.file_path, "w", newline="\n")
        self.data_file.write(
            self.tsv_row_str(rtype="type", time="time", name="name", value="value")  # Write header with row names.
        )
        self.write_info_line("experiment_name", self.experiment_name)
        self.write_info_line("task_name", self.sm_info.name)
        self.write_info_line("task_file_hash", self.sm_info.task_hash)
        self.write_info_line("setup_id", self.setup_ID)
        self.write_info_line("framework_version", self.sm_info.framework_version)
        self.write_info_line("micropython_version", self.sm_info.micropython_version)
        self.write_info_line("subject_id", self.subject_ID)
        self.write_info_line("start_time", datetime.utcnow().isoformat(timespec="milliseconds"))
        self.analog_writers = {
            ID: Analog_writer(ai["name"], ai["fs"], ai["dtype"], self.file_path)
            for ID, ai in self.sm_info.analog_inputs.items()
        }

    def write_info_line(self, name, value, time=0):
        self.data_file.write(self.tsv_row_str("info", time=time, name=name, value=value))

    def tsv_row_str(self, rtype, time="", name="", value=""):
        time_str = f"{time/1000:.3f}" if type(time) == int else time
        return f"{time_str}\t{rtype}\t{name}\t{value}\n"

    def copy_task_file(self, data_dir, tasks_dir, dir_name="task_files"):
        """If not already present, copy task file to data_dir/dir_name
        appending the files djb2 hash to the file name."""
        exp_tasks_dir = os.path.join(data_dir, dir_name)
        if not os.path.exists(exp_tasks_dir):
            os.mkdir(exp_tasks_dir)
        task_file_path = os.path.join(tasks_dir, self.sm_info.name + ".py")
        task_save_name = os.path.split(self.sm_info.name)[1] + "_{}.py".format(self.sm_info.task_hash)
        if task_save_name not in os.listdir(exp_tasks_dir):
            copyfile(task_file_path, os.path.join(exp_tasks_dir, task_save_name))

    def close_files(self):
        if self.data_file:
            self.write_info_line("end_time", self.end_datetime.isoformat(timespec="milliseconds"), self.end_timestamp)
            self.data_file.close()
            self.data_file = None
            self.file_path = None
        for analog_writer in self.analog_writers.values():
            analog_writer.close_files()
        self.analog_writers = {}

    def process_data(self, new_data):
        """If data _file is open new data is written to file.  If print_func is specified
        human readable data strings are passed to it."""
        if self.data_file:
            self.write_to_file(new_data)
        if self.print_func:
            self.print_func(self.data_to_string(new_data).replace("\t\t", "\t"), end="")
        if self.data_consumers:
            for data_consumer in self.data_consumers:
                data_consumer.process_data(new_data)

    def write_to_file(self, new_data):
        data_string = self.data_to_string(new_data)
        if data_string:
            self.data_file.write(data_string)
            self.data_file.flush()
        for nd in new_data:
            if nd.type == "A":
                self.analog_writers[nd.ID].save_analog_chunk(timestamp=nd.time, data_array=nd.data)

    def data_to_string(self, new_data):
        """Convert list of data tuples into a string.  If verbose=True state and event names are used,
        if verbose=False state and event IDs are used."""
        data_string = ""
        for nd in new_data:
            if nd.type == "D":  # State entry or event.
                if nd.ID in self.sm_info.states.values():
                    data_string += self.tsv_row_str("state", time=nd.time, name=self.ID2name_fw[nd.ID])
                else:
                    data_string += self.tsv_row_str("event", time=nd.time, name=self.ID2name_fw[nd.ID])
            elif nd.type == "P":  # User print output.
                data_string += self.tsv_row_str("print", time=nd.time, value=nd.data)
            elif nd.type == "V":  # Variable.
                data_string += self.tsv_row_str("variable", time=nd.time, name=nd.ID, value=nd.data)
            elif nd.type == "!":  # Warning
                data_string += self.tsv_row_str("warning", value=nd.data)
            elif nd.type == "!!":  # Error
                data_string += self.tsv_row_str("error", value=nd.data.replace("\n", "|").replace("\r", "|"))
            elif nd.type == "S":  # Framework stop.
                self.end_datetime = datetime.utcnow()
                self.end_timestamp = nd.time
        return data_string


class Analog_writer:
    """Class for writing data from one analog input to disk."""

    def __init__(self, name, sampling_rate, data_type, session_filepath):
        self.name = name
        self.sampling_rate = sampling_rate
        self.data_type = data_type
        self.open_data_files(session_filepath)

    def open_data_files(self, session_filepath):
        ses_path_stem, file_ext = os.path.splitext(session_filepath)
        self.path_stem = ses_path_stem + f"_{self.name}"
        self.t_tempfile_path = self.path_stem + ".time.temp"
        self.d_tempfile_path = self.path_stem + f".data-1{self.data_type}.temp"
        self.time_tempfile = open(self.t_tempfile_path, "wb")
        self.data_tempfile = open(self.d_tempfile_path, "wb")
        self.next_chunk_start_time = 0

    def close_files(self):
        """Close data files. Convert temp files to numpy."""
        self.time_tempfile.close()
        self.data_tempfile.close()
        with open(self.t_tempfile_path, "rb") as f:
            times = np.frombuffer(f.read(), dtype="float64")
            np.save(self.path_stem + ".time.npy", times)
        with open(self.d_tempfile_path, "rb") as f:
            data = np.frombuffer(f.read(), dtype=self.data_type)
            np.save(self.path_stem + ".data.npy", data)
        os.remove(self.t_tempfile_path)
        os.remove(self.d_tempfile_path)

    def save_analog_chunk(self, timestamp, data_array):
        """Save a chunk of analog data to .pca data file."""
        if np.abs(self.next_chunk_start_time - timestamp / 1000) < 0.001:
            chunk_start_time = self.next_chunk_start_time
        else:
            chunk_start_time = timestamp / 1000
        times = (np.arange(len(data_array), dtype="float64") / self.sampling_rate) + chunk_start_time  # Seconds
        self.time_tempfile.write(times.tobytes())
        self.data_tempfile.write(data_array.tobytes())
        self.time_tempfile.flush()
        self.data_tempfile.flush()
        self.next_chunk_start_time = chunk_start_time + len(data_array) / self.sampling_rate
