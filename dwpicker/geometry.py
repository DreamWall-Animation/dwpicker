import math
from PySide2 import QtCore


POINT_RADIUS = 8
POINT_OFFSET = 4
DIRECTIONS = [
    'top_left',
    'bottom_left',
    'top_right',
    'bottom_right',
    'left',
    'right',
    'top',
    'bottom']


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


def get_topleft_rect(rect):
    """
    this function return a manipulator rect for the transform
    handler.
      *__________________________
       |                        |
       |                        |
       |________________________|
    """
    if rect is None:
        return None
    point = rect.topLeft()
    return QtCore.QRectF(
        point.x() - (POINT_RADIUS / 2.0) - POINT_OFFSET,
        point.y() - (POINT_RADIUS / 2.0) - POINT_OFFSET,
        POINT_RADIUS, POINT_RADIUS)


def get_bottomleft_rect(rect):
    """
    this function return a manipulator rect for the transform
    handler.
       __________________________
       |                        |
       |                        |
       |________________________|
      *
    """
    if rect is None:
        return None
    point = rect.bottomLeft()
    return QtCore.QRectF(
        point.x() - (POINT_RADIUS / 2.0) - POINT_OFFSET,
        point.y() + (POINT_RADIUS / 2.0) - POINT_OFFSET,
        POINT_RADIUS, POINT_RADIUS)


def get_topright_rect(rect):
    """
    this function return a manipulator rect for the transform
    handler.
       __________________________*
       |                        |
       |                        |
       |________________________|
    """
    if rect is None:
        return None
    point = rect.topRight()
    return QtCore.QRectF(
        point.x() + (POINT_RADIUS / 2.0) - POINT_OFFSET,
        point.y() - (POINT_RADIUS / 2.0) - POINT_OFFSET,
        POINT_RADIUS, POINT_RADIUS)


def get_bottomright_rect(rect):
    """
    this function return a manipulator rect for the transform
    handler.
       __________________________
       |                        |
       |                        |
       |________________________|
                                 *
    """
    if rect is None:
        return None
    point = rect.bottomRight()
    return QtCore.QRectF(
        point.x() + (POINT_RADIUS / 2.0) - POINT_OFFSET,
        point.y() + (POINT_RADIUS / 2.0) - POINT_OFFSET,
        POINT_RADIUS, POINT_RADIUS)


def get_left_side_rect(rect):
    """
    this function return a manipulator rect for the transform
    handler.
       __________________________
       |                        |
      *|                        |
       |________________________|
    """
    if rect is None:
        return None
    top = rect.top() + (rect.height() / 2.0)
    return QtCore.QRectF(
        rect.left() - (POINT_RADIUS / 2.0) - POINT_OFFSET,
        top - (POINT_RADIUS / 2.0),
        POINT_RADIUS, POINT_RADIUS)


def get_right_side_rect(rect):
    """
    this function return a manipulator rect for the transform
    handler.
       __________________________
       |                        |
       |                        |*
       |________________________|
    """
    if rect is None:
        return None
    top = rect.top() + (rect.height() / 2.0)
    return QtCore.QRectF(
        rect.right() + (POINT_RADIUS / 2.0) - POINT_OFFSET,
        top - (POINT_RADIUS / 2.0),
        POINT_RADIUS, POINT_RADIUS)


def get_top_side_rect(rect):
    """
    this function return a manipulator rect for the transform
    handler.
       _____________*____________
       |                        |
       |                        |
       |________________________|
    """
    if rect is None:
        return None
    return QtCore.QRectF(
        rect.left() + (rect.width() / 2.0) - (POINT_RADIUS / 2.0),
        rect.top() - (POINT_RADIUS / 2.0) - POINT_OFFSET,
        POINT_RADIUS, POINT_RADIUS)


def get_bottom_side_rect(rect):
    """
    this function return a manipulator rect for the transform
    handler.
       __________________________
       |                        |
       |                        |
       |________________________|
                    *
    """
    if rect is None:
        return None
    return QtCore.QRectF(
        rect.left() + (rect.width() / 2.0) - (POINT_RADIUS / 2.0),
        rect.bottom() + (POINT_RADIUS / 2.0) - POINT_OFFSET,
        POINT_RADIUS, POINT_RADIUS)


def grow_rect(rect, value):
    if rect is None:
        return None
    return QtCore.QRectF(
        rect.left() - value,
        rect.top() - value,
        rect.width() + (value * 2),
        rect.height() + (value * 2))


