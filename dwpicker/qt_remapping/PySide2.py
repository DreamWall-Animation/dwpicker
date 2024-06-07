
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6 import __version__


QtWidgets.QShortcut = QtGui.QShortcut
QtWidgets.QAction = QtGui.QAction

QtGui.QMouseEvent.pos = QtGui.QMouseEvent.position
QtGui.QMouseEvent.globalPos = QtGui.QMouseEvent.globalPosition

QtGui.QWheelEvent.pos = QtGui.QWheelEvent.position

QtCore.Qt.BackgroundColorRole = QtCore.Qt.BackgroundRole
