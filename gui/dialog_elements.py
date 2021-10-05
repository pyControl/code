from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
from gui.utility import variable_constants

class spin_var:
    def __init__(self, init_var_dict, label, min, max, step, varname):
        center = QtCore.Qt.AlignCenter
        Vcenter = QtCore.Qt.AlignVCenter
        right = QtCore.Qt.AlignRight
        button_width = 65
        spin_width = 85
        self.label = QtGui.QLabel(label)
        self.label.setAlignment(right | Vcenter)
        self.varname = varname

        if isinstance(min, float) or isinstance(max, float) or isinstance(step, float):
            self.spn = QtGui.QDoubleSpinBox()
        else:
            self.spn = QtGui.QSpinBox()

        self.spn.setRange(min, max)
        self.spn.setValue(eval(init_var_dict[varname]))
        self.spn.setSingleStep(step)
        self.spn.setAlignment(center)
        self.spn.setMinimumWidth(spin_width)
        self.value_text_colour("gray")

        self.get_btn = QtGui.QPushButton("Get")
        self.get_btn.setMinimumWidth(button_width)
        self.get_btn.setMaximumWidth(button_width)
        self.get_btn.setAutoDefault(False)
        self.get_btn.clicked.connect(self.get)

        self.set_btn = QtGui.QPushButton("Set")
        self.set_btn.setMinimumWidth(button_width)
        self.set_btn.setMaximumWidth(button_width)
        self.set_btn.setAutoDefault(False)
        self.set_btn.clicked.connect(self.set)

    def add_to_grid(self, grid, row):
        grid.addWidget(self.label, row, 0)
        grid.addWidget(self.spn, row, 1)
        grid.addWidget(self.get_btn, row, 2)
        grid.addWidget(self.set_btn, row, 3)

    def setEnabled(self, doEnable):
        self.label.setEnabled(doEnable)
        self.spn.setEnabled(doEnable)
        self.get_btn.setEnabled(doEnable)
        self.set_btn.setEnabled(doEnable)

    def setBoard(self, board):
        self.board = board

    def get(self):
        if self.board.framework_running:  # Value returned later.
            self.board.get_variable(self.varname)
            QtCore.QTimer.singleShot(200, self.reload)
        else:  # Value returned immediately.
            self.spn.setValue(self.board.get_variable(self.varname))

    def set(self):
        self.board.set_variable(self.varname, round(self.spn.value(), 2))
        if self.board.framework_running:  # Value returned later.
            QtCore.QTimer.singleShot(200, self.reload)
        else:  # Value returned immediately.
            msg = QtGui.QMessageBox()
            msg.setText("Variable Changed")
            msg.exec()
            self.spn.setValue(self.board.get_variable(self.varname))

    def reload(self):
        """Reload value from sm_info.  sm_info is updated when variables are output
        during framework run due to get/set."""
        self.value_text_colour("black")
        self.spn.setValue(eval(str(self.board.sm_info["variables"][self.varname])))
        QtCore.QTimer.singleShot(1000, self.value_text_colour)

    def setVisible(self, makeVisible):
        self.label.setVisible(makeVisible)
        self.spn.setVisible(makeVisible)
        self.get_btn.setVisible(makeVisible)
        self.set_btn.setVisible(makeVisible)

    def setHint(self, hint):
        self.label.setToolTip(hint)

    def value_text_colour(self, color="gray"):
        self.spn.setStyleSheet("color: {};".format(color))

    def setSuffix(self,suffix):
        self.spn.setSuffix(suffix)

class standard_var:
    def __init__(self, init_var_dict, label, varname, text_width=80):
        center = QtCore.Qt.AlignCenter
        Vcenter = QtCore.Qt.AlignVCenter
        right = QtCore.Qt.AlignRight
        button_width = 65
        self.label = QtGui.QLabel(label)
        self.label.setAlignment(right | Vcenter)
        self.varname = varname

        self.line_edit = QtGui.QLineEdit()
        self.line_edit.setAlignment(center)
        self.line_edit.setMinimumWidth(text_width)
        self.line_edit.setMaximumWidth(text_width)
        self.line_edit.setText(init_var_dict[varname])
        self.line_edit.textChanged.connect(lambda x: self.value_text_colour("black"))
        self.line_edit.returnPressed.connect(self.set)
        self.value_text_colour("gray")

        self.get_btn = QtGui.QPushButton("Get")
        self.get_btn.setMinimumWidth(button_width)
        self.get_btn.setMaximumWidth(button_width)
        self.get_btn.setAutoDefault(False)
        self.get_btn.clicked.connect(self.get)

        self.set_btn = QtGui.QPushButton("Set")
        self.set_btn.setMinimumWidth(button_width)
        self.set_btn.setMaximumWidth(button_width)
        self.set_btn.setAutoDefault(False)
        self.set_btn.clicked.connect(self.set)

    def add_to_grid(self, grid, row):
        grid.addWidget(self.label, row, 0)
        grid.addWidget(self.line_edit, row, 1)
        grid.addWidget(self.get_btn, row, 2)
        grid.addWidget(self.set_btn, row, 3)

    def setEnabled(self, doEnable):
        self.label.setEnabled(doEnable)
        self.line_edit.setEnabled(doEnable)
        self.get_btn.setEnabled(doEnable)
        self.set_btn.setEnabled(doEnable)

    def setBoard(self, board):
        self.board = board

    def get(self):
        if self.board.framework_running:  # Value returned later.
            self.board.get_variable(self.varname)
            QtCore.QTimer.singleShot(200, self.reload)
        else:  # Value returned immediately.
            self.line_edit.setText(str(self.board.get_variable(self.varname)))

    def set(self):
        try:
            v_value = eval(self.line_edit.text(), variable_constants)
        except Exception:
            self.line_edit.setText("Invalid value")
            return
        self.board.set_variable(self.varname, v_value)
        if self.board.framework_running:  # Value returned later.
            QtCore.QTimer.singleShot(200, self.reload)
        else:  # Value returned immediately.
            msg = QtGui.QMessageBox()
            msg.setText("Variable Changed")
            msg.exec()
            self.line_edit.setText(str(self.board.get_variable(self.varname)))

    def reload(self):
        """Reload value from sm_info.  sm_info is updated when variables are output
        during framework run due to get/set."""
        self.value_text_colour("black")
        self.line_edit.setText(str(self.board.sm_info["variables"][self.varname]))
        QtCore.QTimer.singleShot(1000, self.value_text_colour)

    def setHint(self, hint):
        self.label.setToolTip(hint)

    def value_text_colour(self, color="gray"):
        self.line_edit.setStyleSheet("color: {};".format(color))

class checkbox_var:
    def __init__(self, init_var_dict, label, varname):
        self.varname = varname
        self.label = QtGui.QLabel(label)
        self.label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        self.checkbox = QtGui.QCheckBox()
        self.checkbox.setChecked(eval(init_var_dict[varname]))
        self.checkbox.clicked.connect(self.set)

    def setBoard(self, board):
        self.board = board
    
    def add_to_grid(self, grid, row):
        grid.addWidget(self.label, row, 0)
        grid.addWidget(self.checkbox, row, 1)
    
    def set(self):
        self.board.set_variable(self.varname,self.checkbox.isChecked()) 
        if not self.board.framework_running: # Value returned later.
            msg = QtGui.QMessageBox()
            msg.setText("Variable Changed")
            msg.exec()

    def setHint(self, hint):
        self.label.setToolTip(hint)

