from copy import deepcopy
from functools import partial

from maya import cmds
import maya.OpenMaya as om
from dwpicker.pyside import QtWidgets, QtGui, QtCore

from dwpicker.align import align_shapes_on_line
from dwpicker.compatibility import ensure_general_options_sanity
from dwpicker.document import PickerDocument
from dwpicker.dialog import warning, CommandEditorDialog
from dwpicker.interactive import SelectionSquare
from dwpicker.interactionmanager import InteractionManager
from dwpicker.geometry import get_combined_rects, get_connection_path
from dwpicker.languages import execute_code
from dwpicker.optionvar import (
    save_optionvar, DEFAULT_BG_COLOR, DEFAULT_TEXT_COLOR, DEFAULT_WIDTH,
    DEFAULT_HEIGHT, DEFAULT_LABEL, DISPLAY_HIERARCHY_IN_PICKER,
    LAST_COMMAND_LANGUAGE, SYNCHRONYZE_SELECTION, ZOOM_SENSITIVITY)
from dwpicker.painting import (
    draw_shape, draw_selection_square, draw_picker_focus, draw_connections)
from dwpicker.qtutils import get_cursor, clear_layout
from dwpicker.shape import (
    build_multiple_shapes, cursor_in_shape, rect_intersects_shape)
from dwpicker.stack import create_stack_splitters, count_panels
from dwpicker.selection import (
    select_targets, select_shapes_from_selection, get_selection_mode,
    NameclashError)
from dwpicker.templates import BUTTON, COMMAND
from dwpicker.viewport import ViewportMapper


SPLITTER_STYLE = """\
QSplitter::handle {
    background-color: rgba(0, 0, 0, 50);
    border: 1px solid #444;
    width: 2px;
    height: 2px;
}
"""


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

    def __init__(self, document=None, editable=True, parent=None):
        super(PickerStackedView, self).__init__(parent)
        self.document = document or PickerDocument.create()
        mtd = self.general_option_changed
        self.document.general_option_changed.connect(mtd)
        self.document.data_changed.connect(self.full_refresh)
        self.editable = editable
        self.pickers = []
        self.widget = None
        self.last_selected_tab = None

        self.layers_menu = VisibilityLayersMenu(document)
        self.layers_menu.visibilities_changed.connect(self.update)

        self.as_sub_tab = document.data['general']['panels.as_sub_tab']
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet(SPLITTER_STYLE)
        self.create_pickers()
        self.create_panels()

    def register_callbacks(self):
        for picker in self.pickers:
            picker.register_callbacks()

    def unregister_callbacks(self):
        for picker in self.pickers:
            picker.unregister_callbacks()

    def reset(self, force_all=False):
        if not force_all and not isinstance(self.widget, QtWidgets.QTabWidget):
            for picker in self.pickers:
                if picker.rect().contains(get_cursor(picker)):
                    picker.reset()
                    return picker.panel

        elif not force_all:
            picker = self.pickers[self.widget.currentIndex()]
            picker.reset()
            return

        # If no picker hovered, focus all.
        if self.document.data['general']['panels.as_sub_tab']:
            viewsize = self.pickers[0].viewportmapper.viewsize
        else:
            viewsize = None
        for picker in self.pickers:
            picker.reset(viewsize)

    def create_pickers(self):
        self.unregister_callbacks()
        self.pickers = [
            PickerPanelView(
                self.document, self.editable, i, self.layers_menu, self)
            for i in range(self.document.panel_count())]
        for picker in self.pickers:
            picker.size_event_triggered.connect(self.picker_resized)
        self.register_callbacks()

    def picker_resized(self, event):
        data = self.document.data
        if not data['general']['panels.as_sub_tab']:
            return
        for i, picker in enumerate(self.pickers):
            if i == self.widget.currentIndex():
                continue
            picker.adjust_center(event.size(), event.oldSize())

    def copy_pickers(self):
        self.pickers = [p.copy() for p in self.pickers]
        for picker in self.pickers:
            picker.size_event_triggered.connect(self.picker_resized)

    def create_panels(self, panel=None):
        data = self.document.data
        if not self.as_sub_tab:
            panels = data['general']['panels']
            orientation = data['general']['panels.orientation']
            self.widget = create_stack_splitters(
                panels, self.pickers, orientation)
        else:
            self.widget = QtWidgets.QTabWidget()
            names = data['general']['panels.names']
            for picker, name in zip(self.pickers, names):
                self.widget.addTab(picker, name)

            # Check "if panel is not None" (0 is a valid value,
            # so "if panel" would be incorrect)
            if panel is not None:
                self.widget.setCurrentIndex(panel)
                self.last_selected_tab = panel
            elif self.last_selected_tab:
                self.widget.setCurrentIndex(self.last_selected_tab)
            self.widget.currentChanged.connect(self.on_tab_changed)

        clear_layout(self.layout)
        self.layout.addWidget(self.widget)

    def on_tab_changed(self, index):
        self.last_selected_tab = index

    def full_refresh(self):
        panels = self.document.data['general']['panels']
        if count_panels(panels) != len(self.pickers):
            self.create_pickers()
        self.create_panels()

    def general_option_changed(self, _, option):
        value = self.document.data['general'][option]
        panels = self.document.data['general']['panels']
        reset = False
        if option == 'panels.as_sub_tab':
            state = self.document.data['general']['panels.as_sub_tab']
            self.as_sub_tab = state

        if option in ('panels', 'panels.orientation', 'panels.as_sub_tab'):
            ensure_general_options_sanity(self.document.data['general'])
            if count_panels(panels) != len(self.pickers):
                self.create_pickers()
                reset = True
            else:
                self.copy_pickers()
                reset = option in ('panels.orientation', 'panels.as_sub_tab')
            self.create_panels()

        if option == 'panels.names' and self.as_sub_tab:
            for i, name in enumerate(value):
                self.widget.setTabText(i, name)

        if option == 'hidden_layers':
            self.layers_menu.hidden_layers = value

        if reset:
            QtCore.QTimer.singleShot(0, partial(self.reset, force_all=True))
        self.update()

    def set_auto_center(self, state):
        for picker in self.pickers:
            picker.auto_center = state


