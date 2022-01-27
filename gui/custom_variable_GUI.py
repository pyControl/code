from gui.dialog_elements import *

class Custom_GUI(QtGui.QDialog):
    # Dialog for setting and getting task variables.
    def __init__(self, parent, board, generator_data):
        super(QtGui.QDialog, self).__init__(parent)
        self.parent = parent
        self.generator_data = generator_data
        self.setWindowTitle("Set Variables")
        self.layout = QtGui.QVBoxLayout(self)
        toolBar = QtGui.QToolBar()
        toolBar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        toolBar.setIconSize(QtCore.QSize(15, 15))
        self.layout.addWidget(toolBar)
        self.edit_action = QtGui.QAction(QtGui.QIcon("gui/icons/edit.svg"),"&edit", self)
        self.edit_action.setEnabled(True)
        self.edit_action.triggered.connect(self.edit)
        toolBar.addAction(self.edit_action)
        self.variables_grid = Custom_variables_grid(self, board, generator_data)
        self.layout.addWidget(self.variables_grid)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
    
    def edit(self):
        self.parent.open_gui_editor(self.generator_data)


class Custom_variables_grid(QtGui.QWidget):
    def __init__(self, parent, board, generator_data):
        super(QtGui.QWidget, self).__init__(parent)
        grid_layout = QtGui.QGridLayout()
        variables = board.sm_info["variables"]
        init_vars = {
            v_name: v_value_str for (v_name, v_value_str) in sorted(variables.items())
        }

        variable_tabs = QtGui.QTabWidget()

        used_vars = []
        for tab in generator_data['ordered_tabs']:        # create widgets
            widget = QtGui.QWidget()
            layout = QtGui.QGridLayout()
            tab_data = generator_data[tab]
            used_vars.extend(tab_data['ordered_inputs'])
            for row,var in enumerate(tab_data['ordered_inputs']):
                control = tab_data[var]
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
            variable_tabs.addTab(widget,tab)

        leftover_widget = QtGui.QWidget()
        leftover_layout = QtGui.QGridLayout()
        leftover_vars = sorted(list( set(variables) - set(used_vars)), key=str.lower)
        leftover_vars = [v_name for v_name in leftover_vars if not v_name[-3:] == '___' and v_name != 'variable_gui']
        if len(leftover_vars) > 0:
            for row,var in enumerate(leftover_vars):
                globals()[var] = standard_var(init_vars, var, var)
                globals()[var].setBoard(board)
                globals()[var].add_to_grid(leftover_layout, row )
            leftover_widget.setLayout(leftover_layout)
            variable_tabs.addTab(leftover_widget,"...")

        grid_layout.addWidget(variable_tabs, 0, 0, QtCore.Qt.AlignLeft)
        grid_layout.setRowStretch(15, 1)

        self.setLayout(grid_layout)