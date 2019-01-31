from pyqtgraph.Qt import QtGui, QtCore, QtWidgets

# --------------------------------------------------------------------------------
# GUI utility functions, classes, variables.
# --------------------------------------------------------------------------------

variable_constants = { #  Constants that can be used in setting the value of task variables.
                        'ms'    : 1,
                        'second': 1000,
                        'minute': 60000,
                        'hour'  : 3600000
                     }

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

def cbox_set_item(cbox, item_name, insert=False):
    '''Set the selected item in a combobox to the name provided.  If name is
    not in item list returns False if insert is False or inserts item if insert 
    is True.'''
    index = cbox.findText(item_name, QtCore.Qt.MatchFixedString)
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
    '''Call a widgets resize event with its current size.  Used when rows are added
    by user to tables to prevent mangling of the table layout.'''
    size = QtCore.QSize(widget.frameGeometry().width(), widget.frameGeometry().height())
    resize = QtGui.QResizeEvent(size, size)
    widget.resizeEvent(resize)

# ----------------------------------------------------------------------------------
# Detachable Tab Widget
# ----------------------------------------------------------------------------------

class detachableTabWidget(QtWidgets.QTabWidget):
    '''The DetachableTabWidget adds functionality to QTabWidget that
    allows tabs to be detached and re-attached. Tabs can be detached
    by dragging the tab away from the tab bar or by double clicking
    the tab. Tabs can be re-attached by dragging them onto the tab 
    widget or by closing the detached tab window.  The original order
    of the tabs is preserved when they are re-attached.

    Adapted from Stack Overflow post:
    https://stackoverflow.com/questions/47267195/in-pyqt4-is-it-possible-to-detach-tabs-from-a-qtabwidget

    Original by Stack Overflow user Blackwood.
    Adapted for PyQt5 by Stack Overflow user Bridgetjs.
    '''

    def __init__(self, parent=None):

        super().__init__()

        self.tabBar = TabBar(self)
        self.tabBar.onDetachTabSignal.connect(self.detachTab)

        self.setTabBar(self.tabBar)

        self.detachedTabs = {}

        QtWidgets.qApp.aboutToQuit.connect(self.closeDetachedTabs) # Close all detached tabs if the application is closed explicitly

    def setMovable(self, movable):
        '''Disable default movable functionality of QTabWidget.'''
        pass

    @QtCore.pyqtSlot(int, QtCore.QPoint)
    def detachTab(self, index, point):
        '''Detach the tab by removing it's contents and placing them 
        in a DetachedTab window.
        - index:  index location of the tab to be detached
        - point:  screen position for creating the new DetachedTab window.
        '''
        # Get the tab content
        name = self.tabText(index)
        contentWidget = self.widget(index)

        try:
            contentWidgetRect = contentWidget.frameGeometry()
        except AttributeError:
            return

        # Create a new detached tab window
        detachedTab = DetachedTab(name, contentWidget)
        detachedTab.setWindowModality(QtCore.Qt.NonModal)
        detachedTab.setGeometry(contentWidgetRect)
        detachedTab.onCloseSignal.connect(self.attachTab)
        detachedTab.onDropSignal.connect(self.detachedTabDrop)
        detachedTab.move(point)
        detachedTab.show()

        # Create a reference to maintain access to the detached tab
        self.detachedTabs[name] = detachedTab

    def addTab(self, contentWidget, name):
        '''Assign a rank to the tab equal to the number of tabs
        already added.  Tabs are ordered by rank when re-attached.
        '''
        contentWidget.rank = self.count()
        super(detachableTabWidget, self).addTab(contentWidget, name)

    def attachTab(self, contentWidget, name):
        '''Re-attach the tab by removing the content from the 
        DetachedTab window, closing it, and placing the content back
        into the DetachableTabWidget.  The tab is inserted at
        the index needed to order the tabs by their rank attribute.
        - contentWidget : content widget from the DetachedTab window
        - name          : name of the detached tab
        '''
        # Make the content widget a child of this widget
        contentWidget.setParent(self)

        # Remove the reference
        del self.detachedTabs[name]

        # Insert tab at correct location to order tabs by rank.
        insertAt = sum([self.widget(i).rank < contentWidget.rank
                        for i in range(self.count())])
        index = self.insertTab(insertAt, contentWidget, name)

        # Make this tab the current tab
        if index > -1:
            self.setCurrentIndex(index)

    @QtCore.pyqtSlot(str, QtCore.QPoint)
    def detachedTabDrop(self, name, dropPos):
        '''Reatach tab if dropped on detachableTabWidget.
        - name    : name of the detached tab
        - dropPos : mouse cursor position when the drop occurred
        '''
        tabDropPos = self.mapFromGlobal(dropPos)
        if self.rect().contains(tabDropPos):
            self.detachedTabs[name].close()

    def closeDetachedTabs(self):
        '''Close all tabs that are currently detached.'''
        listOfDetachedTabs = []

        for key in self.detachedTabs:
            listOfDetachedTabs.append(self.detachedTabs[key])

        for detachedTab in listOfDetachedTabs:
            detachedTab.close()


