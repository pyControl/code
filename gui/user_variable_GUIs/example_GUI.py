from gui.dialog_elements import *

class Blink_gui(QtGui.QDialog):
    # Dialog for setting and getting task variables.
    def __init__(self, parent, board):
        super(QtGui.QDialog, self).__init__(parent)
        self.setWindowTitle("Blink Variable GUI")
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

        self.enable_red = checkbox_var(init_vars, "🔴 <b>Red Active</b>", "red_enabled")
        self.enable_green = checkbox_var(init_vars, "🟢 <b>Green Active</b>", "green_enabled")
        self.blink_counts = standard_var(init_vars, "<b>Blink Counts</b>", "blink_counts")
        self.blink_rate = spin_var(init_vars, "⏱️ <b>Blink Rate</b>", 0.2, 30, 0.5, "blink_rate")
        self.blink_rate.setSuffix(" Hz")
        self.blink_counts.setHint('The number of times each color blinks when active [red,green]')
        self.blink_rate.setHint("Frequency of alternating LED blinks")


        # place widgets in layout
        for i, var in enumerate([self.enable_red, self.enable_green,self.blink_rate,self.blink_counts]):
            var.setBoard(board)
            row = i + 1
            var.add_to_grid(layout, row)

        widget.setLayout(layout)
        grid_layout.addWidget(widget, 0, 0, QtCore.Qt.AlignLeft)
        grid_layout.setRowStretch(15, 1)
