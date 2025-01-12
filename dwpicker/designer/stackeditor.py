from decimal import Decimal, getcontext
from PySide2 import QtWidgets, QtGui, QtCore


HANDLER_WIDTH = 16
HANDLER_HEIGHT = 16


class StackEditor(QtWidgets.QWidget):
    panelsChanged = QtCore.Signal(object)
    panelSelected = QtCore.Signal(int)
    panelDoubleClicked = QtCore.Signal(int)

    def __init__(self, parent=None):
        super(StackEditor, self).__init__(parent)
        self.data = [[1., [1.]]]
        self.orientation = 'vertical'
        self.stack_rects = get_stack_rects(
            self.data, self.rect(), self.orientation)
        self.setMouseTracking(True)
        self.clicked_action = None
        self.selected_index = None
        self.panels_are_changed = False
        self.panel_is_selected = None

    def set_orientation(self, orientation):
        self.orientation = orientation
        self.stack_rects = get_stack_rects(
            self.data, self.rect(), self.orientation)
        self.update()

    def set_data(self, data):
        self.data = data
        self.update()

    def sizeHint(self):
        return QtCore.QSize(300, 210)

    def resizeEvent(self, event):
        self.stack_rects = get_stack_rects(
            self.data, self.rect(), self.orientation)

    def mousePressEvent(self, event):
        if event.button() != QtCore.Qt.LeftButton:
            return
        self.clicked_action = self.get_action(event.pos())

    def mouseDoubleClickEvent(self, event):
        if event.button() != QtCore.Qt.LeftButton:
            return
        clicked_action = self.get_action(event.pos())
        if clicked_action[0] == 'select':
            panel = self.panel_number(clicked_action[1])
            self.panelSelected.emit(panel)
            self.panelDoubleClicked.emit(panel)
            self.selected_index = clicked_action[1]
            self.update()

    def panel_number(self, index):
        k = 1
        for i, (_, rows) in enumerate(self.data):
            for j in range(len(rows)):
                if [i, j] == index:
                    return k
                k += 1

    def mouseReleaseEvent(self, event):
        if event.button() != QtCore.Qt.LeftButton or not self.clicked_action:
            return
        index = self.clicked_action[1]
        if self.clicked_action[0] == 'delete':
            delete_panel(self.data, index)
            self.stack_rects = get_stack_rects(
                self.data, self.rect(), self.orientation)
            self.panelsChanged.emit(self.data)
        elif self.clicked_action[0] == 'select':
            index = self.clicked_action[1]
            if index == self.selected_index:
                self.selected_index = None
                self.panelSelected.emit(-1)
            else:
                self.selected_index = index
                self.panelSelected.emit(self.panel_number(self.selected_index))
        else:
            self.check_buffer_states()
        self.update()
        self.clicked_action = None

    def check_buffer_states(self):
        if self.panel_is_selected is not None:
            self.panelSelected.emit(self.panel_is_selected)
        if self.panels_are_changed:
            self.panelsChanged.emit(self.data)
        self.panel_is_selected = None
        self.panels_are_changed = False

    def get_action(self, cursor):
        for i, column in enumerate(self.stack_rects):
            for j, rect in enumerate(column):
                if not rect.contains(cursor):
                    continue

                if get_close_handler_rect(rect).contains(cursor):
                    if i + j:
                        return 'delete', [i, j]

                hrect = get_horizontal_handler_rect(rect)
                vrect = get_vertical_handler_rect(rect)
                if self.orientation == 'horizontal':
                    hrect, vrect = vrect, hrect

                if hrect.contains(cursor):
                    if j == len(column) - 1:
                            return 'create vertical', [i, j]
                    return 'move vertical', [i, j]

                if vrect.contains(cursor):
                    if i == len(self.data) - 1:
                        return 'create horizontal', [i, j]
                    return 'move horizontal', [i, j]

                return 'select', [i, j]

    def mouseMoveEvent(self, event):
        if not self.clicked_action:
            return
        vertical = self.orientation == 'vertical'

        if self.clicked_action[0] == 'create vertical':
            index = self.clicked_action[1]
            col = self.data[index[0]][1]
            col[-1] -= .1
            col.append(.1)
            self.clicked_action = 'move vertical', index
            self.selected_index = [index[0], index[1] + 1]
            self.panel_is_selected = self.panel_number(self.selected_index)
            self.panels_are_changed = True

        elif self.clicked_action[0] == 'create horizontal':
            index = self.clicked_action[1]
            self.data[-1][0] -= .1
            self.data.append([.1, [1.]])
            self.clicked_action = 'move horizontal', index
            self.selected_index = [index[0] + 1, 0]
            self.panel_is_selected = self.panel_number(self.selected_index)
            self.panels_are_changed = True

        elif self.clicked_action[0] == 'move vertical' and vertical:
            index = self.clicked_action[1]
            y = event.pos().y() / self.height()
            move_vertical(self.data, index, y)
            self.panels_are_changed = True

        elif self.clicked_action[0] == 'move vertical':
            index = self.clicked_action[1]
            x = event.pos().x() / self.width()
            move_vertical(self.data, index, x)
            self.panels_are_changed = True

        elif self.clicked_action[0] == 'move horizontal' and vertical:
            index = self.clicked_action[1]
            x = event.pos().x() / self.width()
            move_horizontal(self.data, index, x)
            self.panels_are_changed = True

        elif self.clicked_action[0] == 'move horizontal':
            index = self.clicked_action[1]
            y = event.pos().y() / self.height()
            move_horizontal(self.data, index, y)
            self.panels_are_changed = True

        self.stack_rects = get_stack_rects(
            self.data, self.rect(), self.orientation)
        self.update()

    def paintEvent(self, _):
        painter = QtGui.QPainter(self)
        k = 1
        original_pen = painter.pen()
        original_brush = painter.brush()
        for i, column in enumerate(self.stack_rects):
            for j, rect in enumerate(column):
                if [i, j] == self.selected_index:
                    pen = QtGui.QPen(QtGui.QColor('yellow'))
                    pen.setWidth(5)
                    painter.setPen(pen)
                    brush = QtGui.QBrush(original_brush)
                    color = brush.color()
                    color.setAlpha(50)
                    brush.setColor(color)
                    brush.setStyle(QtCore.Qt.FDiagPattern)
                    painter.setBrush(brush)
                else:
                    pen = original_pen
                    painter.setPen(pen)
                    painter.setBrush(original_brush)

                painter.drawRect(rect)

                painter.setPen(QtCore.Qt.NoPen)
                painter.setBrush(pen.color())
                handler_rect = get_horizontal_handler_rect(rect)
                painter.drawPath(up_arrow(handler_rect))
                handler_rect = get_vertical_handler_rect(rect)
                painter.drawPath(left_arrow(handler_rect))

                painter.setPen(original_pen)
                painter.setBrush(original_brush)
                font = QtGui.QFont()
                font.setPointSize(15)
                font.setBold(True)
                painter.setFont(font)
                painter.drawText(rect, QtCore.Qt.AlignCenter, str(k))
                k += 1
                if i + j == 0:
                    continue
                font = QtGui.QFont()
                font.setBold(True)
                painter.setFont(font)
                painter.drawText(
                    get_close_handler_rect(rect), QtCore.Qt.AlignCenter, 'X')
        painter.end()


