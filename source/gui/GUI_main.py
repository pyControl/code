import os
import sys
import ctypes
import traceback
import logging
import platform

from pathlib import Path
from serial.tools import list_ports
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets

from source.gui.settings import VERSION, get_setting, user_folder
from source.gui.run_task_tab import Run_task_tab
from source.gui.dialogs import Keyboard_shortcuts_dialog, Settings_dialog, Error_log_dialog
from source.gui.configure_experiment_tab import Configure_experiment_tab
from source.gui.run_experiment_tab import Run_experiment_tab
from source.gui.setups_tab import Setups_tab

if platform.system() == "Windows":  # Needed on windows to get taskbar icon to display correctly.
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("pyControl")


# --------------------------------------------------------------------------------
# GUI_main
# --------------------------------------------------------------------------------


class GUI_main(QtWidgets.QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.setWindowTitle(f"pyControl v{VERSION}")
        self.setGeometry(10, 30, 700, 800)  # Left, top, width, height.

        # Variables
        self.refresh_interval = 1000  # How often refresh method is called when not running (ms).
        self.available_tasks = None  # List of task file names in tasks folder.
        self.available_ports = None  # List of available serial ports.
        self.available_experiments = None  # List of experiment in experiments folder.
        self.available_tasks_changed = False
        self.available_experiments_changed = False
        self.available_ports_changed = False
        self.task_directory = user_folder("tasks")
        self.data_dir_changed = False
        self.current_tab_ind = 0  # Which tab is currently selected.
        self.app = app

        # Dialogs.
        self.shortcuts_dialog = Keyboard_shortcuts_dialog(parent=self)
        self.settings_dialog = Settings_dialog(parent=self)
        self.error_log_dialog = Error_log_dialog(parent=self)

        # Widgets.
        self.tab_widget = QtWidgets.QTabWidget(self)
        self.setCentralWidget(self.tab_widget)

        self.run_task_tab = Run_task_tab(self)
        self.experiments_tab = QtWidgets.QStackedWidget(self)
        self.setups_tab = Setups_tab(self)

        self.configure_experiment_tab = Configure_experiment_tab(self)
        self.run_experiment_tab = Run_experiment_tab(self)

        self.experiments_tab.addWidget(self.configure_experiment_tab)
        self.experiments_tab.addWidget(self.run_experiment_tab)

        self.tab_widget.addTab(self.run_task_tab, "Run task")
        self.tab_widget.addTab(self.experiments_tab, "Experiments")
        self.tab_widget.addTab(self.setups_tab, "Setups")

        self.tab_widget.currentChanged.connect(self.tab_changed)

        # Timers
        self.refresh_timer = QtCore.QTimer()  # Timer to regularly call refresh() when not running.
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(self.refresh_interval)

        # Initial setup.
        self.refresh()  # Refresh tasks and ports lists.

        # Add Menu Bar
        main_menu = self.menuBar()
        ## --------View menu--------
        view_menu = main_menu.addMenu("View")
        # View Data Directory
        data_action = QtGui.QAction("&Data directory", self)
        data_action.setShortcut("Ctrl+D")
        data_action.triggered.connect(self.go_to_data)
        view_menu.addAction(data_action)
        # View Task Directory
        task_action = QtGui.QAction("&Tasks directory", self)
        task_action.setShortcut("Ctrl+T")
        task_action.triggered.connect(self.go_to_tasks)
        view_menu.addAction(task_action)
        # View error log
        error_log_action = QtGui.QAction("&Error log", self)
        error_log_action.setShortcut("Ctrl+E")
        error_log_action.triggered.connect(self.show_error_log)
        view_menu.addAction(error_log_action)
        ## --------Settings menu--------
        settings_menu = main_menu.addMenu("Settings")
        # Folder paths
        self.settings_action = QtGui.QAction("&Edit settings", self)
        self.settings_action.setShortcut("Ctrl+,")
        self.settings_action.triggered.connect(self.settings_dialog.exec)
        settings_menu.addAction(self.settings_action)
        # ---------Help menu----------
        help_menu = main_menu.addMenu("Help")
        # Go to readthedocs
        documentation_action = QtGui.QAction("&Documentation", self)
        documentation_action.triggered.connect(self.view_docs)
        documentation_action.setIcon(QtGui.QIcon("source/gui/icons/book.svg"))
        help_menu.addAction(documentation_action)
        # Go to Google forum
        forum_action = QtGui.QAction("&Help and Discussions", self)
        forum_action.triggered.connect(self.view_forum)
        forum_action.setIcon(QtGui.QIcon("source/gui/icons/help.svg"))
        help_menu.addAction(forum_action)
        # Go to GitHub Repository
        github_action = QtGui.QAction("&GitHub Repository", self)
        github_action.triggered.connect(self.view_github)
        github_action.setIcon(QtGui.QIcon("source/gui/icons/github.svg"))  # https://simpleicons.org/?q=github
        help_menu.addAction(github_action)
        # Keyboard shortcuts dialog.
        shortcuts_action = QtGui.QAction("&Keyboard shortcuts", self)
        shortcuts_action.triggered.connect(self.shortcuts_dialog.show)
        shortcuts_action.setIcon(QtGui.QIcon("source/gui/icons/keyboard.svg"))
        help_menu.addAction(shortcuts_action)

        self.pcx2json()
        self.show()

    def go_to_data(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(get_setting("folders", "data")))

    def go_to_tasks(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(user_folder("tasks")))

    def view_docs(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://pycontrol.readthedocs.io/en/latest/"))

    def view_forum(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://github.com/orgs/pyControl/discussions"))

    def view_github(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://github.com/pyControl/pyControl"))

    def show_error_log(self):
        try:
            with open("ErrorLog.txt", "r", encoding="utf-8") as reader:
                text = reader.read()
            self.error_log_dialog.log_viewer.setText(text)
            self.error_log_dialog.exec()
        except FileNotFoundError:
            QtWidgets.QMessageBox.information(
                self,
                "No error log",
                "You have no errors",
                QtWidgets.QMessageBox.StandardButton.Ok,
            )

    def get_nested_file_list(self, folder_to_walk, file_extension):
        """Return list of files within a parent directory and subdirectories in the format:
        subdir_1/subdir_2/filename"""
        nested_files = []
        for dirpath, _, filenames in os.walk(folder_to_walk):
            nested_files += [
                os.path.join(dirpath, file).split(folder_to_walk)[1][1 : -len(file_extension)]
                for file in filenames
                if file.endswith(file_extension)
            ]
        return nested_files

    def pcx2json(self):
        """Converts legacy .pcx files to .json files"""
        exp_dir = Path(user_folder("experiments"))
        for f in exp_dir.glob("*.pcx"):
            f.rename(f.with_suffix(".json"))

    def refresh(self):
        """Called regularly when framework not running."""
        # Scan task folder.
        # this function gets called every second. Normally we would use get_setting("folder","tasks")
        # but there is no need to constantly be rereading the settings.json file that isn't changing
        # so we use this self.task_directory variable that is only updated when a new user settting is saved
        tasks = self.get_nested_file_list(self.task_directory, ".py")
        self.available_tasks_changed = tasks != self.available_tasks
        if self.available_tasks_changed:
            self.available_tasks = tasks
        # Scan experiments folder.
        experiments = self.get_nested_file_list(user_folder("experiments"), ".json")
        self.available_experiments_changed = experiments != self.available_experiments
        if self.available_experiments_changed:
            self.available_experiments = experiments
        # Scan serial ports.
        ports = set([c[0] for c in list_ports.comports() if ("Pyboard" in c[1]) or ("USB Serial Device" in c[1])])
        self.available_ports_changed = ports != self.available_ports
        if self.available_ports_changed:
            self.available_ports = ports
        # Refresh tabs.
        self.run_task_tab.refresh()
        self.configure_experiment_tab.refresh()
        self.setups_tab.refresh()
        # Clear flags.
        self.data_dir_changed = False

    def tab_changed(self, new_tab_ind):
        """Called whenever the active tab is changed."""
        if self.current_tab_ind == 0:
            self.run_task_tab.disconnect()
        elif self.current_tab_ind == 2:
            self.setups_tab.disconnect()
        self.current_tab_ind = new_tab_ind

    # Exception handling.

    def excepthook(self, ex_type, ex_value, ex_traceback):
        """Called whenever an uncaught exception occurs."""
        if hasattr(self.tab_widget.currentWidget(), "excepthook"):
            self.tab_widget.currentWidget().excepthook(ex_type, ex_value, ex_traceback)
        logging.error("".join(traceback.format_exception(ex_type, ex_value, ex_traceback)))


# --------------------------------------------------------------------------------
# Launch GUI.
# --------------------------------------------------------------------------------


def launch_GUI():
    """Launch the pyControl GUI."""
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setWindowIcon(QtGui.QIcon("source/gui/icons/logo.svg"))
    font = QtGui.QFont()
    font.setPixelSize(get_setting("GUI", "ui_font_size"))
    app.setFont(font)
    gui_main = GUI_main(app)
    sys.excepthook = gui_main.excepthook
    sys.exit(app.exec())
