import math
from functools import partial
from PySide2 import QtWidgets, QtCore, QtGui

from dwpicker.geometry import (
    ViewportMapper, Transform, distance, get_global_rect, grow_rect,
    path_symmetry, resize_path_with_reference, resize_rect_with_direction)
from dwpicker.qtutils import icon
from dwpicker.interactionmanager import InteractionManager
from dwpicker.interactive import SelectionSquare, Manipulator
from dwpicker.painting import (
    draw_selection_square, draw_manipulator, draw_tangents)
from dwpicker.qtutils import get_cursor
from dwpicker.selection import Selection, get_selection_mode
from dwpicker.shapepath import (
    offset_tangent, get_default_path, offset_path, auto_tangent,
    create_polygon_shape, rotate_custom_shape)


class PathEditor(QtWidgets.QWidget):
    pathEdited = QtCore.Signal()

    def __init__(self, parent=None):
        super(PathEditor, self).__init__(parent)
        self.setWindowTitle('Shape path editor')
        self.canvas = ShapeEditorCanvas()
        self.canvas.pathEdited.connect(self.pathEdited.emit)

        delete = QtWidgets.QAction(icon('delete.png'), '', self)
        delete.triggered.connect(self.canvas.delete)

        smooth_tangent = QtWidgets.QAction(icon('tangent.png'), '', self)
        smooth_tangent.triggered.connect(self.canvas.smooth_tangents)

        break_tangent = QtWidgets.QAction(icon('tangentbreak.png'), '', self)
        break_tangent.triggered.connect(self.canvas.break_tangents)

        hsymmetry = QtWidgets.QAction(icon('h_symmetry.png'), '', self)
        hsymmetry.triggered.connect(partial(self.canvas.symmetry, True))

        vsymmetry = QtWidgets.QAction(icon('v_symmetry.png'), '', self)
        vsymmetry.triggered.connect(partial(self.canvas.symmetry, False))

        self.polygon_spinbox = QtWidgets.QSpinBox(self)
        self.polygon_spinbox.setMinimum(3)  # Minimum of 3 sides for a polygon

        self.angle_spinbox = QtWidgets.QSpinBox(self)
        self.angle_spinbox.setValue(45)
        self.angle_spinbox.setMinimum(-360)
        self.angle_spinbox.setMaximum(360)
        self.angle_spinbox.setVisible(False)

        polygon_action = QtWidgets.QAction(icon('polygon.png'), 'Create Polygon', self)
        polygon_action.triggered.connect(partial(create_polygon_shape, self, self.polygon_spinbox))
        rotation_action = QtWidgets.QAction(icon('rotation.png'), 'Rotate Shape', self)
        rotation_action.triggered.connect(partial(rotate_custom_shape, self, self.angle_spinbox))

        toggle = QtWidgets.QAction(icon('dock.png'), '', self)
        toggle.triggered.connect(self.toggle_flag)

        self.toolbar = QtWidgets.QToolBar()
        self.toolbar.setIconSize(QtCore.QSize(18, 18))
        self.toolbar.addAction(delete)
        self.toolbar.addAction(smooth_tangent)
        self.toolbar.addAction(break_tangent)
        self.toolbar.addAction(hsymmetry)
        self.toolbar.addAction(vsymmetry)
        self.polygon_spinbox_action = self.toolbar.addWidget(self.polygon_spinbox)
        self.toolbar.addAction(polygon_action)
        self.angle_spinbox_action = self.toolbar.addWidget(self.angle_spinbox)
        self.toolbar.addAction(rotation_action)

        self.toolbar2 = QtWidgets.QToolBar()
        self.toolbar2.setIconSize(QtCore.QSize(18, 18))
        self.toolbar2.addAction(toggle)

        toolbars = QtWidgets.QHBoxLayout()
        toolbars.setContentsMargins(0, 0, 0, 0)
        toolbars.addWidget(self.toolbar)
        toolbars.addStretch()
        toolbars.addWidget(self.toolbar2)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addLayout(toolbars)
        layout.addWidget(self.canvas)

    def toggle_flag(self):
        point = self.mapToGlobal(self.rect().topLeft())
        state = not self.windowFlags() & QtCore.Qt.Tool
        self.setWindowFlag(QtCore.Qt.Tool, state)
        self.show()
        if state:
            self.move(point)

    def set_options(self, options):
        if options is None:
            self.canvas.set_path(None)
            return
        self.canvas.set_path(
            options['shape.path'] or get_default_path(options))

    def path(self):
        return self.canvas.path

    def path_rect(self):
        return get_global_rect(
            [QtCore.QPointF(*p['point']) for p in self.canvas.path])

