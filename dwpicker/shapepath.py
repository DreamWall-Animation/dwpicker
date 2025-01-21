import math
from PySide2 import QtGui, QtCore
from dwpicker.viewport import ViewportMapper, to_screenspace_coords


def get_default_path(options):
    width = options['shape.width']
    height = options['shape.height']
    return [
        {
            'point': [0, 0],
            'tangent_in': None,
            'tangent_out': None,
        },
        {
            'point': [width, 0],
            'tangent_in': None,
            'tangent_out': None,
        },
        {
            'point': [width, height],
            'tangent_in': None,
            'tangent_out': None,
        },
        {
            'point': [0, height],
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


def auto_tangent(point, previous_point, next_point):
    in_middle = (
        point[0] + previous_point[0]) / 2, (point[1] + previous_point[1]) / 2
    out_middle = (point[0] + next_point[0]) / 2, (point[1] + next_point[1]) / 2
    in_opposite = [2 * point[0] - in_middle[0], 2 * point[1] - in_middle[1]]
    out_opposite = [2 * point[0] - out_middle[0], 2 * point[1] - out_middle[1]]
    return [
        [
            (in_middle[0] + out_opposite[0]) / 2,
            (in_middle[1] + out_opposite[1]) / 2
        ],
        [
            (in_opposite[0] + out_middle[0]) / 2,
            (in_opposite[1] + out_middle[1]) / 2
        ]]


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


def get_absolute_path(reference_point, relative_path):
    absolute_path = []
    for point in relative_path:
        tin = [
                reference_point[0] + point['tangent_in'][0],
                reference_point[1] + point['tangent_in'][1]
            ] if point['tangent_in'] else None
        to = [
            reference_point[0] + point['tangent_out'][0],
            reference_point[1] + point['tangent_out'][1]
        ] if point['tangent_out'] else None

        center = [
            reference_point[0] + point['point'][0],
            reference_point[1] + point['point'][1]]
        absolute_path.append(
            {'point': center, 'tangent_in': tin, 'tangent_out': to})
    return absolute_path


def get_relative_path(reference_point, absolute_path):
    relative_path = []
    for point in absolute_path:
        tin = [
                point['tangent_in'][0] - reference_point[0],
                point['tangent_in'][1] - reference_point[1]
            ] if point['tangent_in'] else None

        to = [
            point['tangent_out'][0] - reference_point[0],
            point['tangent_out'][1] - reference_point[1]
        ] if point['tangent_out'] else None

        point = [
            point['point'][0] - reference_point[0],
            point['point'][1] - reference_point[1]]

        relative_path.append(
            {'point': point, 'tangent_in': tin, 'tangent_out': to})

    return relative_path


def get_shape_painter_path(shape, viewportmapper=None):
    if not shape.options['shape.path']:
        return

    left, top = shape.options['shape.left'], shape.options['shape.top']
    path = get_absolute_path((left, top), shape.options['shape.path'])
    return get_worldspace_qpath(path, viewportmapper)


def get_shape_space_painter_path(
        shape, force_world_space=True, viewportmapper=None):
    path = get_absolute_path(shape)
    if shape.options['shape.space'] == 'world' or force_world_space:
        return get_worldspace_qpath(path, viewportmapper)
    return get_screenspace_qpath(
        path=path,
        anchor=shape.options['shape.anchor'],
        viewport_size=viewportmapper.viewsize)


def get_screenspace_qpath(path, point, anchor, viewport_size):
    if not path:
        return QtGui.QPainterPath()

    def add(p1, p2):
        return p1[0] + p2[0], p1[1] + p2[1]

    painter_path = QtGui.QPainterPath()
    start = QtCore.QPointF(*add(path[0]['point'], point))
    painter_path.moveTo(to_screenspace_coords(start, anchor, viewport_size))
    for i in range(len(path)):
        p1 = path[i]
        p2 = path[i + 1 if i + 1 < len(path) else 0]
        c1 = QtCore.QPointF(*add(p1['tangent_out'] or p1['point'], point))
        c2 = QtCore.QPointF(*add(p2['tangent_in'] or p2['point'], point))
        end = QtCore.QPointF(*add(p2['point'], point))
        painter_path.cubicTo(
            to_screenspace_coords(c1, anchor, viewport_size),
            to_screenspace_coords(c2, anchor, viewport_size),
            to_screenspace_coords(end, anchor, viewport_size))
    return painter_path


def get_worldspace_qpath(path, viewportmapper=None):
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


def create_polygon_shape(path_editor, polygon):
    if not path_editor.polygon_spinbox_action.isVisible():
        path_editor.angle_spinbox_action.setVisible(False)
        return path_editor.polygon_spinbox_action.setVisible(True)
    polygon_edges = polygon.value()
    x_point, y_point = path_editor.canvas.path[0]['point']
    shape_path = polygon_shape_format(
        radius=45, n=polygon_edges, x_origin=x_point, y_origin=y_point)
    path_editor.canvas.path = shape_path
    path_editor.pathEdited.emit()
    path_editor.canvas.focus()


def rotate_custom_shape(path_editor, angle):
    if not path_editor.angle_spinbox_action.isVisible():
        path_editor.polygon_spinbox_action.setVisible(False)
        return path_editor.angle_spinbox_action.setVisible(True)
    angle_value = math.radians(angle.value())

    vertices = [
        (point["point"][0], point["point"][1])
        for point in path_editor.canvas.path]
    cx = sum(x for x, y in vertices) / len(vertices)
    cy = sum(y for x, y in vertices) / len(vertices)

    # Helper function to rotate a point
    def rotate_point(x, y, cx, cy, angle):
        x_rotated = (
            math.cos(angle) * (x - cx) - math.sin(angle) * (y - cy) + cx)
        y_rotated = (
            math.sin(angle) * (x - cx) + math.cos(angle) * (y - cy) + cy)
        return x_rotated, y_rotated

    rotated_shape_path = []
    for point_data in path_editor.canvas.path:
        x, y = point_data["point"]
        tangent_in = point_data["tangent_in"]
        tangent_out = point_data["tangent_out"]

        # Rotate the point
        x_rotated, y_rotated = rotate_point(x, y, cx, cy, angle_value)

        # Rotate the tangents if they exist
        if tangent_in:
            tan_in_x, tan_out_y = tangent_in
            tan_in_rotated = rotate_point(
                tan_in_x, tan_out_y, cx, cy, angle_value)
        else:
            tan_in_rotated = None

        if tangent_out:
            tan_out_x, tan_out_y = tangent_out
            tan_out_rotated = rotate_point(
                tan_out_x, tan_out_y, cx, cy, angle_value)
        else:
            tan_out_rotated = None

        # Update the shape path
        rotated_shape_path.append({
            "point": [x_rotated, y_rotated],
            "tangent_in": [
                tan_in_rotated[0], tan_in_rotated[1]]
                if tan_in_rotated else None,
            "tangent_out": [
                tan_out_rotated[0], tan_out_rotated[1]]
                if tan_out_rotated else None,})

    path_editor.canvas.path = rotated_shape_path
    path_editor.pathEdited.emit()
    path_editor.canvas.focus()


def calculate_polygon(radius, n):
    vertices = []
    angle_step = 2 * math.pi / n
    for i in range(n):
        x = radius * math.cos(i * angle_step)
        y = radius * math.sin(i * angle_step)
        vertices.append((x, y))
    # Shift to ensure first vertex is at origin (0, 0)
    x_shift, y_shift = vertices[0]
    adjusted_vertices = [(x - x_shift, y - y_shift) for x, y in vertices]
    return adjusted_vertices


def polygon_shape_format(radius, n, x_origin, y_origin):
    vertices = calculate_polygon(radius, n)
    offset_vertices = [(x + x_origin, y + y_origin) for x, y in vertices]
    shape_path = []
    for vertex in offset_vertices:
        shape_path.append({
            "point": [vertex[0], vertex[1]],
            "tangent_in": None,
            "tangent_out": None
        })
    return shape_path