def relative(value, in_min, in_max, out_min, out_max):
    """
    this function resolve simple equation and return the unknown value
    in between two values.
    a, a" = in_min, out_min
    b, b " = out_max, out_max
    c = value
    ? is the unknown processed by function.
    a --------- c --------- b
    a" --------------- ? ---------------- b"
    """
    factor = float((value - in_min)) / (in_max - in_min)
    width = out_max - out_min
    return out_min + (width * (factor))


def distance(a, b):
    """ return distance between two points """
    x = (b.x() - a.x())**2
    y = (b.y() - a.y())**2
    return math.sqrt(abs(x + y))


def get_relative_point(rect, point):
    x = point.x() - rect.left()
    y = point.y() - rect.top()
    return QtCore.QPoint(x, y)


def get_quarter(a, b, c):
    quarter = None
    if b.y() <= a.y() and b.x() < c.x():
        quarter = 0
    elif b.y() < a.y() and b.x() >= c.x():
        quarter = 1
    elif b.y() >= a.y() and b.x() > c.x():
        quarter = 2
    elif b.y() >= a.y() and b.x() <= c.x():
        quarter = 3
    return quarter


def get_point_on_line(angle, ray):
    x = 50 + ray * math.cos(float(angle))
    y = 50 + ray * math.sin(float(angle))
    return QtCore.QPoint(x, y)


def get_angle_c(a, b, c):
    return math.degrees(math.atan(distance(a, b) / distance(a, c)))


def get_absolute_angle_c(a, b, c):
    quarter = get_quarter(a, b, c)
    try:
        angle_c = get_angle_c(a, b, c)
    except ZeroDivisionError:
        return 360 - (90 * quarter)

    if quarter == 0:
        return round(180.0 + angle_c, 1)
    elif quarter == 1:
        return round(270.0 + (90 - angle_c), 1)
    elif quarter == 2:
        return round(angle_c, 1)
    elif quarter == 3:
        return math.fabs(round(90.0 + (90 - angle_c), 1))


def proportional_rect(rect, percent=None):
    """ return a scaled rect with a percentage """
    factor = float(percent) / 100
    width = rect.width() * factor
    height = rect.height() * factor
    left = rect.left() + round((rect.width() - width) / 2)
    top = rect.top() + round((rect.height() - height) / 2)
    return QtCore.QRect(left, top, width, height)


def resize_rect_with_reference(rect, in_reference_rect, out_reference_rect):
    """
    __________________________________  B
    |    ________________  A         |
    |    |               |           |
    |    |_______________|           |
    |                                |
    |________________________________|
    __________________________  C
    |    ?                   |
    |                        |
    |________________________|
    A = rect given
    B = in_reference_rect
    C = out_reference_rect
    the function process the fourth rect,
    it scale the A rect using the B, C scales as reference
    """

    left = relative(
        value=rect.left(),
        in_min=in_reference_rect.left(),
        in_max=in_reference_rect.right(),
        out_min=out_reference_rect.left(),
        out_max=out_reference_rect.right())
    top = relative(
        value=rect.top(),
        in_min=in_reference_rect.top(),
        in_max=in_reference_rect.bottom(),
        out_min=out_reference_rect.top(),
        out_max=out_reference_rect.bottom())
    right = relative(
        value=rect.right(),
        in_min=in_reference_rect.left(),
        in_max=in_reference_rect.right(),
        out_min=out_reference_rect.left(),
        out_max=out_reference_rect.right())
    bottom = relative(
        value=rect.bottom(),
        in_min=in_reference_rect.top(),
        in_max=in_reference_rect.bottom(),
        out_min=out_reference_rect.top(),
        out_max=out_reference_rect.bottom())
    rect.setCoords(left, top, right, bottom)


def resize_rect_with_direction(rect, cursor, direction, force_square=False):
    if direction == 'top_left':
        if cursor.x() < rect.right() and cursor.y() < rect.bottom():
            rect.setTopLeft(cursor)
            if force_square:
                left = rect.right() - rect.height()
                rect.setLeft(left)

    elif direction == 'bottom_left':
        if cursor.x() < rect.right() and cursor.y() > rect.top():
            rect.setBottomLeft(cursor)
            if force_square:
                rect.setHeight(rect.width())

    elif direction == 'top_right':
        if cursor.x() > rect.left() and cursor.y() < rect.bottom():
            rect.setTopRight(cursor)
            if force_square:
                rect.setWidth(rect.height())

    elif direction == 'bottom_right':
        if cursor.x() > rect.left() and cursor.y() > rect.top():
            rect.setBottomRight(cursor)
            if force_square:
                rect.setHeight(rect.width())

    elif direction == 'left':
        if cursor.x() < rect.right():
            rect.setLeft(cursor.x())
            if force_square:
                rect.setHeight(rect.width())

    elif direction == 'right':
        if cursor.x() > rect.left():
            rect.setRight(cursor.x())
            if force_square:
                rect.setHeight(rect.width())

    elif direction == 'top':
        if cursor.y() < rect.bottom():
            rect.setTop(cursor.y())
            if force_square:
                rect.setWidth(rect.height())

    elif direction == 'bottom':
        if cursor.y() > rect.top():
            rect.setBottom(cursor.y())
            if force_square:
                rect.setWidth(rect.height())


