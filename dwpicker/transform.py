from dwpicker.pyside import QtCore
from dwpicker.shapepath import get_absolute_path, get_relative_path

class Transform:
    def __init__(self, snap=None):
        self.snap = snap
        self.direction = None
        self.rect = None
        self.mode = None
        self.square = False
        self.reference_x = None
        self.reference_y = None
        self.reference_rect = None

    def set_rect(self, rect):
        self.rect = rect
        if rect is None:
            self.reference_x = None
            self.reference_y = None
            return

    def set_reference_point(self, cursor):
        self.reference_x = cursor.x() - self.rect.left()
        self.reference_y = cursor.y() - self.rect.top()

    def resize(self, shapes, cursor):
        if self.snap is not None:
            x, y = snap(cursor.x(), cursor.y(), self.snap)
            cursor.setX(x)
            cursor.setY(y)
        resize_rect_with_direction(
            self.rect, cursor, self.direction, force_square=self.square)
        self.apply_relative_transformation(shapes)

    def apply_relative_transformation(self, shapes):
        for shape in shapes:
            resize_shape_with_reference(shape, self.reference_rect, self.rect)

        self.reference_rect = QtCore.QRectF(
            self.rect.topLeft(), self.rect.size())

    def move(self, shapes, cursor):
        x = cursor.x() - self.reference_x
        y = cursor.y() - self.reference_y
        if self.snap is not None:
            x, y = snap(x, y, self.snap)
        self.apply_topleft(shapes, x, y)

    def shift(self, shapes, offset):
        x, y = offset
        if self.snap is not None:
            x *= self.snap[0]
            y *= self.snap[1]
        x = self.rect.left() + x
        y = self.rect.top() + y
        if self.snap:
            x, y = snap(x, y, self.snap)
        self.apply_topleft(shapes, x, y)

    def apply_topleft(self, shapes, x, y):
        width = self.rect.width()
        height = self.rect.height()
        self.rect.setTopLeft(QtCore.QPoint(x, y))
        self.rect.setWidth(width)
        self.rect.setHeight(height)
        self.apply_relative_transformation(shapes)


def snap(x, y, snap):
    x = snap[0] * round(x / snap[0])
    y = snap[1] * round(y / snap[1])
    return round(x), round(y)


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


def resize_shape_with_reference(shape, reference_rect, rect):
    if not shape.options['shape.path']:
        resize_rect_with_reference(shape.rect, reference_rect, rect)
        return
    point = shape.options['shape.left'], shape.options['shape.top']
    absolute_path = get_absolute_path(point, shape.options['shape.path'])

    resize_rect_with_reference(shape.rect, reference_rect, rect)
    shape.synchronize_rect()

    resize_path_with_reference(absolute_path, reference_rect, rect)
    point = shape.options['shape.left'], shape.options['shape.top']
    relative_path = get_relative_path(point, absolute_path)
    shape.options['shape.path'] = relative_path
    shape.update_path()


def resize_path_with_reference(path, in_reference_rect, out_reference_rect):
    for point in path:
        for key in ['point', 'tangent_in', 'tangent_out']:
            if point[key] is not None:
                x = relative(
                    point[key][0],
                    in_min=in_reference_rect.left(),
                    in_max=in_reference_rect.right(),
                    out_min=out_reference_rect.left(),
                    out_max=out_reference_rect.right())
                y = relative(
                    point[key][1],
                    in_min=in_reference_rect.top(),
                    in_max=in_reference_rect.bottom(),
                    out_min=out_reference_rect.top(),
                    out_max=out_reference_rect.bottom())
                point[key] = [x, y]


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
    point = QtCore.QPointF(cursor)

    if direction == 'top_left':
        point.setX(min((point.x(), rect.right() - 1)))
        point.setY(min((point.y(), rect.bottom() - 1)))
        rect.setTopLeft(point)
        if force_square:
            left = rect.right() - rect.height()
            rect.setLeft(left)

    elif direction == 'bottom_left':
        point.setX(min((point.x(), rect.right() - 1)))
        point.setY(max((point.y(), rect.top() + 1)))
        rect.setBottomLeft(point)
        if force_square:
            rect.setHeight(rect.width())

    elif direction == 'top_right':
        point.setX(max((point.x(), rect.left() + 1)))
        point.setY(min((point.y(), rect.bottom() + 1)))
        rect.setTopRight(point)
        if force_square:
            rect.setWidth(rect.height())

    elif direction == 'bottom_right':
        point.setX(max((point.x(), rect.left() + 1)))
        point.setY(max((point.y(), rect.top() + 1)))
        rect.setBottomRight(point)
        if force_square:
            rect.setHeight(rect.width())

    elif direction == 'left':
        point.setX(min((point.x(), rect.right() - 1)))
        rect.setLeft(point.x())
        if force_square:
            rect.setHeight(rect.width())

    elif direction == 'right':
        point.setX(max((point.x(), rect.left() + 1)))
        rect.setRight(point.x())
        if force_square:
            rect.setHeight(rect.width())

    elif direction == 'top':
        point.setY(min((point.y(), rect.bottom() - 1)))
        rect.setTop(point.y())
        if force_square:
            rect.setWidth(rect.height())

    elif direction == 'bottom':
        point.setY(max((point.y(), rect.top() + 1)))
        rect.setBottom(point.y())
        if force_square:
            rect.setWidth(rect.height())
