
from PySide2 import QtWidgets, QtCore


class VisibilityLayersEditor(QtWidgets.QWidget):
    removeLayer = QtCore.Signal(str)
    selectLayerContent = QtCore.Signal(str)

    def __init__(self, parent=None):
        super(VisibilityLayersEditor, self).__init__(parent)
        self.model = VisbilityLayersModel()
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
        return self.model.layers_data[indexes[0].row()][0]

    def call_remove_layer(self):
        layer = self.selected_layer()
        if not layer:
            return
        self.removeLayer.emit(layer)

    def call_select_layer(self):
        layer = self.selected_layer()
        if not layer:
            return
        self.selectLayerContent.emit(layer)

    def set_shapes(self, shapes):
        self.model.set_shapes(shapes)


class VisbilityLayersModel(QtCore.QAbstractTableModel):
    HEADERS = 'name', 'shapes'

    def __init__(self, parent=None):
        super(VisbilityLayersModel, self).__init__(parent)
        self.layers_data = []

    def rowCount(self, _):
        return len(self.layers_data)

    def columnCount(self, _):
        return len(self.HEADERS)

    def set_shapes(self, shapes):
        self.layoutAboutToBeChanged.emit()
        data = {}
        for shape in shapes:
            if not shape.visibility_layer():
                continue
            data[shape.visibility_layer()] = data.setdefault(
                shape.visibility_layer(), 0) + 1
        self.layers_data = sorted(data.items())
        self.layoutChanged.emit()

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Vertical or role != QtCore.Qt.DisplayRole:
            return
        return self.HEADERS[section]

    def data(self, index, role):
        if not index.isValid():
            return
        if role == QtCore.Qt.TextAlignmentRole:
            if index.column() == 1:
                return QtCore.Qt.AlignCenter

        if role != QtCore.Qt.DisplayRole:
            return

        if index.column() == 0:
            return self.layers_data[index.row()][0]
        if index.column() == 1:
            return str(self.layers_data[index.row()][1])
