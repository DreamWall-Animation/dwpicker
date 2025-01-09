from functools import partial
from collections import defaultdict

from maya import cmds
import maya.OpenMaya as om
from PySide2 import QtWidgets, QtGui, QtCore

from dwpicker.dialog import warning
from dwpicker.interactive import (
    SelectionSquare, cursor_in_shape, rect_intersects_shape)
from dwpicker.interactive import Shape
from dwpicker.interactionmanager import InteractionManager
from dwpicker.geometry import split_line, get_combined_rects
from dwpicker.languages import execute_code, EXECUTION_WARNING
from dwpicker.optionvar import (
    SYNCHRONYZE_SELECTION, ZOOM_SENSITIVITY)
from dwpicker.painting import (
    ViewportMapper, draw_shape, draw_selection_square, draw_picker_focus)
from dwpicker.qtutils import get_cursor, clear_layout
from dwpicker.stack import create_stack_splitters, count_splitters
from dwpicker.selection import (
    select_targets, select_shapes_from_selection, get_selection_mode,
    NameclashError)


SPLITTER_STYLE = """\
QSplitter::handle {
    background-color: rgba(0, 0, 0, 50);
    border: 1px solid #444;
    width: 2px;
    height: 2px;
}
"""


def align_shapes_on_line(shapes, point1, point2):
    centers = split_line(point1, point2, len(shapes))
    for center, shape in zip(centers, shapes):
        shape.rect.moveCenter(center)
        shape.synchronize_rect()
        shape.update_path()


def set_shapes_hovered(
        shapes,
        world_cursor,
        viewport_cursor,
        selection_rect,
        viewport_selection_rect,
        viewportmapper=None):
    """
    It set hovered the shape if his rect contains the cursor.
    """
    if not shapes:
        return
    world_cursor = world_cursor.toPoint()
    shapes = [s for s in shapes if not s.is_background()]
    selection_shapes_intersect_selection = [
        s for s in shapes
        if cursor_in_shape(s, world_cursor, viewport_cursor, False, viewportmapper)
        or rect_intersects_shape(
            shape=s,
            unit_rect=selection_rect,
            viewport_rect=viewport_selection_rect,
            force_world_space=False,
            viewportmapper=viewportmapper)]
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


def detect_hovered_shape(shapes, world_cursor, screen_cursor, viewportmapper):
    if not shapes:
        return
    for shape in reversed(shapes):
        hovered = cursor_in_shape(
            shape=shape,
            world_cursor=world_cursor,
            viewpoert_cursor=screen_cursor,
            force_world_space=False,
            viewportmapper=viewportmapper)
        if hovered and not shape.is_background():
            return shape


def list_targets(shapes):
    return {t for s in shapes for t in s.targets()}


class PickerStackedView(QtWidgets.QWidget):
    dataChanged = QtCore.Signal()
    addButtonRequested = QtCore.Signal(int, int, int, int)
    updateButtonRequested = QtCore.Signal(object)
    deleteButtonRequested = QtCore.Signal()

    def __init__(self, editable=True, parent=None):
        super(PickerStackedView, self).__init__(parent)
        self.editable = editable
        self.pickers = []
        self.shapes = []
        self.layers_menu = VisibilityLayersMenu()
        self.layers_menu.visibilities_changed.connect(self.update)

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet(SPLITTER_STYLE)

    def register_callbacks(self):
        for picker in self.pickers:
            picker.register_callbacks()

    def unregister_callbacks(self):
        for picker in self.pickers:
            picker.unregister_callbacks()

    def reset(self, force_all=False):
        if not force_all:
            for picker in self.pickers:
                if picker.rect().contains(get_cursor(self)):
                    picker.reset()
                    return
        # If no picker hovered, focus all.
        for picker in self.pickers:
            picker.reset()

    def create_pickers(self, data):
        self.unregister_callbacks()
        self.pickers = [
            PickerView(self.editable, i, self.layers_menu, self)
            for i in range(count_splitters(data['general']['panels']))]

        for picker in self.pickers:
            picker.dataChanged.connect(self.dataChanged.emit)
            picker.multipleShapesAdded.connect(self.add_multiple_shapes)
            picker.addButtonRequested.connect(self.addButtonRequested.emit)
            picker.updateButtonRequested.connect(self.updateButtonRequested.emit)
            picker.deleteButtonRequested.connect(self.deleteButtonRequested.emit)

    def create_splitters(self, data):
        panels = data['general']['panels']
        orientation = data['general']['panels.orientation']
        splitter = create_stack_splitters(panels, self.pickers, orientation)
        clear_layout(self.layout)
        self.layout.addWidget(splitter)

    def set_picker_data(
            self, data, panels_changed=False, panels_resized=False):
        update_splitters = panels_changed or panels_resized or not self.pickers
        if panels_changed or not self.pickers:
            self.create_pickers(data)
        self.set_auto_center(False)
        if update_splitters:
            self.create_splitters(data)

        self.dispatch_picker_data(data)
        # HACK: delay the auto_center switch to avoid weird resize issue at
        # splitter recreation time.
        QtCore.QTimer.singleShot(1, partial(self.set_auto_center, True))

    def set_auto_center(self, state):
        for picker in self.pickers:
            picker.auto_center = state

    def dispatch_picker_data(self, data):
        self.shapes = [Shape(s) for s in data['shapes']]
        self.layers_menu.set_shapes(self.shapes)

        panels_zoom_locked = data['general']['panels.zoom_locked']
        for picker, zoom_locked in zip(self.pickers, panels_zoom_locked):
            picker.zoom_locked = zoom_locked
            picker.shapes = []
            picker.global_commands = data['general']['menu_commands']
            picker.interaction_manager.shapes = []

        for shape in self.shapes:
            if shape.options['panel'] >= len(self.pickers):
                continue
            picker = self.pickers[shape.options['panel']]
            picker.shapes.append(shape)
            picker.interaction_manager.shapes.append(shape)

        self.update()

    def add_shape(self, shape, prepend=False):
        if prepend:
            self.shapes.insert(0, shape)
        else:
            self.shapes.append(shape)
        self.layers_menu.set_shapes(self.shapes)

        if shape.options['panel'] >= len(self.pickers):
            return

        picker = self.pickers[shape.options['panel']]
        if prepend:
            picker.shapes.insert(0, shape)
        else:
            picker.shapes.append(shape)
        picker.update()

    def add_multiple_shapes(self, shapes):
        self.shapes.extend(shapes)
        self.layers_menu.set_shapes(self.shapes)
        self.dataChanged.emit()

    def remove_shape(self, shape):
        self.shapes.remove(shape)
        if shape.options['panel'] >= len(self.pickers):
            return
        picker = self.pickers[shape.options['panel']]
        picker.shapes.remove(shape)

    def set_drag_shapes(self, shapes, panel):
        self.pickers[panel].drag_shapes = shapes


