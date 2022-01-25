from gui.dialog_elements import *

class Custom_GUI(QtGui.QDialog):
    # Dialog for setting and getting task variables.
    def __init__(self, parent, board, generator_data):
        super(QtGui.QDialog, self).__init__(parent)
        self.setWindowTitle(f"{generator_data['title']} GUI")
        self.layout = QtGui.QVBoxLayout(self)
        self.variables_grid = Grid(self, board, generator_data)
        self.layout.addWidget(self.variables_grid)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)


class Grid(QtGui.QWidget):
    def __init__(self, parent, board, generator_data):
        super(QtGui.QWidget, self).__init__(parent)
        variables = board.sm_info["variables"]
        self.grid_layout = QtGui.QGridLayout()
        initial_variables_dict = {
            v_name: v_value_str for (v_name, v_value_str) in sorted(variables.items())
        }
        self.gui = GUI(self, self.grid_layout, board, initial_variables_dict, generator_data)
        self.setLayout(self.grid_layout)


class GUI(QtGui.QWidget):
    def __init__(self, parent, grid_layout, board, init_vars, generator_data):
        super(QtGui.QWidget, self).__init__(parent)
        self.board = board

        # create widgets
        widget = QtGui.QWidget()
        layout = QtGui.QGridLayout()

        for row,var in enumerate(generator_data['ordered_elements']):
            control = generator_data[var]
            if control['widget'] == 'slider':
                globals()[var] = slider_var(init_vars, control['label'], control['min'], control['max'], control['step'], var)
                globals()[var].setSuffix(' '+control['suffix'])

            elif control['widget'] == 'spinbox':
                globals()[var] = spin_var(init_vars, control['label'], control['min'], control['max'], control['step'], var)
                globals()[var].setSuffix(' '+control['suffix'])
                
            elif control['widget'] == 'checkbox':
                globals()[var] = checkbox_var(init_vars, control['label'], var)

            elif control['widget'] == 'line edit':
                globals()[var] = standard_var(init_vars, control['label'], var)
        
            globals()[var].setHint(control['hint'])
            globals()[var].setBoard(board)
            globals()[var].add_to_grid(layout,row)

        widget.setLayout(layout)
        grid_layout.addWidget(widget, 0, 0, QtCore.Qt.AlignLeft)
        grid_layout.setRowStretch(15, 1)

