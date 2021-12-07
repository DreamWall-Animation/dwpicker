from PySide2 import QtCore, QtGui
from dwpicker.qtutils import VALIGNS, HALIGNS
from dwpicker.geometry import grow_rect


MANIPULATOR_BORDER = 5
SELECTION_COLOR = '#3388FF'


class PaintContext():
    def __init__(self):
        self.zoom = 1
        self.center = [0, 0]
        self.cursor_background_alpha = 0.2
        self.zone_alpha = 0.2

    @property
    def manipulator_border(self):
        return self.relatives(MANIPULATOR_BORDER)

    def relatives(self, value):
        return value * self.zoom

    def absolute(self, value):
        return value / self.zoom

    def absolute_point(self, point):
        return QtCore.QPointF(
            self.absolute(point.x() - self.center[0]),
            self.absolute(point.y() - self.center[1]))

    def relative_point(self, point):
        return QtCore.QPointF(
            self.relatives(point.x()) + self.center[0],
            self.relatives(point.y()) + self.center[1])

    def absolute_rect(self, rect):
        top_left = self.absolute_point(rect.topLeft())
        width = self.absolute(rect.width())
        height = self.absolute(rect.height())
        return QtCore.QRectF(top_left.x(), top_left.y(), width, height)

    def relatives_rect(self, rect):
        return QtCore.QRectF(
            (rect.left() * self.zoom) + self.center[0],
            (rect.top() * self.zoom) + self.center[1],
            rect.width() * self.zoom,
            rect.height() * self.zoom)

    def zoomin(self):
        self.zoom += self.zoom / 10.0
        self.zoom = min(self.zoom, 5.0)

    def zoomout(self):
        self.zoom -= self.zoom / 10.0
        self.zoom = max(self.zoom, .1)

    def reset(self):
        self.center = [0, 0]
        self.zoom = 1


def draw_editor(painter, rect, snap=None, paintcontext=None):
    paintcontext = paintcontext or PaintContext()
    rect = paintcontext.relatives_rect(rect)
    # draw border
    pen = QtGui.QPen(QtGui.QColor('#333333'))
    pen.setStyle(QtCore.Qt.DashDotLine)
    pen.setWidthF(paintcontext.relatives(3))
    brush = QtGui.QBrush(QtGui.QColor(255, 255, 255, 25))
    painter.setPen(pen)
    painter.setBrush(brush)
    painter.drawRect(rect)

    if snap is None:
        return
    # draw snap grid
    snap = paintcontext.relatives(snap[0]), paintcontext.relatives(snap[1])
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


def draw_editor_center(painter, rect, point, paintcontext=None):
    paintcontext = paintcontext or PaintContext()
    rect = paintcontext.relatives_rect(rect)
    color = QtGui.QColor(200, 200, 200, 125)
    painter.setPen(QtGui.QPen(color))
    painter.setBrush(QtGui.QBrush(color))
    painter.drawRect(rect)

    path = get_center_path(QtCore.QPoint(*point))
    pen = QtGui.QPen(QtGui.QColor(50, 125, 255))
    pen.setWidthF(paintcontext.relatives(2))
    painter.setPen(pen)
    painter.drawPath(path)


def get_center_path(point):
    ext = 12
    int_ = 5
    path = QtGui.QPainterPath(point)
    path.moveTo(QtCore.QPoint(point.x() - ext, point.y()))
    path.lineTo(QtCore.QPoint(point.x() - int_, point.y()))
    path.moveTo(QtCore.QPoint(point.x() + int_, point.y()))
    path.lineTo(QtCore.QPoint(point.x() + ext, point.y()))
    path.moveTo(QtCore.QPoint(point.x(), point.y() - ext))
    path.lineTo(QtCore.QPoint(point.x(), point.y() - int_))
    path.moveTo(QtCore.QPoint(point.x(), point.y() + int_))
    path.lineTo(QtCore.QPoint(point.x(), point.y() + ext))
    path.addEllipse(point, 1, 1)
    return path