class PickerView(QtWidgets.QWidget):
    dataChanged = QtCore.Signal()
    multipleShapesAdded = QtCore.Signal(list)
    addButtonRequested = QtCore.Signal(int, int, int, int)
    updateButtonRequested = QtCore.Signal(object)
    deleteButtonRequested = QtCore.Signal()

    def __init__(self, editable=True, panel=0, layers_menu=None, parent=None):
        super(PickerView, self).__init__(parent)
        self.callbacks = []
        self.panel = panel
        self.auto_center = True
        self.editable = editable
        self.interaction_manager = InteractionManager()
        self.viewportmapper = ViewportMapper()
        self.selection_square = SelectionSquare()
        self.layers_menu = layers_menu or VisibilityLayersMenu()
        self.setMouseTracking(True)
        self.global_commands = []
        self.shapes = []
        self.clicked_shape = None
        self.drag_shapes = []
        self.zoom_locked = False

    def register_callbacks(self):
        self.unregister_callbacks()
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

    def set_picker_data(self, data):
        shapes = [Shape(s) for s in data['shapes'] if s['panel'] == self.panel]
        self.shapes = shapes
        self.global_commands = data['general']['menu_commands']
        self.interaction_manager.shapes = shapes
        self.layers_menu.set_shapes(shapes)
        self.update()

    def visible_shapes(self):
        return [
            s for s in self.shapes if
            not s.visibility_layer()
            or s.visibility_layer() not in self.layers_menu.hidden_layers]

    def reset(self):
        shapes = [
            s for s in self.visible_shapes() if
            s.options['shape.space'] == 'world']
        shapes_rects = [s.rect for s in shapes if s.selected]
        if not shapes_rects:
            shapes_rects = [s.rect for s in shapes]
        if not shapes_rects:
            self.update()
            return
        self.viewportmapper.viewsize = self.size()
        rect = get_combined_rects(shapes_rects)
        if self.zoom_locked:
            x = rect.center().x() - (self.size().width() / 2)
            y = rect.center().y() - (self.size().height() / 2)
            self.viewportmapper.origin = QtCore.QPointF(x, y)
        else:
            self.viewportmapper.focus(rect)
        self.update()

    def resizeEvent(self, event):
        if not self.auto_center:
            return
        self.viewportmapper.viewsize = self.size()
        size = (event.size() - event.oldSize()) / 2
        offset = QtCore.QPointF(size.width(), size.height())
        self.viewportmapper.origin -= offset
        self.update()

    def enterEvent(self, _):
        self.update()

    def leaveEvent(self, _):
        self.update()

    def mousePressEvent(self, event):
        self.setFocus(QtCore.Qt.MouseFocusReason)
        self.shapes.extend(self.drag_shapes)
        world_cursor = self.viewportmapper.to_units_coords(event.pos())
        shapes = self.visible_shapes()
        self.clicked_shape = detect_hovered_shape(
            shapes=shapes,
            world_cursor=world_cursor.toPoint(),
            screen_cursor=event.pos(),
            viewportmapper=self.viewportmapper)
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
        world_cursor = self.viewportmapper.to_units_coords(event.pos())
        zoom = self.interaction_manager.zoom_button_pressed
        shapes = self.visible_shapes()
        hovered_shape = detect_hovered_shape(
            shapes=shapes,
            world_cursor=world_cursor.toPoint(),
            screen_cursor=event.pos(),
            viewportmapper=self.viewportmapper)

        interact = (
            self.clicked_shape and
            self.clicked_shape is hovered_shape and
            self.clicked_shape.is_interactive())

        if zoom and self.interaction_manager.alt_pressed:
            self.release(event)
            return

        if self.interaction_manager.mode == InteractionManager.DRAGGING:
            self.multipleShapesAdded.emit(self.drag_shapes[:])
            self.drag_shapes = []
            self.release(event)
            return

        elif self.interaction_manager.mode == InteractionManager.SELECTION and not interact:
            try:
                select_targets(shapes, selection_mode=selection_mode)
            except NameclashError as e:
                warning('Selection Error', str(e), parent=self)
                self.release(event)
                return

        if not self.clicked_shape:
            if self.interaction_manager.right_click_pressed:
                self.call_context_menu()

        elif self.clicked_shape is hovered_shape:
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
        world_cursor=self.viewportmapper.to_units_coords(event.pos())
        selection_rect = (
            self.selection_square.rect or
            QtCore.QRectF(world_cursor, world_cursor))
        unit_selection_rect = self.viewportmapper.to_units_rect(selection_rect)
        unit_selection_rect = unit_selection_rect.toRect()

        set_shapes_hovered(
            shapes=self.visible_shapes(),
            world_cursor=world_cursor,
            viewport_cursor=event.pos(),
            selection_rect=unit_selection_rect,
            viewport_selection_rect=selection_rect,
            viewportmapper=self.viewportmapper)

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
        screen_cursor = get_cursor(self)
        world_cursor = self.viewportmapper.to_units_coords(screen_cursor)
        shape = detect_hovered_shape(
            self.visible_shapes(), world_cursor, screen_cursor,
            self.viewportmapper)
        context_menu = PickerMenu(self.global_commands, shape)

        method = partial(self.add_button, world_cursor, button_type=0)
        context_menu.add_single.triggered.connect(method)
        context_menu.add_single.setEnabled(bool(cmds.ls(selection=True)))

        method = partial(self.add_button, world_cursor, button_type=1)
        context_menu.add_multiple.triggered.connect(method)
        state = len(cmds.ls(selection=True)) > 1
        context_menu.add_multiple.setEnabled(state)

        method = partial(self.add_button, world_cursor, button_type=2)
        context_menu.add_command.triggered.connect(method)

        method = partial(self.updateButtonRequested.emit, self.clicked_shape)
        context_menu.update_button.triggered.connect(method)
        state = bool(self.clicked_shape) and bool(cmds.ls(selection=True))
        context_menu.update_button.setEnabled(state)

        method = self.deleteButtonRequested.emit
        context_menu.delete_selected.triggered.connect(method)

        if self.layers_menu.displayed:
            context_menu.addSeparator()
            context_menu.addMenu(self.layers_menu)

        action = context_menu.exec_(QtGui.QCursor.pos())
        if isinstance(action, CommandAction):
            if not shape:
                self.execute_menu_command(action.command)
                return
            shape.execute(command=action.command)

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
        self.addButtonRequested.emit(
            self.panel, position.x(), position.y(), button_type)

    def paintEvent(self, _):
        try:
            painter = QtGui.QPainter()
            painter.begin(self)
            if self.rect().contains(get_cursor(self)):
                draw_picker_focus(painter, self.rect())
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
                draw_shape(
                    painter, shape,
                    force_world_space=False,
                    viewportmapper=self.viewportmapper)
            if self.selection_square.rect:
                draw_selection_square(
                    painter, self.selection_square.rect)
        except BaseException:
            pass  # avoid crash
            # TODO: log the error
        finally:
            painter.end()


class CommandAction(QtWidgets.QAction):
    def __init__(self, command, parent=None):
        super(CommandAction).__init__(command['caption'], parent)
        self.command = command


class PickerMenu(QtWidgets.QMenu):
    def __init__(self, global_commands=None, shape=None, parent=None):
        super(PickerMenu, self).__init__(parent)
        if shape and shape.options['action.menu_commands']:
            for command in shape.options['action.menu_commands']:
                self.addAction(CommandAction(command, self))
            if not global_commands:
                self.addSeparator()

        if global_commands:
            for command in global_commands:
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
    visibilities_changed = QtCore.Signal()
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
        self.visibilities_changed.emit()