class PickerPanelView(QtWidgets.QWidget):
    size_event_triggered = QtCore.Signal(object)

    def __init__(
            self, document, editable=True, panel=0, layers_menu=None,
            parent=None):
        super(PickerPanelView, self).__init__(parent)
        self._shown = False

        self.document = document
        self.document.shapes_changed.connect(self.update)
        self.callbacks = []
        self.panel = panel
        self.auto_center = True
        self.editable = editable
        self.interaction_manager = InteractionManager()
        self.viewportmapper = ViewportMapper()
        self.selection_square = SelectionSquare()
        self.layers_menu = layers_menu
        self.setMouseTracking(True)
        self.clicked_shape = None
        self.drag_shapes = []

    def copy(self):
        self.unregister_callbacks()
        picker = PickerPanelView(
            self.document, self.editable, self.panel, self.layers_menu)
        picker.register_callbacks()
        picker.viewportmapper = self.viewportmapper
        picker.register_callbacks()
        picker.auto_center = self.auto_center
        self.deleteLater()
        return picker

    def showEvent(self, event):
        if self._shown:
            return super(PickerPanelView, self).showEvent(event)
        self._shown = True
        self.reset(self.size(), selection_only=False)

    @property
    def zoom_locked(self):
        return self.document.data['general']['panels.zoom_locked'][self.panel]

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
        shapes = self.document.shapes_by_panel[self.panel]
        select_shapes_from_selection(shapes)
        self.update()

    def visible_shapes(self):
            return [
            s for s in self.document.shapes_by_panel[self.panel] if
            not s.visibility_layer()
            or s.visibility_layer() not in self.layers_menu.hidden_layers]

    def reset(self, viewsize=None, selection_only=True):
        shapes = [
            s for s in self.visible_shapes() if
            s.options['shape.space'] == 'world' and not
            s.options['shape.ignored_by_focus']]
        shapes_rects = [
            s.bounding_rect() for s in shapes if
            not selection_only or s.selected]
        if not shapes_rects:
            shapes_rects = [s.bounding_rect() for s in shapes]
        if not shapes_rects:
            self.update()
            return
        self.viewportmapper.viewsize = viewsize or self.size()
        rect = get_combined_rects(shapes_rects)
        if self.zoom_locked:
            self.viewportmapper.zoom = 1
            x = rect.center().x() - (self.size().width() / 2)
            y = rect.center().y() - (self.size().height() / 2)
            self.viewportmapper.origin = QtCore.QPointF(x, y)
        else:
            self.viewportmapper.focus(rect)
        self.update()

    def resizeEvent(self, event):
        if not self.auto_center or event.oldSize() == QtCore.QSize(-1, -1):
            return
        self.adjust_center(event.size(), event.oldSize())
        self.size_event_triggered.emit(event)

    def adjust_center(self, size, old_size):
        self.viewportmapper.viewsize = self.size()
        size = (size - old_size) / 2
        offset = QtCore.QPointF(size.width(), size.height())
        self.viewportmapper.origin -= offset
        self.update()

    def enterEvent(self, _):
        self.update()

    def leaveEvent(self, _):
        self.update()

    def mousePressEvent(self, event):

        self.setFocus(QtCore.Qt.MouseFocusReason)
        if self.drag_shapes and event.button() == QtCore.Qt.LeftButton:
            pos = self.viewportmapper.to_units_coords(event.pos())
            align_shapes_on_line(self.drag_shapes, pos, pos)

        world_cursor = self.viewportmapper.to_units_coords(event.pos())
        shapes = self.visible_shapes()
        self.clicked_shape = detect_hovered_shape(
            shapes=shapes,
            world_cursor=world_cursor.toPoint(),
            screen_cursor=event.pos(),
            viewportmapper=self.viewportmapper)

        shapes = self.document.shapes_by_panel[self.panel]
        hsh = any(s.hovered for s in shapes)
        self.interaction_manager.update(
            event,
            pressed=True,
            has_shape_hovered=hsh,
            dragging=bool(self.drag_shapes))

    def mouseDoubleClickEvent(self, event):
        world_cursor = self.viewportmapper.to_units_coords(event.pos())
        shapes = self.visible_shapes()
        clicked_shape = detect_hovered_shape(
            shapes=shapes,
            world_cursor=world_cursor.toPoint(),
            screen_cursor=event.pos(),
            viewportmapper=self.viewportmapper)

        if not clicked_shape or event.button() != QtCore.Qt.LeftButton:
            return

        shift = self.interaction_manager.shift_pressed
        ctrl = self.interaction_manager.ctrl_pressed
        selection_mode = get_selection_mode(shift=shift, ctrl=ctrl)
        shapes = self.document.all_children(clicked_shape.options['id'])
        for shape in shapes:
            shape.hovered = True
        select_targets(self.visible_shapes(), selection_mode=selection_mode)

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
            self.add_drag_shapes()
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

    def add_drag_shapes(self):
        shapes_data = [s.options for s in self.drag_shapes]
        self.document.add_shapes(shapes_data, hierarchize=True)
        self.document.shapes_changed.emit()
        self.document.record_undo()
        self.drag_shapes = []

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
            return self.update()

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
            return self.update()

        elif self.interaction_manager.mode == InteractionManager.NAVIGATION:
            offset = self.interaction_manager.mouse_offset(event.pos())
            if offset is not None:
                self.viewportmapper.origin = (
                    self.viewportmapper.origin - offset)
            return self.update()
        self.update()

    def call_context_menu(self):
        if not self.editable:
            return

        screen_cursor = get_cursor(self)
        world_cursor = self.viewportmapper.to_units_coords(screen_cursor)
        shape = detect_hovered_shape(
            self.visible_shapes(), world_cursor, screen_cursor,
            self.viewportmapper)

        global_commands = self.document.data['general']['menu_commands']
        context_menu = PickerMenu(global_commands, shape)

        method = partial(self.add_button, world_cursor, button_type=0)
        context_menu.add_single.triggered.connect(method)
        context_menu.add_single.setEnabled(bool(cmds.ls(selection=True)))

        method = partial(self.add_button, world_cursor, button_type=1)
        context_menu.add_multiple.triggered.connect(method)
        state = len(cmds.ls(selection=True)) > 1
        context_menu.add_multiple.setEnabled(state)

        method = partial(self.add_button, world_cursor, button_type=2)
        context_menu.add_command.triggered.connect(method)

        method = partial(self.update_button, self.clicked_shape)
        context_menu.update_button.triggered.connect(method)
        state = bool(self.clicked_shape) and bool(cmds.ls(selection=True))
        context_menu.update_button.setEnabled(state)

        context_menu.delete_selected.triggered.connect(self.delete_buttons)

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
            print(traceback.format_exc())

    def update_button(self, shape):
        shape.set_targets(cmds.ls(selection=True))
        self.document.record_undo()

    def delete_buttons(self):
        selected_shapes = [s for s in self.document.shapes if s.selected]
        self.document.remove_shapes(selected_shapes)
        self.document.record_undo()
        self.document.shapes_changed.emit()

    def get_quick_options(self):

        return {
            'bgcolor.normal': cmds.optionVar(query=DEFAULT_BG_COLOR),
            'text.color': cmds.optionVar(query=DEFAULT_TEXT_COLOR),
            'shape.width': cmds.optionVar(query=DEFAULT_WIDTH),
            'shape.height': cmds.optionVar(query=DEFAULT_HEIGHT),
            'text.content': cmds.optionVar(query=DEFAULT_LABEL)}

    def add_button(self, position, button_type=0):
        """
        Button types:
            0 = Single button from selection.
            1 = Multiple buttons from selection.
            2 = Command button.
        """
        targets = cmds.ls(selection=True)
        if not targets and button_type <= 1:
            return warning("Warning", "No targets selected")

        if button_type == 1:
            overrides = self.get_quick_options()
            overrides['panel'] = self.panel
            shapes = build_multiple_shapes(targets, overrides)
            if not shapes:
                return
            self.drag_shapes = shapes
            return

        shape_data = deepcopy(BUTTON)
        shape_data['panel'] = self.panel
        shape_data['shape.left'] = position.x()
        shape_data['shape.top'] = position.y()
        shape_data.update(self.get_quick_options())
        if button_type == 0:
            shape_data['action.targets'] = targets
        else:
            text, result = (
                QtWidgets.QInputDialog.getText(self, 'Button text', 'text'))
            if not result:
                return
            shape_data['text.content'] = text
            command = deepcopy(COMMAND)
            languages = ['python', 'mel']
            language = languages[cmds.optionVar(query=LAST_COMMAND_LANGUAGE)]
            command['language'] = language
            dialog = CommandEditorDialog(command)
            if not dialog.exec_():
                return
            command = dialog.command_data()
            index = languages.index(command['language'])
            save_optionvar(LAST_COMMAND_LANGUAGE, index)
            shape_data['action.commands'] = [command]

        width = max([
            shape_data['shape.width'],
            len(shape_data['text.content']) * 7])
        shape_data['shape.width'] = width

        self.document.add_shapes([shape_data])
        self.document.record_undo()
        self.document.shapes_changed.emit()

    def paintEvent(self, _):
        try:
            painter = QtGui.QPainter()
            painter.begin(self)
            # Color background.
            color = self.document.data['general']['panels.colors'][self.panel]
            if color:
                painter.setPen(QtCore.Qt.NoPen)
                painter.setBrush(QtGui.QColor(color))
                painter.drawRect(self.rect())

            # Color border focus.
            if self.rect().contains(get_cursor(self)):
                draw_picker_focus(painter, self.rect())

            # List renderable shapes.
            painter.setRenderHints(QtGui.QPainter.Antialiasing)
            hidden_layers = self.layers_menu.hidden_layers
            shapes = [
                shape for shape in self.document.shapes_by_panel[self.panel] if
                not shape.visibility_layer() or
                shape.visibility_layer() not in hidden_layers]
            if self.interaction_manager.left_click_pressed:
                shapes.extend(self.drag_shapes)

            # Draw shapes and create a mask for arrows shapes.
            cutter = QtGui.QPainterPath()
            cutter.setFillRule(QtCore.Qt.WindingFill)
            for shape in shapes:
                qpath = draw_shape(
                    painter, shape,
                    force_world_space=False,
                    viewportmapper=self.viewportmapper)
                screen_space = shape.options['shape.space'] == 'screen'
                if not shape.options['background'] or screen_space:
                    cutter.addPath(qpath)

            # Draw hierarchy connections.
            connections_path = QtGui.QPainterPath()
            if cmds.optionVar(query=DISPLAY_HIERARCHY_IN_PICKER):
                for shape in shapes:
                    if shape.options['shape.space'] == 'screen':
                        continue
                    for child in shape.options['children']:
                        child = self.document.shapes_by_id.get(child)
                        hidden = (
                            child and
                            child.visibility_layer() and
                            child.visibility_layer() in hidden_layers)
                        screen_space = child.options['shape.space'] == 'screen'
                        panel = child.options['panel'] != shape.options['panel']
                        if hidden or screen_space or panel:
                            continue
                        start_point = shape.bounding_rect().center()
                        end_point = child.bounding_rect().center()
                        path = get_connection_path(
                            start_point, end_point, self.viewportmapper)
                        connections_path.addPath(path)
            connections_path = connections_path.subtracted(cutter)
            draw_connections(painter, connections_path)

            # Draw Selection square/
            if self.selection_square.rect:
                draw_selection_square(
                    painter, self.selection_square.rect)

        except BaseException as e:
            import traceback
            print(traceback.format_exc())
            print(str(e))
            pass  # avoid crash
            # TODO: log the error
        finally:
            painter.end()


class CommandAction(QtWidgets.QAction):
    def __init__(self, command, parent=None):
        super(CommandAction, self).__init__(command['caption'], parent)
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
    def __init__(self, document, parent=None):
        super(VisibilityLayersMenu, self).__init__('Visibility layers', parent)
        self.document = document
        self.document.shapes_changed.connect(self.update_actions)
        self.hidden_layers = document.data['general']['hidden_layers'][:]
        self.update_actions()

    @property
    def displayed(self):
        return bool(self.document.shapes_by_layer)

    def update_actions(self):
        self.clear()
        layers = list(self.document.shapes_by_layer)
        action = QtWidgets.QAction('Show all')
        for layer in layers:
            action = QtWidgets.QAction(layer, self)
            action.setCheckable(True)
            action.setChecked(layer not in self.hidden_layers)
            action.toggled.connect(partial(self.set_hidden_layer, layer))
            self.addAction(action)

    def set_hidden_layer(self, layer, state):
        if state is False and layer not in self.hidden_layers:
            self.hidden_layers.append(layer)
        if state is True and layer in self.hidden_layers:
            self.hidden_layers.remove(layer)
        self.visibilities_changed.emit()
