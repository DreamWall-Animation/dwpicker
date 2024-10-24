from PySide6 import QtCore
from dwpicker.geometry import split_line


def align_shapes(shapes, direction):
    _direction_matches[direction](shapes)


def align_left(shapes):
    left = min(s.rect.left() for s in shapes)
    for shape in shapes:
        shape.rect.moveLeft(left)
        shape.synchronize_rect()


def align_h_center(shapes):
    x = sum(s.rect.center().x() for s in shapes) / len(shapes)
    for shape in shapes:
        shape.rect.moveCenter(QtCore.QPointF(x, shape.rect.center().y()))
        shape.synchronize_rect()


def align_right(shapes):
    right = max(s.rect.right() for s in shapes)
    for shape in shapes:
        shape.rect.moveRight(right)
        shape.synchronize_rect()


def align_top(shapes):
    top = min(s.rect.top() for s in shapes)
    for shape in shapes:
        shape.rect.moveTop(top)
        shape.synchronize_rect()


def align_v_center(shapes):
    y = sum(s.rect.center().y() for s in shapes) / len(shapes)
    for shape in shapes:
        shape.rect.moveCenter(QtCore.QPointF(shape.rect.center().x(), y))
        shape.synchronize_rect()


def align_bottom(shapes):
    bottom = max(s.rect.bottom() for s in shapes)
    for shape in shapes:
        shape.rect.moveBottom(bottom)
        shape.synchronize_rect()


def arrange_horizontal(shapes):
    if len(shapes) < 3:
        return
    shapes = sorted(shapes, key=lambda s: s.rect.center().x())
    centers = split_line(
        point1=shapes[0].rect.center(),
        point2=shapes[-1].rect.center(),
        step_number=len(shapes))
    for shape, center in zip(shapes, centers):
        point = QtCore.QPointF(center.x(), shape.rect.center().y())
        shape.rect.moveCenter(point)
        shape.synchronize_rect()


def arrange_vertical(shapes):
    if len(shapes) < 3:
        return
    shapes = sorted(shapes, key=lambda s: s.rect.center().y())
    centers = split_line(
        point1=shapes[0].rect.center(),
        point2=shapes[-1].rect.center(),
        step_number=len(shapes))
    for shape, center in zip(shapes, centers):
        point = QtCore.QPointF(shape.rect.center().x(), center.y())
        shape.rect.moveCenter(point)
        shape.synchronize_rect()


_direction_matches = {
    'left': align_left,
    'h_center': align_h_center,
    'right': align_right,
    'top': align_top,
    'v_center': align_v_center,
    'bottom': align_bottom
}
