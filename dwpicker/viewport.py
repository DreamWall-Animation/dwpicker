
from dwpicker.pyside import QtCore, QtGui


class ViewportMapper():
    """
    Used to translate/map between:
        - abstract/data/units coordinates
        - viewport/display/pixels coordinates
    """
    def __init__(self):
        self.zoom = 1
        self.origin = QtCore.QPointF(0, 0)
        # We need the viewport size to be able to center the view or to
        # automatically set zoom from selection:
        self.viewsize = QtCore.QSize(300, 300)

    def to_viewport(self, value):
        return value * self.zoom

    def to_units(self, pixels):
        return pixels / self.zoom

    def to_viewport_coords(self, units_point):
        return QtCore.QPointF(
            self.to_viewport(units_point.x()) - self.origin.x(),
            self.to_viewport(units_point.y()) - self.origin.y())

    def to_units_coords(self, pixels_point):
        return QtCore.QPointF(
            self.to_units(pixels_point.x() + self.origin.x()),
            self.to_units(pixels_point.y() + self.origin.y()))

    def to_viewport_rect(self, units_rect):
        return QtCore.QRectF(
            (units_rect.left() * self.zoom) - self.origin.x(),
            (units_rect.top() * self.zoom) - self.origin.y(),
            units_rect.width() * self.zoom,
            units_rect.height() * self.zoom)

    def to_units_rect(self, pixels_rect):
        top_left = self.to_units_coords(pixels_rect.topLeft())
        width = self.to_units(pixels_rect.width())
        height = self.to_units(pixels_rect.height())
        return QtCore.QRectF(top_left.x(), top_left.y(), width, height)

    def zoomin(self, factor=10.0):
        self.zoom += self.zoom * factor
        self.zoom = min(self.zoom, 5.0)

    def zoomout(self, factor=10.0):
        self.zoom -= self.zoom * factor
        self.zoom = max(self.zoom, .1)

    def center_on_point(self, units_center):
        """Given current zoom and viewport size, set the origin point."""
        self.origin = QtCore.QPointF(
            units_center.x() * self.zoom - self.viewsize.width() / 2,
            units_center.y() * self.zoom - self.viewsize.height() / 2)

    def focus(self, units_rect):
        self.zoom = min([
            float(self.viewsize.width()) / units_rect.width(),
            float(self.viewsize.height()) / units_rect.height()])
        if self.zoom > 1:
            self.zoom *= 0.7  # lower zoom to add some breathing space
        self.zoom = max(self.zoom, .1)
        self.center_on_point(units_rect.center())

    def to_viewport_transform(self):
        transform = QtGui.QTransform()
        transform.scale(self.zoom, self.zoom)
        transform.translate(
            self.to_units(-self.origin.x()),
            self.to_units(-self.origin.y()))
        return transform

    def to_units_transform(self):
        transform = QtGui.QTransform()
        transform.translate(self.origin.x(), self.origin.y())
        transform.scale(1 / self.zoom, 1 / self.zoom)
        return transform

    def to_viewport_path(self, path):
        return self.to_viewport_transform().map(path)

    def to_units_path(self, path):
        return self.to_units_transform().map(path)


def to_screenspace_coords(point, anchor, viewport_size):
    if anchor == 'top_left':
        return point

    point = QtCore.QPointF(point)
    if anchor == 'top_right':
        x = viewport_size.width() + point.x()
        return QtCore.QPointF(x, point.y())

    y = viewport_size.height() + point.y()
    if anchor == 'bottom_left':
        return QtCore.QPointF(point.x(), y)

    if anchor == 'bottom_right':
        x = viewport_size.width() + point.x()
        return QtCore.QPointF(x, y)
