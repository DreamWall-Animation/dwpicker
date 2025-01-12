
from PySide2 import QtWidgets, QtCore


ORIENTATIONS = {
    'horizontal': QtCore.Qt.Horizontal,
    'vertical': QtCore.Qt.Vertical
}


def create_stack_splitters(data, widgets, orientation='vertical'):
    """
    data: [[.25, [1.]], [.5, [.5, .5]], [.25, [.3, .5, .2]]]
    widgets: List[QWidgets.QWidget]
    """
    key = 'horizontal' if orientation == 'vertical' else 'vertical'
    orientation_1 = ORIENTATIONS[key]
    key = 'vertical' if orientation == 'vertical' else 'horizontal'
    orientation_2 = ORIENTATIONS[key]
    root_splitter = QtWidgets.QSplitter(orientation_1)
    widget_it = iter(widgets)
    for i, (column, rows) in enumerate(data):
        splitter = QtWidgets.QSplitter(orientation_2)
        root_splitter.addWidget(splitter)
        root_splitter.setStretchFactor(i, int(column * 100))
        for j, row in enumerate(rows):
            widget = next(widget_it, QtWidgets.QWidget())
            splitter.addWidget(widget)
            splitter.setStretchFactor(j, int(row * 100))
    root_splitter.setSizes([int(d[0] * 100) for d in data])
    root_splitter.update()
    return root_splitter


def count_panels(panels):
    result = 0
    for _, rows in panels:
        result += len(rows)
    return result
