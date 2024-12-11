from functools import partial

from maya import cmds
import maya.OpenMaya as om
from PySide2 import QtWidgets, QtGui, QtCore

from dwpicker.dialog import warning
from dwpicker.interactive import (
    SelectionSquare, cursor_in_shape, rect_intersects_shape)
from dwpicker.interactionmanager import InteractionManager
from dwpicker.geometry import split_line, get_combined_rects
from dwpicker.languages import execute_code, EXECUTION_WARNING
from dwpicker.optionvar import (
    SYNCHRONYZE_SELECTION, ZOOM_SENSITIVITY)
from dwpicker.painting import ViewportMapper, draw_shape
from dwpicker.qtutils import get_cursor
from dwpicker.selection import (
    select_targets, select_shapes_from_selection, get_selection_mode,
    NameclashError)


def align_shapes_on_line(shapes, point1, point2):
    centers = split_line(point1, point2, len(shapes))
    for center, shape in zip(centers, shapes):
        shape.rect.moveCenter(center)
        shape.synchronize_rect()
        shape.update_path()


def set_shapes_hovered(shapes, cursor, selection_rect=None):
    """
    It set hovered the shape if his rect contains the cursor.
    """
    if not shapes:
        return
    cursor = cursor.toPoint()
    selection_rect = selection_rect or QtCore.QRect(cursor, cursor)
    shapes = [s for s in shapes if not s.is_background()]
    selection_shapes_intersect_selection = [
        s for s in shapes
        if cursor_in_shape(s, cursor) or
        rect_intersects_shape(s, selection_rect)]

    targets = list_targets(selection_shapes_intersect_selection)
    for s in shapes:
        if s.targets():
            # Set all buttons hovered from his targets contents.
            # I the physically hovered buttons contains targets, this will
            # highlight all buttons containing similare targets.
            state = next((False for t in s.targets() if t not in targets), True)
        elif not s.is_background():
            # Simple highlighting method for the interactive buttons.
            state = s in selection_shapes_intersect_selection
        else:
            state = False
        s.hovered = state


def detect_hovered_shape(shapes, cursor):
    if not shapes:
        return
    for shape in reversed(shapes):
        if cursor_in_shape(shape, cursor) and not shape.is_background():
            return shape


def list_targets(shapes):
    return {t for s in shapes for t in s.targets()}


