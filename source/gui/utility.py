import os
from concurrent.futures import ThreadPoolExecutor
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
from source.communication.pycboard import MsgType

# --------------------------------------------------------------------------------
# GUI utility functions, classes, variables.
# --------------------------------------------------------------------------------

variable_constants = {  #  Constants that can be used in setting the value of task variables.
    "ms": 1,
    "second": 1000,
    "minute": 60000,
    "hour": 3600000,
}

# --------------------------------------------------------------------------------


class TableCheckbox(QtWidgets.QWidget):
    """Checkbox that is centered in cell when placed in table."""

    def __init__(self, parent=None):
        super(QtWidgets.QWidget, self).__init__(parent)
        self.checkbox = QtWidgets.QCheckBox(parent=parent)
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.addWidget(self.checkbox)
        self.layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.layout.setContentsMargins(0, 0, 0, 0)

    def isChecked(self):
        return self.checkbox.isChecked()

    def setChecked(self, state):
        self.checkbox.setChecked(state)


# --------------------------------------------------------------------------------


def cbox_update_options(cbox, options):
    """Update the options available in a qcombobox without changing the selection."""
    selected = str(cbox.currentText())
    available = sorted(list(set([selected] + options)), key=str.lower)
    i = available.index(selected)
    cbox.clear()
    cbox.addItems(available)
    cbox.setCurrentIndex(i)


def cbox_set_item(cbox, item_name, insert=False):
    """Set the selected item in a combobox to the name provided.  If name is
    not in item list returns False if insert is False or inserts item if insert
    is True."""
    index = cbox.findText(item_name, QtCore.Qt.MatchFlag.MatchFixedString)
    if index >= 0:
        cbox.setCurrentIndex(index)
        return True
    else:
        if insert:
            cbox.insertItem(0, item_name)
            cbox.setCurrentIndex(0)
            return True
        else:
            return False


# --------------------------------------------------------------------------------


def null_resize(widget):
    """Call a widgets resize event with its current size.  Used when rows are added
    by user to tables to prevent mangling of the table layout."""
    size = QtCore.QSize(widget.frameGeometry().width(), widget.frameGeometry().height())
    resize = QtGui.QResizeEvent(size, size)
    widget.resizeEvent(resize)


# ----------------------------------------------------------------------------------


def init_keyboard_shortcuts(widget, shortcut_dict):
    """Initialises keyboard shortcuts in the qtgui object ‘widget’.
    Shortcuts are defined in shortcut_dict where the keys are strings
    of the keysequence and values are the action (e.g. a function call) to
    execute when the keysequence is pressed."""
    for key_str, action in shortcut_dict.items():
        key_seq = QtGui.QKeySequence(key_str)
        shortcut = QtGui.QShortcut(key_seq, widget, action)


# ----------------------------------------------------------------------------------
# Detachable Tab Widget
# ----------------------------------------------------------------------------------


