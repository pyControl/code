import os
import sys
import traceback

from serial.tools import list_ports
from pyqtgraph.Qt import QtGui, QtCore

from config.paths import dirs
from config.gui_settings import  VERSION, ui_font_size
from gui.run_task_tab import Run_task_tab
from gui.dialogs import Board_config_dialog, Keyboard_shortcuts_dialog, Paths_dialog
from gui.configure_experiment_tab import Configure_experiment_tab
from gui.run_experiment_tab import Run_experiment_tab
from gui.setups_tab import Setups_tab

# --------------------------------------------------------------------------------
# GUI_main
# --------------------------------------------------------------------------------

class GUI_main(QtGui.QMainWindow):
 
    def __init__(self):
        super().__init__()
        self.setWindowTitle('pyControl v{}'.format(VERSION))
        self.setGeometry(10, 30, 700, 800) # Left, top, width, height.

        # Variables
        self.refresh_interval = 1000 # How often refresh method is called when not running (ms).
        self.available_tasks = None  # List of task file names in tasks folder.
        self.available_ports = None  # List of available serial ports.
        self.available_experiments = None # List of experiment in experiments folder.
        self.available_tasks_changed = False
        self.available_experiments_changed = False
        self.available_ports_changed = False
        self.data_dir_changed = False
        self.current_tab_ind = 0 # Which tab is currently selected.
        self.app = None # Overwritten with QtGui.QApplication instance in main.

        # Dialogs.

        self.config_dialog = Board_config_dialog(parent=self)
        self.shortcuts_dialog = Keyboard_shortcuts_dialog(parent=self)
        self.paths_dialog = Paths_dialog(parent=self)

        # Widgets.
        self.tab_widget = QtGui.QTabWidget(self)
        self.setCentralWidget(self.tab_widget)

        self.run_task_tab = Run_task_tab(self)  
        self.experiments_tab = QtGui.QStackedWidget(self)
        self.setups_tab = Setups_tab(self)

        self.configure_experiment_tab = Configure_experiment_tab(self)
        self.run_experiment_tab = Run_experiment_tab(self)

        self.experiments_tab.addWidget(self.configure_experiment_tab)
        self.experiments_tab.addWidget(self.run_experiment_tab)

        self.tab_widget.addTab(self.run_task_tab,'Run task')
        self.tab_widget.addTab(self.experiments_tab,'Experiments')
        self.tab_widget.addTab(self.setups_tab, 'Setups')

        self.tab_widget.currentChanged.connect(self.tab_changed) 

        # Timers

        self.refresh_timer = QtCore.QTimer() # Timer to regularly call refresh() when not running.
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(self.refresh_interval)

        # Initial setup.
        self.refresh()    # Refresh tasks and ports lists.

        # Add Menu Bar
        main_menu = self.menuBar()
        ## --------Folders menu--------
        folders_menu = main_menu.addMenu('Folders')
        # View Data Directory
        data_action = QtGui.QAction("&Data", self)
        data_action.setShortcut("Ctrl+D")
        data_action.triggered.connect(self.go_to_data)
        folders_menu.addAction(data_action)
        # View Task Directory
        task_action = QtGui.QAction("&Tasks", self)
        task_action.setShortcut("Ctrl+T")
        task_action.triggered.connect(self.go_to_tasks)
        folders_menu.addAction(task_action)
        ## --------Settings menu--------
        settings_menu = main_menu.addMenu('Settings')
        # Folder paths
        paths_action = QtGui.QAction("&Folder paths", self)
        paths_action.triggered.connect(self.paths_dialog.exec)
        settings_menu.addAction(paths_action)
        # ---------Help menu----------
        help_menu= main_menu.addMenu('Help')
        # Go to readthedocs
        documentation_action= QtGui.QAction("&Documentation", self)
        documentation_action.triggered.connect(self.view_docs)
        documentation_action.setIcon(QtGui.QIcon("gui/icons/book.svg"))
        help_menu.addAction(documentation_action)
        # Go to Google forum
        forum_action= QtGui.QAction("&Forum", self)
        forum_action.triggered.connect(self.view_forum)
        forum_action.setIcon(QtGui.QIcon("gui/icons/google-groups.svg")) #https://iconscout.com/icon/google-groups-1
        help_menu.addAction(forum_action)
        # Go to GitHub Repository
        github_action= QtGui.QAction("&GitHub Repository", self)
        github_action.triggered.connect(self.view_github)
        github_action.setIcon(QtGui.QIcon("gui/icons/github.svg")) #https://simpleicons.org/?q=github
        help_menu.addAction(github_action)
        # Keyboard shortcuts dialog.
        shortcuts_action = QtGui.QAction("&Keyboard shortcuts", self)
        shortcuts_action.triggered.connect(self.shortcuts_dialog.show)
        shortcuts_action.setIcon(QtGui.QIcon("gui/icons/keyboard.svg"))
        help_menu.addAction(shortcuts_action)

        self.show()

    def go_to_data(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(dirs['data']))

    def go_to_tasks(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(dirs['tasks']))

    def view_docs(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://pycontrol.readthedocs.io/en/latest/"))

    def view_forum(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://groups.google.com/forum/#!forum/pycontrol"))

    def view_github(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://github.com/pyControl/pyControl"))

    def get_task_file_list(self):
        '''Return list of .py files in tasks folder and subfolders in format:
        subdir_1/subdir_2/task_file_name.py'''
        task_files = []
        for (dirpath, dirnames, filenames) in os.walk(dirs['tasks']):
            task_files += [os.path.join(dirpath, file).split(dirs['tasks'])[1][1:-3]
                           for file in filenames if file.endswith('.py')]
        return task_files

    def refresh(self):
        '''Called regularly when framework not running.'''
        # Scan task folder.
        tasks = self.get_task_file_list()
        self.available_tasks_changed = tasks != self.available_tasks
        if self.available_tasks_changed:    
            self.available_tasks = tasks
        # Scan experiments folder.
        experiments = [t.split('.')[0] for t in os.listdir(dirs['experiments']) if t[-4:] == '.pcx']
        self.available_experiments_changed = experiments != self.available_experiments
        if self.available_experiments_changed:    
            self.available_experiments = experiments
        # Scan serial ports.
        ports = set([c[0] for c in list_ports.comports()
                     if ('Pyboard' in c[1]) or ('USB Serial Device' in c[1])])
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
        '''Called whenever the active tab is changed.'''
        if self.current_tab_ind == 0: 
            self.run_task_tab.disconnect()
        elif self.current_tab_ind == 2:
            self.setups_tab.disconnect()
        self.current_tab_ind = new_tab_ind

    # Exception handling.

    def excepthook(self, ex_type, ex_value, ex_traceback):
        '''Called whenever an uncaught exception occurs.'''
        if hasattr(self.tab_widget.currentWidget(), 'excepthook'):
           self.tab_widget.currentWidget().excepthook(ex_type, ex_value, ex_traceback)
        traceback.print_exception(ex_type, ex_value, ex_traceback)

# --------------------------------------------------------------------------------
# Launch GUI.
# --------------------------------------------------------------------------------

def launch_GUI():
    '''Launch the pyControl GUI.'''
    app = QtGui.QApplication(sys.argv)
    app.setStyle('Fusion')
    font = QtGui.QFont()
    font.setPixelSize(ui_font_size)
    app.setFont(font)
    gui_main = GUI_main()
    gui_main.app = app # To allow app functions to be called from GUI.
    sys.excepthook = gui_main.excepthook
    sys.exit(app.exec_())