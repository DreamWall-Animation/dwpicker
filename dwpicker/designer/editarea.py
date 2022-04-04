from PySide2 import QtCore, QtGui, QtWidgets

from dwpicker.interactive import Manipulator, SelectionSquare
from dwpicker.geometry import Transform, get_combined_rects
from dwpicker.painting import draw_editor, draw_shape
from dwpicker.qtutils import get_cursor
from dwpicker.selection import Selection, get_selection_mode


class ShapeEditArea(QtWidgets.QWidget):
    selectedShapesChanged = QtCore.Signal()
    increaseUndoStackRequested = QtCore.Signal()
    centerMoved = QtCore.Signal(int, int)

    def __init__(self, options, parent=None):
        super(ShapeEditArea, self).__init__(parent)
        self.setFixedSize(750, 550)
        self.setMouseTracking(True)
        self.options = options

        self.selection = Selection()
        self.selection_square = SelectionSquare()
        self.manipulator = Manipulator()
        self.transform = Transform()

        self.shapes = []
        self.clicked_shape = None
        self.clicked = False
        self.selecting = False
        self.handeling = False
        self.manipulator_moved = False
        self.increase_undo_on_release = False
        self.lock_background_shape = True

        self.ctrl_pressed = False
        self.shit_pressed = False

    def set_lock_background_shape(self, state):
        self.lock_background_shape = state

    def get_hovered_shape(self, cursor):
        for shape in reversed(self.list_shapes()):
            if shape.rect.contains(cursor):
                return shape

    def list_shapes(self):
        if self.lock_background_shape:
            return [
                shape for shape in self.shapes
                if not shape.is_background()]
        return self.shapes

    def mousePressEvent(self, _):
        self.setFocus(QtCore.Qt.MouseFocusReason)  # This is not automatic

        cursor = get_cursor(self)
        self.clicked = True
        hovered_shape = self.get_hovered_shape(cursor)
        self.transform.direction = self.manipulator.get_direction(cursor)

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

        self.handeling = bool(hovered_shape) or self.transform.direction
        self.selecting = not self.handeling and self.clicked
        self.repaint()

    def mouseMoveEvent(self, _):
        cursor = get_cursor(self)
        if self.handeling:
            rect = self.manipulator.rect
            if self.transform.direction:
                self.transform.resize((s.rect for s in self.selection), cursor)
                self.manipulator.update_geometries()
            elif rect is not None:
                self.transform.move((s.rect for s in self.selection), cursor)
                self.manipulator.update_geometries()
            for shape in self.selection:
                shape.synchronize_rect()
                shape.synchronize_image()

            self.manipulator_moved = True
            self.increase_undo_on_release = True
            self.selectedShapesChanged.emit()

        elif self.selecting:
            self.selection_square.handle(cursor)
            for shape in self.list_shapes():
                shape.hovered = self.selection_square.intersects(shape.rect)

        else:
            for shape in self.list_shapes():
                shape.hovered = shape.rect.contains(cursor)

        self.repaint()

    def mouseReleaseEvent(self, _):
        if self.increase_undo_on_release:
            self.increaseUndoStackRequested.emit()
            self.increase_undo_on_release = False

        if self.selecting:
            self.select_shapes()

        self.selection_square.release()
        self.clicked = False
        self.handeling = False
        self.selecting = False
        self.repaint()

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

        self.repaint()

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
            pass  # avoid crash
            # TODO: log the error
        finally:
            painter.end()

    def paint(self, painter):
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        draw_editor(painter, self.rect(), snap=self.transform.snap)
        for shape in self.shapes:
            draw_shape(painter, shape)
        self.manipulator.draw(painter, get_cursor(self))
        self.selection_square.draw(painter)
