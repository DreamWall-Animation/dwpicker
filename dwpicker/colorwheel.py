import math
from PySide2 import QtWidgets, QtGui, QtCore
from dwpicker.qtutils import get_cursor
from dwpicker.geometry import (
    get_relative_point, get_point_on_line, get_absolute_angle_c)


CONICAL_GRADIENT = (
    (0.0, (0, 255, 255)),
    (0.16, (0, 0, 255)),
    (0.33, (255, 0, 255)),
    (0.5, (255, 0, 0)),
    (0.66, (255, 255, 0)),
    (0.83, (0, 255, 0)),
    (1.0, (0, 255, 255)))
TRANSPARENT = 0, 0, 0, 0
BLACK = 'black'
WHITE = 'white'


class ColorDialog(QtWidgets.QDialog):
    def __init__(self, hexacolor, parent=None):
        super(ColorDialog, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.colorwheel = ColorWheel()
        self.colorwheel.set_current_color(QtGui.QColor(hexacolor))
        self.ok = QtWidgets.QPushButton('ok')
        self.ok.released.connect(self.accept)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.colorwheel)
        self.layout.addWidget(self.ok)

    def colorname(self):
        return self.colorwheel.current_color().name()

    def exec_(self):
        point = get_cursor(self)
        point.setX(point.x() - 50)
        point.setY(point.y() - 75)
        self.move(point)
        return super(ColorDialog, self).exec_()


class ColorWheel(QtWidgets.QWidget):
    currentColorChanged = QtCore.Signal(QtGui.QColor)

    def __init__(self, parent=None):
        super(ColorWheel, self).__init__(parent)
        self._is_clicked = False
        self._rect = QtCore.QRect(25, 25, 50, 50)
        self._current_color = QtGui.QColor(WHITE)
        self._color_point = QtCore.QPoint(150, 50)
        self._current_tool = None
        self._angle = 180
        self.setFixedSize(100, 100)
        self.initUI()

    def initUI(self):
        self._conicalGradient = QtGui.QConicalGradient(
            self.width() / 2, self.height() / 2, 180)
        for pos, (r, g, b) in CONICAL_GRADIENT:
            self._conicalGradient.setColorAt(pos, QtGui.QColor(r, g, b))

        top = self._rect.top()
        bottom = self._rect.top() + self._rect.height()
        self._vertical_gradient = QtGui.QLinearGradient(0, top, 0, bottom)
        self._vertical_gradient.setColorAt(0.0, QtGui.QColor(*TRANSPARENT))
        self._vertical_gradient.setColorAt(1.0, QtGui.QColor(BLACK))

        left = self._rect.left()
        right = self._rect.left() + self._rect.width()
        self._horizontal_gradient = QtGui.QLinearGradient(left, 0, right, 0)
        self._horizontal_gradient.setColorAt(0.0, QtGui.QColor(WHITE))

    def paintEvent(self, _):
        try:
            painter = QtGui.QPainter()
            painter.begin(self)
            self.paint(painter)
        except BaseException:
            pass  # avoid crash
            # TODO: log the error
        finally:
            painter.end()

    def mousePressEvent(self, event):
        tool = 'rect' if self._rect.contains(event.pos()) else 'wheel'
        self._current_tool = tool
        self.mouse_update(event)

    def mouseMoveEvent(self, event):
        self._is_clicked = True
        self.mouse_update(event)

    def mouse_update(self, event):
        if self._current_tool == 'rect':
            self.color_point = event.pos()
        else:
            center = self._get_center()
            a = QtCore.QPoint(event.pos().x(), center.y())
            self._angle = get_absolute_angle_c(a=a, b=event.pos(), c=center)

        self.repaint()
        self.currentColorChanged.emit(self.current_color())

    def mouseReleaseEvent(self, event):
        self._is_clicked = False

    def paint(self, painter):
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        pen = QtGui.QPen(QtGui.QColor(0, 0, 0, 0))
        pen.setWidth(0)
        pen.setJoinStyle(QtCore.Qt.MiterJoin)

        painter.setBrush(self._conicalGradient)
        painter.setPen(pen)
        painter.drawRoundedRect(
            6, 6, (self.width() - 12), (self.height() - 12),
            self.width(), self.height())

        painter.setBrush(self.palette().color(QtGui.QPalette.Background))
        painter.drawRoundedRect(
            12.5, 12.5, (self.width() - 25), (self.height() - 25),
            self.width(), self.height())

        self._horizontal_gradient.setColorAt(
            1.0, self._get_current_wheel_color())
        painter.setBrush(self._horizontal_gradient)
        painter.drawRect(self._rect)

        painter.setBrush(self._vertical_gradient)
        painter.drawRect(self._rect)

        pen.setColor(QtGui.QColor(BLACK))
        pen.setWidth(3)
        painter.setPen(pen)

        angle = math.radians(self._angle)
        painter.drawLine(
            get_point_on_line(angle, 37),
            get_point_on_line(angle, 46))

        pen.setWidth(5)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        painter.setPen(pen)
        painter.drawPoint(self._color_point)

    @property
    def color_point(self):
        return self._color_point

    @color_point.setter
    def color_point(self, point):
        if point.x() < self._rect.left():
            x = self._rect.left()
        elif point.x() > self._rect.left() + self._rect.width():
            x = self._rect.left() + self._rect.width()
        else:
            x = point.x()

        if point.y() < self._rect.top():
            y = self._rect.top()
        elif point.y() > self._rect.top() + self._rect.height():
            y = self._rect.top() + self._rect.height()
        else:
            y = point.y()

        self._color_point = QtCore.QPoint(x, y)

    def _get_current_wheel_color(self):
        degree = 360 - self._angle
        return QtGui.QColor(*degree_to_color(degree))

    def _get_center(self):
        return QtCore.QPoint(self.width() / 2, self.height() / 2)

    def current_color(self):
        point = get_relative_point(self._rect, self.color_point)
        x_factor = 1.0 - (float(point.x()) / self._rect.width())
        y_factor = 1.0 - (float(point.y()) / self._rect.height())
        r, g, b, _ = self._get_current_wheel_color().getRgb()

        # fade to white
        differences = 255.0 - r, 255.0 - g, 255.0 - b
        r += round(differences[0] * x_factor)
        g += round(differences[1] * x_factor)
        b += round(differences[2] * x_factor)

        # fade to black
        r = round(r * y_factor)
        g = round(g * y_factor)
        b = round(b * y_factor)

        return QtGui.QColor(r, g, b)

    def set_current_color(self, color):
        [r, g, b] = color.getRgb()[:3]
        self._angle = 360.0 - (QtGui.QColor(r, g, b).getHslF()[0] * 360.0)
        self._angle = self._angle if self._angle != 720.0 else 0

        x = ((((
            sorted([r, g, b], reverse=True)[0] -
            sorted([r, g, b])[0]) / 255.0) * self._rect.width()) +
            self._rect.left())

        y = ((((
            255 - (sorted([r, g, b], reverse=True)[0])) / 255.0) *
            self._rect.height()) + self._rect.top())

        self._current_color = color
        self._color_point = QtCore.QPoint(x, y)
        self.repaint()


