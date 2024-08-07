from PySide2 import QtCore, QtGui, QtWidgets

from dwpicker.interactive import Manipulator, SelectionSquare
from dwpicker.geometry import Transform, get_combined_rects
from dwpicker.painting import draw_editor, draw_shape, ViewportMapper
from dwpicker import picker
from dwpicker.qtutils import get_cursor
from dwpicker.selection import Selection, get_selection_mode, NameclashError, select_targets


class ShapeEditArea(QtWidgets.QWidget):
    selectedShapesChanged = QtCore.Signal()
    increaseUndoStackRequested = QtCore.Signal()
    centerMoved = QtCore.Signal(int, int)
    callContextMenu = QtCore.Signal(QtCore.QPoint)

    def __init__(self, options, parent=None):
        super(ShapeEditArea, self).__init__(parent)
        self.setFixedSize(750, 550)
        self.setMouseTracking(True)
        self.options = options

        self.selection = Selection()
        self.selection_square = SelectionSquare()
        self.selection_square_4shapes = SelectionSquare()
        self.manipulator = Manipulator()
        self.transform = Transform()

        self.shapes = []
        self.clicked_shape = None
        self.left_clicked = False
        self.middle_clicked = False
        self.clicked = False
        self.selecting = False
        self.handeling = False
        self.manipulator_moved = False
        self.increase_undo_on_release = False
        self.lock_background_shape = True

        self.mode_manager = picker.ModeManager()
        self.viewportmapper = ViewportMapper()
        self.context_menu = None
        self.drag_shapes = []
        self.zoom_locked = False

        self.ctrl_pressed = False
        self.shit_pressed = False

    def set_lock_background_shape(self, state):
        self.lock_background_shape = state

    def get_hovered_shape(self, cursor):
        scaled_cursor_point = self.viewportmapper.to_units_coords(cursor)
        count = 0
        for shape in reversed(self.list_shapes()):
            count+=1
            if shape.rect.contains(scaled_cursor_point):
                return shape

    def list_shapes(self):
        if self.lock_background_shape:
            return [
                shape for shape in self.shapes
                if not shape.is_background()]
        return self.shapes

    def mousePressEvent(self, event):
        self.setFocus(QtCore.Qt.MouseFocusReason)  # This is not automatic
        if event.button() == QtCore.Qt.LeftButton:
            self.clicked=True
            self.left_clicked = True
        elif event.button() == QtCore.Qt.MiddleButton:
            self.clicked=True
            self.middle_clicked=True
        else:
            return

        # widget.mapFromGlobal(QtGui.QCursor.pos())
        # get cursor pos for widget: ShapeEditArea.maptoGlobal()
        # in viewport (visible to screen) coordinates of the widget.
        cursor = get_cursor(self)
        event_pos = event.pos()
        scaled_cursor_point = self.viewportmapper.to_units_coords(event.pos()).toPoint()

        self.clicked = True
        scaled_cursor = self.viewportmapper.to_units_coords(event.pos()).toPoint()
        # QtCore.QPoint

        scaled_cursor_pos = self.viewportmapper.to_units_coords(event.pos())
        #QtCore.QPointF

        hovered_shape = self.get_hovered_shape(cursor)
        self.transform.direction = self.manipulator.get_direction(scaled_cursor_point)

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
            self.selection_square_4shapes.clicked(scaled_cursor_pos)

        if self.manipulator.rect is not None:

            self.transform.set_rect(self.manipulator.rect)

            #self.transform.set_rect(self.manipulator.rect)
            self.transform.reference_rect = QtCore.QRect(self.manipulator.rect)
            #self.transform.reference_rect = QtCore.QRect(self.manipulator.rect)
            self.transform.set_reference_point(cursor)
            #self.transform.set_reference_point(cursor)

        self.handeling = bool(hovered_shape) or self.transform.direction
        self.selecting = not self.handeling and self.clicked

        self.mode_manager.update(
            event,
            pressed=True,
            has_shape_hovered=hovered_shape,
            dragging=bool(self.drag_shapes))
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
        cursor = get_cursor(self)

        t_cursor = get_cursor(self)
        scaled_cursor_point = self.viewportmapper.to_units_coords(event.pos()).toPoint()
        event_pos = event.pos()

        if self.handeling and self.left_clicked:

            # get manipulator rect if one was created (via mouse left drag)
            rect = self.manipulator.rect

            if self.transform.direction:
                self.transform.resize((s.rect for s in self.selection), scaled_cursor_point)
                self.manipulator.update_geometries(viewportmapper=self.viewportmapper)
            elif rect is not None:
                self.transform.move((s.rect for s in self.selection), cursor)
                self.manipulator.update_geometries(viewportmapper=self.viewportmapper)

            for shape in self.selection:
                shape.synchronize_rect()
                shape.synchronize_image()

            self.manipulator_moved = True
            self.increase_undo_on_release = True
            self.selectedShapesChanged.emit()

        elif self.selecting and self.left_clicked:
            self.selection_square_4shapes.handle(scaled_cursor_point)
            self.selection_square.handle(cursor)

            for shape in self.list_shapes():
                shape.hovered = self.selection_square_4shapes.intersects(shape.rect)

        elif self.middle_clicked:
            if self.zoom_locked:
                return self.repaint()

            offset = self.mode_manager.mouse_offset(event.pos())
            if offset is not None:
                self.viewportmapper.origin = (
                    self.viewportmapper.origin - offset)
        else:
            count=0

            for shape in self.list_shapes():
                shape.hovered = shape.rect.contains(scaled_cursor_point )
                if shape.hovered:
                    count +=1

        self.repaint()

    def mouseReleaseEvent(self, event):
        context_menu_condition = (
            event.button() == QtCore.Qt.RightButton and
            not self.left_clicked and
            not self.handeling and
            not self.selecting)
        if context_menu_condition:
            return self.callContextMenu.emit(event.pos())

        shift = self.mode_manager.shift_pressed
        ctrl = self.mode_manager.ctrl_pressed
        selection_mode = get_selection_mode(shift=shift, ctrl=ctrl)
        zoom = self.mode_manager.zoom_button_pressed

        # don't do anything if right button pressed
        if event.button() not in [QtCore.Qt.LeftButton, QtCore.Qt.MiddleButton]:
            return

        if self.increase_undo_on_release:
            self.increaseUndoStackRequested.emit()
            self.increase_undo_on_release = False

        if self.selecting:
            self.select_shapes()

        self.selection_square.release()
        self.selection_square_4shapes.release()
        self.left_clicked = False
        self.clicked = False
        self.middle_clicked = False
        self.handeling = False
        self.selecting = False
        self.repaint()

    def select_shapes(self):
        shapes = [
            s for s in self.list_shapes()
            if s.rect.intersects(self.selection_square_4shapes.rect)]
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

        self.repaint()

    def update_selection(self):
        rect = get_combined_rects([shape.rect for shape in self.selection])
        self.manipulator.set_rect(rect,viewportmapper=self.viewportmapper)
        self.selectedShapesChanged.emit()

    def paintEvent(self, _):
        try:
            painter = QtGui.QPainter()
            painter.begin(self)

            self.paint(painter,viewportmapper=self.viewportmapper)
        except BaseException:
            pass  # avoid crash
            # TODO: log the error
        finally:
            painter.end()

    def paint(self, painter,viewportmapper=None):
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        draw_editor(painter, self.rect(), snap=self.transform.snap,
                    viewportmapper=viewportmapper)
        for shape in self.shapes:
            draw_shape(painter, shape,viewportmapper=viewportmapper)

        cursor = get_cursor(self)
        self.manipulator.draw(painter, get_cursor(self),viewportmapper)
        self.selection_square.draw(painter, get_cursor(self),viewportmapper)
