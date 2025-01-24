
import os
import json
from copy import deepcopy
from PySide2 import QtWidgets, QtCore, QtGui
from dwpicker.geometry import grow_rect, resize_rect_with_ratio
from dwpicker.qtutils import get_cursor
from dwpicker.shapepath import get_worldspace_qpath, rotate_path
from dwpicker.transform import resize_path_with_reference
from dwpicker.viewport import ViewportMapper


SHAPES = (
    ('fat_arrow.dws', [0.0, 90, 180, 270]),
    ('thin_arrow.dws', [0.0, 90, 180, 270]),
    ('diamond.dws', [0.0]),
    ('pie.dws', [0.0, 90, 180, 270]),
    ('half_circle.dws', [0.0, 90, 180, 270]),
    ('star_5.dws', [0.0, 180.0]),
    ('star_6.dws', [0.0, 90.0]),
)


class ShapeLibraryMenu(QtWidgets.QWidget):
    path_selected = QtCore.Signal(object)

    def __init__(self, parent):
        super(ShapeLibraryMenu, self).__init__(parent, QtCore.Qt.Popup)
        shapes_directory = os.path.join(os.path.dirname(__file__), 'shapes')
        layout = QtWidgets.QGridLayout(self)
        layout.setSpacing(2)

        row, col = 0, 0
        for file, angles in SHAPES:
            with open(os.path.join(shapes_directory, file), 'r') as f:
                path = json.load(f)
                for angle in angles:
                    rotated_path = rotate_path(path, angle, (0, 0))
                    button = PathButton(rotated_path)
                    button.clicked.connect(self.emit_path)
                    layout.addWidget(button, row, col)
                    col += 1
                    if col > 4:
                        row += 1
                        col = 0

    def emit_path(self, path):
        self.path_selected.emit(path)
        self.hide()


class PathButton(QtWidgets.QAbstractButton):
    clicked = QtCore.Signal(object)
    a = 0
    def __init__(self, path, parent=None):
        super(PathButton, self).__init__(parent)
        self.path = deepcopy(path)
        qpath = get_worldspace_qpath(path, ViewportMapper())
        input_ = qpath.boundingRect()
        output = grow_rect(QtCore.QRect(0, 0, 60, 60), -10)
        PathButton.a += 1
        output = resize_rect_with_ratio(input_, output)
        resize_path_with_reference(path, input_, output)
        self.painter_path = get_worldspace_qpath(path, ViewportMapper())
        self.setFixedSize(QtCore.QSize(60, 60))
        self.setMouseTracking(True)

    def mouseMoveEvent(self, event):
        self.update()
        return super(PathButton, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() != QtCore.Qt.LeftButton:
            return
        self.clicked.emit(self.path)

    def enterEvent(self, event):
        self.update()
        return super(PathButton, self).enterEvent(event)

    def leaveEvent(self, event):
        self.update()
        return super(PathButton, self).leaveEvent(event)

    def paintEvent(self, _):
        painter = QtGui.QPainter(self)
        bordercolor = '#2B2B2B'
        painter.setPen(QtGui.QColor(bordercolor))
        bgcolor = (
            '#5285A6' if self.rect().contains(get_cursor(self)) else '#444444')
        painter.setBrush(QtGui.QColor(bgcolor))
        rect = self.rect()
        rect.setHeight(rect.height() - 1)
        rect.setWidth(rect.width() - 1)
        painter.drawRect(rect)
        painter.setRenderHints(QtGui.QPainter.Antialiasing)

        painter.setBrush(QtGui.QColor('#FFFD55'))
        painter.setPen(QtGui.QColor('#FFFD55'))
        painter.drawPath(self.painter_path)
        painter.end()
