from PySide2 import QtWidgets, QtGui, QtCore
from maya import cmds

from dwpicker.colorwheel import ColorDialog
from dwpicker.optionvar import (
    save_optionvar, DEFAULT_LABEL, DEFAULT_HEIGHT, DEFAULT_WIDTH,
    DEFAULT_TEXT_COLOR, DEFAULT_BG_COLOR)


class QuickOptions(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(QuickOptions, self).__init__(parent=parent)
        self.bg_color = ColorButton()
        self.bg_color.colorChanged.connect(self.save_ui_states)
        self.text_color = ColorButton()
        self.text_color.colorChanged.connect(self.save_ui_states)
        validator = QtGui.QIntValidator()
        self.width = QtWidgets.QLineEdit()
        self.width.returnPressed.connect(self.save_ui_states)
        self.width.setValidator(validator)
        self.width.setFixedWidth(50)
        self.height = QtWidgets.QLineEdit()
        self.height.returnPressed.connect(self.save_ui_states)
        self.height.setValidator(validator)
        self.height.setFixedWidth(50)
        self.label = QtWidgets.QLineEdit()
        self.label.returnPressed.connect(self.save_ui_states)

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setSpacing(0)
        self.layout.addWidget(QtWidgets.QLabel('Bg-color: '))
        self.layout.addWidget(self.bg_color)
        self.layout.addSpacing(12)
        self.layout.addWidget(QtWidgets.QLabel('Text-color: '))
        self.layout.addWidget(self.text_color)
        self.layout.addSpacing(12)
        self.layout.addWidget(QtWidgets.QLabel('Size: '))
        self.layout.addWidget(self.width)
        self.layout.addWidget(self.height)
        self.layout.addSpacing(12)
        self.layout.addWidget(QtWidgets.QLabel('Label: '))
        self.layout.addWidget(self.label)

        self.load_ui_states()

    def save_ui_states(self, *_):
        values = self.values
        save_optionvar(DEFAULT_BG_COLOR, values['bgcolor.normal'])
        save_optionvar(DEFAULT_TEXT_COLOR, values['text.color'])
        save_optionvar(DEFAULT_WIDTH, values['shape.width'])
        save_optionvar(DEFAULT_HEIGHT, values['shape.height'])
        save_optionvar(DEFAULT_LABEL, values['text.content'])

    def load_ui_states(self):
        self.values = {
            'bgcolor.normal': cmds.optionVar(query=DEFAULT_BG_COLOR),
            'text.color': cmds.optionVar(query=DEFAULT_TEXT_COLOR),
            'shape.width': cmds.optionVar(query=DEFAULT_WIDTH),
            'shape.height': cmds.optionVar(query=DEFAULT_HEIGHT),
            'text.content': cmds.optionVar(query=DEFAULT_LABEL)}

    @property
    def values(self):
        return {
            'bgcolor.normal': self.bg_color.name,
            'text.color': self.text_color.name,
            'shape.width': int(self.width.text()) if self.width.text() else 10,
            'shape.height': int(self.height.text()) if self.height.text() else 10,
            'text.content': self.label.text()}

    @values.setter
    def values(self, values):
        self.bg_color.name = values['bgcolor.normal']
        self.text_color.name = values['text.color']
        self.width.setText(str(values['shape.width']))
        self.height.setText(str(values['shape.height']))
        self.label.setText(str(values['text.content']))


class ColorButton(QtWidgets.QAbstractButton):
    colorChanged = QtCore.Signal()

    def __init__(self, parent=None):
        super(ColorButton, self).__init__(parent=parent)
        self.setFixedSize(20, 20)
        self.color = QtGui.QColor(QtCore.Qt.black)
        self.released.connect(self.pick_color)

    def pick_color(self):
        dialog = ColorDialog(self.name)
        result = dialog.exec_()
        if result != QtWidgets.QDialog.Accepted:
            return
        self.name = dialog.colorname()
        self.colorChanged.emit()
        self.repaint()

    @property
    def name(self):
        return self.color.name()

    @name.setter
    def name(self, value):
        self.color.setNamedColor(value)

    def paintEvent(self, _):
        try:
            painter = QtGui.QPainter()
            painter.begin(self)
            painter.setBrush(QtGui.QBrush(self.color))
            if self.rect().contains(QtGui.QCursor.pos()):
                color = QtCore.Qt.transparent
            else:
                color = QtCore.Qt.gray
            painter.setPen(QtGui.QPen(color))
            painter.drawRect(self.rect())
        except BaseException:
            pass  # avoid crash
            # TODO: log the error
        finally:
            painter.end()
