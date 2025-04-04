# -*- coding: utf-8 -*-

from functools import partial
from dwpicker.pyside import QtGui, QtCore, QtWidgets
from dwpicker.colorwheel import ColorDialog
from dwpicker.dialog import get_image_path
from dwpicker.geometry import grow_rect
from dwpicker.path import format_path
from dwpicker.qtutils import icon
from dwpicker.stack import count_panels

# don't use style sheet like that, find better design
TOGGLER_STYLESHEET = (
    'background: rgb(0, 0, 0, 75); text-align: left; font: bold')
X = '✘'
V = '✔'


class BoolCombo(QtWidgets.QComboBox):
    valueSet = QtCore.Signal(bool)

    def __init__(self, state=True, parent=None):
        super(BoolCombo, self).__init__(parent)
        self.addItem('True')
        self.addItem('False')
        self.setCurrentText(str(state))
        self.currentIndexChanged.connect(self.current_index_changed)

    def state(self):
        return self.currentText() == 'True'

    def current_index_changed(self):
        self.valueSet.emit(self.state())


class BrowseEdit(QtWidgets.QWidget):
    valueSet = QtCore.Signal(str)

    def __init__(self, parent=None):
        super(BrowseEdit, self).__init__(parent)

        self.text = QtWidgets.QLineEdit()
        self.text.returnPressed.connect(self.apply)
        self.text.focusOutEvent = self.text_focus_out_event
        self.button = QtWidgets.QToolButton(self)
        self.button.setIcon(icon('mini-open.png'))
        self.button.setFixedSize(21, 21)
        self.button.released.connect(self.browse)

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.text)
        self.layout.addWidget(self.button)

        self._value = self.value()

    def text_focus_out_event(self, _):
        self.apply()

    def browse(self):
        filename = get_image_path(self) or ''
        format_path(filename)
        if not filename:
            return
        self.text.setText(filename)
        self.apply()

    def apply(self):
        text = format_path(self.text.text())
        self.text.setText(text)
        self.valueSet.emit(text)

    def value(self):
        value = format(self.text.text())
        return value if value != '' else None

    def set_value(self, value):
        self.text.setText(value)


class WidgetToggler(QtWidgets.QPushButton):
    def __init__(self, label, widget, parent=None):
        super(WidgetToggler, self).__init__(parent)
        self.setStyleSheet(TOGGLER_STYLESHEET)
        self.setText(' v ' + label)
        self.widget = widget
        self.setCheckable(True)
        self.setChecked(True)
        self.toggled.connect(self._call_toggled)

    def _call_toggled(self, state):
        if state is True:
            self.widget.show()
            self.setText(self.text().replace('>', 'v'))
        else:
            self.widget.hide()
            self.setText(self.text().replace('v', '>'))


class ColorButton(QtWidgets.QAbstractButton):
    def __init__(self, parent=None):
        super(ColorButton, self).__init__(parent)
        self.color = 'grey'
        self.setFixedSize(21, 21)
        self.hover = False

    def enterEvent(self, event):
        self.hover = True
        self.update()

    def leaveEvent(self, event):
        self.hover = False
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setBrush(QtGui.QColor(self.color))
        painter.setPen(QtCore.Qt.black)
        rect = self.rect()
        rect.setWidth(rect.width() - 1)
        rect.setHeight(rect.height() - 1)
        painter.drawRect(rect)
        if not self.hover:
            painter.end()
            return
        rect = grow_rect(rect, -3).toRect()
        pixmap = icon('picker.png').pixmap(rect.size())
        painter.drawPixmap(rect, pixmap)
        painter.end()


