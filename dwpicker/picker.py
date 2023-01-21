from functools import partial

from maya import cmds
import maya.OpenMaya as om
from PySide2 import QtWidgets, QtGui, QtCore

from dwpicker.interactive import SelectionSquare
from dwpicker.dialog import warning
from dwpicker.geometry import split_line, get_combined_rects
from dwpicker.optionvar import (
    SYNCHRONYZE_SELECTION, ZOOM_BUTTON, ZOOM_SENSITIVITY)
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


def frame_shapes(shapes):
    offset_x = min(shape.rect.left() for shape in shapes)
    offset_y = min(shape.rect.top() for shape in shapes)
    offset = -min([offset_x, 0]), -min([offset_y, 0])

    for shape in shapes:
        shape.rect.moveLeft(shape.rect.left() + offset[0])
        shape.rect.moveTop(shape.rect.top() + offset[1])
        shape.synchronize_rect()


def set_shapes_hovered(shapes, cursor, selection_rect=None):
    """
    It set hovered the shape if his rect contains the cursor.
    """
    if not shapes:
        return
    cursor = cursor.toPoint()
    selection_rect = selection_rect or QtCore.QRect(cursor, cursor)
    selection_shapes = [s for s in shapes if s.targets()]
    selection_shapes_hovered = [
        s for s in selection_shapes
        if s.rect.contains(cursor) or
        s.rect.intersects(selection_rect)]
    targets = list_targets(selection_shapes_hovered)

    for s in selection_shapes:
        state = next((False for t in s.targets() if t not in targets), True)
        s.hovered = state


def detect_hovered_shape(shapes, cursor):
    if not shapes:
        return
    for shape in reversed(shapes):
        if not (shape.is_interactive() or shape.targets()):
            continue
        if shape.rect.contains(cursor):
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
        self.mode_manager = ModeManager()
        self.viewportmapper = ViewportMapper()
        self.selection_square = SelectionSquare()
        self.setMouseTracking(True)
        self.shapes = None
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
        self.repaint()

    def set_shapes(self, shapes):
        self.shapes = shapes
        self.mode_manager.shapes = shapes
        self.reset()
        self.repaint()

    def reset(self):
        shapes_rects = [s.rect for s in self.shapes if s.selected]
        if not shapes_rects:
            shapes_rects = [s.rect for s in self.shapes]
        if not shapes_rects:
            self.repaint()
            return
        self.viewportmapper.viewsize = self.size()
        rect = get_combined_rects(shapes_rects)
        self.viewportmapper.focus(rect)
        self.repaint()

    def resizeEvent(self, event):
        self.viewportmapper.viewsize = self.size()
        size = (event.size() - event.oldSize()) / 2
        offset = QtCore.QPointF(size.width(), size.height())
        self.viewportmapper.origin -= offset
        self.repaint()

    def mousePressEvent(self, event):
        self.setFocus(QtCore.Qt.MouseFocusReason)
        self.shapes.extend(self.drag_shapes)
        cursor = self.viewportmapper.to_units_coords(event.pos()).toPoint()
        self.clicked_shape = detect_hovered_shape(self.shapes, cursor)
        hsh = any(s.hovered for s in self.shapes)
        self.mode_manager.update(
            event,
            pressed=True,
            has_shape_hovered=hsh,
            dragging=bool(self.drag_shapes))

    def mouseReleaseEvent(self, event):
        shift = self.mode_manager.shift_pressed
        ctrl = self.mode_manager.ctrl_pressed
        selection_mode = get_selection_mode(shift=shift, ctrl=ctrl)
        cursor = self.viewportmapper.to_units_coords(event.pos()).toPoint()
        zoom = self.mode_manager.zoom_button_pressed
        interact = (
            self.clicked_shape and
            self.clicked_shape is detect_hovered_shape(self.shapes, cursor) and
            self.clicked_shape.is_interactive())

        if zoom and self.mode_manager.alt_pressed:
            self.release(event)
            return

        if self.mode_manager.mode == ModeManager.DRAGGING:
            self.drag_shapes = []
            self.dataChanged.emit()

        elif self.mode_manager.mode == ModeManager.SELECTION and not interact:
            try:
                select_targets(self.shapes, selection_mode=selection_mode)
            except NameclashError as e:
                warning('Selection Error', str(e), parent=self)
                self.release(event)
                return

        if not self.clicked_shape:
            if self.mode_manager.right_click_pressed:
                self.call_context_menu()

        elif self.clicked_shape is detect_hovered_shape(self.shapes, cursor):
            if self.mode_manager.right_click_pressed:
                self.call_context_menu()
            elif self.clicked_shape.targets():
                self.clicked_shape.select(selection_mode)
            if interact:
                self.clicked_shape.execute(
                    left=self.mode_manager.left_click_pressed,
                    right=self.mode_manager.right_click_pressed)

        self.release(event)

    def release(self, event):
        self.mode_manager.update(event, pressed=False)
        self.selection_square.release()
        self.clicked_shape = None
        self.repaint()

    def wheelEvent(self, event):
        # To center the zoom on the mouse, we save a reference mouse position
        # and compare the offset after zoom computation.
        if self.zoom_locked:
            return
        factor = .25 if event.angleDelta().y() > 0 else -.25
        self.zoom(factor, event.pos())
        self.repaint()

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
            self.shapes,
            self.viewportmapper.to_units_coords(event.pos()),
            selection_rect)

        if self.mode_manager.mode == ModeManager.DRAGGING:
            point1 = self.viewportmapper.to_units_coords(
                self.mode_manager.anchor)
            point2 = self.viewportmapper.to_units_coords(event.pos())
            align_shapes_on_line(self.drag_shapes, point1, point2)

        elif self.mode_manager.mode == ModeManager.SELECTION:
            if not self.selection_square.handeling:
                self.selection_square.clicked(event.pos())
            self.selection_square.handle(event.pos())
            return self.repaint()

        elif self.mode_manager.mode == ModeManager.ZOOMING:
            if self.zoom_locked:
                return self.repaint()
            offset = self.mode_manager.mouse_offset(event.pos())
            if offset is not None and self.mode_manager.zoom_anchor:
                sensitivity = float(cmds.optionVar(query=ZOOM_SENSITIVITY))
                factor = (offset.x() + offset.y()) / sensitivity
                self.zoom(factor, self.mode_manager.zoom_anchor)

        elif self.mode_manager.mode == ModeManager.NAVIGATION:
            if self.zoom_locked:
                return self.repaint()
            offset = self.mode_manager.mouse_offset(event.pos())
            if offset is not None:
                self.viewportmapper.origin = (
                    self.viewportmapper.origin - offset)

        self.repaint()

    def call_context_menu(self):
        if not self.editable:
            return

        self.context_menu = PickerMenu()
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

        self.context_menu.exec_(QtGui.QCursor.pos())

    def add_button(self, position, button_type=0):
        """
        Button types:
            0 = Single button from selection.
            1 = Multiple buttons from selection.
            2 = Command button.
        """
        position = self.viewportmapper.to_units_coords(position).toPoint()
        self.addButtonRequested.emit(position.x(), position.y(), button_type)

    def paintEvent(self, event):
        try:
            painter = QtGui.QPainter()
            painter.begin(self)
            painter.setRenderHints(QtGui.QPainter.Antialiasing)
            if not self.shapes:
                return
            for shape in self.shapes:
                draw_shape(painter, shape, self.viewportmapper)
            self.selection_square.draw(painter)
        except BaseException:
            pass  # avoid crash
            # TODO: log the error
        finally:
            painter.end()