class PickerView(QtWidgets.QWidget):
    dataChanged = QtCore.Signal()
    addButtonRequested = QtCore.Signal(int, int, int)
    updateButtonRequested = QtCore.Signal(object)
    deleteButtonRequested = QtCore.Signal()

    def __init__(self, editable=True, parent=None):
        super(PickerView, self).__init__(parent)
        self.callbacks = []
        self.editable = editable
        self.interaction_manager = InteractionManager()
        self.viewportmapper = ViewportMapper()
        self.selection_square = SelectionSquare()
        self.layers_menu = VisibilityLayersMenu()
        self.setMouseTracking(True)
        self.shapes = []
        self.clicked_shape = None
        self.context_menu = None
        self.drag_shapes = []
        self.zoom_locked = False

    def register_callbacks(self):
        method = self.sync_with_maya_selection
        cb = om.MEventMessage.addEventCallback('SelectionChanged', method)
        self.callbacks.append(cb)

    def unregister_callbacks(self):
        for callback in self.callbacks:
            om.MMessage.removeCallback(callback)
            self.callbacks.remove(callback)

    def sync_with_maya_selection(self, *_):
        if not cmds.optionVar(query=SYNCHRONYZE_SELECTION):
            return
        select_shapes_from_selection(self.shapes)
        self.update()

    def set_shapes(self, shapes):
        self.shapes = shapes
        self.interaction_manager.shapes = shapes
        self.layers_menu.set_shapes(shapes)
        self.update()

    def visible_shapes(self):
        return [
            s for s in self.shapes if
            not s.visibility_layer()
            or s.visibility_layer() not in self.layers_menu.hidden_layers]

    def reset(self):
        shapes = self.visible_shapes()
        shapes_rects = [s.rect for s in shapes if s.selected]
        if not shapes_rects:
            shapes_rects = [s.rect for s in shapes]
        if not shapes_rects:
            self.update()
            return
        self.viewportmapper.viewsize = self.size()
        rect = get_combined_rects(shapes_rects)
        self.viewportmapper.focus(rect)
        self.update()

    def resizeEvent(self, event):
        self.viewportmapper.viewsize = self.size()
        size = (event.size() - event.oldSize()) / 2
        offset = QtCore.QPointF(size.width(), size.height())
        self.viewportmapper.origin -= offset
        self.update()

    def mousePressEvent(self, event):
        self.setFocus(QtCore.Qt.MouseFocusReason)
        self.shapes.extend(self.drag_shapes)
        cursor = self.viewportmapper.to_units_coords(event.pos()).toPoint()
        shapes = self.visible_shapes()
        self.clicked_shape = detect_hovered_shape(shapes, cursor)
        hsh = any(s.hovered for s in self.shapes)
        self.interaction_manager.update(
            event,
            pressed=True,
            has_shape_hovered=hsh,
            dragging=bool(self.drag_shapes))

    def mouseReleaseEvent(self, event):
        shift = self.interaction_manager.shift_pressed
        ctrl = self.interaction_manager.ctrl_pressed
        selection_mode = get_selection_mode(shift=shift, ctrl=ctrl)
        cursor = self.viewportmapper.to_units_coords(event.pos()).toPoint()
        zoom = self.interaction_manager.zoom_button_pressed
        shapes = self.visible_shapes()
        interact = (
            self.clicked_shape and
            self.clicked_shape is detect_hovered_shape(shapes, cursor) and
            self.clicked_shape.is_interactive())

        if zoom and self.interaction_manager.alt_pressed:
            self.release(event)
            return

        if self.interaction_manager.mode == InteractionManager.DRAGGING:
            self.drag_shapes = []
            self.dataChanged.emit()

        elif self.interaction_manager.mode == InteractionManager.SELECTION and not interact:
            try:
                select_targets(self.shapes, selection_mode=selection_mode)
            except NameclashError as e:
                warning('Selection Error', str(e), parent=self)
                self.release(event)
                return

        if not self.clicked_shape:
            if self.interaction_manager.right_click_pressed:
                self.call_context_menu()

        elif self.clicked_shape is detect_hovered_shape(self.shapes, cursor):
            show_context = (
                self.interaction_manager.right_click_pressed and
                not self.clicked_shape.has_right_click_command())
            left_clicked = self.interaction_manager.left_click_pressed
            if show_context:
                self.call_context_menu()

            elif left_clicked and self.clicked_shape.targets():
                self.clicked_shape.select(selection_mode)

            if interact:
                button = (
                    'left' if self.interaction_manager.left_click_pressed
                    else 'right')
                self.clicked_shape.execute(
                    button=button,
                    ctrl=self.interaction_manager.ctrl_pressed,
                    shift=self.interaction_manager.shift_pressed)

        self.release(event)

    def release(self, event):
        self.interaction_manager.update(event, pressed=False)
        self.selection_square.release()
        self.clicked_shape = None
        self.update()

    def wheelEvent(self, event):
        # To center the zoom on the mouse, we save a reference mouse position
        # and compare the offset after zoom computation.
        if self.zoom_locked:
            return
        factor = .25 if event.angleDelta().y() > 0 else -.25
        self.zoom(factor, event.pos())
        self.update()

    def zoom(self, factor, reference):
        abspoint = self.viewportmapper.to_units_coords(reference)
        if factor > 0:
            self.viewportmapper.zoomin(abs(factor))
        else:
            self.viewportmapper.zoomout(abs(factor))
        relcursor = self.viewportmapper.to_viewport_coords(abspoint)
        vector = relcursor - reference
        self.viewportmapper.origin = self.viewportmapper.origin + vector

    def mouseMoveEvent(self, event):
        selection_rect = self.selection_square.rect
        if selection_rect:
            selection_rect = self.viewportmapper.to_units_rect(selection_rect)
            selection_rect = selection_rect.toRect()

        set_shapes_hovered(
            self.visible_shapes(),
            self.viewportmapper.to_units_coords(event.pos()),
            selection_rect)

        if self.interaction_manager.mode == InteractionManager.DRAGGING:
            point1 = self.viewportmapper.to_units_coords(
                self.interaction_manager.anchor)
            point2 = self.viewportmapper.to_units_coords(event.pos())
            align_shapes_on_line(self.drag_shapes, point1, point2)

        elif self.interaction_manager.mode == InteractionManager.SELECTION:
            if not self.selection_square.handeling:
                self.selection_square.clicked(event.pos())
            self.selection_square.handle(event.pos())
            return self.update()

        elif self.interaction_manager.mode == InteractionManager.ZOOMING:
            if self.zoom_locked:
                return self.update()
            offset = self.interaction_manager.mouse_offset(event.pos())
            if offset is not None and self.interaction_manager.zoom_anchor:
                sensitivity = float(cmds.optionVar(query=ZOOM_SENSITIVITY))
                factor = (offset.x() + offset.y()) / sensitivity
                self.zoom(factor, self.interaction_manager.zoom_anchor)

        elif self.interaction_manager.mode == InteractionManager.NAVIGATION:
            if self.zoom_locked:
                return self.update()
            offset = self.interaction_manager.mouse_offset(event.pos())
            if offset is not None:
                self.viewportmapper.origin = (
                    self.viewportmapper.origin - offset)

        self.update()

    def call_context_menu(self):
        if not self.editable:
            return

        self.context_menu = PickerMenu(self.clicked_shape)
        position = get_cursor(self)

        method = partial(self.add_button, position, button_type=0)
        self.context_menu.add_single.triggered.connect(method)
        self.context_menu.add_single.setEnabled(bool(cmds.ls(selection=True)))

        method = partial(self.add_button, position, button_type=1)
        self.context_menu.add_multiple.triggered.connect(method)
        state = len(cmds.ls(selection=True)) > 1
        self.context_menu.add_multiple.setEnabled(state)

        method = partial(self.add_button, position, button_type=2)
        self.context_menu.add_command.triggered.connect(method)

        method = partial(self.updateButtonRequested.emit, self.clicked_shape)
        self.context_menu.update_button.triggered.connect(method)
        state = bool(self.clicked_shape) and bool(cmds.ls(selection=True))
        self.context_menu.update_button.setEnabled(state)

        method = self.deleteButtonRequested.emit
        self.context_menu.delete_selected.triggered.connect(method)

        if self.layers_menu.displayed:
            self.context_menu.addMenu(self.layers_menu)

        action = self.context_menu.exec_(QtGui.QCursor.pos())
        if isinstance(action, CommandAction):
            self.execute_menu_command(action.command)

    def execute_menu_command(self, command):
        try:
            execute_code(
                language=command['language'],
                code=command['command'],
                deferred=command['deferred'],
                compact_undo=command['force_compact_undo'])
        except Exception as e:
            import traceback
            print(EXECUTION_WARNING.format(
                name=self.options['text.content'], error=e))
            print(traceback.format_exc())

    def add_button(self, position, button_type=0):
        """
        Button types:
            0 = Single button from selection.
            1 = Multiple buttons from selection.
            2 = Command button.
        """
        position = self.viewportmapper.to_units_coords(position).toPoint()
        self.addButtonRequested.emit(position.x(), position.y(), button_type)

    def paintEvent(self, _):
        try:
            painter = QtGui.QPainter()
            painter.begin(self)
            painter.setRenderHints(QtGui.QPainter.Antialiasing)
            if not self.shapes:
                return
            hidden_layers = self.layers_menu.hidden_layers
            for shape in self.shapes:
                visible = (
                    not shape.visibility_layer() or
                    not shape.visibility_layer() in hidden_layers)
                if not visible:
                    continue
                draw_shape(painter, shape, self.viewportmapper)
            self.selection_square.draw(painter)
        except BaseException:
            pass  # avoid crash
            # TODO: log the error
        finally:
            painter.end()