class ColorEdit(QtWidgets.QWidget):
    valueSet = QtCore.Signal(str)

    def __init__(self, parent=None):
        super(ColorEdit, self).__init__(parent)

        self.color = ColorButton()
        self.color.released.connect(self.pick_color)
        self.text = QtWidgets.QLineEdit()
        self.text.returnPressed.connect(self.apply)
        self.text.focusInEvent = self.focusInEvent
        self.text.focusOutEvent = self.focusOutEvent

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.color)
        self.layout.addWidget(self.text)
        self.layout.setStretchFactor(self.color, 1)
        self.layout.setStretchFactor(self.text, 5)

        self._value = self.value()

    def focusInEvent(self, event):
        self._value = self.value()
        return super(ColorEdit, self).focusInEvent(event)

    def focusOutEvent(self, event):
        self.apply()
        return super(ColorEdit, self).focusOutEvent(event)

    def pick_color(self):
        color = self.text.text() or None
        dialog = ColorDialog(color)
        if dialog.exec_():
            self.text.setText(dialog.colorname())
            self.color.color = dialog.colorname()
            self.color.update()
            self.apply()

    def apply(self):
        self.color.color = self.value()
        self.color.update()
        if self._value != self.value():
            self.valueSet.emit(self.value())
        self._value = self.value()

    def value(self):
        value = self.text.text()
        return value if value != '' else None

    def set_color(self, color=None):
        self.color.color = color or 'grey'
        self.text.setText(color)
        self.color.update()


class LineEdit(QtWidgets.QLineEdit):
    valueSet = QtCore.Signal(float)
    VALIDATOR_CLS = QtGui.QDoubleValidator

    def __init__(self, minimum=None, maximum=None, parent=None):
        super(LineEdit, self).__init__(parent)
        self.validator = self.VALIDATOR_CLS() if self.VALIDATOR_CLS else None
        if minimum is not None:
            self.validator.setBottom(minimum)
        if maximum is not None:
            self.validator.setTop(maximum)
        self.setValidator(self.validator)
        self._value = self.value()
        self.returnPressed.connect(self.apply)

    def focusInEvent(self, event):
        self._value = self.value()
        return super(LineEdit, self).focusInEvent(event)

    def focusOutEvent(self, event):
        self.apply()
        return super(LineEdit, self).focusOutEvent(event)

    def apply(self):
        if self._value != self.value():
            self.valueSet.emit(self.value())
        self._value = self.value()

    def value(self):
        if self.text() == '':
            return None
        return float(self.text().replace(',', '.'))


class TextEdit(LineEdit):
    VALIDATOR_CLS = None
    valueSet = QtCore.Signal(str)

    def value(self):
        if self.text() == '':
            return None
        return self.text()


class NumEdit(LineEdit):
    valueSet = QtCore.Signal(float)
    VALIDATOR_CLS = QtGui.QDoubleValidator

    def __init__(self, minimum=None, maximum=None, parent=None):
        super(NumEdit, self).__init__(parent)
        self.dragging = False
        self.init_mouse_pos = QtCore.QPoint()
        self.last_mouse_pos = QtCore.QPoint()

        self.minimum = minimum
        self.maximum = maximum
        # Minimum horizontal pixels to move before adjusting value
        self.drag_threshold = 15

        self.setMouseTracking(True)

    def mousePressEvent(self, event):
        if event.button() != QtCore.Qt.MiddleButton:
            return super(NumEdit, self).mousePressEvent(event)

        self.setStyleSheet("background-color: #5285A6;")
        self.clearFocus()
        self.dragging = True
        self.init_mouse_pos = event.globalPos()
        self.last_mouse_pos = event.globalPos()
        event.accept()

    def mouseMoveEvent(self, event):
        if not self.dragging:
            return super(NumEdit, self).mouseMoveEvent(event)

        delta = event.globalPos() - self.last_mouse_pos
        self.last_mouse_pos = event.globalPos()

        delta_threshold = abs(
            self.init_mouse_pos.x() - self.last_mouse_pos.x())
        if self.drag_threshold:
            if delta_threshold < self.drag_threshold:
                return
            self.drag_threshold = False

        self.setStyleSheet("")
        current_value = float(self.text()) if self.text() else 0.0

        is_integer = self.VALIDATOR_CLS == QtGui.QIntValidator
        step = 1 if is_integer else 0.1
        adjustment = delta.x() * step
        new_value = current_value + adjustment

        if self.validator:
            min_val, max_val = self.validator.bottom(), self.validator.top()
            new_value = max(min_val, min(new_value, max_val))

        if is_integer:
            self.setText(str(int(new_value)))
        else:
            self.setText("{0:.2f}".format(new_value))

    def mouseReleaseEvent(self, event):
        self.drag_threshold = 15
        self.setStyleSheet("")
        if event.button() != QtCore.Qt.MiddleButton:
            return super(NumEdit, self).mouseReleaseEvent(event)

        self.dragging = False
        event.accept()
        self.emit_value()
        self.clearFocus()

    def emit_value(self):
        current_value = self.value()
        if current_value is not None:
            self.valueSet.emit(current_value)

    def value(self):
        if self.text() == '':
            return None
        return float(self.text().replace(',', '.'))

    def enterEvent(self, event):
        if not self.hasFocus():
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.SplitHCursor)
        super(NumEdit, self).enterEvent(event)

    def leaveEvent(self, event):
        QtWidgets.QApplication.restoreOverrideCursor()
        super(NumEdit, self).leaveEvent(event)

    def focusInEvent(self, event):
        QtWidgets.QApplication.restoreOverrideCursor()
        super(NumEdit, self).focusInEvent(event)

    def focusOutEvent(self, event):
        if self.underMouse():
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.SplitHCursor)
        super(NumEdit, self).focusOutEvent(event)


