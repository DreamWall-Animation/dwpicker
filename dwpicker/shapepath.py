
import math
from PySide2 import QtGui, QtCore
from dwpicker.geometry import ViewportMapper


def get_default_path(shape):
    left = shape['shape.left']
    top = shape['shape.top']
    width = shape['shape.width']
    height = shape['shape.height']
    return [
        {
            'point': [left, top],
            'tangent_in': None,
            'tangent_out': None,
        },
        {
            'point': [left + width, top],
            'tangent_in': None,
            'tangent_out': None,
        },
        {
            'point': [left + width, top + height],
            'tangent_in': None,
            'tangent_out': None,
        },
        {
            'point': [left, top + height],
            'tangent_in': None,
            'tangent_out': None,
        },
    ]


def offset_path(path, offset, selection=None):
    for i in selection or range(len(path)):
        path[i]['point'][0] += offset.x()
        path[i]['point'][1] += offset.y()
        point = path[i]['tangent_in']
        if point:
            point[0] += offset.x()
            point[1] += offset.y()
        point = path[i]['tangent_out']
        if point:
            point[0] += offset.x()
            point[1] += offset.y()


def offset_tangent(
        start_tangent_pos, end_tangent_pos, center_pos, offset, lock=True):
    start_vector = [
        start_tangent_pos[0] - center_pos[0],
        start_tangent_pos[1] - center_pos[1]]

    new_start_pos = [
        center_pos[0] + start_vector[0] + offset[0],
        center_pos[1] + start_vector[1] + offset[1]]

    if not lock:
        return new_start_pos, end_tangent_pos

    opposite_vector = [
        end_tangent_pos[0] - center_pos[0],
        end_tangent_pos[1] - center_pos[1]]

    opposite_length = math.sqrt(
        opposite_vector[0] ** 2 + opposite_vector[1] ** 2)
    opposite_angle = math.atan2(opposite_vector[1], opposite_vector[0])

    new_start_vector = [
        new_start_pos[0] - center_pos[0],
        new_start_pos[1] - center_pos[1]]

    angle_delta = math.atan2(
        new_start_vector[1],
        new_start_vector[0]) - math.atan2(start_vector[1], start_vector[0])
    new_opposite_angle = opposite_angle + angle_delta

    new_end_pos = [
        center_pos[0] + opposite_length * math.cos(new_opposite_angle),
        center_pos[1] + opposite_length * math.sin(new_opposite_angle)]

    return new_start_pos, new_end_pos


def get_path(path):
    painter_path = QtGui.QPainterPath()
    painter_path.moveTo(QtCore.QPointF(*path[0]['point']))
    for i in range(len(path)):
        point = path[i]
        point2 = path[i + 1 if i + 1 < len(path) else 0]
        c1 = QtCore.QPointF(*(point['tangent_out'] or point['point']))
        c2 = QtCore.QPointF(*(point2['tangent_in'] or point2['point']))
        end = QtCore.QPointF(*point2['point'])
        painter_path.cubicTo(c1, c2, end)
    return painter_path


def get_painter_path(path, viewportmapper=None):
    if not path:
        return QtGui.QPainterPath()
    viewportmapper = viewportmapper or ViewportMapper()
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
