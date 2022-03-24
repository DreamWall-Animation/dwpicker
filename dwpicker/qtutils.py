import inspect
import os
import sys
from PySide2 import QtGui, QtWidgets, QtCore
from maya import cmds
import maya.OpenMayaUI as omui
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
import shiboken2


# Ensure backward compatibility.
if sys.version_info[0] == 3:
    long = int


VALIGNS = {
    'top': QtCore.Qt.AlignTop,
    'center': QtCore.Qt.AlignVCenter,
    'bottom': QtCore.Qt.AlignBottom}
HALIGNS = {
    'left': QtCore.Qt.AlignLeft,
    'center': QtCore.Qt.AlignHCenter,
    'right': QtCore.Qt.AlignRight}
HERE = os.path.dirname(__file__)
ERROR_IMPORT_MSG = ('''
ERROR: Dwpicker: DwPicker is not found in Python paths.
    - Please use sys.path.append('<dwpicker forlder>') and relaunch it.
    - Or add '<picker folder>' to environment variable PYTHONPATH''')

RESTORE_CMD = ("""
try:
    import {0}
    {0}.{1}.restore()
except ImportError:
    print("{2}")
""")
mixin_windows = {}


if sys.version_info[0] != 2:
    long = int


def icon(filename):
    return QtGui.QIcon(os.path.join(HERE, 'icons', filename))


def get_cursor(widget):
    return widget.mapFromGlobal(QtGui.QCursor.pos())


def set_shortcut(keysequence, parent, method, context=None):
    shortcut = QtWidgets.QShortcut(QtGui.QKeySequence(keysequence), parent)
    shortcut.setContext(context or QtCore.Qt.WidgetWithChildrenShortcut)
    shortcut.activated.connect(method)
    return shortcut


def remove_workspace_control(control_name):
    workspace_control_name = control_name + "WorkspaceControl"
    cmds.deleteUI(workspace_control_name, control=True)


def maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    if ptr is not None:
        return shiboken2.wrapInstance(long(ptr), QtWidgets.QWidget)


class DockableBase(MayaQWidgetDockableMixin):
    """
    Code from https://kainev.com/qt-for-maya-dockable-windows
    Thanks for this !

    Convenience class for creating dockable Maya windows.
    """

    def __init__(self, control_name, **kwargs):
        super(DockableBase, self).__init__(**kwargs)
        self.setObjectName(control_name)

    def show(self, dockable=True, *_, **kwargs):
        """
        Show UI with generated uiScript argument
        """
        modulename = inspect.getmodule(self).__name__
        classname = self.__class__.__name__
        command = RESTORE_CMD.format(modulename, classname, ERROR_IMPORT_MSG)
        super(DockableBase, self).show(
            dockable=dockable, uiScript=command, **kwargs)

    @classmethod
    def restore(cls):
        """
        Internal method to restore the UI when Maya is opened.
        """
        # Create UI instance
        instance = cls()
        # Get the empty WorkspaceControl created by Maya
        workspace_control = omui.MQtUtil.getCurrentParent()
        # Grab the pointer to our instance as a Maya object
        mixinPtr = omui.MQtUtil.findControl(instance.objectName())
        # Add our UI to the WorkspaceControl
        omui.MQtUtil.addWidgetToMayaLayout(
            long(mixinPtr), long(workspace_control))
        # Store reference to UI
        global mixin_windows
        mixin_windows[instance.objectName()] = instance