class ShapeEditorCanvas(QtWidgets.QWidget):
    pathEdited = QtCore.Signal()

    def __init__(self, parent=None):
        super(ShapeEditorCanvas, self).__init__(parent)
        self.viewportmapper = ViewportMapper()
        self.viewportmapper.viewsize = self.size()
        self.selection_square = SelectionSquare()
        self.manipulator = Manipulator()
        self.transform = Transform()
        self.selection = Selection()
        self.interaction_manager = InteractionManager()
        self.setMouseTracking(True)
        self.path = []

    def sizeHint(self):
        return QtCore.QSize(300, 200)

    def mousePressEvent(self, event):
        if not self.path:
            return

        cursor = self.viewportmapper.to_units_coords(get_cursor(self))
        self.transform.direction = self.manipulator.get_direction(cursor)
        self.current_action = self.get_action()
        if self.current_action and self.current_action[0] == 'move point':
            self.selection.set([self.current_action[1]])
            self.update_manipulator_rect()
        if self.manipulator.rect is not None:
            self.transform.set_rect(
                self.manipulator.rect.toRect())
            self.transform.reference_rect = QtCore.QRect(
                self.manipulator.rect.toRect())
            self.transform.set_reference_point(cursor)

        has_shape_hovered = bool(self.current_action)
        self.interaction_manager.update(
            event, pressed=True,
            has_shape_hovered=has_shape_hovered,
            dragging=has_shape_hovered)
        self.selection_square.clicked(cursor)
        self.update()

    def get_action(self):
        if not self.path:
            return

        cursor = self.viewportmapper.to_units_coords(get_cursor(self))
        if self.manipulator.rect and self.manipulator.rect.contains(cursor):
            return 'move points', None
        direction = self.manipulator.get_direction(cursor)
        if direction:
            return 'resize points', direction
        for i, data in enumerate(self.path):
            point = QtCore.QPointF(*data['point'])
            if distance(point, cursor) < 5:
                return 'move point', i
            if data['tangent_in']:
                point = QtCore.QPointF(*data['tangent_in'])
                if distance(point, cursor) < 5:
                    return 'move in', i
            if data['tangent_out']:
                point = QtCore.QPointF(*data['tangent_out'])
                if distance(point, cursor) < 5:
                    return 'move out', i
        index = is_point_on_path_edge(self.path, cursor)
        if index is not None:
            return 'create point', index

    def mouseMoveEvent(self, event):
        if not self.path:
            return

        cursor = self.viewportmapper.to_units_coords(get_cursor(self)).toPoint()
        if self.interaction_manager.mode == InteractionManager.NAVIGATION:
            offset = self.interaction_manager.mouse_offset(event.pos())
            if offset is not None:
                origin = self.viewportmapper.origin - offset
                self.viewportmapper.origin = origin

        elif self.interaction_manager.mode == InteractionManager.SELECTION:
            self.selection_square.handle(cursor)

        elif self.interaction_manager.mode == InteractionManager.DRAGGING:
            if not self.current_action:
                return self.update()

            offset = self.interaction_manager.mouse_offset(event.pos())
            if not offset:
                return self.update()

            offset = QtCore.QPointF(
                self.viewportmapper.to_units(offset.x()),
                self.viewportmapper.to_units(offset.y()))

            if self.current_action[0] == 'move points':
                offset_path(self.path, offset, self.selection)
                self.update_manipulator_rect()

            elif self.current_action[0] == 'resize points':
                resize_rect_with_direction(
                    self.transform.rect, cursor,
                    self.transform.direction)
                path = (
                    [self.path[i] for i in self.selection] if
                    self.selection else self.path)
                resize_path_with_reference(
                    path,
                    self.transform.reference_rect,
                    self.transform.rect)
                rect = self.transform.rect
                self.transform.reference_rect.setTopLeft(rect.topLeft())
                self.transform.reference_rect.setSize(rect.size())
                self.manipulator.set_rect(QtCore.QRectF(self.transform.rect))
                self.manipulator.update_geometries()

            elif self.current_action[0] == 'move point':
                offset_path(self.path, offset, [self.current_action[1]])

            elif self.current_action and self.current_action[0] == 'move in':
                move_tangent(
                    point=self.path[self.current_action[1]],
                    tangent_in_moved=True,
                    offset=offset,
                    lock=not self.interaction_manager.ctrl_pressed)

            elif self.current_action[0] == 'move out':
                move_tangent(
                    point=self.path[self.current_action[1]],
                    tangent_in_moved=False,
                    offset=offset,
                    lock=not self.interaction_manager.ctrl_pressed)

            elif self.current_action[0] == 'create point':
                self.interaction_manager.mouse_offset(event.pos())
                point = {
                    'point': [cursor.x(), cursor.y()],
                    'tangent_in': None,
                    'tangent_out': None}
                index = self.current_action[1] + 1
                self.path.insert(index, point)
                self.autotangent(index)
                self.current_action = 'move point', index
                self.selection.set([index])
                self.update_manipulator_rect()

        self.update()

    def move_point(self, i, offset):
        self.path[i]['point'][0] += offset.x()
        self.path[i]['point'][1] += offset.y()
        point = self.path[i]['tangent_in']
        if point:
            point[0] += offset.x()
            point[1] += offset.y()
        point = self.path[i]['tangent_out']
        if point:
            point[0] += offset.x()
            point[1] += offset.y()

    def mouseReleaseEvent(self, event):
        if not self.path:
            return

        if self.current_action:
            self.pathEdited.emit()

        if self.interaction_manager.mode == InteractionManager.SELECTION:
            self.select()

        self.selection_square.release()
        self.interaction_manager.update(
            event, pressed=False, has_shape_hovered=False, dragging=False)
        self.update()

    def select(self):
        shift = self.interaction_manager.shift_pressed
        ctrl = self.interaction_manager.ctrl_pressed
        self.selection.mode = get_selection_mode(shift=shift, ctrl=ctrl)
        rect = self.selection_square.rect
        points = []
        indexes = []
        for i, p in enumerate(self.path):
            point = QtCore.QPointF(*p['point'])
            if rect.contains(point):
                indexes.append(i)
                points.append(point)
        self.selection.set(indexes)
        self.update_manipulator_rect(points)

    def update_manipulator_rect(self, points=None):
        if points is None:
            points = [
                QtCore.QPointF(*self.path[i]['point'])
                for i in self.selection]
        if len(points) < 2:
            self.manipulator.set_rect(None)
            return

        rect = get_global_rect(points)
        self.manipulator.set_rect(rect)

    def wheelEvent(self, event):
        # To center the zoom on the mouse, we save a reference mouse position
        # and compare the offset after zoom computation.
        factor = .25 if event.angleDelta().y() > 0 else -.25
        self.zoom(factor, event.pos())
        self.update()

    def resizeEvent(self, event):
        self.viewportmapper.viewsize = self.size()
        size = (event.size() - event.oldSize()) / 2
        offset = QtCore.QPointF(size.width(), size.height())
        self.viewportmapper.origin -= offset
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

    def paintEvent(self, event):
        if not self.path:
            return

        try:
            painter = QtGui.QPainter(self)
            painter.setPen(QtGui.QPen())
            color = QtGui.QColor('black')
            color.setAlpha(50)
            painter.setBrush(color)
            rect = QtCore.QRect(
                0, 0, self.rect().width() - 1, self.rect().height() - 1)
            painter.drawRect(rect)
            painter.setBrush(QtGui.QBrush())
            draw_shape_path(
                painter, self.path, self.selection, self.viewportmapper)
            draw_tangents(painter, self.path, self.viewportmapper)
            if self.selection_square.rect:
                draw_selection_square(
                    painter, self.selection_square.rect, self.viewportmapper)

            conditions = (
                self.manipulator.rect is not None and
                all(self.manipulator.handler_rects()))

            if conditions:
                draw_manipulator(
                    painter, self.manipulator,
                    get_cursor(self), self.viewportmapper)

        finally:
            painter.end()

    def delete(self):
        if len(self.path) - len(self.selection) < 3:
            return QtWidgets.QMessageBox.critical(
                self, 'Error', 'Shape must at least contains 3 control points')

        for i in sorted(self.selection, reverse=True):
            del self.path[i]
        self.selection.clear()
        self.update_manipulator_rect()
        self.pathEdited.emit()
        self.update()

    def break_tangents(self):
        for i in self.selection:
            self.path[i]['tangent_in'] = None
            self.path[i]['tangent_out'] = None
        self.pathEdited.emit()
        self.update()

    def smooth_tangents(self):
        if not self.selection:
            return

        for i in self.selection:
            self.autotangent(i)
        self.update()
        self.pathEdited.emit()

    def autotangent(self, i):
        point = self.path[i]['point']
        next_index = i + 1 if i < (len(self.path) - 1) else 0
        next_point = self.path[next_index]['point']
        previous_point = self.path[i - 1]['point']
        tan_in, tan_out = auto_tangent(point, previous_point, next_point)
        self.path[i]['tangent_in'] = tan_in
        self.path[i]['tangent_out'] = tan_out

    def set_path(self, path):
        self.path = path
        self.selection.clear()
        self.manipulator.set_rect(None)
        self.focus()

    def focus(self):
        if not self.path:
            self.update()
            return
        points = [QtCore.QPointF(*p['point']) for p in self.path]
        rect = get_global_rect(points)
        self.viewportmapper.focus(grow_rect(rect, 15))
        self.update()

    def symmetry(self, horizontal=False):
        path = (
            [self.path[i] for i in self.selection] if
            self.selection else self.path)

        if self.manipulator.rect:
            center = self.manipulator.rect.center()
        else:
            points = [QtCore.QPointF(*p['point']) for p in self.path]
            rect = get_global_rect(points)
            center = rect.center()

        path_symmetry(path, center, horizontal=horizontal)
        self.pathEdited.emit()
        self.update()


