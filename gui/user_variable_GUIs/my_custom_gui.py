 # This file was automatically generated from pyConrtol's GUI Generator version 0 
from gui.dialog_elements import *

class my_custom_gui(QtGui.QDialog):
    # Dialog for setting and getting task variables.
    def __init__(self, parent, board):
        super(QtGui.QDialog, self).__init__(parent)
        self.setWindowTitle("my_custom_gui GUI")
        self.layout = QtGui.QVBoxLayout(self)
        self.variables_grid = Grid(self, board)
        self.layout.addWidget(self.variables_grid)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)


class Grid(QtGui.QWidget):
    def __init__(self, parent, board):
        super(QtGui.QWidget, self).__init__(parent)
        variables = board.sm_info["variables"]
        self.grid_layout = QtGui.QGridLayout()
        initial_variables_dict = {
            v_name: v_value_str for (v_name, v_value_str) in sorted(variables.items())
        }
        self.gui = GUI(self, self.grid_layout, board, initial_variables_dict)
        self.setLayout(self.grid_layout)


class GUI(QtGui.QWidget):
    def __init__(self, parent, grid_layout, board, init_vars):
        super(QtGui.QWidget, self).__init__(parent)
        self.board = board

        # create widgets
        widget = QtGui.QWidget()
        layout = QtGui.QGridLayout()
        self.green_enabled = checkbox_var(init_vars, "🟢Green active", "green_enabled")
        self.green_enabled.setHint("")
        self.green_enabled.setBoard(board)
        self.green_enabled.add_to_grid(layout,0)

        self.green_count = spin_var(init_vars, "🟢Green count", 0, 10, 1, "green_count")
        self.green_count.setSuffix(" blinks")
        self.green_count.setHint("")
        self.green_count.setBoard(board)
        self.green_count.add_to_grid(layout,1)

        self.red_enabled = checkbox_var(init_vars, "🔴Red active", "red_enabled")
        self.red_enabled.setHint("")
        self.red_enabled.setBoard(board)
        self.red_enabled.add_to_grid(layout,2)

        self.red_count = spin_var(init_vars, "🔴Red count", 0, 10, 1, "red_count")
        self.red_count.setSuffix(" blinks")
        self.red_count.setHint("")
        self.red_count.setBoard(board)
        self.red_count.add_to_grid(layout,3)

        self.blink_rate = slider_var(init_vars, "⏱️Blink rate", 1, 15, .5, "blink_rate")
        self.blink_rate.setSuffix(" Hz")
        self.blink_rate.setHint("Rate which LED blinks")
        self.blink_rate.setBoard(board)
        self.blink_rate.add_to_grid(layout,4)


        widget.setLayout(layout)
        grid_layout.addWidget(widget, 0, 0, QtCore.Qt.AlignLeft)
        grid_layout.setRowStretch(15, 1)

