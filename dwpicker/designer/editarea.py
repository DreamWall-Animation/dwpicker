from PySide2 import QtCore, QtGui, QtWidgets
from maya import cmds

from dwpicker.interactive import Manipulator, SelectionSquare, cursor_in_shape
from dwpicker.interactionmanager import InteractionManager
from dwpicker.optionvar import SNAP_GRID_X, SNAP_GRID_Y, SNAP_ITEMS
from dwpicker.geometry import Transform, ViewportMapper, get_combined_rects
from dwpicker.painting import draw_editor, draw_shape, draw_manipulator, draw_selection_square
from dwpicker.qtutils import get_cursor
from dwpicker.selection import Selection, get_selection_mode


def load_saved_snap():
    if not cmds.optionVar(query=SNAP_ITEMS):
        return
    return (
        cmds.optionVar(query=SNAP_GRID_X),
        cmds.optionVar(query=SNAP_GRID_Y))


class ShapeEditArea(QtWidgets.QWidget):
    selectedShapesChanged = QtCore.Signal()
    increaseUndoStackRequested = QtCore.Signal()
    centerMoved = QtCore.Signal(int, int)
    callContextMenu = QtCore.Signal(QtCore.QPoint)

    def __init__(self, options, parent=None):
        super(ShapeEditArea, self).__init__(parent)
        self.setMouseTracking(True)
        self.options = options

        self.viewportmapper = ViewportMapper()
        self.viewportmapper.viewsize = self.size()

        self.interaction_manager = InteractionManager()

        self.selection = Selection()
        self.selection_square = SelectionSquare()
        self.manipulator = Manipulator()
        self.transform = Transform(load_saved_snap())

        self.shapes = []
        self.clicked_shape = None
        self.manipulator_moved = False
        self.increase_undo_on_release = False
        self.lock_background_shape = True

        self.ctrl_pressed = False
        self.shit_pressed = False

    def wheelEvent(self, event):
        # To center the zoom on the mouse, we save a reference mouse position
        # and compare the offset after zoom computation.
        factor = .25 if event.angleDelta().y() > 0 else -.25
        self.zoom(factor, event.pos())
        self.update()

    def focus(self):
        shapes = [s for s in self.shapes if s.selected] or self.shapes
        shapes_rects = [s.rect for s in shapes]
        if not shapes_rects:
            self.update()
            return
        self.viewportmapper.viewsize = self.size()
        rect = get_combined_rects(shapes_rects)
        self.viewportmapper.focus(rect)
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

    def set_lock_background_shape(self, state):
        self.lock_background_shape = state

    def get_hovered_shape(self, cursor):
        for shape in reversed(self.list_shapes()):
            if cursor_in_shape(shape, cursor):
                return shape

    def list_shapes(self):
        if self.lock_background_shape:
            return [
                shape for shape in self.shapes
                if not shape.is_background()]
        return self.shapes

    def mousePressEvent(self, event):
        self.setFocus(QtCore.Qt.MouseFocusReason)  # This is not automatic

        cursor = self.viewportmapper.to_units_coords(get_cursor(self))
        hovered_shape = self.get_hovered_shape(cursor)
        self.transform.direction = self.manipulator.get_direction(cursor)

        if event.button() != QtCore.Qt.LeftButton:
            self.interaction_manager.update(
                event,
                pressed=True,
                has_shape_hovered=False,
                dragging=False)
            self.update()
            return

        conditions = (
            hovered_shape and
            hovered_shape not in self.selection and
            not self.transform.direction)

        if conditions:
            self.selection.set([hovered_shape])
            self.update_selection()

        elif not hovered_shape and not self.transform.direction:
            self.selection.set([])
            self.update_selection()
            self.selection_square.clicked(cursor)

        if self.manipulator.rect is not None:
            self.transform.set_rect(self.manipulator.rect)
            self.transform.reference_rect = QtCore.QRect(self.manipulator.rect)
            self.transform.set_reference_point(cursor)

        self.update()

        self.interaction_manager.update(
            event,
            pressed=True,
            has_shape_hovered=bool(hovered_shape),
            dragging=bool(hovered_shape) or self.transform.direction)

    def resizeEvent(self, event):
        self.viewportmapper.viewsize = self.size()
        size = (event.size() - event.oldSize()) / 2
        offset = QtCore.QPointF(size.width(), size.height())
        self.viewportmapper.origin -= offset
        self.update()

    def mouseMoveEvent(self, event):
        cursor = self.viewportmapper.to_units_coords(get_cursor(self)).toPoint()

        if self.interaction_manager.mode == InteractionManager.DRAGGING:
            rect = self.manipulator.rect
            if self.transform.direction:
                self.transform.resize(self.selection.shapes, cursor)
                self.manipulator.update_geometries()
            elif rect is not None:
                self.transform.move(shapes=self.selection, cursor=cursor)
                self.manipulator.update_geometries()
            for shape in self.selection:
                shape.synchronize_rect()
                shape.update_path()
                shape.synchronize_image()
            self.manipulator_moved = True
            self.increase_undo_on_release = True
            self.selectedShapesChanged.emit()

        elif self.interaction_manager.mode == InteractionManager.SELECTION:
            self.selection_square.handle(cursor)
            for shape in self.list_shapes():
                shape.hovered = self.selection_square.intersects(shape)

        elif self.interaction_manager.mode == InteractionManager.NAVIGATION:
            offset = self.interaction_manager.mouse_offset(event.pos())
            if offset is not None:
                self.viewportmapper.origin = (
                    self.viewportmapper.origin - offset)

        else:
            for shape in self.list_shapes():
                shape.hovered = cursor_in_shape(shape, cursor)

        self.update()

    def mouseReleaseEvent(self, event):

        if event.button() == QtCore.Qt.RightButton:
            self.interaction_manager.update(event, pressed=False)
            return self.callContextMenu.emit(event.pos())

        if event.button() != QtCore.Qt.LeftButton:
            self.interaction_manager.update(event, pressed=False)
            return

        if self.increase_undo_on_release:
            self.increaseUndoStackRequested.emit()
            self.increase_undo_on_release = False

        if self.interaction_manager.mode == InteractionManager.SELECTION:
            self.select_shapes()

        self.interaction_manager.update(event, pressed=False)
        self.selection_square.release()
        self.update()

    def select_shapes(self):
        shapes = [
            s for s in self.list_shapes()
            if s.rect.intersects(self.selection_square.rect)]
        if shapes:
            self.selection.set(shapes)
            self.update_selection()

    def keyPressEvent(self, event):
        self.key_event(event, True)

    def keyReleaseEvent(self, event):
        self.key_event(event, False)

    def key_event(self, event, pressed):
        if event.key() == QtCore.Qt.Key_Shift:
            self.transform.square = pressed
            self.shit_pressed = pressed

        if event.key() == QtCore.Qt.Key_Control:
            self.ctrl_pressed = pressed

        self.selection.mode = get_selection_mode(
            shift=self.shit_pressed,
            ctrl=self.ctrl_pressed)

        self.update()

    def update_selection(self):
        rect = get_combined_rects([shape.rect for shape in self.selection])
        self.manipulator.set_rect(rect)
        self.selectedShapesChanged.emit()

    def paintEvent(self, _):
        try:
            painter = QtGui.QPainter()
            painter.begin(self)
            self.paint(painter)
        except BaseException:
            import traceback
            print(traceback.format_exc())
            pass  # avoid crash
            # TODO: log the error
        finally:
            painter.end()

    def paint(self, painter):
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        draw_editor(
            painter, self.rect(),
            snap=self.transform.snap,
            viewportmapper=self.viewportmapper)
        for shape in self.shapes:
            draw_shape(painter, shape, self.viewportmapper)

        conditions = (
            self.manipulator.rect is not None and
            all(self.manipulator.handler_rects()))

        if conditions:
            draw_manipulator(
                painter, self.manipulator,
                get_cursor(self), self.viewportmapper)

        if self.selection_square.rect:
            draw_selection_square(
                painter, self.selection_square.rect, self.viewportmapper)