class FloatEdit(NumEdit):
    valueSet = QtCore.Signal(float)
    VALIDATOR_CLS = QtGui.QDoubleValidator

    def __init__(self, maximum=None, minimum=None, decimals=2, parent=None):
        super(FloatEdit, self).__init__(maximum, minimum, parent)

        if minimum is None and maximum is None:
            self.validator = None
        else:
            # using sys.maxsize creates an overflow error, float('inf') is not
            # sipported by python 2
            maximum = 999999999. if maximum is None else maximum
            self.validator = self.VALIDATOR_CLS(
                minimum, maximum, decimals, self)
            self.setValidator(self.validator)


class IntEdit(NumEdit):
    valueSet = QtCore.Signal(int)
    VALIDATOR_CLS = QtGui.QIntValidator

    def __init__(self, maximum=None, minimum=None, parent=None):
        super(IntEdit, self).__init__(maximum, minimum, parent)

        if minimum is None and maximum is None:
            self.validator = None
        else:
            # using sys.maxsize creates an overflow error.
            maximum = 999999999 if maximum is None else maximum
            self.validator = self.VALIDATOR_CLS(minimum, maximum, self)
            self.setValidator(self.validator)

    def value(self):
        if self.text() == '':
            return None
        return int(float(self.text()))


class Title(QtWidgets.QLabel):
    def __init__(self, title, parent=None):
        super(Title, self).__init__(parent)
        self.setFixedHeight(20)
        self.setStyleSheet('background: rgb(0, 0, 0, 25)')
        self.setText('<b>&nbsp;&nbsp;&nbsp;' + title)


class TouchEdit(QtWidgets.QLineEdit):
    def keyPressEvent(self, event):
        self.setText(QtGui.QKeySequence(event.key()).toString().lower())
        self.textEdited.emit(self.text())


class CommandButton(QtWidgets.QWidget):
    released = QtCore.Signal()
    playReleased = QtCore.Signal()

    def __init__(self, label, parent=None):
        super(CommandButton, self).__init__(parent)
        self.mainbutton = QtWidgets.QPushButton(label)
        self.mainbutton.released.connect(self.released.emit)
        self.playbutton = QtWidgets.QPushButton(icon('play.png'), '')
        self.playbutton.released.connect(self.playReleased.emit)
        self.playbutton.setFixedSize(22, 22)
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(2)
        self.layout.addWidget(self.mainbutton)
        self.layout.addWidget(self.playbutton)


class LayerEdit(QtWidgets.QWidget):
    valueSet = QtCore.Signal(object)

    def __init__(self, parent=None):
        super(LayerEdit, self).__init__(parent)
        self.layer = QtWidgets.QLineEdit()
        self.layer.setReadOnly(True)
        self.reset = QtWidgets.QPushButton('x')
        self.reset.released.connect(self.do_reset)

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.layer)
        self.layout.addWidget(self.reset)

    def set_layer(self, text):
        self.layer.setText(text or '')

    def do_reset(self):
        if not self.layer.text():
            return
        self.layer.setText('')
        self.valueSet.emit(None)