def painter_path(path, viewportmapper):
    painter_path = QtGui.QPainterPath()
    start = QtCore.QPointF(*path[0]['point'])
    painter_path.moveTo(viewportmapper.to_viewport_coords(start))
    for i in range(len(path)):
        point = path[i]
        point2 = path[i + 1 if i + 1 < len(path) else 0]
        c1 = QtCore.QPointF(*(point['tangent_out'] or point['point']))
        c2 = QtCore.QPointF(*(point2['tangent_in'] or point2['point']))
        end = QtCore.QPointF(*point2['point'])
        painter_path.cubicTo(
            viewportmapper.to_viewport_coords(c1),
            viewportmapper.to_viewport_coords(c2),
            viewportmapper.to_viewport_coords(end))
    return painter_path


def draw_shape_path(painter, path, selection, viewportmapper):
    painter.setPen(QtCore.Qt.gray)
    painter.drawPath(painter_path(path, viewportmapper))
    rect = QtCore.QRectF(0, 0, 5, 5)
    for i, point in enumerate(path):
        center = QtCore.QPointF(*point['point'])
        rect.moveCenter(viewportmapper.to_viewport_coords(center))
        painter.setBrush(QtCore.Qt.white if i in selection else QtCore.Qt.NoBrush)
        painter.drawRect(rect)


