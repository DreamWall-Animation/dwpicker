from functools import partial, lru_cache
from PySide2 import QtGui, QtCore, QtWidgets
from dwpicker.compatibility import ensure_general_options_sanity
from dwpicker.colorwheel import ColorDialog
from dwpicker.dialog import get_image_path
from dwpicker.geometry import grow_rect
from dwpicker.path import format_path
from dwpicker.qtutils import icon
from dwpicker.stack import count_splitters

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


class ColorEdit(QtWidgets.QWidget):
    valueSet = QtCore.Signal(str)

    def __init__(self, parent=None):
        super(ColorEdit, self).__init__(parent)

        self.pixmap = QtWidgets.QLabel()
        self.pixmap.setFixedSize(21, 21)
        color = QtWidgets.QApplication.palette().color(
            QtGui.QPalette.Base)
        self.pixmap.setPixmap(_color_pixmap(color, self.pixmap.size()))
        self.text = QtWidgets.QLineEdit()
        self.text.returnPressed.connect(self.apply)
        self.text.focusInEvent = self.focusInEvent
        self.text.focusOutEvent = self.focusOutEvent
        self.button = QtWidgets.QToolButton(self)
        self.button.setIcon(icon('picker.png'))
        self.button.setFixedSize(21, 21)
        self.button.released.connect(self.pick_color)

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.pixmap)
        self.layout.addWidget(self.text)
        self.layout.addWidget(self.button)
        self.layout.setStretchFactor(self.pixmap, 1)
        self.layout.setStretchFactor(self.text, 5)
        self.layout.setStretchFactor(self.button, 1)

        self._value = self.value()

    def focusInEvent(self, event):
        self._value = self.value()
        return super(ColorEdit, self).focusInEvent(event)

    def focusOutEvent(self, event):
        self.apply()
        return super(ColorEdit, self).focusOutEvent(event)

    def showEvent(self, event):
        super(ColorEdit, self).showEvent(event)
        self.pixmap.setFixedSize(21, 21)

    def pick_color(self):
        color = self.text.text() or None
        dialog = ColorDialog(color)
        if dialog.exec_():
            self.text.setText(dialog.colorname())
            self.pixmap.setPixmap(
                _color_pixmap(dialog.colorname(), self.pixmap.size()))
            self.apply()

    def apply(self):
        if self._value != self.value():
            self.valueSet.emit(self.value())
        self._value = self.value()

    def value(self):
        value = self.text.text()
        return value if value != '' else None

    def set_color(self, color=None):
        self.text.setText(color)
        color = color or QtWidgets.QApplication.palette().color(
            QtGui.QPalette.Base)
        self.pixmap.setPixmap(_color_pixmap(color, self.pixmap.size()))


def _color_pixmap(colorname, qsize):
    pixmap = QtGui.QPixmap(qsize)
    painter = QtGui.QPainter(pixmap)
    painter.setBrush(QtGui.QColor(colorname))
    painter.setPen(QtCore.Qt.black)
    painter.drawRect(0, 0, qsize.width(), qsize.height())
    painter.end()
    return pixmap


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


class FloatEdit(LineEdit):
    valueSet = QtCore.Signal(float)
    VALIDATOR_CLS = QtGui.QDoubleValidator

    def __init__(self, minimum=None, maximum=None, decimals=2, parent=None):
        super().__init__(parent)
        self.dragging = False
        self.last_mouse_pos = QtCore.QPoint()

        if minimum is not None and maximum is None:
            maximum = float('inf')

        self.validator = self.VALIDATOR_CLS(minimum, maximum, decimals,
                                            self) if minimum is not None or maximum is not None else None
        if self.validator:
            self.setValidator(self.validator)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MiddleButton:
            self.dragging = True
            self.last_mouse_pos = event.globalPos()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.dragging:
            delta = event.globalPos() - self.last_mouse_pos
            self.last_mouse_pos = event.globalPos()

            current_value = float(self.text()) if self.text() else 0.0
            adjustment = delta.x() * 0.1  # Fine control adjustment
            new_value = current_value + adjustment

            if self.validator:
                min_val, max_val = self.validator.bottom(), self.validator.top()
                new_value = max(min_val, min(new_value, max_val))

            self.setText(f"{new_value:.2f}")
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.MiddleButton:
            self.dragging = False
            event.accept()

            self.emitValue()

        else:
            super().mouseReleaseEvent(event)

    def emitValue(self):
        current_value = self.value()
        if current_value is not None:
            self.valueSet.emit(current_value)

    def value(self):
        if self.text() == '':
            return None
        return float(self.text().replace(',', '.'))