class ZoomsLockedEditor(QtWidgets.QWidget):

    def __init__(self, document, parent=None):
        super(ZoomsLockedEditor, self).__init__(parent)
        self.model = ZoomLockedModel(document)

        self.table = QtWidgets.QTableView()
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.AllEditTriggers)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        mode = QtWidgets.QHeaderView.ResizeToContents
        self.table.horizontalHeader().setSectionResizeMode(mode)
        self.table.setFixedHeight(120)
        self.table.setItemDelegateForColumn(0, CheckDelegate())
        self.table.setModel(self.model)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.table)


class ZoomLockedModel(QtCore.QAbstractTableModel):
    HEADERS = 'Z-lock', 'BG Color', 'Name'

    def __init__(self, document, parent=None):
        super(ZoomLockedModel, self).__init__(parent)
        self.document = document
        self.document.changed.connect(self.layoutChanged.emit)

    def columnCount(self, _):
        return 3

    def rowCount(self, _):
        return count_panels(self.document.data['general']['panels'])

    def flags(self, _):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable

    def headerData(self, section, orientation, role):
        if role != QtCore.Qt.DisplayRole:
            return
        if orientation == QtCore.Qt.Vertical:
            return str(section + 1)
        return self.HEADERS[section]

    def set_zoom_locked(self, row, state):
        self.layoutAboutToBeChanged.emit()
        self.document.data['general']['panels.zoom_locked'][row] = state
        self.document.general_option_changed.emit(
            'attribute_editor', 'panels.zoom_locked')
        self.document.record_undo()
        self.layoutChanged.emit()

    def setData(self, index, value, role):
        if index.column() == 0:
            return False

        if index.column() == 1 and role == QtCore.Qt.EditRole:
            if value and not QtGui.QColor(value).isValid():
                if QtGui.QColor('#' + value).isValid():
                    value = '#' + value
                else:
                    return False
            value = value or None
            self.document.data['general']['panels.colors'][index.row()] = value
            self.document.general_option_changed.emit(
                'attribute_editor', 'panels.colors')
            self.document.record_undo()
            return True

        if index.column() == 2 and role == QtCore.Qt.EditRole:
            self.document.data['general']['panels.names'][index.row()] = value
            self.document.general_option_changed.emit(
                'attribute_editor', 'panels.names')
            self.document.record_undo()
            return True

        return False

    def data(self, index, role):
        if not index.isValid():
            return

        general = self.document.data['general']
        if role == QtCore.Qt.DecorationRole:
            if index.column() == 1:
                color = general['panels.colors'][index.row()]
                return get_color_icon(color)

        if role in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            if index.column() == 1:
                color = general['panels.colors'][index.row()]
                return str(color) if color else ''
            if index.column() == 2:
                return str(general['panels.names'][index.row()])


# @lru_cache()
def get_color_icon(color, size=None):
    px = QtGui.QPixmap(QtCore.QSize(*(size if size else (64, 64))))
    px.fill(QtCore.Qt.transparent)
    rect = QtCore.QRectF(0, 0, px.size().width(), px.size().height())
    painter = QtGui.QPainter(px)
    try:
        if not color:
            painter.drawRect(rect)
            font = QtGui.QFont()
            font.setPixelSize(50)
            option = QtGui.QTextOption()
            option.setAlignment(QtCore.Qt.AlignCenter)
            painter.setPen(QtGui.QPen(QtGui.QColor('#ddd')))
            painter.setFont(font)
            painter.drawText(grow_rect(rect, 300), X, option)
            painter.end()
            return QtGui.QIcon(px)

        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QColor(color))
        painter.drawRect(rect)
        painter.end()
        return QtGui.QIcon(px)

    except BaseException:
        import traceback
        print(traceback.format_exc())
        painter.end()
        return QtGui.QIcon()


