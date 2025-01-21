from PySide2 import QtCore
from dwpicker.geometry import split_line


def align_shapes(shapes, direction):
    _direction_matches[direction](shapes)


def align_left(shapes):
    left = min(s.bounding_rect().left() for s in shapes)
    for shape in shapes:
        shape_left = left + (shape.rect.left() - shape.bounding_rect().left())
        shape.rect.moveLeft(shape_left)
        shape.synchronize_rect()
        shape.update_path()


def align_h_center(shapes):
    x = sum(s.bounding_rect().center().x() for s in shapes) / len(shapes)
    for shape in shapes:
        offset = shape.bounding_rect().center().x() - shape.rect.center().x()
        shape_x = x - offset
        shape.rect.moveCenter(QtCore.QPointF(shape_x, shape.rect.center().y()))
        shape.synchronize_rect()
        shape.update_path()


def align_right(shapes):
    right = max(s.bounding_rect().right() for s in shapes)
    for shape in shapes:
        offset = (shape.rect.left() - shape.bounding_rect().left())
        shape_right = right - offset
        shape.rect.moveRight(shape_right)
        shape.synchronize_rect()
        shape.update_path()


def align_top(shapes):
    top = min(s.bounding_rect().top() for s in shapes)
    for shape in shapes:
        shape_top = top + (shape.rect.top() - shape.bounding_rect().top())
        shape.rect.moveTop(shape_top)
        shape.synchronize_rect()
        shape.update_path()


def align_v_center(shapes):
    y = sum(s.bounding_rect().center().y() for s in shapes) / len(shapes)
    for shape in shapes:
        offset = shape.bounding_rect().center().y() - shape.rect.center().y()
        shape_y = y - offset
        shape.rect.moveCenter(QtCore.QPointF(shape.rect.center().x(), shape_y))
        shape.synchronize_rect()
        shape.update_path()


def align_bottom(shapes):
    bottom = max(s.bounding_rect().bottom() for s in shapes)
    for shape in shapes:
        offset = shape.rect.bottom() - shape.bounding_rect().bottom()
        shape_bottom = bottom + offset
        shape.rect.moveBottom(shape_bottom)
        shape.synchronize_rect()
        shape.update_path()


def arrange_horizontal(shapes):
    if len(shapes) < 3:
        return
    shapes = sorted(shapes, key=lambda s: s.bounding_rect().center().x())
    centers = split_line(
        point1=shapes[0].bounding_rect().center(),
        point2=shapes[-1].bounding_rect().center(),
        step_number=len(shapes))
    for shape, center in zip(shapes, centers):
        offset = shape.bounding_rect().center().x() - shape.rect.center().x()
        point = QtCore.QPointF(center.x() - offset, shape.rect.center().y())
        shape.rect.moveCenter(point)
        shape.synchronize_rect()
        shape.update_path()


def arrange_vertical(shapes):
    if len(shapes) < 3:
        return
    shapes = sorted(shapes, key=lambda s: s.bounding_rect().center().y())
    centers = split_line(
        point1=shapes[0].bounding_rect().center(),
        point2=shapes[-1].bounding_rect().center(),
        step_number=len(shapes))
    for shape, center in zip(shapes, centers):
        offset = shape.bounding_rect().center().y() - shape.rect.center().y()
        point = QtCore.QPointF(shape.rect.center().x(), center.y() - offset)
        shape.rect.moveCenter(point)
        shape.synchronize_rect()
        shape.update_path()


_direction_matches = {
    'left': align_left,
    'h_center': align_h_center,
    'right': align_right,
    'top': align_top,
    'v_center': align_v_center,
    'bottom': align_bottom
}
