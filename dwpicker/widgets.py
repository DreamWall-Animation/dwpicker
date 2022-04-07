from PySide2 import QtGui, QtCore, QtWidgets

from dwpicker.colorwheel import ColorDialog
from dwpicker.dialog import get_image_path
from dwpicker.qtutils import icon

# don't use style sheet like that, find better design
TOGGLER_STYLESHEET = (
    'background: rgb(0, 0, 0, 75); text-align: left; font: bold')


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
        self.button = QtWidgets.QPushButton('B')
        self.button.setFixedSize(21, 21)
        self.button.released.connect(self.browse)

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.text)
        self.layout.addWidget(self.button)

        self._value = self.value()

    def browse(self):
        filename = get_image_path(self)
        if not filename:
            return
        self.text.setText(filename)
        self.apply()

    def apply(self):
        self.valueSet.emit(self.text.text())

    def value(self):
        value = self.text.text()
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

        self.text = QtWidgets.QLineEdit()
        self.text.returnPressed.connect(self.apply)
        self.text.focusInEvent = self.focusInEvent
        self.text.focusOutEvent = self.focusOutEvent
        self.button = QtWidgets.QPushButton(icon('picker.png'), '')
        self.button.setFixedSize(21, 21)
        self.button.released.connect(self.pick_color)

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.text)
        self.layout.addWidget(self.button)

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
        result = dialog.exec_()
        if result == QtWidgets.QDialog.Accepted:
            self.text.setText(dialog.colorname())
            self.apply()

    def apply(self):
        if self._value != self.value():
            self.valueSet.emit(self.value())
        self._value = self.value()

    def value(self):
        value = self.text.text()
        return value if value != '' else None

    def set_color(self, color):
        self.text.setText(color)


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