class detachableTabWidget(QtWidgets.QTabWidget):
    """The DetachableTabWidget adds functionality to QTabWidget that allows tabs to be
    detached and re-attached. Tabs can be detached by dragging the tab away from the
    tab bar or by double clicking the tab. Tabs are be re-attached by closing the
    detached tab window. The original ordering of the tabs is preserved when they are
    re-attached.

    Adapted from Stack Overflow post:
    https://stackoverflow.com/questions/47267195/in-pyqt4-is-it-possible-to-detach-tabs-from-a-qtabwidget

    Original by Stack Overflow user Blackwood.
    Adapted for PyQt5 by Stack Overflow user Bridgetjs.
    """

    def __init__(self, parent=None):
        super().__init__()

        self.tabBar = TabBar(self)
        self.tabBar.onDetachTabSignal.connect(self.detachTab)

        self.setTabBar(self.tabBar)

        self.detachedTabs = {}

    def setMovable(self, movable):
        """Disable default movable functionality of QTabWidget."""
        pass

    @QtCore.pyqtSlot(int, QtCore.QPoint)
    def detachTab(self, index, point):
        """Detach the tab, creating a new DetachedTab window with the contents.
        - index:  index location of the tab to be detached
        - point:  screen position for creating the new DetachedTab window.
        """
        # Get the tab content
        name = self.tabText(index)
        contentWidget = self.widget(index)

        try:
            contentWidgetRect = contentWidget.frameGeometry()
        except AttributeError:
            return

        # Create a new detached tab window
        detachedTab = DetachedTab(name, contentWidget)
        detachedTab.setWindowModality(QtCore.Qt.WindowModality.NonModal)
        detachedTab.setGeometry(contentWidgetRect)
        detachedTab.onCloseSignal.connect(self.attachTab)
        detachedTab.move(point)
        detachedTab.show()

        # Create a reference to maintain access to the detached tab
        self.detachedTabs[name] = detachedTab

    def addTab(self, contentWidget, name):
        """Assign a rank to the tab equal to the number of tabs already added.
        Tabs are ordered by rank when re-attached.
        """
        contentWidget.rank = self.count()
        super(detachableTabWidget, self).addTab(contentWidget, name)

    def attachTab(self, contentWidget, name):
        """Re-attach the tab by removing the content from the DetachedTab window,
        closing it, and placing the content back into the DetachableTabWidget.
        The tab is inserted at the index needed to order the tabs by rank.
        - contentWidget : content widget from the DetachedTab window
        - name          : name of the detached tab
        """
        # Make the content widget a child of this widget
        contentWidget.setParent(self)

        # Remove the reference
        del self.detachedTabs[name]

        # Insert tab at correct location to order tabs by rank.
        insertAt = sum([self.widget(i).rank < contentWidget.rank for i in range(self.count())])
        self.insertTab(insertAt, contentWidget, name)

    def closeDetachedTabs(self):
        """Close all tabs that are currently detached."""
        listOfDetachedTabs = []

        for key in self.detachedTabs:
            listOfDetachedTabs.append(self.detachedTabs[key])

        for detachedTab in listOfDetachedTabs:
            detachedTab.close()


class DetachedTab(QtWidgets.QMainWindow):
    """When a tab is detached, the contents are placed into this QMainWindow.
    The tab can be re-attached by closing the detached tab window.
    """

    onCloseSignal = QtCore.pyqtSignal(QtWidgets.QWidget, str)

    def __init__(self, name, contentWidget):
        QtWidgets.QMainWindow.__init__(self, None)

        self.setObjectName(name)
        self.setWindowTitle(name)

        self.contentWidget = contentWidget
        self.setCentralWidget(self.contentWidget)
        self.contentWidget.show()

    def closeEvent(self, event):
        """If the window is closed, emit the onCloseSignal and give the content
        widget back to the DetachableTabWidget
        - event : a close event
        """
        self.onCloseSignal.emit(self.contentWidget, self.objectName())


