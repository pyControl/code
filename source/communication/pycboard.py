import os
import re
import time
import json
import inspect
from serial import SerialException
from array import array
from .pyboard import Pyboard, PyboardError
from .data_logger import Data_logger
from .message import MsgType, Datatuple
from source.gui.settings import VERSION, user_folder
from dataclasses import dataclass

# ----------------------------------------------------------------------------------------
#  Helper functions.
# ----------------------------------------------------------------------------------------


# djb2 hashing algorithm used to check integrity of transfered files.
def _djb2_file(file_path):
    with open(file_path, "rb") as f:
        h = 5381
        while True:
            c = f.read(4)
            if not c:
                break
            h = ((h << 5) + h + int.from_bytes(c, "little")) & 0xFFFFFFFF
    return h


# Used on pyboard for file transfer.
def _receive_file(file_path, file_size):
    usb = pyb.USB_VCP()
    usb.setinterrupt(-1)
    buf_size = 512
    buf = bytearray(buf_size)
    buf_mv = memoryview(buf)
    bytes_remaining = file_size
    try:
        with open(file_path, "wb") as f:
            while bytes_remaining > 0:
                bytes_read = usb.recv(buf, timeout=5)
                usb.write(b"OK")
                if bytes_read:
                    bytes_remaining -= bytes_read
                    f.write(buf_mv[:bytes_read])
    except:
        fs_stat = os.statvfs("/flash")
        fs_free_space = fs_stat[0] * fs_stat[3]
        if fs_free_space < bytes_remaining:
            usb.write(b"NS")  # Out of space.
        else:
            usb.write(b"ER")


@dataclass
class State_machine_info:
    name: str
    task_hash: int
    states: dict
    events: dict
    ID2name: dict
    analog_inputs: dict
    variables: dict
    framework_version: str
    micropython_version: float


# ----------------------------------------------------------------------------------------
#  Pycboard class.
# ----------------------------------------------------------------------------------------


