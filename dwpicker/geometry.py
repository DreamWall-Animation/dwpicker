import math
from PySide2 import QtCore, QtGui


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
    return QtCore.QRectF(left, top, width, height)


def get_shapes_bounding_rects(shapes):
    rects = [
        shape.rect if shape.options['shape'] != 'custom' else
        shape.path.boundingRect()
        for shape in shapes]
    return get_combined_rects(rects)


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

    return QtCore.QRectF(l, t, r-l, b-t)


def get_global_rect(points):
    left = min(p.x() for p in points)
    top = min(p.y() for p in points)
    width = max(p.x() for p in points) - left
    height = max(p.y() for p in points) - top
    return QtCore.QRectF(left, top, width, height)


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


def rect_top_left_symmetry(rect, point, horizontal=True):
    topleft = rect.topLeft()
    if horizontal:
        dist = (topleft.x() - point.x()) * 2
        vector = QtCore.QPoint(dist, 0)
    else:
        dist = (topleft.y() - point.y()) * 2
        vector = QtCore.QPoint(0, dist)
    topleft = rect.topLeft() - vector
    rect.moveTopLeft(topleft)
    return rect


def path_symmetry(path, horizontal=True):
    for point in path:
        for key in ['point', 'tangent_in', 'tangent_out']:
            if point[key] is None:
                continue
            if horizontal:
                point[key][0] = -point[key][0]
            else:
                point[key][1] = -point[key][1]


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