class TabBar(QtWidgets.QTabBar):
    """The TabBar class re-implements some of the functionality of the QTabBar widget
    to detect drag events and double clicks, and cause them to detach the tab.
    """

    onDetachTabSignal = QtCore.pyqtSignal(int, QtCore.QPoint)

    def __init__(self, parent=None):
        QtWidgets.QTabBar.__init__(self, parent)

        self.setAcceptDrops(True)
        self.setElideMode(QtCore.Qt.TextElideMode.ElideRight)
        self.setSelectionBehaviorOnRemove(QtWidgets.QTabBar.SelectionBehavior.SelectLeftTab)

        self.dragStartPos = QtCore.QPoint()
        self.dragDropedPos = QtCore.QPoint()
        self.mouseCursor = QtGui.QCursor()
        self.dragInitiated = False

    def mouseDoubleClickEvent(self, event):
        """Send the onDetachTabSignal when a tab is double clicked.
        - event : a mouse double click event
        """
        event.accept()
        self.onDetachTabSignal.emit(self.tabAt(event.pos()), self.mouseCursor.pos())

    def mousePressEvent(self, event):
        """Set the starting position for a drag event when the mouse button is pressed.
        - event : a mouse press event.
        """
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.dragStartPos = event.pos()

        self.dragDropedPos.setX(0)
        self.dragDropedPos.setY(0)

        self.dragInitiated = False

        QtWidgets.QTabBar.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        """If the current movement is a drag convert it into a QDrag. If the drag ends
        outside the tab bar emit an onDetachTabSignal.
        - event : a mouse move event.
        """
        # Determine if the current movement is detected as a drag
        if not self.dragStartPos.isNull() and (
            (event.pos() - self.dragStartPos).manhattanLength() < QtWidgets.QApplication.startDragDistance()
        ):
            self.dragInitiated = True

        # If the current movement is a drag initiated by the left button
        if ((event.buttons() & QtCore.Qt.MouseButton.LeftButton)) and self.dragInitiated:
            # Stop the move event
            finishMoveEvent = QtGui.QMouseEvent(
                QtCore.QEvent.Type.MouseMove,
                QtCore.QPointF(event.pos()),
                QtCore.Qt.MouseButton.NoButton,
                QtCore.Qt.MouseButton.NoButton,
                QtCore.Qt.KeyboardModifier.NoModifier,
            )
            QtWidgets.QTabBar.mouseMoveEvent(self, finishMoveEvent)

            # Convert the move event into a drag
            drag = QtGui.QDrag(self)
            mimeData = QtCore.QMimeData()
            drag.setMimeData(mimeData)
            # Create the appearance of dragging the tab content
            pixmap = self.parent().widget(self.tabAt(self.dragStartPos)).grab()
            targetPixmap = QtGui.QPixmap(pixmap.size())
            targetPixmap.fill(QtCore.Qt.GlobalColor.transparent)
            painter = QtGui.QPainter(targetPixmap)
            painter.setOpacity(0.85)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()
            drag.setPixmap(targetPixmap)

            # Initiate the drag
            dropAction = drag.exec(QtCore.Qt.DropAction.MoveAction | QtCore.Qt.DropAction.CopyAction)

            # For Linux:  Here, drag.exec() will not return MoveAction on Linux.  So it
            #             must be set manually
            if self.dragDropedPos.x() != 0 and self.dragDropedPos.y() != 0:
                dropAction = QtCore.Qt.DropAction.MoveAction

            # If the drag completed outside of the tab bar, detach the tab and move
            # the content to the current cursor position
            if dropAction == QtCore.Qt.DropAction.IgnoreAction:
                event.accept()
                self.onDetachTabSignal.emit(self.tabAt(self.dragStartPos), self.mouseCursor.pos())

        else:
            QtWidgets.QTabBar.mouseMoveEvent(self, event)

    def dropEvent(self, event):
        """Get the position of the end of the drag.
        event : a drop event.
        """
        self.dragDropedPos = event.pos()
        QtWidgets.QTabBar.dropEvent(self, event)


# ----------------------------------------------------------------------------------
# Nested Menu
# ----------------------------------------------------------------------------------