def is_point_on_path_edge(path, cursor, tolerance=3):
    stroker = QtGui.QPainterPathStroker()
    stroker.setWidth(tolerance * 2)

    for i in range(len(path)):
        point = path[i]
        painter_path = QtGui.QPainterPath()
        painter_path.moveTo(QtCore.QPointF(*point['point']))

        point2 = path[i + 1 if i + 1 < len(path) else 0]
        c1 = QtCore.QPointF(*(point['tangent_out'] or point['point']))
        c2 = QtCore.QPointF(*(point2['tangent_in'] or point2['point']))
        end = QtCore.QPointF(*point2['point'])
        painter_path.cubicTo(c1, c2, end)

        stroke = stroker.createStroke(painter_path)
        if stroke.contains(cursor):
            return i

    return None


def move_tangent(point, tangent_in_moved, offset, lock):
    center_point = point['point']
    tangent_in = point['tangent_in' if tangent_in_moved else 'tangent_out']
    tangent_out = point['tangent_out' if tangent_in_moved else 'tangent_in']
    offset = offset.x(), offset.y()
    tangent_in, tangent_out = offset_tangent(
        tangent_in, tangent_out, center_point, offset, lock)
    point['tangent_in'if tangent_in_moved else 'tangent_out'] = tangent_in
    point['tangent_out'if tangent_in_moved else 'tangent_in'] = tangent_out


if __name__ == '__main__':
    try:
        se.close()
    except:
        pass
    from dwpicker.qtutils import maya_main_window
    se = PathEditor(maya_main_window())
    se.setWindowFlags(QtCore.Qt.Window)
    se.show()
