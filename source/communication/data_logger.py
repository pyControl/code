import os
import json
import numpy as np
from datetime import datetime
from shutil import copyfile
from .message import MsgType, Datatuple

# ----------------------------------------------------------------------------------------
#  Data_logger
# ----------------------------------------------------------------------------------------


def ms_to_readable_time(milliseconds):
    seconds, milliseconds = divmod(milliseconds, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
    if minutes:
        return f"{minutes}:{seconds:02d}.{milliseconds:03d}"
    return f"{seconds}.{milliseconds:03d}"


class Data_logger:
    """Class for logging data from a pyControl setup to disk"""

    def __init__(self, board, print_func=None):
        self.board = board
        self.print_func = print_func
        self.reset()

    def reset(self):
        self.data_file = None
        self.file_path = None
        self.subject_ID = None
        self.analog_writers = {}
        self.pre_run_prints = []

    def open_data_file(self, data_dir, experiment_name, setup_ID, subject_ID, datetime_now=None):
        """Open file tsv/txt file for event data and write header information.
        If state machine uses analog inputs instantiate analog data writers."""
        self.data_dir = data_dir
        self.experiment_name = experiment_name
        self.subject_ID = subject_ID
        self.setup_ID = setup_ID
        if datetime_now is None:
            datetime_now = datetime.now()
        self.end_timestamp = None
        file_name = self.subject_ID + datetime_now.strftime("-%Y-%m-%d-%H%M%S") + ".tsv"
        self.file_path = os.path.join(self.data_dir, file_name)
        self.data_file = open(self.file_path, "w", encoding="utf-8", newline="\n")
        self.data_file.write(
            self.tsv_row_str(
                time="time", rtype="type", subtype="subtype", content="content"
            )  # Write header with row names.
        )
        self.write_info_line("experiment_name", self.experiment_name)
        self.write_info_line("task_name", self.board.sm_info.name)
        self.write_info_line("task_file_hash", self.board.sm_info.task_hash)
        self.write_info_line("setup_id", self.setup_ID)
        self.write_info_line("framework_version", self.board.sm_info.framework_version)
        self.write_info_line("micropython_version", self.board.sm_info.micropython_version)
        self.write_info_line("subject_id", self.subject_ID)
        self.write_info_line("start_time", datetime.utcnow().isoformat(timespec="milliseconds"))
        self.write_to_file(self.pre_run_prints)
        self.pre_run_prints = []
        self.analog_writers = {
            ID: Analog_writer(ai["name"], ai["fs"], ai["dtype"], self.file_path)
            for ID, ai in self.board.sm_info.analog_inputs.items()
        }

    def write_info_line(self, subtype, content, time=0):
        self.data_file.write(self.tsv_row_str("info", time, subtype, content))

    def tsv_row_str(self, rtype, time, subtype="", content=""):
        time_str = f"{time/1000:.3f}" if isinstance(time, int) else time
        return f"{time_str}\t{rtype}\t{subtype}\t{content}\n"

    def copy_task_file(self, data_dir, tasks_dir, dir_name="task_files"):
        """If not already present, copy task file to data_dir/dir_name
        appending the files djb2 hash to the file name."""
        exp_tasks_dir = os.path.join(data_dir, dir_name)
        if not os.path.exists(exp_tasks_dir):
            os.mkdir(exp_tasks_dir)
        task_file_path = os.path.join(tasks_dir, self.board.sm_info.name + ".py")
        task_save_name = os.path.split(self.board.sm_info.name)[1] + "_{}.py".format(self.board.sm_info.task_hash)
        if task_save_name not in os.listdir(exp_tasks_dir):
            copyfile(task_file_path, os.path.join(exp_tasks_dir, task_save_name))

    def close_files(self):
        if self.data_file:
            self.write_info_line("end_time", self.end_datetime.isoformat(timespec="milliseconds"), self.end_timestamp)
            self.data_file.close()
            self.data_file = None
        for analog_writer in self.analog_writers.values():
            analog_writer.close_files()
        self.analog_writers = {}

    def process_data(self, new_data):
        """If data_file is open new data is written to file.  If print_func is specified
        human readable data strings are passed to it."""
        if self.data_file:
            self.write_to_file(new_data)
        if self.print_func:
            self.print_func(self.data_to_string(new_data, prettify=True), end="")

    def write_to_file(self, new_data):
        data_string = self.data_to_string(new_data)
        if data_string:
            self.data_file.write(data_string)
            self.data_file.flush()
        for nd in new_data:
            if nd.type == MsgType.ANLOG:
                writer_id, data = nd.content
                self.analog_writers[writer_id].save_analog_chunk(timestamp=nd.time, data_array=data)

    def data_to_string(self, new_data, prettify=False, max_len=60):
        """Convert list of data tuples into a string.  If prettify is True the string is formatted
        for the GUI data log, if False for the tsv data file."""
        data_string = ""
        for nd in new_data:
            time = ms_to_readable_time(nd.time) if prettify else nd.time
            if nd.type == MsgType.STATE:  # State entry.
                data_string += self.tsv_row_str("state", time, content=self.board.sm_info.ID2name[nd.content])
            elif nd.type == MsgType.EVENT:  # Event.
                data_string += self.tsv_row_str("event", time, nd.subtype, self.board.sm_info.ID2name[nd.content])
            elif nd.type == MsgType.PRINT:  # User print output.
                if prettify:
                    print_str = nd.content.replace("\n", "\n\t\t\t")
                else:
                    print_str = nd.content.replace("\n", "|").replace("\r", "|")
                data_string += self.tsv_row_str("print", time, nd.subtype, content=print_str)
            elif nd.type == MsgType.VARBL:  # Variable.
                var_str = nd.content
                if prettify:
                    variables_dict = json.loads(nd.content)
                    if len(repr(variables_dict)) > max_len:  # Wrap variables across multiple lines.
                        var_str = "{\n"
                        for var_name, var_value in sorted(variables_dict.items(), key=lambda x: x[0].lower()):
                            var_str += f'\t\t\t"{var_name}": {var_value}\n'
                        var_str += "\t\t\t}"
                data_string += self.tsv_row_str("variable", time, nd.subtype, content=var_str)
            elif nd.type == MsgType.WARNG:  # Warning
                data_string += self.tsv_row_str("warning", time, content=nd.content)
            elif nd.type in (MsgType.ERROR, MsgType.STOPF):  # Error or stop framework.
                self.end_datetime = datetime.utcnow()
                self.end_timestamp = nd.time
                if nd.type == MsgType.ERROR:
                    content = nd.content
                    if prettify:
                        content = f"\n\n{content}"
                    else:
                        content = content.replace("\n", "|").replace("\r", "|")
                    data_string += self.tsv_row_str("error", time, content=content)
        return data_string

    def print_message(self, msg, source="u"):
        """Print a message to the log and data file. If called pre-run message is logged when
        data file is opened, if called post run message is logged to previously open data file."""
        new_data = [
            Datatuple(
                time=self.board.get_timestamp() if self.board.framework_running else self.board.timestamp,
                type=MsgType.PRINT,
                subtype=MsgType.PRINT.get_subtype(source),
                content=msg,
            )
        ]
        if self.board.framework_running:
            self.process_data(new_data)
            if self.board.data_consumers:
                for data_consumer in self.board.data_consumers:
                    data_consumer.process_data(new_data)
        else:
            self.print_func(self.data_to_string(new_data, prettify=True), end="")
            if self.board.timestamp == 0:  # Pre-run, store note to log when file opened.
                self.pre_run_prints += new_data
            elif self.file_path:  # Post-run, log note to previous data file.
                with open(self.file_path, "a") as data_file:
                    data_file.write(self.data_to_string(new_data))


# ----------------------------------------------------------------------------------------
#  Analog_writer
# ----------------------------------------------------------------------------------------


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