class CheckDelegate(QtWidgets.QItemDelegate):

    def mouseReleaseEvent(self, event):
        if event.button() != QtCore.Qt.LeftButton:
            return
        self.update()

    def createEditor(self, parent, _, index):
        model = index.model()
        general = model.document.data['general']
        state = general['panels.zoom_locked'][index.row()]
        model.set_zoom_locked(index.row(), not state)
        checker = CheckWidget(not state, parent)
        checker.toggled.connect(partial(model.set_zoom_locked, index.row()))
        return checker

    def paint(self, painter, option, index):
        model = index.model()
        general = model.document.data['general']
        state = general['panels.zoom_locked'][index.row()]

        center = option.rect.center()
        painter.setBrush(QtCore.Qt.NoBrush)
        rect = QtCore.QRectF(center.x() - 10, center.y() - 10, 20, 20)
        if not state:
            return
        font = QtGui.QFont()
        font.setPixelSize(20)
        option = QtGui.QTextOption()
        option.setAlignment(QtCore.Qt.AlignCenter)
        painter.drawText(rect, V, option)


class CheckWidget(QtWidgets.QWidget):
    toggled = QtCore.Signal(bool)

    def __init__(self, state, parent=None):
        super(CheckWidget, self).__init__(parent)
        self.state = state

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.state = not self.state
            self.toggled.emit(self.state)
            self.update()

    def paintEvent(self, _):
        painter = QtGui.QPainter(self)
        center = self.rect().center()
        painter.setBrush(QtCore.Qt.NoBrush)
        rect = QtCore.QRectF(center.x() - 15, center.y() - 15, 30, 30)
        painter.drawRect(rect)
        if not self.state:
            return
        font = QtGui.QFont()
        font.setPixelSize(20)
        option = QtGui.QTextOption()
        option.setAlignment(QtCore.Qt.AlignCenter)
        painter.drawText(rect, V, option)


class ChildrenWidget(QtWidgets.QWidget):
    children_changed = QtCore.Signal(list)

    def __init__(self, document, display_options, parent=None):
        super(ChildrenWidget, self).__init__(parent)
        self.display_options = display_options
        self.model = ChildrenModel(document)
        self.list = QtWidgets.QListView()
        self.list.setModel(self.model)
        self.list.selectionModel().selectionChanged.connect(
            self.hightlight_children)
        mode = QtWidgets.QAbstractItemView.ExtendedSelection
        self.list.setSelectionMode(mode)
        self.delete = QtWidgets.QPushButton('Delete')
        self.delete.released.connect(self.call_delete)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.list)
        layout.addWidget(self.delete)

    def hightlight_children(self, *_):
        indexes = self.list.selectedIndexes()
        ids = [self.model.data(i, QtCore.Qt.DisplayRole) for i in indexes]
        self.display_options.highlighted_children_ids = ids
        self.display_options.options_changed.emit()

    def clear(self):
        self.model.layoutAboutToBeChanged.emit()
        self.display_options.highlighted_children_ids = []
        self.list.selectionModel().clear()
        self.model.children = []
        self.model.layoutChanged.emit()

    def call_delete(self):
        indexes = self.list.selectedIndexes()
        indexes = sorted(indexes, key=lambda i: i.row(), reverse=True)
        self.model.layoutAboutToBeChanged.emit()
        for index in indexes:
            self.model.children.pop(index.row())
        self.model.layoutChanged.emit()
        self.display_options.highlighted_children_ids = []
        self.display_options.options_changed.emit()
        self.children_changed.emit(self.model.children[:])

    def set_children(self, children):
        self.model.layoutAboutToBeChanged.emit()
        self.model.children = children[:]
        self.model.layoutChanged.emit()


class ChildrenModel(QtCore.QAbstractListModel):
    def __init__(self, document, parent=None):
        super(ChildrenModel, self).__init__(parent)
        self.document = document
        self.children = []

    def rowCount(self, _):
        return len(self.children)

    def data(self, index, role):
        id_ = self.children[index.row()]
        if role == QtCore.Qt.DisplayRole:
            return id_

        if id_ in self.document.shapes_by_id:
            return

        if role == QtCore.Qt.BackgroundRole:
            brush = QtGui.QBrush(QtGui.QColor('#555555'))
            brush.setStyle(QtCore.Qt.BDiagPattern)
            return brush

        if role == QtCore.Qt.FontRole:
            font = QtGui.QFont()
            font.setStrikeOut(True)
            font.setItalic(True)
            return font

        if role == QtCore.Qt.TextColorRole:
            return QtGui.QColor('#999999')