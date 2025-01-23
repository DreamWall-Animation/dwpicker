from functools import partial
from PySide2 import QtWidgets, QtCore, QtGui
from dwpicker.widgets import V, CheckWidget


class VisibilityLayersEditor(QtWidgets.QWidget):
    selectLayerContent = QtCore.Signal(str)

    def __init__(self, document, parent=None):
        super(VisibilityLayersEditor, self).__init__(parent)
        self.document = document

        self.model = VisbilityLayersModel(document)

        self.table = QtWidgets.QTableView()
        self.table.setModel(self.model)
        self.table.setItemDelegateForColumn(0, CheckDelegate())
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.AllEditTriggers)
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)
        self.table.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.table.setFixedHeight(100)

        self.select_content = QtWidgets.QPushButton('Select layer content')
        self.select_content.released.connect(self.call_select_layer)
        self.remove_layer = QtWidgets.QPushButton('Remove selected layer')
        self.remove_layer.released.connect(self.call_remove_layer)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.table)
        layout.addWidget(self.select_content)
        layout.addWidget(self.remove_layer)

    def selected_layer(self):
        indexes = self.table.selectedIndexes()
        if not indexes:
            return

        layer = sorted(list(self.document.shapes_by_layer))[indexes[0].row()]
        return layer

    def call_remove_layer(self):
        layer = self.selected_layer()
        if not layer:
            return

        for shape in self.document.shapes_by_layer[layer]:
            if shape.visibility_layer() == layer:
                shape.options['visibility_layer'] = None
        self.model.layoutAboutToBeChanged.emit()
        self.document.sync_shapes_caches()
        self.document.shapes_changed.emit()
        self.document.record_undo()
        self.model.layoutChanged.emit()

    def call_select_layer(self):
        layer = self.selected_layer()
        if not layer:
            return
        self.selectLayerContent.emit(layer)


class CheckDelegate(QtWidgets.QItemDelegate):

    def mouseReleaseEvent(self, event):
        if event.button() != QtCore.Qt.LeftButton:
            return
        self.update()

    def createEditor(self, parent, _, index):
        model = index.model()
        hidden_layers = model.document.data['general']['hidden_layers']
        layer = model.data(index)
        state = layer in hidden_layers
        model.set_hidden_layer(layer, not state)

        checker = CheckWidget(not state, parent)
        checker.toggled.connect(partial(model.set_hidden_layer, layer))
        return checker

    def paint(self, painter, option, index):
        model = index.model()
        hidden_layers = model.document.data['general']['hidden_layers']
        state = model.data(index) in hidden_layers

        center = option.rect.center()
        painter.setBrush(QtCore.Qt.NoBrush)
        rect = QtCore.QRectF(center.x() - 10, center.y() - 10, 20, 20)
        if not state:
            return
        font = QtGui.QFont()
        font.setPixelSize(20)
        option = QtGui.QTextOption()
        option.setAlignment(QtCore.Qt.AlignCenter)
        painter.drawText(rect, V, option)


class VisbilityLayersModel(QtCore.QAbstractTableModel):
    HEADERS = 'hide', 'name', 'shapes'

    def __init__(self, document, parent=None):
        super(VisbilityLayersModel, self).__init__(parent)
        self.document = document
        self.document.changed.connect(self.layoutChanged.emit)

    def rowCount(self, _):
        return len(self.document.shapes_by_layer)

    def columnCount(self, _):
        return len(self.HEADERS)

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Vertical or role != QtCore.Qt.DisplayRole:
            return
        return self.HEADERS[section]

    def flags(self, index):
        flags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        if index.column() == 0:
            flags |= QtCore.Qt.ItemIsEditable
        return flags

    def set_hidden_layer(self, layer, state):
        self.layoutAboutToBeChanged.emit()
        hidden_layers = self.document.data['general']['hidden_layers']
        if state and layer not in hidden_layers:
            hidden_layers.append(layer)
        elif not state and layer in hidden_layers:
            hidden_layers.remove(layer)
        else:
            self.layoutChanged.emit()
            return
        self.document.record_undo()
        self.document.general_option_changed.emit(
            'attribute_editor', 'hidden_layers')
        self.layoutChanged.emit()

    def data(self, index, role=QtCore.Qt.UserRole):
        if not index.isValid():
            return
        if role == QtCore.Qt.TextAlignmentRole:
            if index.column() == 2:
                return QtCore.Qt.AlignCenter

        layers = sorted(list(self.document.shapes_by_layer))

        if role == QtCore.Qt.UserRole:
            return layers[index.row()]

        if role != QtCore.Qt.DisplayRole:
            return

        if index.column() == 1:
            return layers[index.row()]

        if index.column() == 2:
            layer = layers[index.row()]
            return str(len(self.document.shapes_by_layer[layer]))