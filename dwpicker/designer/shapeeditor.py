
from PySide2 import QtWidgets, QtCore, QtGui
from dwpicker.geometry import ViewportMapper


class ShapeEditor(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(ShapeEditor, self).__init__(parent)
        self.viewportmapper = ViewportMapper()
        self.viewportmapper.viewsize = self.size()

    def wheelEvent(self, event):
        # To center the zoom on the mouse, we save a reference mouse position
        # and compare the offset after zoom computation.
        factor = .25 if event.angleDelta().y() > 0 else -.25
        self.zoom(factor, event.pos())
        self.update()

    def resizeEvent(self, event):
        self.viewportmapper.viewsize = self.size()
        size = (event.size() - event.oldSize()) / 2
        offset = QtCore.QPointF(size.width(), size.height())
        self.viewportmapper.origin -= offset
        self.update()

    def zoom(self, factor, reference):
        abspoint = self.viewportmapper.to_units_coords(reference)
        if factor > 0:
            self.viewportmapper.zoomin(abs(factor))
        else:
            self.viewportmapper.zoomout(abs(factor))
        relcursor = self.viewportmapper.to_viewport_coords(abspoint)
        vector = relcursor - reference
        self.viewportmapper.origin = self.viewportmapper.origin + vector

    def paintEvent(self, event):
        try:
            painter = QtGui.QPainter(self)
            painter.drawPath(painter_path(PATH, self.viewportmapper))
            rect = QtCore.QRectF(0, 0, 5, 5)
            for point in PATH:
                center = QtCore.QPointF(*point['point'])
                rect.moveCenter(self.viewportmapper.to_viewport_coords(center))
                painter.drawRect(rect)
            painter.setBrush(QtCore.Qt.yellow)
            painter.setPen(QtCore.Qt.yellow)
            for point in PATH:
                tangent_in = QtCore.QPointF(*point['tangent_in'])
                tangent_in = self.viewportmapper.to_viewport_coords(tangent_in)
                rect.moveCenter(tangent_in)
                painter.drawRect(rect)
                tangent_out = QtCore.QPointF(*point['tangent_out'])
                tangent_out = self.viewportmapper.to_viewport_coords(tangent_out)
                rect.moveCenter(tangent_out)
                painter.drawRect(rect)
                center = QtCore.QPointF(*point['point'])
                center = self.viewportmapper.to_viewport_coords(center)
                painter.drawLine(tangent_in, center)
                painter.drawLine(tangent_out, center)
        finally:
            painter.end()


PATH = [
    {
        'point': [0, 0],
        'tangent_in': [-100, 0],
        'tangent_out': [100, 0],
        'tengent_lock': True,
    },
    {
        'point': [100, 100],
        'tangent_in': [100, 0],
        'tangent_out': [100, 200],
        'tengent_lock': True,
    },
    {
        'point': [0, 200],
        'tangent_in': [-100, 200],
        'tangent_out': [100, 200],
        'tengent_lock': True,
    },
    {
        'point': [-100, 100],
        'tangent_in': [-100, 200],
        'tangent_out': [-100, 0],
        'tengent_lock': True,
    },
]


def painter_path(path, viewportmapper):
    painter_path = QtGui.QPainterPath()
    start = QtCore.QPointF(*path[0]['point'])
    painter_path.moveTo(viewportmapper.to_viewport_coords(start))
    for i in range(len(path)):
        point = path[i]
        point2 = path[i + 1 if i + 1 < len(path) else 0]
        c1 = QtCore.QPointF(*(point['tangent_out'] or point['point']))
        c2 = QtCore.QPointF(*(point2['tangent_in'] or point2['point']))
        end = QtCore.QPointF(*point2['point'])
        painter_path.cubicTo(
            viewportmapper.to_viewport_coords(c1),
            viewportmapper.to_viewport_coords(c2),
            viewportmapper.to_viewport_coords(end))
    return painter_path


try:
    se.close()
except:
    pass
se = ShapeEditor()
se.setWindowFlags(QtCore.Qt.Tool)
se.show()
