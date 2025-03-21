from dwpicker.pyside import QtWidgets, QtCore


class CustomSplitterHandle(QtWidgets.QSplitterHandle):
    def __init__(self, orientation, parent):
        super(CustomSplitterHandle, self).__init__(orientation, parent)
        self.splitter = parent

    def toggle_left_widget(self):
        """Collapse or expand the left widget"""
        sizes = self.splitter.sizes()
        if sizes[0] > 0:  # If left widget is visible
            self.splitter.setSizes([0, sizes[1]])
        else:
            self.splitter.setSizes([sizes[1] // 2, sizes[1] // 2])


class CustomSplitter(QtWidgets.QSplitter):
    def __init__(self, orientation, parent=None):
        super(CustomSplitter, self).__init__(orientation, parent)
        self.splitter_handle = None

    def createHandle(self):
        handle = CustomSplitterHandle(self.orientation(), self)
        self.splitter_handle = handle
        return handle
