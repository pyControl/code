from pyqtgraph.Qt import QtGui, QtCore

# --------------------------------------------------------------------------------
# GUI utility functions and classes
# --------------------------------------------------------------------------------

class TableCheckbox(QtGui.QWidget):
    '''Checkbox that is centered in cell when placed in table.'''

    def __init__(self, parent=None):
        super(QtGui.QWidget, self).__init__(parent)
        self.checkbox = QtGui.QCheckBox(parent=parent)
        self.layout = QtGui.QHBoxLayout(self)
        self.layout.addWidget(self.checkbox)
        self.layout.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.setContentsMargins(0,0,0,0)

    def isChecked(self):
        return self.checkbox.isChecked()

    def setChecked(self, state):
        self.checkbox.setChecked(state)

# --------------------------------------------------------------------------------

def cbox_update_options(cbox, options):
    '''Update the options available in a qcombobox without changing the selection.'''
    selected = str(cbox.currentText())
    available = sorted(list(set([selected]+options)))
    i = available.index(selected)
    cbox.clear()
    cbox.addItems(available)
    cbox.setCurrentIndex(i)

def cbox_set_item(cbox, item_name):
    '''Set the selected item in a combobox to the name provided'''
    index = cbox.findText(item_name, QtCore.Qt.MatchFixedString)
    if index >= 0:
         cbox.setCurrentIndex(index)
         return True
    else:
        return False