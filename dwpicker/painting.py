from PySide2 import QtCore, QtGui
from maya import cmds

from dwpicker.optionvar import ZOOM_SENSITIVITY
from dwpicker.qtutils import VALIGNS, HALIGNS
from dwpicker.geometry import grow_rect, get_connection_path
from dwpicker.shape import to_shape_space_rect, to_shape_space
from dwpicker.viewport import ViewportMapper


SELECTION_COLOR = '#3388FF'
PANEL_COLOR = '#00FFFF'
FOCUS_COLOR = '#FFFFFF'
MANIPULATOR_BORDER = 5
CONNECTION_COLOR = '#666666'


def factor_sensitivity(factor):
    sensitivity = cmds.optionVar(query=ZOOM_SENSITIVITY) / 50.0
    return factor * sensitivity


def draw_world_coordinates(painter, rect, color, viewportmapper):
    center = viewportmapper.to_viewport_coords(QtCore.QPoint(0, 0))
    top_center = QtCore.QPointF(center.x(), rect.top())
    bottom_center = QtCore.QPointF(center.x(), rect.bottom())
    left_center = QtCore.QPointF(rect.left(), center.y())
    right_center = QtCore.QPointF(rect.right(), center.y())

    color.setAlpha(100)
    pen = QtGui.QPen(color)
    pen.setWidthF(2)
    painter.setPen(pen)
    painter.drawLine(top_center, bottom_center)
    painter.drawLine(left_center, right_center)


def draw_parenting_shapes(
        painter, child, potential_parent, cursor, viewportmapper):
    draw_shape_as_child_background(
        painter, child, 'yellow',
        alpha=150, padding=3, pen_width=5,
        viewportmapper=viewportmapper)
    if potential_parent:
        draw_shape_as_child_background(
            painter, potential_parent, 'white', alpha=255, padding=3,
            pen_width=5,
            viewportmapper=viewportmapper)
        start_point = potential_parent.bounding_rect().center()
        end_point = child.bounding_rect().center()
        path = get_connection_path(start_point, end_point, viewportmapper)
        draw_connections(painter, path, 'white')
        return
    end_point = child.bounding_rect().center()
    start_point = viewportmapper.to_units_coords(cursor)
    path = get_connection_path(
        start_point, end_point, viewportmapper=viewportmapper)
    pen = QtGui.QPen('yellow')
    pen.setWidthF(2)
    pen.setJoinStyle(QtCore.Qt.MiterJoin)
    painter.setPen(pen)
    painter.setBrush(QtGui.QColor(CONNECTION_COLOR))
    painter.drawPath(path)


def draw_connections(painter, path, color=None):
    pen = QtGui.QPen(color or CONNECTION_COLOR)
    pen.setWidthF(1.5)
    pen.setJoinStyle(QtCore.Qt.MiterJoin)
    painter.setPen(pen)
    painter.setBrush(QtGui.QColor(CONNECTION_COLOR))
    painter.drawPath(path)


