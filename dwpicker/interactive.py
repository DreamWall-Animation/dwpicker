

from dwpicker.pyside import QtCore

from dwpicker.geometry import (
    DIRECTIONS, get_topleft_rect, get_bottomleft_rect, get_topright_rect,
    get_bottomright_rect, get_left_side_rect, get_right_side_rect,
    get_top_side_rect, get_bottom_side_rect)
from dwpicker.shape import rect_intersects_shape


class SelectionSquare():
    def __init__(self):
        self.rect = None
        self.handeling = False

    def clicked(self, cursor):
        self.handeling = True
        self.rect = QtCore.QRectF(cursor, cursor)

    def handle(self, cursor):
        self.rect.setBottomRight(cursor)

    def release(self):
        self.handeling = False
        self.rect = None

    def intersects(self, shape):
        if not shape or not self.rect:
            return False
        return rect_intersects_shape(shape, self.rect)


class Manipulator():
    def __init__(self, viewportmapper=None):
        self._rect = None
        self.viewportmapper = viewportmapper
        self._is_hovered = False

    @property
    def rect(self):
        return self._rect

    def viewport_handlers(self):
        rect = self.viewportmapper.to_viewport_rect(self.rect)
        return [
            get_topleft_rect(rect) if rect else None,
            get_bottomleft_rect(rect) if rect else None,
            get_topright_rect(rect) if rect else None,
            get_bottomright_rect(rect) if rect else None,
            get_left_side_rect(rect) if rect else None,
            get_right_side_rect(rect) if rect else None,
            get_top_side_rect(rect) if rect else None,
            get_bottom_side_rect(rect) if rect else None]

    def get_direction(self, viewport_cursor):
        if self.rect is None:
            return None
        for i, rect in enumerate(self.viewport_handlers()):
            if rect.contains(viewport_cursor):
                return DIRECTIONS[i]

    def hovered_rects(self, cursor):
        rects = []
        for rect in self.viewport_handlers() + [self.rect]:
            if not rect:
                continue
            if rect.contains(cursor):
                rects.append(rect)
        return rects

    def set_rect(self, rect):
        self._rect = rect