def draw_shape(painter, shape, paintcontext=None):
    paintcontext = paintcontext or PaintContext()
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
    pen.setWidthF(paintcontext.relatives(bordersize))
    painter.setPen(pen)
    painter.setBrush(QtGui.QBrush(backgroundcolor))
    rect = paintcontext.relatives_rect(shape.rect)
    if options['shape'] == 'square':
        painter.drawRect(rect)
    elif options['shape'] == 'round':
        painter.drawEllipse(rect)
    else: # 'rounded_rect'
        x = paintcontext.relatives(options['shape.cornersx'])
        y = paintcontext.relatives(options['shape.cornersy'])
        painter.drawRoundedRect(rect, x, y)

    if shape.pixmap is not None:
        rect = shape.image_rect or content_rect
        rect = paintcontext.relatives_rect(rect)
        painter.drawPixmap(rect.toRect(), shape.pixmap)

    painter.setPen(QtGui.QPen(textcolor))
    painter.setBrush(QtGui.QBrush(textcolor))
    option = QtGui.QTextOption()
    flags = VALIGNS[options['text.valign']] | HALIGNS[options['text.halign']]
    option.setAlignment(flags)
    font = QtGui.QFont()
    font.setBold(options['text.bold'])
    font.setItalic(options['text.italic'])
    size = round(paintcontext.relatives(options['text.size']))
    font.setPixelSize(size)
    painter.setFont(font)
    text = options['text.content']
    content_rect = paintcontext.relatives_rect(content_rect)
    painter.drawText(content_rect, flags, text)


def draw_selection_square(painter, rect, paintcontext=None):
    paintcontext = paintcontext or PaintContext()
    rect = paintcontext.relatives_rect(rect)
    bordercolor = QtGui.QColor(SELECTION_COLOR)
    backgroundcolor = QtGui.QColor(SELECTION_COLOR)
    backgroundcolor.setAlpha(85)
    painter.setPen(QtGui.QPen(bordercolor))
    painter.setBrush(QtGui.QBrush(backgroundcolor))
    painter.drawRect(rect)


def draw_manipulator(painter, manipulator, cursor, paintcontext=None):
    paintcontext = paintcontext or PaintContext()
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
        rect = paintcontext.relatives_rect(rect)
        pen.setWidth(3 if rect in hovered else 1)
        painter.setPen(pen)
        painter.drawEllipse(rect)

    pen.setWidth(1)
    pen.setStyle(QtCore.Qt.DashLine)  # if not moving else QtCore.Qt.SolidLine)
    painter.setPen(pen)
    painter.setBrush(QtGui.QBrush(QtGui.QColor(0, 0, 0, 0)))
    rect = paintcontext.relatives_rect(manipulator.rect)
    painter.drawRect(rect)


def draw_aiming_background(painter, rect, paintcontext=None):
    paintcontext = paintcontext or PaintContext()
    rect = paintcontext.relatives_rect(rect)
    pen = QtGui.QPen(QtGui.QColor(0, 0, 0, 0))
    brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 1))
    painter.setPen(pen)
    painter.setBrush(brush)
    painter.drawRect(rect)


def draw_aiming(painter, center, target, paintcontext=None):
    paintcontext = paintcontext or PaintContext()
    pen = QtGui.QPen(QtGui.QColor(35, 35, 35))
    pen.setWidth(paintcontext.relatives(3))
    painter.setPen(pen)
    painter.setBrush(QtGui.QColor(0, 0, 0, 0))
    center = paintcontext.relative_point(center)
    target = paintcontext.relatives_rect(target)
    painter.drawLine(center, target)


def get_hovered_path(rect, paintcontext=None):
    paintcontext = paintcontext or PaintContext()
    rect = paintcontext.relatives_rect(rect)
    manipulator_rect = grow_rect(rect, paintcontext.manipulator_border)
    path = QtGui.QPainterPath()
    path.addRect(rect)
    path.addRect(manipulator_rect)
    return path