def get_stack_rects(data, rect, orientation):
    if orientation == 'vertical':
        return get_vertical_stack_rects(data, rect)
    return get_horizontal_stack_rects(data, rect)


def get_horizontal_stack_rects(data, rect):
    result = []
    y = 0
    for height, rows in data:
        column = []
        x = 0
        for width in rows:
            panel_rect = QtCore.QRectF(
                x * rect.width(),
                y * rect.height(),
                (width * rect.width()) - 1,
                (height * rect.height()) - 1)
            column.append(panel_rect)
            x += width
        y += height
        result.append(column)
    return result


def get_vertical_stack_rects(data, rect):
    result = []
    x = 0
    for width, rows in data:
        column = []
        y = 0
        for height in rows:
            panel_rect = QtCore.QRectF(
                x * rect.width(),
                y * rect.height(),
                (width * rect.width()) - 1,
                (height * rect.height()) - 1)
            column.append(panel_rect)
            y += height
        x += width
        result.append(column)
    return result


def get_vertical_handler_rect(rect):
    return QtCore.QRectF(
        rect.right() - HANDLER_WIDTH,
        rect.center().y() - (HANDLER_HEIGHT / 2),
        HANDLER_WIDTH, HANDLER_HEIGHT)


def get_horizontal_handler_rect(rect):
    return QtCore.QRectF(
        rect.center().x() - (HANDLER_WIDTH / 2),
        rect.bottom() - HANDLER_HEIGHT,
        HANDLER_WIDTH, HANDLER_HEIGHT)


