from copy import deepcopy
from PySide2 import QtCore, QtGui
from dwpicker.geometry import proportional_rect
from dwpicker.languages import execute_code, EXECUTION_WARNING
from dwpicker.path import expand_path
from dwpicker.selection import select_targets
from dwpicker.shapepath import (
    get_shape_painter_path, get_screenspace_qpath, get_absolute_path,
    get_default_path, get_worldspace_qpath)
from dwpicker.templates import BUTTON
from dwpicker.viewport import to_screenspace_coords


def build_multiple_shapes(targets, override):
    shapes = [deepcopy(BUTTON) for _ in range(len(targets))]
    for shape, target in zip(shapes, targets):
        if override:
            shape.update(override)
        shape['action.targets'] = [target]
    return [Shape(shape) for shape in shapes]


def rect_intersects_shape(
        shape, unit_rect, viewport_rect=None,
        force_world_space=True,
        viewportmapper=None):

    if force_world_space or shape.options['shape.space'] == 'world':
        if shape.path and shape.options['shape'] == 'custom':
            return shape.path.intersects(unit_rect)
        return shape.rect.intersects(unit_rect)

    if shape.path and shape.options['shape'] == 'custom':
        path = get_screenspace_qpath(
            path=shape.options['shape.path'],
            point=(shape.options['shape.left'], shape.options['shape.top']),
            anchor=shape.options['shape.anchor'],
            viewport_size=viewportmapper.viewsize)
        return path.intersects(viewport_rect)

    rect = to_shape_space_rect(
        rect=shape.rect,
        shape=shape,
        force_world_space=False,
        viewportmapper=viewportmapper)

    return rect.intersects(viewport_rect)


def to_shape_space(value, shape, force_world_space, viewportmapper):
    if shape.options['shape.space'] == 'world' or force_world_space:
        return viewportmapper.to_viewport(value)
    return value


def to_shape_space_rect(rect, shape, force_world_space, viewportmapper):
    if shape.options['shape.space'] == 'world' or force_world_space:
        return viewportmapper.to_viewport_rect(rect)
    rect = QtCore.QRectF(rect)
    point = to_screenspace_coords(
        rect.topLeft(), shape.options['shape.anchor'], viewportmapper.viewsize)
    rect.moveTopLeft(point)
    return rect


def cursor_in_shape(
        shape,
        world_cursor,
        viewpoert_cursor=None,
        force_world_space=True,
        viewportmapper=None):

    if force_world_space or shape.options['shape.space'] == 'world':
        if shape.path and shape.options['shape'] == 'custom':
            return shape.path.contains(world_cursor)
        return shape.rect.contains(world_cursor)

    if shape.path and shape.options['shape'] == 'custom':
        path = get_screenspace_qpath(
            path=shape.options['shape.path'],
            point=(shape.options['shape.left'], shape.options['shape.top']),
            anchor=shape.options['shape.anchor'],
            viewport_size=viewportmapper.viewsize)
        return path.contains(viewpoert_cursor)

    rect = to_shape_space_rect(
        rect=shape.rect,
        shape=shape,
        force_world_space=False,
        viewportmapper=viewportmapper)
    return rect.contains(viewpoert_cursor)


def get_shape_rect_from_options(options):
    return QtCore.QRectF(
        options['shape.left'],
        options['shape.top'],
        options['shape.width'],
        options['shape.height'])


class Shape():
    def __init__(self, options):
        # This is necessary for temprary Shape object used in multiple shapes
        # creation.
        if 'children' not in options:
            options['children'] = []

        self.hovered = False
        self.clicked = False
        self.selected = False
        self.options = options
        self.rect = get_shape_rect_from_options(options)
        self.pixmap = None
        self.image_rect = None
        self.path = get_shape_painter_path(self)
        self.synchronize_image()
        self._buffer_path = None

    def set_clicked(self, cursor):
        self.clicked = self.rect.contains(cursor)

    def release(self, cursor):
        self.clicked = False
        self.hovered = self.rect.contains(cursor)

    def update_path(self):
        if self.options['shape'] == 'custom' and not self.options['shape.path']:
            self.options['shape.path'] = get_default_path(self.options)
        self.path = get_shape_painter_path(self)
        self._buffer_path = None

    def get_painter_path(self, force_world_space, viewportmapper=None):
        if self.options['shape.space'] == 'world' or force_world_space:
            if self._buffer_path is None:
                left, top = self.options['shape.left'], self.options['shape.top']
                path = self.options['shape.path'] or get_default_path(self.options)
                self._buffer_path = get_worldspace_qpath(get_absolute_path((left, top), path))
            return viewportmapper.to_viewport_path(self._buffer_path)

        return get_screenspace_qpath(
            path=self.options['shape.path'],
            point=(self.options['shape.left'], self.options['shape.top']),
            anchor=self.options['shape.anchor'],
            viewport_size=viewportmapper.viewsize)

    def synchronize_rect(self):
        self.options['shape.left'] = self.rect.left()
        self.options['shape.top'] = self.rect.top()
        self.options['shape.width'] = self.rect.width()
        self.options['shape.height'] = self.rect.height()

    def bounding_rect(self):
        if self.options['shape'] == 'custom':
            return self.path.boundingRect()
        return self.rect

    def content_rect(self):
        rect = (
            self.rect if self.options['shape'] != 'custom' else
            self.path.boundingRect())
        if self.options['shape'] == 'round':
            return proportional_rect(rect, 70)
        return rect

    def execute(self, command=None, button=None, shift=False, ctrl=False):
        if command is not None:
            commands = [command]
        else:
            commands = _find_commands(
                self.options['action.commands'],
                button, shift=shift, ctrl=ctrl)
        for command in commands:
            try:
                execute_code(
                    language=command['language'],
                    code=command['command'],
                    shape=self,
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
        if self.options['image.fit'] and not self.options['image.ratio']:
            self.image_rect = None
            return
        if not self.options['image.fit']:
            self.image_rect = QtCore.QRectF(
                self.rect.left(),
                self.rect.top(),
                self.options['image.width'],
                self.options['image.height'])
            self.image_rect.moveCenter(self.bounding_rect().center())
            return
        rect = self.bounding_rect()
        ratio = self.options['image.width'] / self.options['image.height']
        width = rect.width()
        height = rect.width() / ratio
        if rect.height() < height:
            width = rect.height() * ratio
            height = rect.height()
        self.image_rect = QtCore.QRectF(rect.left(), rect.top(), width, height)
        self.image_rect.moveCenter(rect.center())


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
