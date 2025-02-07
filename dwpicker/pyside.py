try:
    ModuleNotFoundError
except NameError:
    class ModuleNotFoundError(ImportError): # Python2 backward compatilibity
        pass

from maya import cmds
try:
    if int(cmds.about(majorVersion=True)) >= 2025:
        from PySide6 import QtCore, QtGui, QtWidgets
        from PySide6 import __version__
        import shiboken6 as shiboken2

        QtWidgets.QShortcut = QtGui.QShortcut
        QtWidgets.QAction = QtGui.QAction

        QtGui.QMouseEvent.pos = lambda x: x.position().toPoint()
        QtGui.QMouseEvent.globalPos = QtGui.QMouseEvent.globalPosition

        QtGui.QWheelEvent.pos = QtGui.QWheelEvent.position

        QtCore.Qt.BackgroundColorRole = QtCore.Qt.BackgroundRole
    else:
        raise TypeError()
except (ModuleNotFoundError, TypeError):
    from PySide2 import QtCore, QtGui, QtWidgets
    import shiboken2