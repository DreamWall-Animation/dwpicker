from dwpicker.pyside import QtWidgets, QtCore


class CustomSplitterHandle(QtWidgets.QSplitterHandle):
    def __init__(self, orientation, parent):
        super(CustomSplitterHandle, self).__init__(orientation, parent)

        self.split_button = QtWidgets.QPushButton("▶", self)
        self.split_button.setCursor(QtCore.Qt.ArrowCursor)
        self.split_button.setFixedSize(30, 30)
        self.split_button.clicked.connect(self.toggle_left_widget)
        self.splitter = parent

    def resizeEvent(self, event):
        super(CustomSplitterHandle, self).resizeEvent(event)
        if self.orientation() == QtCore.Qt.Horizontal:
            self.split_button.move(
                (self.width() - self.split_button.width()) // 2,
                (self.height() - self.split_button.height()) // 2)

    def toggle_left_widget(self):
        """Collapse or expand the left widget"""
        sizes = self.splitter.sizes()
        if sizes[0] > 0:  # If left widget is visible
            self.splitter.setSizes([0, sizes[1]])
            self.split_button.setText("▶")
        else:
            self.splitter.setSizes([sizes[1] // 2, sizes[1] // 2])
            self.split_button.setText("◀")


class CustomSplitter(QtWidgets.QSplitter):
    def createHandle(self):
        return CustomSplitterHandle(self.orientation(), self)
