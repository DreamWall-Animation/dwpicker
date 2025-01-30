
from dwpicker.pyside import QtCore
from maya import cmds
from dwpicker.optionvar import (
    ISOLATE_CURRENT_PANEL_SHAPES, DISPLAY_HIERARCHY_IN_CANVAS)


class DisplayOptions(QtCore.QObject):
    options_changed = QtCore.Signal()

    def __init__(self):
        super(DisplayOptions, self).__init__()
        self.isolate = cmds.optionVar(query=ISOLATE_CURRENT_PANEL_SHAPES)
        self.current_panel = -1
        self.highlighted_children_ids = []
        state = cmds.optionVar(query=DISPLAY_HIERARCHY_IN_CANVAS)
        self.display_hierarchy = bool(state)