class Pycboard(Pyboard):
    """Pycontrol board inherits from Pyboard and adds functionality for file transfer
    and pyControl operations.
    """

    device_class2file = {}  # Dict mapping device classes to file where they are defined {class_name: device_file}

    def __init__(self, serial_port, baudrate=115200, verbose=True, print_func=print, data_consumers=None):
        self.serial_port = serial_port
        self.print = print_func  # Function used for print statements.
        self.data_logger = Data_logger(board=self, print_func=print_func)
        self.data_consumers = data_consumers
        self.status = {"serial": None, "framework": None, "usb_mode": None}
        self.device_files_on_pyboard = {}  # Dict {file_name:file_hash} of files in devices folder on pyboard.
        if not Pycboard.device_class2file:  # Scan devices folder to find files where device classes are defined.
            self.make_device_class2file_map()
        try:
            super().__init__(self.serial_port, baudrate=baudrate)
            self.status["serial"] = True
            self.reset()
            self.unique_ID = eval(self.eval("pyb.unique_id()").decode())
            v_tuple = eval(
                self.eval("sys.implementation.version if hasattr(sys, 'implementation') else (0,0,0)").decode()
            )
            self.micropython_version = float("{}.{}{}".format(*v_tuple))
        except SerialException as e:
            self.status["serial"] = False
            raise (e)
        if verbose:  # Print status.
            if self.status["serial"]:
                self.print("\nMicropython version: {}".format(self.micropython_version))
            else:
                self.print("Error: Unable to open serial connection.")
                return
            if self.status["framework"]:
                self.print(f"Framework version: {self.framework_version}")
                if self.framework_version != VERSION:
                    self.print(
                        "\nThe pyControl framework version on the board does not match the GUI version. "
                        "It is recommended to reload the pyControl framework to the pyboard to ensure compatibility."
                    )
            else:
                if self.status["framework"] is None:
                    self.print("pyControl Framework: Not loaded")
                else:
                    self.print("pyControl Framework: Import error")
                return

    def reset(self):
        """Enter raw repl (soft reboots pyboard), import modules."""
        self.enter_raw_repl()  # Soft resets pyboard.
        self.exec(inspect.getsource(_djb2_file))  # define djb2 hashing function.
        self.exec(inspect.getsource(_receive_file))  # define receive file function.
        self.exec("import os; import gc; import sys; import pyb")
        self.framework_running = False
        error_message = None
        self.status["usb_mode"] = self.eval("pyb.usb_mode()").decode()
        self.data_logger.reset()
        try:
            self.exec("from pyControl import *; import devices")
            self.status["framework"] = True  # Framework imported OK.
            self.device_files_on_pyboard = self.get_folder_contents("devices", get_hash=True)
        except PyboardError as e:
            error_message = e.args[2].decode()
            if ("ImportError: no module named 'pyControl'" in error_message) or (
                "ImportError: no module named 'devices'" in error_message
            ):
                self.status["framework"] = None  # Framework not installed.
            else:
                self.status["framework"] = False  # Framework import error.
        try:
            self.framework_version = self.eval("fw.VERSION").decode()
        except PyboardError:
            self.framework_version = "<1.8"
        return error_message

    def hard_reset(self, reconnect=True):
        self.print("\nResetting pyboard.")
        try:
            self.exec_raw_no_follow("pyb.hard_reset()")
        except PyboardError:
            pass
        self.close()  # Close serial connection.
        if reconnect:
            time.sleep(5.0)  # Wait 5 seconds before trying to reopen serial connection.
            try:
                super().__init__(self.serial_port, baudrate=115200)  # Reopen serial conection.
                self.reset()
            except SerialException:
                self.print("Unable to reopen serial connection.")
        else:
            self.print("\nSerial connection closed.")

    def gc_collect(self):
        """Run a garbage collection on pyboard to free up memory."""
        self.exec("gc.collect()")
        time.sleep(0.01)

    def DFU_mode(self):
        """Put the pyboard into device firmware update mode."""
        self.exec("import pyb")
        try:
            self.exec_raw_no_follow("pyb.bootloader()")
        except PyboardError:
            pass  # Error occurs on older versions of micropython but DFU is entered OK.
        self.print("\nEntered DFU mode, closing serial connection.\n")
        self.close()

    def disable_mass_storage(self):
        """Modify the boot.py file to make the pyboards mass storage invisible to the
        host computer."""
        self.print("\nDisabling USB flash drive")
        self.write_file("boot.py", "import machine\nimport pyb\npyb.usb_mode('VCP')")
        self.hard_reset(reconnect=False)

    def enable_mass_storage(self):
        """Modify the boot.py file to make the pyboards mass storage visible to the
        host computer."""
        self.print("\nEnabling USB flash drive")
        self.write_file("boot.py", "import machine\nimport pyb\npyb.usb_mode('VCP+MSC')")
        self.hard_reset(reconnect=False)

    # ------------------------------------------------------------------------------------
    # Pyboard filesystem operations.
    # ------------------------------------------------------------------------------------

    def write_file(self, target_path, data):
        """Write data to file at specified path on pyboard, any data already
        in the file will be deleted."""
        try:
            self.exec("with open('{}','w') as f: f.write({})".format(target_path, repr(data)))
        except PyboardError as e:
            raise PyboardError(e)

    def get_file_hash(self, target_path):
        """Get the djb2 hash of a file on the pyboard."""
        try:
            file_hash = int(self.eval("_djb2_file('{}')".format(target_path)).decode())
        except PyboardError:  # File does not exist.
            return -1
        return file_hash

    def transfer_file(self, file_path, target_path=None):
        """Copy file at file_path to location target_path on pyboard."""
        if not target_path:
            target_path = os.path.split(file_path)[-1]
        file_size = os.path.getsize(file_path)
        file_hash = _djb2_file(file_path)
        error_message = (
            "\n\nError: Unable to transfer file. See the troubleshooting docs:\n"
            "https://pycontrol.readthedocs.io/en/latest/user-guide/troubleshooting/"
        )
        # Try to load file, return once file hash on board matches that on computer.
        for i in range(10):
            if file_hash == self.get_file_hash(target_path):
                return
            self.exec_raw_no_follow("_receive_file('{}',{})".format(target_path, file_size))
            with open(file_path, "rb") as f:
                while True:
                    chunk = f.read(512)
                    if not chunk:
                        break
                    self.serial.write(chunk)
                    response_bytes = self.serial.read(2)
                    if response_bytes != b"OK":
                        if response_bytes == b"NS":
                            self.print("\n\nInsufficient space on pyboard filesystem to transfer file.")
                        else:
                            self.print(error_message)
                        time.sleep(0.01)
                        self.serial.reset_input_buffer()
                        raise PyboardError
                self.follow(3)
        # Unable to transfer file.
        self.print(error_message)
        raise PyboardError

    def transfer_folder(
        self, folder_path, target_folder=None, file_type="all", files="all", remove_files=True, show_progress=False
    ):
        """Copy a folder into the root directory of the pyboard.  Folders that
        contain subfolders will not be copied successfully.  To copy only files of
        a specific type, change the file_type argument to the file suffix (e.g. 'py').
        To copy only specified files pass a list of file names as files argument."""
        if not target_folder:
            target_folder = os.path.split(folder_path)[-1]
        if files == "all":
            files = os.listdir(folder_path)
            if file_type != "all":
                files = [f for f in files if f.split(".")[-1] == file_type]
        try:
            self.exec("os.mkdir({})".format(repr(target_folder)))
        except PyboardError:
            # Folder already exists.
            if remove_files:  # Remove any files not in sending folder.
                target_files = self.get_folder_contents(target_folder)
                remove_files = list(set(target_files) - set(files))
                for f in remove_files:
                    target_path = target_folder + "/" + f
                    self.remove_file(target_path)
        for f in files:
            file_path = os.path.join(folder_path, f)
            target_path = target_folder + "/" + f
            self.transfer_file(file_path, target_path)
            if show_progress:
                self.print(".", end="")

    def remove_file(self, file_path):
        """Remove a file from the pyboard."""
        try:
            self.exec("os.remove({})".format(repr(file_path)))
        except PyboardError:
            pass  # File does not exist.

    def get_folder_contents(self, folder_path, get_hash=False):
        """Get a list of the files in a folder on the pyboard, if
        get_hash=True a dict {file_name:file_hash} is returned instead"""
        file_list = eval(self.eval("os.listdir({})".format(repr(folder_path))).decode())
        if get_hash:
            return {file_name: self.get_file_hash(folder_path + "/" + file_name) for file_name in file_list}
        else:
            return file_list

    # ------------------------------------------------------------------------------------
    # pyControl operations.
    # ------------------------------------------------------------------------------------

    def load_framework(self):
        """Copy the pyControl framework folder to the board, reset the devices folder
        on pyboard by removing all devices files, and rebuild the device_class2file dict."""
        self.print("\nTransferring pyControl framework to pyboard.", end="")
        self.transfer_folder(os.path.join("source", "pyControl"), file_type="py", show_progress=True)
        self.transfer_folder(user_folder("devices"), files=["__init__.py"], remove_files=True, show_progress=True)
        self.remove_file("hardware_definition.py")
        self.make_device_class2file_map()
        error_message = self.reset()
        if not self.status["framework"]:
            self.print("\nError importing framework:")
            self.print(error_message)
        else:
            self.print(" OK")
        return

    def load_hardware_definition(self, hwd_path):
        """Transfer a hardware definition file to pyboard."""
        if os.path.exists(hwd_path):
            self.transfer_device_files(hwd_path)
            self.print("\nTransferring hardware definition to pyboard.", end="")
            self.transfer_file(hwd_path, target_path="hardware_definition.py")
            self.reset()
            try:
                self.exec("import hardware_definition")
                self.print(" OK")
            except PyboardError as e:
                error_message = e.args[2].decode()
                self.print("\n\nError importing hardware definition:\n")
                self.print(error_message)
        else:
            self.print("Hardware definition file not found.")

    def transfer_device_files(self, ref_file_path):
        """Transfer device driver files defining classes used in ref_file to the pyboard devices folder.
        Driver file that are already on the pyboard are only transferred if they have changed
        on the computer."""
        used_device_files = self._get_used_device_files(ref_file_path)
        files_to_transfer = []
        for device_file in used_device_files:  # File not on pyboard.
            if device_file not in self.device_files_on_pyboard.keys():
                files_to_transfer.append(device_file)
            else:
                file_hash = _djb2_file(os.path.join(user_folder("devices"), device_file))
                if file_hash != self.device_files_on_pyboard[device_file]:  # File has changed.
                    files_to_transfer.append(device_file)
        if files_to_transfer:
            self.print(f"\nTransfering device driver files {files_to_transfer} to pyboard", end="")
            self.transfer_folder(
                user_folder("devices"), files=files_to_transfer, remove_files=False, show_progress=True
            )
            self.reset()
            self.print(" OK")

    def _get_used_device_files(self, ref_file_path):
        """Return a list of device driver file names containing device classes used in ref_file"""
        ref_file_name = os.path.split(ref_file_path)[-1]
        with open(ref_file_path, "r") as f:
            file_content = f.read()
        device_files = [
            device_file
            for device_class, device_file in Pycboard.device_class2file.items()
            if device_class in file_content and not ref_file_name == device_file
        ]
        # Add any device driver files containing classes used in device_files.
        for device_file in device_files.copy():
            device_files += self._get_used_device_files(os.path.join(user_folder("devices"), device_file))
        device_files = list(set(device_files))  # Remove duplicates.
        return device_files

    def make_device_class2file_map(self):
        """Make dict mapping device class names to file in devices folder containing
        the class definition."""
        Pycboard.device_class2file = {}  # Dict {device_classname: device_filename}
        all_device_files = [f for f in os.listdir(user_folder("devices")) if f.endswith(".py")]
        for device_file in all_device_files:
            with open(os.path.join(user_folder("devices"), device_file), "r") as f:
                file_content = f.read()
            pattern = "[\n\r]class\s*(?P<dcname>\w+)\s*"
            list(set([d_name for d_name in re.findall(pattern, file_content)]))
            device_classes = list(set([device_class for device_class in re.findall(pattern, file_content)]))
            for device_class in device_classes:
                Pycboard.device_class2file[device_class] = device_file

    def setup_state_machine(self, sm_name, sm_dir=None, uploaded=False):
        """Transfer state machine descriptor file sm_name.py from folder sm_dir
        to board and setup state machine on pyboard."""
        self.reset()
        if sm_dir is None:
            sm_dir = user_folder("tasks")
        sm_path = os.path.join(sm_dir, sm_name + ".py")
        if uploaded:
            self.print("\nResetting task. ", end="")
        else:
            if not os.path.exists(sm_path):
                self.print("Error: State machine file not found at: " + sm_path)
                raise PyboardError("State machine file not found at: " + sm_path)
            self.transfer_device_files(sm_path)
            self.print("\nTransferring state machine {} to pyboard. ".format(sm_name), end="")
            self.transfer_file(sm_path, "task_file.py")
        self.gc_collect()
        try:
            self.exec("import task_file")
            self.exec("sm.setup_state_machine(task_file)")
            self.print("OK")
        except PyboardError as e:
            self.print("\n\nError: Unable to setup state machine.\n\n" + e.args[2].decode())
            raise PyboardError("Unable to setup state machine.", e.args[2])
        # Get information about state machine.
        states = self.get_states()
        events = self.get_events()
        self.sm_info = State_machine_info(
            name=sm_name,
            task_hash=_djb2_file(sm_path),
            states=states,  # {name:ID}
            events=events,  # {name:ID}
            ID2name={ID: name for name, ID in {**states, **events}.items()},  # {ID:name}
            analog_inputs=self.get_analog_inputs(),  # {ID: {'name':, 'fs':, 'dtype': 'plot':}}
            variables=self.get_variables(),
            framework_version=self.framework_version,
            micropython_version=self.micropython_version,
        )
        self.data_logger.reset()
        self.timestamp = 0

    def get_states(self):
        """Return states as a dictionary {state_name: state_ID}"""
        return eval(self.eval("sm.states").decode())

    def get_events(self):
        """Return events as a dictionary {event_name: state_ID}"""
        return eval(self.eval("sm.events").decode())

    def get_analog_inputs(self):
        """Return analog_inputs as a dictionary: {ID: {'name':, 'fs':, 'dtype': 'plot':}}"""
        return eval(self.exec("hw.get_analog_inputs()").decode().strip())

    def start_framework(self, data_output=True):
        """Start pyControl framwork running on pyboard."""
        self.gc_collect()
        self.exec("fw.data_output = " + repr(data_output))
        self.serial.reset_input_buffer()
        self.last_message_time = 0
        self.exec_raw_no_follow("fw.run()")
        self.framework_running = True

    def stop_framework(self):
        """Stop framework running on pyboard by sending stop command."""
        self.serial.write(b"\x03")  # Stop signal
        self.framework_running = False

    def process_data(self):
        """Read data from serial line, generate list new_data of data tuples,
        pass new_data to data_logger and print_func if specified, return new_data."""
        new_data = []
        error_message = None
        unexpected_input = []
        while self.serial.in_waiting > 0:
            new_byte = self.serial.read(1)
            if new_byte == b"\x07":  # Start of pyControl message.
                # Output any unexpected characters recived prior to message start.
                if unexpected_input:
                    new_data.append(
                        Datatuple(
                            time=self.get_timestamp(),
                            type=MsgType.WARNG,
                            content="Unexpected input received from board: " + "".join(unexpected_input),
                        )
                    )
                    unexpected_input = []
                # Read message.
                checksum = int.from_bytes(self.serial.read(2), "little")
                message_len = int.from_bytes(self.serial.read(2), "little")
                message = self.serial.read(message_len)
                msg_type = MsgType.from_byte(message[4:5])
                subtype_byte = message[5:6]
                msg_subtype = msg_type.get_subtype(subtype_byte.decode())
                content_bytes = message[6:]
                # Compute checksum
                if msg_type == MsgType.ANLOG:  # Need to extract analog data to compute checksum.
                    ID = int.from_bytes(content_bytes[:2], "little")
                    data = array(self.sm_info.analog_inputs[ID]["dtype"], content_bytes[2:])
                    content = (ID, data)
                    message_sum = sum(message[:8]) + sum(data)
                else:
                    message_sum = sum(message)
                # Process message.
                if checksum == message_sum & 0xFFFF:  # Checksum OK.
                    self.last_message_time = time.time()
                    self.timestamp = int.from_bytes(message[:4], "little")
                    if msg_type in (MsgType.EVENT, MsgType.STATE):
                        content = int(content_bytes.decode())  # Event/state ID.
                    elif msg_type in (MsgType.PRINT, MsgType.WARNG):
                        content = content_bytes.decode()  # Print or error string.
                    elif msg_type == MsgType.VARBL:
                        content = content_bytes.decode()  # JSON string
                        self.sm_info.variables.update(json.loads(content))
                    new_data.append(Datatuple(time=self.timestamp, type=msg_type, subtype=msg_subtype, content=content))
                else:  # Bad checksum
                    new_data.append(
                        Datatuple(time=self.get_timestamp(), type=MsgType.WARNG, content="Bad data checksum.")
                    )
            elif new_byte == b"\x04":  # End of framework run.
                self.framework_running = False
                data_err = self.read_until(2, b"\x04>", timeout=10)
                if len(data_err) > 2:  # Error during framework run.
                    error_message = data_err[:-3].decode()
                    new_data.append(Datatuple(time=self.get_timestamp(), type=MsgType.ERROR, content=error_message))
                break
            else:
                unexpected_input.append(new_byte.decode())
        if new_data:
            self.data_logger.process_data(new_data)
            if self.data_consumers:
                for data_consumer in self.data_consumers:
                    data_consumer.process_data(new_data)
        if error_message:
            raise PyboardError(error_message)

    def trigger_event(self, event_name, source="u"):
        """Trigger specified task event on the pyboard."""
        if self.framework_running:
            event_ID = str(self.sm_info.events[event_name])
            self.send_serial_data(event_ID, "E", source)

    def get_timestamp(self):
        """Get the current pyControl timestamp in ms since start of framework run."""
        seconds_elapsed = time.time() - self.last_message_time
        return self.timestamp + round(1000 * (seconds_elapsed))

    def send_serial_data(self, data, command, cmd_type=""):
        """Send data to the pyboard while framework is running."""
        encoded_data = cmd_type.encode() + data.encode()
        data_len = len(encoded_data).to_bytes(2, "little")
        checksum = sum(encoded_data).to_bytes(2, "little")
        self.serial.write(command.encode() + data_len + encoded_data + checksum)

    # ------------------------------------------------------------------------------------
    # Getting and setting variables.
    # ------------------------------------------------------------------------------------

    def set_variable(self, v_name, v_value, source="s"):
        """Set the value of a state machine variable. If framework is not running
        returns True if variable set OK, False if set failed.  Returns None framework
        running, but variable event is later output by board."""
        if v_name not in self.sm_info.variables:
            raise PyboardError("Invalid variable name: {}".format(v_name))
        if self.framework_running:  # Set variable with serial command.
            self.send_serial_data(repr((v_name, v_value)), "V", source)
            return None
        else:  # Set variable using REPL.
            set_OK = eval(self.eval(f"sm.set_variable({repr(v_name)}, {repr(v_value)})").decode())
            if set_OK:
                self.sm_info.variables[v_name] = v_value
            return set_OK

    def get_variable(self, v_name):
        """Get the value of a state machine variable. If framework not running returns
        variable value if got OK, None if get fails.  Returns None if framework
        running, but variable event is later output by board."""
        if v_name not in self.sm_info.variables:
            raise PyboardError("Invalid variable name: {}".format(v_name))
        if self.framework_running:  # Get variable with serial command.
            self.send_serial_data(v_name, "V", "g")
        else:  # Get variable using REPL.
            var_str = self.eval(f"sm.get_variable({repr(v_name)})").decode()
            try:
                return eval(var_str)
            except Exception:  # Variable is a string.
                return var_str

    def get_variables(self):
        """Return variables as a dictionary {v_name: v_value}"""
        return eval(self.eval("{k: v for k, v in sm.variables.__dict__.items() if not hasattr(v, '__init__')}"))