class NestedMenu(QtWidgets.QPushButton):
    """Nested menu dropdown used to select files. The menu items are the names of
    any files of a specified extension in the root_folder and it's sub-directories.
    Items are nested in the menu according to the sub-directory structure.
    initial_text is shown before anything is selected, and if add_default
    is True, initial_text is included as a menu option.
    Adapted from: https://stackoverflow.com/questions/35924235
    """

    def __init__(self, initial_text, file_extension, add_default=False):
        self.callback = lambda task: None
        self.root_menu = QtWidgets.QMenu()
        self.add_default = add_default
        self.default_text = initial_text
        self.file_extension = file_extension
        super().__init__(initial_text)

    def set_callback(self, callback_fxn):
        self.callback = callback_fxn

    def create_action(self, text):
        def fxn():
            if self.text() != text:
                self.callback(text)
                self.setText(text)

        return fxn

    def update_menu(self, root_folder):
        self.root_menu.clear()
        self.submenus_dictionary = {}
        if self.add_default:
            self.root_menu.addAction(self.default_text, self.create_action(self.default_text))
            self.root_menu.addSeparator()
        for dirName, subdirList, fileList in os.walk(root_folder):
            subdirList.sort()
            sub_dir = dirName.split(root_folder)[1][1:]
            if sub_dir:
                parent_menu = self.get_parent_menu(sub_dir)
                sub_menu_name = sub_dir.split(os.path.sep)[-1]
                sub_menu = parent_menu.addMenu(sub_menu_name)
                self.submenus_dictionary[sub_dir] = sub_menu
                for filename in sorted(fileList):
                    if filename.endswith(self.file_extension):
                        menuItem = filename[: -len(self.file_extension)]
                        sub_menu.addAction(menuItem, self.create_action(os.path.join(sub_dir, menuItem)))
            else:  # add root level files
                for filename in sorted(fileList):
                    if filename.endswith(self.file_extension):
                        menuItem = filename[: -len(self.file_extension)]
                        self.root_menu.addAction(menuItem, self.create_action(menuItem))
        self.setMenu(self.root_menu)

    def get_parent_menu(self, sub_dir):
        split_folder = sub_dir.split(os.path.sep)
        if len(split_folder) == 1:
            return self.root_menu
        else:
            return self.submenus_dictionary[os.path.sep.join(split_folder[:-1])]


# ----------------------------------------------------------------------------------
# Task Info
# ----------------------------------------------------------------------------------


class TaskInfo:
    """Class for displaying the current state and most recent event and printed line.
    Instantiates the GUI elements and has their process data method, but does not
    handle layout of the elements.
    """

    def __init__(self):
        self.state_label = QtWidgets.QLabel("State:")
        self.state_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.state_text = QtWidgets.QLineEdit("")
        self.state_text.setReadOnly(True)

        self.event_label = QtWidgets.QLabel("Event:")
        self.event_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.event_text = QtWidgets.QLineEdit("")
        self.event_text.setReadOnly(True)

        self.print_label = QtWidgets.QLabel("Print:")
        self.print_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.print_text = QtWidgets.QLineEdit("")
        self.print_text.setReadOnly(True)

    def process_data(self, new_data):
        """Update the state, event and print line info."""
        try:
            new_state = next(self.sm_info.ID2name[nd.content] for nd in reversed(new_data) if nd.type == MsgType.STATE)
            self.state_text.setText(new_state)
            self.state_text.home(False)
        except StopIteration:
            pass
        try:
            new_event = next(self.sm_info.ID2name[nd.content] for nd in reversed(new_data) if nd.type == MsgType.EVENT)
            self.event_text.setText(new_event)
            self.event_text.home(False)
        except StopIteration:
            pass
        try:
            new_print = next(
                nd.content for nd in reversed(new_data) if nd.type == MsgType.PRINT or nd.subtype == "print"
            )
            self.print_text.setText(new_print)
            self.print_text.setStyleSheet("color: black;")
            self.print_text.home(False)
        except StopIteration:
            pass
        try:
            new_warning = next(nd.content for nd in reversed(new_data) if nd.type == MsgType.WARNG)
            self.print_text.setText("! " + new_warning)
            self.print_text.setStyleSheet("color: orange;")
            self.print_text.home(False)
        except StopIteration:
            pass

    def set_state_machine(self, sm_info):
        self.sm_info = sm_info
        self.state_text.setText("")
        self.event_text.setText("")
        self.print_text.setText("")


# ----------------------------------------------------------------------------------
# Parallel call
# ----------------------------------------------------------------------------------


def parallel_call(method_name, setups):
    """Call specified method of each setup in in parallel using
    ThreadPoolExecutor. Print output is delayed during multithreaded
    operations to avoid error message when trying to call PyQt method
    from annother thread."""
    func = lambda setup: getattr(setup, method_name)()
    for setup in setups:
        setup.start_delayed_print()
    with ThreadPoolExecutor(max_workers=len(setups)) as executor:
        list(executor.map(func, setups))
    for setup in setups:
        setup.end_delayed_print()