class PickerMenu(QtWidgets.QMenu):
    def __init__(self, parent=None):
        super(PickerMenu, self).__init__(parent)
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


class ModeManager:
    FLY_OVER = 'fly_over'
    SELECTION = 'selection'
    NAVIGATION = 'navigation'
    DRAGGING = 'dragging'
    ZOOMING = 'zooming'

    def __init__(self):
        self.shapes = []
        self.left_click_pressed = False
        self.right_click_pressed = False
        self.middle_click_pressed = False
        self.mouse_ghost = None
        self.has_shape_hovered = False
        self.dragging = False
        self.anchor = None
        self.zoom_anchor = None

    @property
    def ctrl_pressed(self):
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        return modifiers == (modifiers | QtCore.Qt.ControlModifier)

    @property
    def shift_pressed(self):
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        return modifiers == (modifiers | QtCore.Qt.ShiftModifier)

    @property
    def alt_pressed(self):
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        return modifiers == (modifiers | QtCore.Qt.AltModifier)

    def update(
            self,
            event,
            pressed=False,
            has_shape_hovered=False,
            dragging=False):

        self.dragging = dragging
        self.has_shape_hovered = has_shape_hovered
        self.update_mouse(event, pressed)

    def update_mouse(self, event, pressed):
        if event.button() == QtCore.Qt.LeftButton:
            self.left_click_pressed = pressed
            self.anchor = event.pos() if self.dragging else None
        elif event.button() == QtCore.Qt.RightButton:
            self.right_click_pressed = pressed
        elif event.button() == QtCore.Qt.MiddleButton:
            self.middle_click_pressed = pressed
        if self.zoom_button_pressed:
            self.zoom_anchor = event.pos() if pressed else None

    @property
    def mode(self):
        if self.dragging:
            return ModeManager.DRAGGING
        elif self.zoom_button_pressed and self.alt_pressed:
            return ModeManager.ZOOMING
        elif self.middle_click_pressed:
            return ModeManager.NAVIGATION
        elif self.left_click_pressed:
            return ModeManager.SELECTION
        self.mouse_ghost = None
        return ModeManager.FLY_OVER

    def mouse_offset(self, position):
        result = position - self.mouse_ghost if self.mouse_ghost else None
        self.mouse_ghost = position
        return result or None

    @property
    def zoom_button_pressed(self):
        button = cmds.optionVar(query=ZOOM_BUTTON)
        return any((
            button == 'left' and self.left_click_pressed,
            button == 'middle' and self.middle_click_pressed,
            button == 'right' and self.right_click_pressed))
