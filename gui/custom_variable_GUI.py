from gui.dialog_elements import *

class Custom_GUI(QtGui.QDialog):
    # Dialog for setting and getting task variables.
    def __init__(self, parent, board, generator_data):
        super(QtGui.QDialog, self).__init__(parent)
        self.parent = parent
        self.generator_data = generator_data
        self.setWindowTitle(f"{self.generator_data['title']} GUI")
        self.layout = QtGui.QVBoxLayout(self)
        toolBar = QtGui.QToolBar()
        self.layout.addWidget(toolBar)
        self.edit_action = QtGui.QAction("Edit", self)
        self.edit_action.setEnabled(True)
        self.edit_action.triggered.connect(self.edit)
        toolBar.addAction(self.edit_action)
        self.variables_grid = Grid(self, board, generator_data)
        self.layout.addWidget(self.variables_grid)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
    
    def edit(self):
        self.parent.open_gui_editor(self.generator_data)


class Grid(QtGui.QWidget):
    def __init__(self, parent, board, generator_data):
        super(QtGui.QWidget, self).__init__(parent)
        self.grid_layout = QtGui.QGridLayout()
        self.gui = GUI(self, self.grid_layout, board, generator_data)
        self.setLayout(self.grid_layout)

class GUI(QtGui.QWidget):
    def __init__(self, parent, grid_layout, board, generator_data):
        super(QtGui.QWidget, self).__init__(parent)
        self.board = board
        
        variables = board.sm_info["variables"]
        init_vars = {
            v_name: v_value_str for (v_name, v_value_str) in sorted(variables.items())
        }

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
        

        leftover_widget = QtGui.QWidget()
        leftover_layout = QtGui.QGridLayout()
        used_vars = generator_data['ordered_elements']
        leftover_vars = sorted(list( set(variables) - set(used_vars)), key=str.lower)
        leftover_vars = [v_name for v_name in leftover_vars if not v_name[-3:] == '___' and v_name != 'variable_gui']
        if len(leftover_vars) > 0:
            for row,var in enumerate(leftover_vars):
                globals()[var] = standard_var(init_vars, var, var)
                globals()[var].setHint(control['hint'])
                globals()[var].setBoard(board)
                globals()[var].add_to_grid(leftover_layout, row )
            leftover_widget.setLayout(leftover_layout)

            variable_tabs = QtGui.QTabWidget()
            variable_tabs.addTab(widget,"custom")
            variable_tabs.addTab(leftover_widget,"standard")

            grid_layout.addWidget(variable_tabs, 0, 0, QtCore.Qt.AlignLeft)
        else:
            grid_layout.addWidget(widget, 0, 0, QtCore.Qt.AlignLeft)

        grid_layout.setRowStretch(15, 1)