def draw_editor_canvas(painter, rect, snap=None, viewportmapper=None):
    viewportmapper = viewportmapper or ViewportMapper()
    color = QtGui.QColor('#333333')
    pen = QtGui.QPen(color)
    pen.setWidthF(2)
    brush = QtGui.QBrush(QtGui.QColor(255, 255, 255, 25))
    painter.setPen(pen)
    painter.setBrush(brush)
    painter.drawRect(rect)

    draw_world_coordinates(painter, rect, color, viewportmapper)
    center = viewportmapper.to_viewport_coords(QtCore.QPoint(0, 0))

    text = QtGui.QStaticText('bottom_right')
    x = center.x() - text.size().width() - 4
    y = center.y() - text.size().height() - 4
    point = QtCore.QPointF(x, y)
    painter.drawStaticText(point, text)

    text = QtGui.QStaticText('bottom_left')
    y = center.y() - text.size().height() - 4
    point = QtCore.QPointF(center.x() + 4, y)
    painter.drawStaticText(point, text)

    text = QtGui.QStaticText('top_right')
    x = center.x() - text.size().width() - 4
    point = QtCore.QPointF(x, center.y() + 4)
    painter.drawStaticText(point, text)

    text = QtGui.QStaticText('top_left')
    point = QtCore.QPointF(center.x() + 4, center.y() + 4)
    painter.drawStaticText(point, text)

    if snap is None:
        return

    if viewportmapper.zoom < 0.5:
        snap = snap[0] * 2, snap[1] * 2

    pen = QtGui.QPen(QtGui.QColor('red'))
    pen.setWidth(
        1 if viewportmapper.zoom < 1 else 2 if
        viewportmapper.zoom < 3 else 3)
    painter.setPen(pen)
    rect = viewportmapper.to_units_rect(rect)
    x_start = ((rect.left() // snap[0]) * snap[0])
    if x_start < rect.left():
        x_start += snap[0]

    y_start = ((rect.top() // snap[1]) * snap[1])
    if y_start < rect.top():
        y_start += snap[1]

    x = x_start
    while x <= rect.right():
        if x >= rect.left():
            y = y_start
            while y <= rect.bottom():
                if y >= rect.top():
                    point = QtCore.QPoint(*(x, y))
                    painter.drawPoint(viewportmapper.to_viewport_coords(point))
                y += snap[1]
        x += snap[0]


def draw_shape_as_child_background(
        painter, shape, color=None, padding=5, pen_width=1.5, alpha=30,
        viewportmapper=None):
    rect = viewportmapper.to_viewport_rect(shape.bounding_rect())
    rect = grow_rect(rect, padding)
    color = QtGui.QColor(color or 'yellow')
    color.setAlpha(alpha)
    pen = QtGui.QPen(color)
    pen.setWidthF(pen_width)
    pen.setStyle(QtCore.Qt.DashLine)
    painter.setPen(pen)
    brush = QtGui.QBrush(color)
    brush.setStyle(QtCore.Qt.BDiagPattern)
    painter.setBrush(brush)
    painter.drawRect(rect)


def draw_shape(
        painter, shape, force_world_space=True,
        draw_selected_state=True, viewportmapper=None):

    viewportmapper = viewportmapper or ViewportMapper()
    options = shape.options
    content_rect = shape.content_rect()
    if shape.clicked or (shape.selected and draw_selected_state):
        bordercolor = QtGui.QColor(options['bordercolor.clicked'])
        backgroundcolor = QtGui.QColor(options['bgcolor.clicked'])
        bordersize = options['borderwidth.clicked']
    elif shape.hovered:
        bordercolor = QtGui.QColor(options['bordercolor.hovered'])
        backgroundcolor = QtGui.QColor(options['bgcolor.hovered'])
        bordersize = options['borderwidth.hovered']
    else:
        bordercolor = QtGui.QColor(options['bordercolor.normal'])
        backgroundcolor = QtGui.QColor(options['bgcolor.normal'])
        bordersize = options['borderwidth.normal']

    textcolor = QtGui.QColor(options['text.color'])
    alpha = options['bordercolor.transparency'] if options['border'] else 255
    bordercolor.setAlpha(255 - alpha)
    backgroundcolor.setAlpha(255 - options['bgcolor.transparency'])

    pen = QtGui.QPen(bordercolor)
    pen.setStyle(QtCore.Qt.SolidLine)
    w = to_shape_space(bordersize, shape, force_world_space, viewportmapper)
    pen.setWidthF(w)
    painter.setPen(pen)
    painter.setBrush(QtGui.QBrush(backgroundcolor))
    rect = to_shape_space_rect(
        shape.rect, shape, force_world_space, viewportmapper)
    r = draw_shape_shape(
        painter, rect, shape, force_world_space, viewportmapper)

    painter.setPen(QtGui.QPen(textcolor))
    painter.setBrush(QtGui.QBrush(textcolor))
    option = QtGui.QTextOption()
    flags = VALIGNS[options['text.valign']] | HALIGNS[options['text.halign']]
    option.setAlignment(flags)
    font = QtGui.QFont()
    font.setBold(options['text.bold'])
    font.setItalic(options['text.italic'])
    size = to_shape_space(
        options['text.size'], shape, force_world_space, viewportmapper)
    font.setPixelSize(round(size))
    painter.setFont(font)
    text = options['text.content']

    content_rect = to_shape_space_rect(
        content_rect, shape, force_world_space, viewportmapper)
    painter.drawText(content_rect, flags, text)
    return r


def draw_shape_shape(painter, rect, shape, force_world_space, viewportmapper):
    options = shape.options
    content_rect = shape.content_rect()
    qpath = QtGui.QPainterPath()

    if options['shape'] == 'square':
        painter.drawRect(rect)
        qpath.addRect(rect)

    elif options['shape'] == 'round':
        painter.drawEllipse(rect)
        qpath.addEllipse(rect)

    elif options['shape'] == 'rounded_rect':
        x = to_shape_space(
            options['shape.cornersx'], shape, force_world_space,
            viewportmapper)
        y = to_shape_space(
            options['shape.cornersy'], shape, force_world_space,
            viewportmapper)
        painter.drawRoundedRect(rect, x, y)
        qpath.addRoundedRect(rect, x, y)

    else:
        qpath = shape.get_painter_path(force_world_space, viewportmapper)
        painter.drawPath(qpath)
        qpath = qpath

    if shape.pixmap is not None:
        painter.setClipPath(qpath)
        transformed_rect = shape.image_rect or content_rect
        transformed_rect = to_shape_space_rect(
            transformed_rect, shape, force_world_space, viewportmapper)
        painter.drawPixmap(transformed_rect.toRect(), shape.pixmap)
        painter.setClipping(False)
    return qpath


def draw_selection_square(painter, rect, viewportmapper=None):
    viewportmapper = viewportmapper or ViewportMapper()
    rect = viewportmapper.to_viewport_rect(rect)
    bordercolor = QtGui.QColor(SELECTION_COLOR)
    backgroundcolor = QtGui.QColor(SELECTION_COLOR)
    backgroundcolor.setAlpha(85)
    painter.setPen(QtGui.QPen(bordercolor))
    painter.setBrush(QtGui.QBrush(backgroundcolor))
    painter.drawRect(rect)


def draw_picker_focus(painter, rect):
    color = QtGui.QColor(FOCUS_COLOR)
    color.setAlpha(10)
    pen = QtGui.QPen(color)
    pen.setWidthF(4)
    painter.setPen(pen)
    painter.setBrush(QtCore.Qt.NoBrush)
    painter.drawRect(rect)
    painter.setBrush(QtGui.QBrush())


def draw_current_panel(painter, rect, viewportmapper=None):
    viewportmapper = viewportmapper or ViewportMapper()
    rect = viewportmapper.to_viewport_rect(rect)
    color = QtGui.QColor(PANEL_COLOR)
    color.setAlpha(30)
    pen = QtGui.QPen(color)
    pen.setWidthF(1.5)
    pen.setStyle(QtCore.Qt.DashLine)
    painter.setPen(pen)
    brush = QtGui.QBrush(color)
    brush.setStyle(QtCore.Qt.BDiagPattern)
    painter.setBrush(brush)
    painter.drawRect(rect)


def draw_manipulator(painter, manipulator, cursor, viewportmapper=None):
    viewportmapper = viewportmapper or ViewportMapper()
    cursor = viewportmapper.to_units_coords(cursor).toPoint()
    hovered = manipulator.hovered_rects(cursor)

    if manipulator.rect in hovered:
        pen = QtGui.QPen(QtGui.QColor(0, 0, 0, 0))
        brush = QtGui.QBrush(QtGui.QColor(125, 125, 125))
        brush.setStyle(QtCore.Qt.FDiagPattern)
        painter.setPen(pen)
        painter.setBrush(brush)
        rect = viewportmapper.to_viewport_rect(manipulator.rect)
        painter.drawPath(get_hovered_path(rect))

    pen = QtGui.QPen(QtGui.QColor('black'))
    brush = QtGui.QBrush(QtGui.QColor('white'))
    painter.setBrush(brush)
    for rect in manipulator.viewport_handlers():
        pen.setWidth(3 if rect in hovered else 1)
        painter.setPen(pen)
        painter.drawEllipse(rect)

    pen.setWidth(1)
    pen.setStyle(QtCore.Qt.DashLine)  # if not moving else QtCore.Qt.SolidLine)
    painter.setPen(pen)
    painter.setBrush(QtGui.QBrush(QtGui.QColor(0, 0, 0, 0)))
    rect = viewportmapper.to_viewport_rect(manipulator.rect)
    painter.drawRect(rect)


def get_hovered_path(rect, viewportmapper=None):
    viewportmapper = viewportmapper or ViewportMapper()
    rect = viewportmapper.to_viewport_rect(rect)
    manipulator_rect = grow_rect(
        rect, viewportmapper.to_viewport(MANIPULATOR_BORDER))
    path = QtGui.QPainterPath()
    path.addRect(rect)
    path.addRect(manipulator_rect)
    return path


def draw_tangents(painter, path, viewportmapper):
    rect = QtCore.QRectF(0, 0, 6, 6)
    painter.setBrush(QtCore.Qt.yellow)
    painter.setPen(QtCore.Qt.yellow)
    for point in path:
        center = QtCore.QPointF(*point['point'])
        center = viewportmapper.to_viewport_coords(center)
        if point['tangent_in'] is not None:
            tangent_in = QtCore.QPointF(*point['tangent_in'])
            tangent_in = viewportmapper.to_viewport_coords(tangent_in)
            rect.moveCenter(tangent_in)
            painter.drawRect(rect)
            painter.drawLine(tangent_in, center)
        if point['tangent_out'] is not None:
            tangent_out = QtCore.QPointF(*point['tangent_out'])
            tangent_out = viewportmapper.to_viewport_coords(tangent_out)
            rect.moveCenter(tangent_out)
            painter.drawRect(rect)
            painter.drawLine(tangent_out, center)