class Transform:
    def __init__(self):
        self.snap = None
        self.direction = None
        self.rect = None
        self.mode = None
        self.square = False
        self.reference_x = None
        self.reference_y = None
        self.reference_rect = None

    def set_rect(self, rect):
        if not isinstance(rect, QtCore.QRect):
            raise ValueError()
        self.rect = rect
        if rect is None:
            self.reference_x = None
            self.reference_y = None
            return

    def set_reference_point(self, cursor):
        self.reference_x = cursor.x() - self.rect.left()
        self.reference_y = cursor.y() - self.rect.top()

    def resize(self, rects, cursor):
        if self.snap is not None:
            x, y = snap(cursor.x(), cursor.y(), self.snap)
            cursor.setX(x)
            cursor.setY(y)
        resize_rect_with_direction(
            self.rect, cursor, self.direction, force_square=self.square)
        self.apply_relative_transformation(rects)

    def apply_relative_transformation(self, rects):
        for rect in rects:
            resize_rect_with_reference(
                rect, self.reference_rect, self.rect)

        self.reference_rect = QtCore.QRect(
            self.rect.topLeft(), self.rect.size())

    def move(self, rects, cursor):
        x = cursor.x() - self.reference_x
        y = cursor.y() - self.reference_y
        if self.snap is not None:
            x, y = snap(x, y, self.snap)
        self.apply_topleft(rects, x, y)

    def shift(self, rects, offset):
        x, y = offset
        if self.snap is not None:
            x *= self.snap[0]
            y *= self.snap[1]
        x = self.rect.left() + x
        y = self.rect.top() + y
        if self.snap:
            x, y = snap(x, y, self.snap)
        self.apply_topleft(rects, x, y)

    def apply_topleft(self, rects, x, y):
        width = self.rect.width()
        height = self.rect.height()
        self.rect.setTopLeft(QtCore.QPoint(x, y))
        self.rect.setWidth(width)
        self.rect.setHeight(height)
        self.apply_relative_transformation(rects)


def snap(x, y, snap):
    x = snap[0] * round(x / snap[0])
    y = snap[1] * round(y / snap[1])
    return x, y


def get_combined_rects(rects):
    """
    this function analyse list of rects and return
    a rect with the smaller top and left and highest right and bottom
    __________________________________ ?
    |              | A               |
    |              |                 |
    |______________|      ___________| B
    |                     |          |
    |_____________________|__________|
    """
    if not rects:
        return None
    l = min(rect.left() for rect in rects)
    t = min(rect.top() for rect in rects)
    r = max(rect.right() for rect in rects)
    b = max(rect.bottom() for rect in rects)

    return QtCore.QRect(l, t, r-l, b-t)


def rect_symmetry(rect, point, horizontal=True):
    """
     ______  rect           ______  result
    |      |               |      |
    |______|               |______|
                   . point

    Compute symmetry for a rect from a given point and axis
    """
    center = rect.center()
    if horizontal:
        dist = (center.x() - point.x()) * 2
        vector = QtCore.QPoint(dist, 0)
    else:
        dist = (center.y() - point.y()) * 2
        vector = QtCore.QPoint(0, dist)
    center = rect.center() - vector
    rect.moveCenter(center)
    return rect


def split_line(point1, point2, step_number):
    """
    split a line on given number of points.
    """
    if step_number <= 1:
        return [point2]
    x_values = split_range(point1.x(), point2.x(), step_number)
    y_values = split_range(point1.y(), point2.y(), step_number)
    return [QtCore.QPoint(x, y) for x, y in zip(x_values, y_values)]


def split_range(input_, output, step_number):
    difference = output - input_
    step = difference / float(step_number - 1)
    return [int(input_ + (step * i)) for i in range(step_number)]


if __name__ == "__main__":
    assert split_range(0, 10, 11) == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