class CommandAction(QtWidgets.QAction):
    def __init__(self, command, parent=None):
        super().__init__(command['caption'], parent)
        self.command = command


class PickerMenu(QtWidgets.QMenu):
    def __init__(self, shape=None, parent=None):
        super(PickerMenu, self).__init__(parent)

        if shape and shape.options['action.menu_commands']:
            for command in shape.options['action.menu_commands']:
                self.addAction(CommandAction(command, self))
            self.addSeparator()

        self.add_single = QtWidgets.QAction('Add single button', self)
        self.add_multiple = QtWidgets.QAction('Add multiple buttons', self)
        self.update_button = QtWidgets.QAction('Update button', self)
        self.add_command = QtWidgets.QAction('Add command', self)
        text = 'Delete selected button(s)'
        self.delete_selected = QtWidgets.QAction(text, self)

        self.addAction(self.add_single)
        self.addAction(self.add_multiple)
        self.addAction(self.update_button)
        self.addSeparator()
        self.addAction(self.add_command)
        self.addSeparator()
        self.addAction(self.delete_selected)


class VisibilityLayersMenu(QtWidgets.QMenu):
    def __init__(self, parent=None):
        super(VisibilityLayersMenu, self).__init__('Visibility layers', parent)
        self.hidden_layers = []
        self.displayed = False

    def set_shapes(self, shapes):
        layers = sorted(
            {s.visibility_layer() for s in shapes if s.visibility_layer()})
        self.clear()
        action = QtWidgets.QAction('Show all')
        for layer in layers:
            action = QtWidgets.QAction(layer, self)
            action.setCheckable(True)
            action.setChecked(layer not in self.hidden_layers)
            action.toggled.connect(partial(self.set_hidden_layer, layer))
            self.addAction(action)
        self.displayed = bool(layers)

    def set_hidden_layer(self, layer, state):
        if state is False and layer not in self.hidden_layers:
            self.hidden_layers.append(layer)
        if state is True and layer in self.hidden_layers:
            self.hidden_layers.remove(layer)
