from PySide2 import QtCore, QtGui
from maya import cmds

from dwpicker.optionvar import ZOOM_SENSITIVITY
from dwpicker.qtutils import VALIGNS, HALIGNS
from dwpicker.geometry import grow_rect, ViewportMapper


SELECTION_COLOR = '#3388FF'
MANIPULATOR_BORDER = 5


def factor_sensitivity(factor):
    sensitivity = cmds.optionVar(query=ZOOM_SENSITIVITY) / 50.0
    return factor * sensitivity


def draw_editor(painter, rect, snap=None, viewportmapper=None):
    viewportmapper = viewportmapper or ViewportMapper()
    rect = viewportmapper.to_viewport_rect(rect)
    # draw border
    pen = QtGui.QPen(QtGui.QColor('#333333'))
    pen.setStyle(QtCore.Qt.DashDotLine)
    pen.setWidthF(viewportmapper.to_viewport(3))
    brush = QtGui.QBrush(QtGui.QColor(255, 255, 255, 25))
    painter.setPen(pen)
    painter.setBrush(brush)
    painter.drawRect(rect)

    if snap is None:
        return
    # draw snap grid
    snap = viewportmapper.to_viewport(snap[0]), viewportmapper.to_viewport(snap[1])
    pen = QtGui.QPen(QtGui.QColor('red'))
    painter.setPen(pen)
    x = 0
    y = 0
    while y < rect.bottom():
        painter.drawPoint(x, y)
        x += snap[0]
        if x > rect.right():
            x = 0
            y += snap[1]


def draw_shape(painter, shape, viewportmapper=None):
    viewportmapper = viewportmapper or ViewportMapper()
    options = shape.options
    content_rect = shape.content_rect()
    if shape.clicked or shape.selected:
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
    pen.setWidthF(viewportmapper.to_viewport(bordersize))
    painter.setPen(pen)
    painter.setBrush(QtGui.QBrush(backgroundcolor))
    rect = viewportmapper.to_viewport_rect(shape.rect)
    if options['shape'] == 'square':
        painter.drawRect(rect)
    elif options['shape'] == 'round':
        painter.drawEllipse(rect)
    else:  # 'rounded_rect'
        x = viewportmapper.to_viewport(options['shape.cornersx'])
        y = viewportmapper.to_viewport(options['shape.cornersy'])
        painter.drawRoundedRect(rect, x, y)

    if shape.pixmap is not None:
        rect = shape.image_rect or content_rect
        rect = viewportmapper.to_viewport_rect(rect)
        painter.drawPixmap(rect.toRect(), shape.pixmap)

    painter.setPen(QtGui.QPen(textcolor))
    painter.setBrush(QtGui.QBrush(textcolor))
    option = QtGui.QTextOption()
    flags = VALIGNS[options['text.valign']] | HALIGNS[options['text.halign']]
    option.setAlignment(flags)
    font = QtGui.QFont()
    font.setBold(options['text.bold'])
    font.setItalic(options['text.italic'])
    size = round(viewportmapper.to_viewport(options['text.size']))
    font.setPixelSize(size)
    painter.setFont(font)
    text = options['text.content']
    content_rect = viewportmapper.to_viewport_rect(content_rect)
    painter.drawText(content_rect, flags, text)


def draw_selection_square(painter, rect, viewportmapper=None):
    viewportmapper = viewportmapper or ViewportMapper()
    rect = viewportmapper.to_viewport_rect(rect)
    bordercolor = QtGui.QColor(SELECTION_COLOR)
    backgroundcolor = QtGui.QColor(SELECTION_COLOR)
    backgroundcolor.setAlpha(85)
    painter.setPen(QtGui.QPen(bordercolor))
    painter.setBrush(QtGui.QBrush(backgroundcolor))
    painter.drawRect(rect)


def draw_manipulator(painter, manipulator, cursor, viewportmapper=None):
    viewportmapper = viewportmapper or ViewportMapper()
    hovered = manipulator.hovered_rects(cursor)

    if manipulator.rect in hovered:
        pen = QtGui.QPen(QtGui.QColor(0, 0, 0, 0))
        brush = QtGui.QBrush(QtGui.QColor(125, 125, 125))
        brush.setStyle(QtCore.Qt.FDiagPattern)
        painter.setPen(pen)
        painter.setBrush(brush)
        painter.drawPath(manipulator.hovered_path)

    pen = QtGui.QPen(QtGui.QColor('black'))
    brush = QtGui.QBrush(QtGui.QColor('white'))
    painter.setBrush(brush)
    for rect in manipulator.handler_rects():
        rect = viewportmapper.to_viewport_rect(rect)
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
