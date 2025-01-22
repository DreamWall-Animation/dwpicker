
from PySide2 import QtWidgets, QtCore


class VisibilityLayersEditor(QtWidgets.QWidget):
    selectLayerContent = QtCore.Signal(str)

    def __init__(self, document, parent=None):
        super(VisibilityLayersEditor, self).__init__(parent)
        self.document = document
        self.model = VisbilityLayersModel(document)
        self.table = QtWidgets.QTableView()
        self.table.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)
        self.table.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(
            QtWidgets.QAbstractItemView.SingleSelection)
        self.table.setModel(self.model)
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


class VisbilityLayersModel(QtCore.QAbstractTableModel):
    HEADERS = 'hide', 'name', 'shapes'

    def __init__(self, document, parent=None):
        super(VisbilityLayersModel, self).__init__(parent)
        self.document = document

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
            flags |= QtCore.Qt.ItemIsUserCheckable
        return flags

    def setData(self, index, value, role):
        if role != QtCore.Qt.CheckStateRole:
            return False

        layer = sorted(list(self.document.shapes_by_layer))[index.row()]
        hidden_layers = self.document.data['general']['hidden_layers']
        if value == QtCore.Qt.Unchecked and layer in hidden_layers:
            hidden_layers.remove(layer)
            self.document.general_option_changed.emit(
                'attribute_editor', 'hidden_layers')
            return True
        elif value == QtCore.Qt.Checked and layer not in hidden_layers:
            hidden_layers.append(layer)
            self.document.general_option_changed.emit(
                'attribute_editor', 'hidden_layers')
            self.document.data['general']['hidden_layers'].append(layer)
            return True
        return False

    def data(self, index, role):
        if not index.isValid():
            return
        if role == QtCore.Qt.TextAlignmentRole:
            if index.column() == 2:
                return QtCore.Qt.AlignCenter

        hidden_layers = self.document.data['general']['hidden_layers']
        layers = sorted(list(self.document.shapes_by_layer))
        if role == QtCore.Qt.CheckStateRole:
            if index.column() == 0:
                return (
                    QtCore.Qt.Checked
                    if layers[index.row()] in hidden_layers
                    else QtCore.Qt.Unchecked)

        if role != QtCore.Qt.DisplayRole:
            return

        if index.column() == 1:
            return layers[index.row()]
        if index.column() == 2:
            layer = layers[index.row()]
            return str(len(self.document.shapes_by_layer[layer]))