class DetachedTab(QtWidgets.QMainWindow):
    '''When a tab is detached, the contents are placed into this
    QMainWindow.  The tab can be re-attached by closing the dialog
    or by dragging the window into the tab bar.
    '''
    onCloseSignal = QtCore.pyqtSignal(QtWidgets.QWidget, str)
    onDropSignal = QtCore.pyqtSignal(str, QtCore.QPoint)

    def __init__(self, name, contentWidget):
        QtWidgets.QMainWindow.__init__(self, None)

        self.setObjectName(name)
        self.setWindowTitle(name)

        self.contentWidget = contentWidget
        self.setCentralWidget(self.contentWidget)
        self.contentWidget.show()

        self.windowDropFilter = WindowDropFilter()
        self.installEventFilter(self.windowDropFilter)
        self.windowDropFilter.onDropSignal.connect(self.windowDropSlot)

    @QtCore.pyqtSlot(QtCore.QPoint)
    def windowDropSlot(self, dropPos):
        '''Handle a window drop event.
        - dropPos :mouse cursor position of the drop
        '''
        self.onDropSignal.emit(self.objectName(), dropPos)

    def closeEvent(self, event):
        '''If the window is closed, emit the onCloseSignal and 
        give the content widget back to the DetachableTabWidget
        - event : a close event
        '''
        self.onCloseSignal.emit(self.contentWidget, self.objectName())


class WindowDropFilter(QtCore.QObject):
    '''An event filter class to detect a QMainWindow drop event.'''
    onDropSignal = QtCore.pyqtSignal(QtCore.QPoint)

    def __init__(self):
        QtCore.QObject.__init__(self)
        self.lastEvent = None

    def eventFilter(self, obj, event):
        ''' Detect a QMainWindow drop event by looking for a
        NonClientAreaMouseMove (173) event that 
        immediately follows a Move event.
        - obj   : the object that generated the event
        - event : the current event
        '''
        # If a NonClientAreaMouseMove (173) event immediately follows a Move event...
        if self.lastEvent == QtCore.QEvent.Move and event.type() == 173:
            # Determine the position of the mouse cursor and emit it with the
            # onDropSignal
            mouseCursor = QtGui.QCursor()
            dropPos = mouseCursor.pos()
            self.onDropSignal.emit(dropPos)
            self.lastEvent = event.type()
            return True
        else:
            self.lastEvent = event.type()
            return False


class TabBar(QtWidgets.QTabBar):
    '''The TabBar class re-implements some of the functionality
    of the QTabBar widget.
    '''
    onDetachTabSignal = QtCore.pyqtSignal(int, QtCore.QPoint)

    def __init__(self, parent=None):
        QtWidgets.QTabBar.__init__(self, parent)

        self.setAcceptDrops(True)
        self.setElideMode(QtCore.Qt.ElideRight)
        self.setSelectionBehaviorOnRemove(QtWidgets.QTabBar.SelectLeftTab)

        self.dragStartPos = QtCore.QPoint()
        self.dragDropedPos = QtCore.QPoint()
        self.mouseCursor = QtGui.QCursor()
        self.dragInitiated = False

    def mouseDoubleClickEvent(self, event):
        '''Send the onDetachTabSignal when a tab is double clicked.
        - event : a mouse double click event
        '''
        event.accept()
        self.onDetachTabSignal.emit(self.tabAt(event.pos()), self.mouseCursor.pos())

    def mousePressEvent(self, event):
        '''Set the starting position for a drag event when the 
        mouse button is pressed.
        - event : a mouse press event.
        '''
        if event.button() == QtCore.Qt.LeftButton:
            self.dragStartPos = event.pos()

        self.dragDropedPos.setX(0)
        self.dragDropedPos.setY(0)

        self.dragInitiated = False

        QtWidgets.QTabBar.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        '''Determine if the current movement is a drag.  If it is,
        convert it into a QDrag. If the drag ends outside the tab bar,
        emit an onDetachTabSignal.
        - event : a mouse move event.
        '''
        # Determine if the current movement is detected as a drag
        if not self.dragStartPos.isNull() and ((event.pos() - self.dragStartPos).manhattanLength() < QtWidgets.QApplication.startDragDistance()):
            self.dragInitiated = True

        # If the current movement is a drag initiated by the left button
        if (((event.buttons() & QtCore.Qt.LeftButton)) and self.dragInitiated):

            # Stop the move event
            finishMoveEvent = QtGui.QMouseEvent(QtCore.QEvent.MouseMove, event.pos(), QtCore.Qt.NoButton, QtCore.Qt.NoButton, QtCore.Qt.NoModifier)
            QtWidgets.QTabBar.mouseMoveEvent(self, finishMoveEvent)

            # Convert the move event into a drag
            drag = QtGui.QDrag(self)
            mimeData = QtCore.QMimeData()
            # mimeData.setData('action', 'application/tab-detach')
            drag.setMimeData(mimeData)
            # screen = QScreen(self.parentWidget().currentWidget().winId())
            # Create the appearance of dragging the tab content
            pixmap = self.parent().widget(self.tabAt(self.dragStartPos)).grab()
            targetPixmap = QtGui.QPixmap(pixmap.size())
            targetPixmap.fill(QtCore.Qt.transparent)
            painter = QtGui.QPainter(targetPixmap)
            painter.setOpacity(0.85)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()
            drag.setPixmap(targetPixmap)

            # Initiate the drag
            dropAction = drag.exec_(QtCore.Qt.MoveAction | QtCore.Qt.CopyAction)

            # For Linux:  Here, drag.exec_() will not return MoveAction on Linux.  So it
            #             must be set manually
            if self.dragDropedPos.x() != 0 and self.dragDropedPos.y() != 0:
                dropAction = QtCore.Qt.MoveAction

            # If the drag completed outside of the tab bar, detach the tab and move
            # the content to the current cursor position
            if dropAction == QtCore.Qt.IgnoreAction:
                event.accept()
                self.onDetachTabSignal.emit(self.tabAt(self.dragStartPos), self.mouseCursor.pos())
                
        else:
            QtWidgets.QTabBar.mouseMoveEvent(self, event)

    def dropEvent(self, event):
        '''Get the position of the end of the drag
         event : a drop event.
         '''
        self.dragDropedPos = event.pos()
        QtWidgets.QTabBar.dropEvent(self, event)