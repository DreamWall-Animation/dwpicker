

from PySide2 import QtCore, QtGui

from dwpicker.geometry import (
    DIRECTIONS, get_topleft_rect, get_bottomleft_rect, get_topright_rect,
    get_bottomright_rect, get_left_side_rect, get_right_side_rect,
    get_global_rect, get_top_side_rect, get_bottom_side_rect,
    proportional_rect)
from dwpicker.languages import execute_code, EXECUTION_WARNING
from dwpicker.path import expand_path
from dwpicker.selection import select_targets
from dwpicker.shapepath import get_painter_path


def cursor_in_shape(shape, cursor):
    if shape.path and shape.options['shape'] == 'custom':
        return shape.path.contains(cursor)
    return shape.rect.contains(cursor)


def rect_intersects_shape(shape, rect):
    if shape.path and shape.options['shape'] == 'custom':
        return shape.path.intersects(rect)
    return shape.rect.intersects(rect)


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


def get_shape_rect_from_options(options):
    if options['shape'] == 'custom' and options['shape.path']:
        points = [QtCore.QPointF(*p['point']) for p in options['shape.path']]
        return get_global_rect(points)
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
        self.path = get_painter_path(options['shape.path'])
        self.synchronize_image()

    def set_clicked(self, cursor):
        self.clicked = self.rect.contains(cursor)

    def release(self, cursor):
        self.clicked = False
        self.hovered = self.rect.contains(cursor)

    def update_path(self):
        self.path = get_painter_path(self.options['shape.path'])

    def synchronize_rect(self):
        self.options['shape.left'] = self.rect.left()
        self.options['shape.top'] = self.rect.top()
        self.options['shape.width'] = self.rect.width()
        self.options['shape.height'] = self.rect.height()

    def content_rect(self):
        if self.options['shape'] == 'round':
            return proportional_rect(self.rect, 70)
        return self.rect

    def execute(self, button, shift=False, ctrl=False):
        commands = _find_commands(
            self.options['action.commands'],
            button, shift=shift, ctrl=ctrl)
        for command in commands:
            try:
                execute_code(
                    language=command['language'],
                    code=command['command'],
                    targets=self.targets(),
                    deferred=command['deferred'],
                    compact_undo=command['force_compact_undo'])
            except Exception as e:
                import traceback
                print(EXECUTION_WARNING.format(
                    object='shape',
                    name=self.options['text.content'],
                    error=e))
                print(traceback.format_exc())

    def select(self, selection_mode='replace'):
        select_targets([self], selection_mode=selection_mode)

    def targets(self):
        return self.options['action.targets']

    def set_targets(self, targets):
        self.options['action.targets'] = targets

    def is_interactive(self):
        return bool(
            [cmd for cmd in self.options['action.commands'] if cmd['enabled']])

    def has_right_click_command(self):
        return bool([
            cmd for cmd in self.options['action.commands']
            if cmd['enabled'] and cmd['button'] == 'right'])

    def is_background(self):
        return self.options['background']

    def visibility_layer(self):
        return self.options['visibility_layer']

    def synchronize_image(self):
        path = expand_path(self.options['image.path'])
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


def _find_commands(commands, button, ctrl=False, shift=False):
    result = []
    for command in commands:
        conditions = (
            command['button'] == button and
            command['ctrl'] == ctrl and
            command['shift'] == shift)
        if conditions:
            result.append(command)
    return result
