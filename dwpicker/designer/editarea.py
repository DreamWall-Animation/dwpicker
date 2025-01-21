from functools import partial
from PySide2 import QtCore, QtGui, QtWidgets
from maya import cmds

from dwpicker.interactive import Manipulator, SelectionSquare
from dwpicker.interactionmanager import InteractionManager
from dwpicker.optionvar import (
    ISOLATE_CURRENT_PANEL_SHAPES, SNAP_GRID_X, SNAP_GRID_Y, SNAP_ITEMS)
from dwpicker.geometry import get_shapes_bounding_rects
from dwpicker.painting import (
    draw_editor, draw_shape, draw_manipulator, draw_selection_square,
    draw_current_panel)
from dwpicker.qtutils import get_cursor
from dwpicker.selection import Selection, get_selection_mode
from dwpicker.shape import cursor_in_shape
from dwpicker.transform import Transform
from dwpicker.viewport import ViewportMapper


def load_saved_snap():
    if not cmds.optionVar(query=SNAP_ITEMS):
        return
    return (
        cmds.optionVar(query=SNAP_GRID_X),
        cmds.optionVar(query=SNAP_GRID_Y))


class ShapeEditArea(QtWidgets.QWidget):
    selectedShapesChanged = QtCore.Signal()
    callContextMenu = QtCore.Signal(QtCore.QPoint)

    def __init__(self, document, parent=None):
        super(ShapeEditArea, self).__init__(parent)
        self.setMouseTracking(True)
        self.current_panel = -1
        self.isolate = cmds.optionVar(query= ISOLATE_CURRENT_PANEL_SHAPES)
        self.document = document
        method = partial(self.update_selection, False)
        self.document.data_changed.connect(method)

        self.viewportmapper = ViewportMapper()
        self.viewportmapper.viewsize = self.size()

        self.interaction_manager = InteractionManager()

        self.selection = Selection(self.document)
        self.selection_square = SelectionSquare()
        self.manipulator = Manipulator(self.viewportmapper)
        self.transform = Transform(load_saved_snap())

        self.clicked_shape = None
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

    def set_current_panel(self, panel):
        self.current_panel = panel
        self.update_selection()
        self.update()

    def select_panel_shapes(self, panel):
        panel_shapes = [
            s for s in self.document.shapes if
            s.options['panel'] == panel]
        if panel_shapes:
            self.selection.set(panel_shapes)
            self.update_selection()

    def focus(self):
        shapes = self.selection.shapes or self.visible_shapes()
        if not shapes:
            self.update()
            return
        self.viewportmapper.viewsize = self.size()
        rect = get_shapes_bounding_rects(shapes)
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
                shape for shape in self.visible_shapes()
                if not shape.is_background()]
        return self.visible_shapes()

    def mousePressEvent(self, event):
        self.setFocus(QtCore.Qt.MouseFocusReason)  # This is not automatic

        cursor = self.viewportmapper.to_units_coords(get_cursor(self))
        hovered_shape = self.get_hovered_shape(cursor)
        self.transform.direction = self.manipulator.get_direction(event.pos())

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
            elif rect is not None:
                self.transform.move(shapes=self.selection, cursor=cursor)
            for shape in self.selection:
                shape.synchronize_rect()
                shape.update_path()
                shape.synchronize_image()
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
            self.document.record_undo()
            self.document.shapes_changed.emit()
            self.increase_undo_on_release = False

        if self.interaction_manager.mode == InteractionManager.SELECTION:
            self.select_shapes()

        elif self.interaction_manager.mode == InteractionManager.DRAGGING:
            self.update_selection(False)

        self.interaction_manager.update(event, pressed=False)
        self.selection_square.release()
        self.update()

    def visible_shapes(self):
        if not self.isolate or self.current_panel < 0:
            return self.document.shapes

        return [
            s for s in self.document.shapes if
            s.options['panel'] == self.current_panel]

    def select_shapes(self):
        shapes = [
            s for s in self.list_shapes()
            if self.selection_square.intersects(s)]
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

    def update_selection(self, changed=True):
        shapes = [s for s in self.selection if s in self.visible_shapes()]
        if shapes:
            rect = get_shapes_bounding_rects(shapes)
        else:
            rect = None
        self.manipulator.set_rect(rect)
        if changed:
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
        current_panel_shapes = []
        for shape in self.document.shapes:
            if shape.options['panel'] == self.current_panel:
                current_panel_shapes.append(shape)

        if current_panel_shapes:
            rect = get_shapes_bounding_rects(current_panel_shapes)
            draw_current_panel(painter, rect, self.viewportmapper)

        for shape in self.visible_shapes():
            draw_shape(
                painter, shape,
                draw_selected_state=False,
                viewportmapper=self.viewportmapper)

        conditions = (
            self.manipulator.rect is not None and
            all(self.manipulator.viewport_handlers()))

        if conditions:
            draw_manipulator(
                painter, self.manipulator,
                get_cursor(self), self.viewportmapper)

        if self.selection_square.rect:
            draw_selection_square(
                painter, self.selection_square.rect, self.viewportmapper)

    def delete_selection(self):
        self.document.remove_shapes(self.selection.shapes)
        self.selection.clear()
        self.document.shapes_changed.emit()
        self.manipulator.set_rect(None)
        self.document.record_undo()
