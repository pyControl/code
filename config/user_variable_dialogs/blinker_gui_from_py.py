# This is an example custom dialog for more advanced users.
# Complex custom dialogs can be directly coded using the PyQt framework

from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
from gui.custom_variables_dialog import Slider_var, Spin_var

# Custom Variable dialog
class Custom_variables_dialog(QtWidgets.QDialog):
    # Dialog for setting and getting task variables.
    def __init__(self, parent, board):
        super(QtWidgets.QDialog, self).__init__(parent)
        self.setWindowTitle("Blink Variable GUI")
        self.layout = QtWidgets.QVBoxLayout(self)
        self.variables_grid = Variables_grid(self, board)
        self.layout.addWidget(self.variables_grid)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)


class Variables_grid(QtWidgets.QWidget):
    def __init__(self, parent, board):
        super(QtWidgets.QWidget, self).__init__(parent)
        variables = board.sm_info["variables"]
        self.grid_layout = QtWidgets.QGridLayout()
        initial_variables_dict = {v_name: v_value_str for (v_name, v_value_str) in sorted(variables.items())}
        self.variables_gui = Variables_gui(self, self.grid_layout, board, initial_variables_dict)
        self.setLayout(self.grid_layout)


class Variables_gui(QtWidgets.QWidget):
    def __init__(self, parent, grid_layout, board, init_vars):
        super(QtWidgets.QWidget, self).__init__(parent)
        self.board = board

        # create widgets
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QGridLayout()
        row = 0

        # blink rate controls
        self.blink_rate = Slider_var(init_vars, "⏱️ <b>Blink Rate</b>", 1, 15, 0.5, "blink_rate")
        self.blink_rate.setSuffix(" Hz")
        self.blink_rate.setHint("Frequency of alternating LED blinks")
        self.blink_rate.setBoard(board)
        self.blink_rate.add_to_grid(layout, row)
        row += 1
        self.min_btn = QtWidgets.QPushButton("min")
        self.mid_btn = QtWidgets.QPushButton("50%")
        self.max_btn = QtWidgets.QPushButton("max")
        for col,btn in enumerate([self.min_btn,self.mid_btn,self.max_btn]):
            layout.addWidget(btn, row,col, QtCore.Qt.AlignmentFlag.AlignCenter)
            btn.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
            btn.setMaximumWidth(70)
        row += 1

        # separator
        layout.addWidget(QtWidgets.QLabel("<hr>"), row, 0, 1, 4)
        row += 1

        # radio buttons
        red_is_enabled = eval(init_vars["red_enabled"])
        green_is_enabled = eval(init_vars["green_enabled"])
        self.both_radio = QtWidgets.QRadioButton()
        self.both_lbl = QtWidgets.QLabel("🔴Both🟢")
        self.red_radio = QtWidgets.QRadioButton()
        self.red_lbl = QtWidgets.QLabel("Red")
        self.red_lbl.setStyleSheet("border:3px solid red;background:red;border-radius:3px;")  # you can use css styling
        self.green_radio = QtWidgets.QRadioButton()
        self.green_lbl = QtWidgets.QLabel("Green")
        self.green_lbl.setStyleSheet("border-radius:3px;border:3px solid green;background:green;color:white")
        if red_is_enabled and green_is_enabled:
            self.both_radio.setChecked(True)
            self.red_radio.setChecked(False)
            self.green_radio.setChecked(False)
        else:
            self.both_radio.setChecked(False)
            if red_is_enabled:
                self.red_radio.setChecked(True)
                self.green_radio.setChecked(False)
            elif green_is_enabled:
                self.red_radio.setChecked(False)
                self.green_radio.setChecked(True)
            else:
                self.red_radio.setChecked(False)
                self.green_radio.setChecked(False)

        layout.addWidget(self.both_lbl, row, 0, QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.red_lbl, row, 1, QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.green_lbl, row, 2, QtCore.Qt.AlignmentFlag.AlignCenter)
        row += 1
        layout.addWidget(self.both_radio, row, 0, QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.red_radio, row, 1, QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.green_radio, row, 2, QtCore.Qt.AlignmentFlag.AlignCenter)
        row += 1

        # counts
        self.red_count = Spin_var(init_vars, "<b>Red count</b>", 1, 10, 1, "red_count")
        self.red_count.setBoard(board)
        self.red_count.add_to_grid(layout, row)
        row += 1
        self.green_count = Spin_var(init_vars, "<b>Green count</b>", 1, 10, 1, "green_count")
        self.green_count.setBoard(board)
        self.green_count.add_to_grid(layout, row)
        row += 1

        # image
        self.picture = QtWidgets.QLabel()
        image = QtGui.QPixmap("config/user_variable_dialogs/example_image.png")
        self.picture.setPixmap(image)
        layout.addWidget(self.picture, row, 0, 1, 4)
        row += 1

        # gif
        self.gif = QtWidgets.QLabel()
        self.movie = QtGui.QMovie("config/user_variable_dialogs/example_movie.gif")
        self.gif.setMovie(self.movie)
        self.movie.start()
        layout.addWidget(self.gif, row, 0, 1, 4)
        row += 1

        layout.setRowStretch(row, 1)
        widget.setLayout(layout)
        grid_layout.addWidget(widget, 0, 0, QtCore.Qt.AlignmentFlag.AlignLeft)

        # connect some buttons to functions
        self.min_btn.clicked.connect(self.slide_to_min)
        self.mid_btn.clicked.connect(self.slide_to_mid)
        self.max_btn.clicked.connect(self.slide_to_max)
        self.both_radio.clicked.connect(self.update_count_options)
        self.red_radio.clicked.connect(self.update_count_options)
        self.green_radio.clicked.connect(self.update_count_options)

        # add close shortcut
        self.close_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+W"), self)
        self.close_shortcut.activated.connect(self.close)

    def update_count_options(self):
        red_val = self.red_radio.isChecked() | self.both_radio.isChecked()
        green_val = self.green_radio.isChecked() | self.both_radio.isChecked()
        self.board.set_variable("red_enabled", red_val)  # update variable
        self.board.set_variable("green_enabled", green_val)
        self.red_count.setEnabled(red_val)  # enable or disable control
        self.green_count.setEnabled(green_val)
        if not self.board.framework_running:  # Value returned later.
            msg = QtWidgets.QMessageBox()
            msg.setText("Variable Changed")
            msg.exec()

    def slide_to_min(self):
        self.blink_rate.slider.setValue(1)
        self.blink_rate.update_val_lbl()
        self.blink_rate.set()

    def slide_to_mid(self):
        self.blink_rate.slider.setValue(7.5)
        self.blink_rate.update_val_lbl()
        self.blink_rate.set()

    def slide_to_max(self):
        self.blink_rate.slider.setValue(15)
        self.blink_rate.update_val_lbl()
        self.blink_rate.set()
