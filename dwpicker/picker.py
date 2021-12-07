from functools import partial

import maya.OpenMaya as om
from PySide2 import QtWidgets, QtGui, QtCore

from dwpicker.interactive import SelectionSquare
from dwpicker.geometry import split_line
from dwpicker.painting import PaintContext
from dwpicker.qtutils import get_cursor
from dwpicker.selection import (
    select_targets, select_shapes_from_selection, get_selection_mode)


def align_shapes_on_line(shapes, point1, point2):
    centers = split_line(point1, point2, len(shapes))
    for center, shape in zip(centers, shapes):
        shape.rect.moveCenter(center)
        shape.synchronize_rect()


def set_shapes_hovered(shapes, cursor, selection_rect=None):
    """
    this function all the given shapes.
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
    targets = {t for s in selection_shapes_hovered for t in s.targets()}

    for shape in selection_shapes:
        for target in shape.targets():
            if target not in targets:
                shape.hovered = False
                break
        else:
            shape.hovered = True

    for shape in shapes:
        if not shape.is_interactive():
            continue
        shape.hovered = shape.rect.contains(cursor)


def detect_hovered_shape(shapes, cursor):
    if not shapes:
        return
    for shape in shapes:
        if not (shape.is_interactive() or shape.targets()):
            continue
        if shape.rect.contains(cursor):
            return shape


class PickerView(QtWidgets.QWidget):
    dataChanged = QtCore.Signal()
    addButtonRequested = QtCore.Signal(int, int, int)
    deleteButtonRequested = QtCore.Signal()

    def __init__(self, parent=None):
        super(PickerView, self).__init__(parent)
        self.callbacks = []
        self.mode_manager = ModeManager()
        self.paintcontext = PaintContext()
        self.selection_square = SelectionSquare()
        self.setMouseTracking(True)
        self.shapes = None
        self.clicked_shape = None
        self.center = [0, 0]
        self.context_menu = None
        self.drag_shapes = []

    def register_callbacks(self):
        function = self.sync_with_maya_selection
        cb = om.MEventMessage.addEventCallback('SelectionChanged', function)
        self.callbacks.append(cb)

    def unregister_callbacks(self):
        for callback in self.callbacks:
            om.MMessage.removeCallback(callback)

    def sync_with_maya_selection(self, *_):
        select_shapes_from_selection(self.shapes)
        self.repaint()

    def set_shapes(self, shapes):
        self.shapes = shapes
        self.mode_manager.shapes = shapes
        self.reset()
        self.repaint()

    def reset(self):
        self.paintcontext.reset()
        rect = self.rect()
        x = rect.center().x() + self.center[0]
        y = rect.center().y() + self.center[1]
        self.paintcontext.center = [x , y]
        self.repaint()

    def resizeEvent(self, event):
        size = (event.size() - event.oldSize()) / 2
        self.paintcontext.center[0] += size.width()
        self.paintcontext.center[1] += size.height()
        self.repaint()

    def keyPressEvent(self, event):
        self.mode_manager.update(event, pressed=True)

    def keyReleaseEvent(self, event):
        self.mode_manager.update(event, pressed=False)

    def mousePressEvent(self, event):
        self.shapes.extend(self.drag_shapes)
        cursor = self.paintcontext.absolute_point(event.pos()).toPoint()
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
        cursor = self.paintcontext.absolute_point(event.pos()).toPoint()

        if self.mode_manager.mode == ModeManager.DRAGGING:
            self.drag_shapes = []
            self.dataChanged.emit()

        elif self.mode_manager.mode == ModeManager.SELECTION:
            select_targets(self.shapes, selection_mode=selection_mode)

        elif not self.clicked_shape:
            if self.mode_manager.right_click_pressed:
                self.call_context_menu()

        elif self.clicked_shape is detect_hovered_shape(self.shapes, cursor):
            if self.clicked_shape.is_interactive():
                self.clicked_shape.execute(
                    left=self.mode_manager.left_click_pressed,
                    right=self.mode_manager.right_click_pressed)
            else:
                self.clicked_shape.select(selection_mode)

        self.mode_manager.update(event, pressed=False)
        self.selection_square.release()
        self.clicked_shape = None
        self.repaint()

    def wheelEvent(self, event):
        # To center the zoom on the mouse, we save a reference mouse position
        # and compare the offset after zoom computation.
        abspoint = self.paintcontext.absolute_point(event.pos())
        if event.angleDelta().y() > 0:
            self.paintcontext.zoomin()
        else:
            self.paintcontext.zoomout()
        relcursor = self.paintcontext.relative_point(abspoint)
        vector = relcursor - event.pos()
        center = self.paintcontext.center
        result = [center[0] - vector.x(), center[1] - vector.y()]
        self.paintcontext.center = result
        self.repaint()

    def mouseMoveEvent(self, event):
        selection_rect = self.selection_square.rect
        if selection_rect:
            selection_rect = self.paintcontext.absolute_rect(selection_rect)
            selection_rect = selection_rect.toRect()

        set_shapes_hovered(
            self.shapes,
            self.paintcontext.absolute_point(event.pos()),
            selection_rect )

        if self.mode_manager.mode == ModeManager.DRAGGING:
            point1 = self.paintcontext.absolute_point(self.mode_manager.anchor)
            point2 = self.paintcontext.absolute_point(event.pos())
            align_shapes_on_line(self.drag_shapes, point1, point2)

        elif self.mode_manager.mode == ModeManager.SELECTION:
            if not self.selection_square.handeling:
                self.selection_square.clicked(event.pos())
            self.selection_square.handle(event.pos())
            return self.repaint()

        elif self.mode_manager.mode == ModeManager.NAVIGATION:
            offset = self.mode_manager.mouse_offset(event.pos())
            if offset is not None:
                x = self.paintcontext.center[0] + offset.x()
                y = self.paintcontext.center[1] + offset.y()
                self.paintcontext.center = [x, y]

        self.repaint()

    def offset(self, point):
        return self.rect().center() + point.toPoint()

    def call_context_menu(self):
        self.context_menu = PickerMenu()
        position = get_cursor(self)

        method = partial(self.add_button, position, button_type=0)
        self.context_menu.add_single.triggered.connect(method)

        method = partial(self.add_button, position, button_type=1)
        self.context_menu.add_multiple.triggered.connect(method)

        method = partial(self.add_button, position, button_type=2)
        self.context_menu.add_command.triggered.connect(method)

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
        position = self.paintcontext.absolute_point(position).toPoint()
        self.addButtonRequested.emit(position.x(), position.y(), button_type)

    def paintEvent(self, event):
        painter = QtGui.QPainter()
        painter.begin(self)
        if not self.shapes:
            return
        for shape in self.shapes:
            shape.draw(painter, self.paintcontext)
        self.selection_square.draw(painter)
        painter.end()


class PickerMenu(QtWidgets.QMenu):
    def __init__(self, parent=None):
        super(PickerMenu, self).__init__(parent)
        self.add_single = QtWidgets.QAction('Add single button', self)
        self.add_multiple = QtWidgets.QAction('Add multiple buttons', self)
        self.add_command = QtWidgets.QAction('Add command', self)
        text = 'Delete selected button(s)'
        self.delete_selected = QtWidgets.QAction(text, self)

        self.addAction(self.add_single)
        self.addAction(self.add_multiple)
        self.addSeparator()
        self.addAction(self.add_command)
        self.addSeparator()
        self.addAction(self.delete_selected)


class ModeManager:
    FLY_OVER = 'fly_over'
    SELECTION = 'selection'
    NAVIGATION = 'navigation'
    DRAGGING = 'dragging'

    def __init__(self):
        self.shapes = []
        self.left_click_pressed = False
        self.right_click_pressed = False
        self.middle_click_pressed = False
        self.mouse_ghost = None
        self.ctrl_pressed = False
        self.shift_pressed = False
        self.alt_pressed = False
        self.has_shape_hovered = False
        self.dragging = False
        self.anchor = None

    def update(
            self,
            event,
            pressed=False,
            has_shape_hovered=False,
            dragging=False):

        if isinstance(event, QtGui.QMouseEvent):
            self.dragging = dragging
            self.has_shape_hovered = has_shape_hovered
            self.update_mouse(event, pressed)
        elif isinstance(event, QtGui.QKeyEvent):
            self.update_keys(event, pressed)

    def update_mouse(self, event, pressed):
        if event.button() == QtCore.Qt.LeftButton:
            self.left_click_pressed = pressed
            self.anchor = event.pos() if self.dragging else None
        elif event.button() == QtCore.Qt.RightButton:
            self.right_click_pressed = pressed
        elif event.button() == QtCore.Qt.MiddleButton:
            self.middle_click_pressed = pressed

    def update_keys(self, event, pressed):
        if event.key() == QtCore.Qt.Key_Shift:
            self.shift_pressed = pressed
        if event.key() == QtCore.Qt.Key_Control:
            self.ctrl_pressed = pressed

    @property
    def mode(self):
        if self.dragging:
            return ModeManager.DRAGGING
        elif self.middle_click_pressed:
            return ModeManager.NAVIGATION
        elif self.left_click_pressed and not self.has_shape_hovered:
            return ModeManager.SELECTION
        self.mouse_ghost = None
        return ModeManager.FLY_OVER

    def mouse_offset(self, position):
        result = position - self.mouse_ghost if self.mouse_ghost else None
        self.mouse_ghost = position
        return result or None