class IntEdit(LineEdit):
    valueSet = QtCore.Signal(int)
    VALIDATOR_CLS = QtGui.QIntValidator

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
    optionSet = QtCore.Signal(str, object)

    def __init__(self, parent=None):
        super(ZoomsLockedEditor, self).__init__(parent)
        self.model = ZoomLockedModel()
        self.model.resultChanged.connect(self.emit_result_changed)

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

    def emit_result_changed(self, key):
        self.optionSet.emit(key, self.model.options[key])
        mode = QtWidgets.QHeaderView.ResizeToContents
        self.table.horizontalHeader().setSectionResizeMode(mode)

    def set_panels(self, panels):
        self.model.layoutAboutToBeChanged.emit()
        self.model.options['panels'] = panels
        ensure_general_options_sanity(self.model.options)
        self.model.layoutChanged.emit()

    def set_options(self, options):
        self.model.layoutAboutToBeChanged.emit()
        ensure_general_options_sanity(options)
        self.model.options = options
        self.model.layoutChanged.emit()


class ZoomLockedModel(QtCore.QAbstractTableModel):
    resultChanged = QtCore.Signal(str)
    HEADERS = 'Z-lock', 'BG Color', 'Name'

    def __init__(self, parent=None):
        super(ZoomLockedModel, self).__init__(parent)
        self.options = None

    def columnCount(self, _):
        return 3

    def rowCount(self, _):
        if not self.options:
            return 0
        return count_splitters(self.options['panels'])

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

        self.options['panels.zoom_locked'][row] = state
        self.resultChanged.emit('panels.zoom_locked')
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
            self.options['panels.colors'][index.row()] = value or None
            self.resultChanged.emit('panels.colors')
            return True

        if index.column() == 2 and role == QtCore.Qt.EditRole:
            self.options['panels.names'][index.row()] = value
            self.resultChanged.emit('panels.names')
            return True

        return False

    def data(self, index, role):
        if not index.isValid():
            return

        if role == QtCore.Qt.DecorationRole:
            if index.column() == 1:
                color = self.options['panels.colors'][index.row()]
                return get_color_icon(color)

        if role in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            if index.column() == 1:
                color = self.options['panels.colors'][index.row()]
                return str(color) if color else ''
            if index.column() == 2:
                return str(self.options['panels.names'][index.row()])


@lru_cache()
def get_color_icon(color, size=None, as_pixmap=False):
    px = QtGui.QPixmap(QtCore.QSize(*(size if size else (64, 64))))
    px.fill(QtCore.Qt.transparent)
    rect = QtCore.QRect(0, 0, px.size().width(), px.size().height())
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
        self.repaint()

    def createEditor(self, parent, _, index):
        model = index.model()
        if not model.options:
            return
        state = model.options['panels.zoom_locked'][index.row()]
        model.set_zoom_locked(index.row(), not state)
        checker = CheckWidget(not state, parent)
        checker.toggled.connect(partial(model.set_zoom_locked, index.row()))
        return checker

    def paint(self, painter, option, index):
        model = index.model()
        if not model.options:
            return
        state = model.options['panels.zoom_locked'][index.row()]

        center = option.rect.center()
        painter.setBrush(QtCore.Qt.NoBrush)
        rect = QtCore.QRect(center.x() - 10, center.y() - 10, 20, 20)
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
        rect = QtCore.QRect(center.x() - 15, center.y() - 15, 30, 30)
        painter.drawRect(rect)
        if not self.state:
            return
        font = QtGui.QFont()
        font.setPixelSize(20)
        option = QtGui.QTextOption()
        option.setAlignment(QtCore.Qt.AlignCenter)
        painter.drawText(rect, V, option)