def get_close_handler_rect(rect):
    return QtCore.QRectF(
        rect.right() - HANDLER_WIDTH,
        rect.top(), HANDLER_HEIGHT, HANDLER_WIDTH)


def delete_panel(data, index):
    column = data[index[0]][1]
    if len(column) > 1:
        data[index[0]][1] = delete_value(column, index[1])
        return
    values = delete_value([c[0] for c in data], index[0])
    del data[index[0]]
    for i, value in enumerate(values):
        data[i][0] = value


def delete_value(values, index):
    getcontext().prec = 50
    decimal_values = [Decimal(v) for v in values]
    values = [
        Decimal(v) for i, v in enumerate(decimal_values) if i != index]
    return [
        float((v / sum(values)).quantize(Decimal('1.00000')))
        for v in values]


def move_vertical(data, index, y):
    column = data[index[0]][1]
    ratios = to_ratios(column)
    if index[1] == 0:
        y = max((.1, y))
    else:
        y = max((ratios[index[1] - 1] + .1, y))
    y = min((y, ratios[index[1] + 1] - .1))
    ratios[index[1]] = y
    data[index[0]][1] = to_weights(ratios)


def move_horizontal(data, index, x):
    ratios = to_ratios(c[0] for c in data)
    if index[0] == 0:
        x = max((.1, x))
    else:
        x = max((ratios[index[0] - 1] + .1, x))
    x = min((x, ratios[index[0] + 1] - .1))
    ratios[index[0]] = x
    for i, col in enumerate(to_weights(ratios)):
        data[i][0] = col


def up_arrow(rect):
    path = QtGui.QPainterPath(rect.bottomLeft())
    path.lineTo(rect.bottomRight())
    point = QtCore.QPointF(rect.center().x(), rect.top())
    path.lineTo(point)
    path.lineTo(rect.bottomLeft())
    return path


def left_arrow(rect):
    path = QtGui.QPainterPath(rect.topRight())
    path.lineTo(rect.bottomRight())
    point = QtCore.QPointF(rect.left(), rect.center().y())
    path.lineTo(point)
    path.lineTo(rect.topRight())
    return path


def to_ratios(weights):
    """
    Convert weight list to ratios.
    input:  [0.2, 0.3, 0.4, 0.1]
    output: [0.2, 0.5, 0.9, 1.0]
    """
    total = 0.0
    result = []
    for weight in weights:
        total += weight
        result.append(total)
    return result


def to_weights(ratios):
    """
    Convert ratio list to weights.
    input:  [0.2, 0.5, 0.9, 1.0]
    output: [0.2, 0.3, 0.4, 0.1]
    """
    result = []
    result.extend(ratio - sum(result) for ratio in ratios)
    return result