def degree_to_color(degree):
    if degree is None:
        return None
    degree = degree / 360.0

    r, g, b = 255.0, 255.0, 255.0
    contain_red = (
        (degree >= 0.0 and degree <= 0.33)
        or (degree >= 0.66 and degree <= 1.0))

    if contain_red:
        if degree >= 0.66 and degree <= 0.83:
            factor = degree - 0.66
            r = round(255 * (factor / .16))
        if (degree > 0.0 and degree < 0.16) or (degree > 0.83 and degree < 1.0):
            r = 255
        elif degree >= 0.16 and degree <= 0.33:
            factor = degree - 0.16
            r = 255 - round(255 * (factor / .16))
    else:
        r = 0
    r = min(r, 255)
    r = max(r, 0)

    # GREEN
    if degree >= 0.0 and degree <= 0.66:
        if degree <= 0.16:
            g = round(255.0 * (degree / .16))
        elif degree < 0.5:
            g = 255
        if degree >= 0.5:
            factor = degree - 0.5
            g = 255 - round(255.0 * (factor / .16))
    else:
        g = 0
    g = min(g, 255.0)
    g = max(g, 0)

    # BLUE
    if degree >= 0.33 and degree <= 1.0:
        if degree <= 0.5:
            factor = degree - 0.33
            b = round(255 * (factor / .16))
        elif degree < 0.83:
            b = 255.0
        if degree >= 0.83 and degree <= 1.0:
            factor = degree - 0.83
            b = 255.0 - round(255.0 * (factor / .16))
    else:
        b = 0
    b = min(b, 255)
    b = max(b, 0)
    return r, g, b
