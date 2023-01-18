
import os
from PySide2 import QtCore, QtGui

from dwpicker.geometry import (
    DIRECTIONS, get_topleft_rect, get_bottomleft_rect, get_topright_rect,
    get_bottomright_rect, get_left_side_rect, get_right_side_rect,
    get_top_side_rect, get_bottom_side_rect, proportional_rect)
from dwpicker.painting import (
    draw_selection_square, draw_manipulator, get_hovered_path, draw_shape)
from dwpicker.languages import execute_code
from dwpicker.selection import select_targets


EXCECUTION_WARNING = (
"""Code execution failed for shape: "{name}"
{error}.
""")


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

    def intersects(self, rect):
        if not rect or not self.rect:
            return False
        return self.rect.intersects(rect)

    def draw(self, painter):
        if self.rect is None:
            return
        draw_selection_square(painter, self.rect)


class Manipulator():
    def __init__(self):
        self._rect = None
        self._is_hovered = False

        self._tl_corner_rect = None
        self._bl_corner_rect = None
        self._tr_corner_rect = None
        self._br_corner_rect = None
        self._l_side_rect = None
        self._r_side_rect = None
        self._t_side_rect = None
        self._b_side_rect = None

        self.hovered_path = None

    @property
    def rect(self):
        return self._rect

    def handler_rects(self):
        return [
            self._tl_corner_rect, self._bl_corner_rect, self._tr_corner_rect,
            self._br_corner_rect, self._l_side_rect, self._r_side_rect,
            self._t_side_rect, self._b_side_rect]

    def get_direction(self, cursor):
        if self.rect is None:
            return None
        for i, rect in enumerate(self.handler_rects()):
            if rect.contains(cursor):
                return DIRECTIONS[i]

    def hovered_rects(self, cursor):
        rects = []
        for rect in self.handler_rects() + [self.rect]:
            if not rect:
                continue
            if rect.contains(cursor):
                rects.append(rect)
        return rects

    def set_rect(self, rect):
        self._rect = rect
        self.update_geometries()

    def update_geometries(self):
        rect = self.rect
        self._tl_corner_rect = get_topleft_rect(rect) if rect else None
        self._bl_corner_rect = get_bottomleft_rect(rect) if rect else None
        self._tr_corner_rect = get_topright_rect(rect) if rect else None
        self._br_corner_rect = get_bottomright_rect(rect) if rect else None
        self._l_side_rect = get_left_side_rect(rect) if rect else None
        self._r_side_rect = get_right_side_rect(rect) if rect else None
        self._t_side_rect = get_top_side_rect(rect) if rect else None
        self._b_side_rect = get_bottom_side_rect(rect) if rect else None
        self.hovered_path = get_hovered_path(rect) if rect else None

    def draw(self, painter, cursor):
        if self.rect is not None and all(self.handler_rects()):
            draw_manipulator(painter, self, cursor)


def get_shape_rect_from_options(options):
    return QtCore.QRectF(
        options['shape.left'],
        options['shape.top'],
        options['shape.width'],
        options['shape.height'])


class Shape():
    def __init__(self, options):
        self.hovered = False
        self.clicked = False
        self.selected = False
        self.options = options
        self.rect = get_shape_rect_from_options(options)
        self.pixmap = None
        self.image_rect = None
        self.synchronize_image()

    def set_hovered(self, cursor):
        self.hovered = self.rect.contains(cursor)

    def set_clicked(self, cursor):
        self.clicked = self.rect.contains(cursor)

    def release(self, cursor):
        self.clicked = False
        self.hovered = self.rect.contains(cursor)

    def synchronize_rect(self):
        self.options['shape.left'] = self.rect.left()
        self.options['shape.top'] = self.rect.top()
        self.options['shape.width'] = self.rect.width()
        self.options['shape.height'] = self.rect.height()

    def content_rect(self):
        if self.options['shape'] == 'round':
            return proportional_rect(self.rect, 70)
        return self.rect

    def execute(self, left=False, right=False):
        side = 'left' if left else 'right' if right else None
        if not side or not self.options['action.' + side]:
            return
        code = self.options['action.{}.command'.format(side)]
        language = self.options['action.{}.language'.format(side)]
        try:
            execute_code(language, code)
        except Exception as e:
            import traceback
            print(EXCECUTION_WARNING.format(
                name=self.options['text.content'], error=e))
            print(traceback.format_exc())

    def select(self, selection_mode='replace'):
        select_targets([self], selection_mode=selection_mode)

    def targets(self):
        return self.options['action.targets']

    def set_targets(self, targets):
        self.options['action.targets'] = targets

    def is_interactive(self):
        # if self.targets():
        #     return False
        return any([self.options['action.right'], self.options['action.left']])

    def is_background(self):
        return not any([
            bool(self.targets()),
            self.options['action.right'],
            self.options['action.left']])

    def synchronize_image(self):
        path = os.path.expandvars(self.options['image.path'])
        self.pixmap = QtGui.QPixmap(path)
        if self.options['image.fit'] is True:
            self.image_rect = None
            return
        self.image_rect = QtCore.QRectF(
            self.rect.left(),
            self.rect.top(),
            self.options['image.width'],
            self.options['image.height'])
        self.image_rect.moveCenter(self.rect.center())
