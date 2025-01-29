from functools import partial
from maya import cmds
from PySide2 import QtGui, QtWidgets, QtCore

from dwpicker.optionvar import (
    BG_LOCKED, DISPLAY_HIERARCHY_IN_CANVAS, ISOLATE_CURRENT_PANEL_SHAPES,
    SNAP_ITEMS, SNAP_GRID_X, SNAP_GRID_Y, save_optionvar)
from dwpicker.qtutils import icon


class MenuWidget(QtWidgets.QWidget):
    addBackgroundRequested = QtCore.Signal()
    addButtonRequested = QtCore.Signal()
    addTextRequested = QtCore.Signal()
    alignRequested = QtCore.Signal(str)
    arrangeRequested = QtCore.Signal(str)
    buttonLibraryRequested = QtCore.Signal(QtCore.QPoint)
    centerValuesChanged = QtCore.Signal(int, int)
    copyRequested = QtCore.Signal()
    copySettingsRequested = QtCore.Signal()
    deleteRequested = QtCore.Signal()
    editCenterToggled = QtCore.Signal(bool)
    lockBackgroundShapeToggled = QtCore.Signal(bool)
    moveDownRequested = QtCore.Signal()
    moveUpRequested = QtCore.Signal()
    onBottomRequested = QtCore.Signal()
    onTopRequested = QtCore.Signal()
    pasteRequested = QtCore.Signal()
    pasteSettingsRequested = QtCore.Signal()
    redoRequested = QtCore.Signal()
    searchAndReplaceRequested = QtCore.Signal()
    snapValuesChanged = QtCore.Signal()
    symmetryRequested = QtCore.Signal(bool)
    undoRequested = QtCore.Signal()
    useSnapToggled = QtCore.Signal(bool)

    def __init__(self, display_options, parent=None):
        super(MenuWidget, self).__init__(parent=parent)
        self.display_options = display_options

        self.delete = QtWidgets.QAction(icon('delete.png'), '', self)
        self.delete.setToolTip('Delete selection')
        self.delete.triggered.connect(self.deleteRequested.emit)

        self.copy = QtWidgets.QAction(icon('copy.png'), '', self)
        self.copy.setToolTip('Copy selection')
        self.copy.triggered.connect(self.copyRequested.emit)

        self.paste = QtWidgets.QAction(icon('paste.png'), '', self)
        self.paste.setToolTip('Paste')
        self.paste.triggered.connect(self.pasteRequested.emit)

        self.undo = QtWidgets.QAction(icon('undo.png'), '', self)
        self.undo.setToolTip('Undo')
        self.undo.triggered.connect(self.undoRequested.emit)
        self.redo = QtWidgets.QAction(icon('redo.png'), '', self)
        self.redo.setToolTip('Redo')
        self.redo.triggered.connect(self.redoRequested.emit)

        icon_ = icon('copy_settings.png')
        self.copy_settings = QtWidgets.QAction(icon_, '', self)
        self.copy_settings.setToolTip('Copy settings')
        self.copy_settings.triggered.connect(self.copySettingsRequested.emit)
        icon_ = icon('paste_settings.png')
        self.paste_settings = QtWidgets.QAction(icon_, '', self)
        self.paste_settings.setToolTip('Paste settings')
        self.paste_settings.triggered.connect(self.pasteSettingsRequested.emit)

        self.search = QtWidgets.QAction(icon('search.png'), '', self)
        self.search.triggered.connect(self.searchAndReplaceRequested.emit)
        self.search.setToolTip('Search and replace')

        icon_ = icon('lock-non-interactive.png')
        self.lock_bg = QtWidgets.QAction(icon_, '', self)
        self.lock_bg.setToolTip('Lock background items')
        self.lock_bg.setCheckable(True)
        self.lock_bg.triggered.connect(self.save_ui_states)
        self.lock_bg.toggled.connect(self.lockBackgroundShapeToggled.emit)

        self.isolate = QtWidgets.QAction(icon('isolate.png'), '', self)
        self.isolate.setToolTip('Isolate current panel shapes')
        self.isolate.setCheckable(True)
        self.isolate.toggled.connect(self.isolate_panel)

        self.hierarchy = QtWidgets.QAction(icon('hierarchy.png'), '', self)
        self.hierarchy.setToolTip('Display hierarchy')
        self.hierarchy.setCheckable(True)
        state = bool(cmds.optionVar(query=DISPLAY_HIERARCHY_IN_CANVAS))
        self.hierarchy.setChecked(state)
        self.hierarchy.toggled.connect(self.toggle_display_hierarchy)

        self.snap = QtWidgets.QAction(icon('snap.png'), '', self)
        self.snap.setToolTip('Snap grid enable')
        self.snap.setCheckable(True)
        self.snap.triggered.connect(self.snap_toggled)
        validator = QtGui.QIntValidator(5, 150)
        self.snapx = QtWidgets.QLineEdit('10')
        self.snapx.setFixedWidth(35)
        self.snapx.setValidator(validator)
        self.snapx.setEnabled(False)
        self.snapx.textEdited.connect(self.snap_value_changed)
        self.snapy = QtWidgets.QLineEdit('10')
        self.snapy.setFixedWidth(35)
        self.snapy.setValidator(validator)
        self.snapy.setEnabled(False)
        self.snapy.textEdited.connect(self.snap_value_changed)
        self.snap.toggled.connect(self.snapx.setEnabled)
        self.snap.toggled.connect(self.snapy.setEnabled)

        icon_ = icon('addshape.png')
        self.call_library = QtWidgets.QAction(icon_, '', self)
        self.call_library.setToolTip('Add button')
        self.call_library.triggered.connect(self._call_library)
        icon_ = icon('addbutton.png')
        self.addbutton = QtWidgets.QAction(icon_, '', self)
        self.addbutton.setToolTip('Add button')
        self.addbutton.triggered.connect(self.addButtonRequested.emit)
        self.addtext = QtWidgets.QAction(icon('addtext.png'), '', self)
        self.addtext.setToolTip('Add text')
        self.addtext.triggered.connect(self.addTextRequested.emit)
        self.addbg = QtWidgets.QAction(icon('addbg.png'), '', self)
        self.addbg.setToolTip('Add background shape')
        self.addbg.triggered.connect(self.addBackgroundRequested.emit)

        icon_ = icon('onbottom.png')
        self.onbottom = QtWidgets.QAction(icon_, '', self)
        self.onbottom.setToolTip('Set selected shapes on bottom')
        self.onbottom.triggered.connect(self.onBottomRequested.emit)
        icon_ = icon('movedown.png')
        self.movedown = QtWidgets.QAction(icon_, '', self)
        self.movedown.setToolTip('Move down selected shapes')
        self.movedown.triggered.connect(self.moveDownRequested.emit)
        self.moveup = QtWidgets.QAction(icon('moveup.png'), '', self)
        self.moveup.setToolTip('Move up selected shapes')
        self.moveup.triggered.connect(self.moveUpRequested.emit)
        self.ontop = QtWidgets.QAction(icon('ontop.png'), '', self)
        self.ontop.setToolTip('Set selected shapes on top')
        self.ontop.triggered.connect(self.onTopRequested.emit)

        self.hsymmetry = QtWidgets.QAction(icon('h_symmetry.png'), '', self)
        self.hsymmetry.setToolTip('Mirror a shape horizontally')
        method = partial(self.symmetryRequested.emit, True)
        self.hsymmetry.triggered.connect(method)
        self.vsymmetry = QtWidgets.QAction(icon('v_symmetry.png'), '', self)
        self.vsymmetry.setToolTip('Mirror a shape vertically')
        method = partial(self.symmetryRequested.emit, False)
        self.vsymmetry.triggered.connect(method)

        method = partial(self.alignRequested.emit, 'left')
        self.align_left = QtWidgets.QAction(icon('align_left.png'), '', self)
        self.align_left.triggered.connect(method)
        self.align_left.setToolTip('Align to left')
        file_ = 'align_h_center.png'
        method = partial(self.alignRequested.emit, 'h_center')
        self.align_h_center = QtWidgets.QAction(icon(file_), '', self)
        self.align_h_center.triggered.connect(method)
        self.align_h_center.setToolTip('Align to center horizontally')
        method = partial(self.alignRequested.emit, 'right')
        self.align_right = QtWidgets.QAction(icon('align_right.png'), '', self)
        self.align_right.triggered.connect(method)
        self.align_right.setToolTip('Align to right')
        method = partial(self.alignRequested.emit, 'top')
        self.align_top = QtWidgets.QAction(icon('align_top.png'), '', self)
        self.align_top.triggered.connect(method)
        self.align_top.setToolTip('Align to top')
        file_ = 'align_v_center.png'
        self.align_v_center = QtWidgets.QAction(icon(file_), '', self)
        method = partial(self.alignRequested.emit, 'v_center')
        self.align_v_center.triggered.connect(method)
        self.align_v_center.setToolTip('Align to center vertically')
        file_ = 'align_bottom.png'
        method = partial(self.alignRequested.emit, 'bottom')
        self.align_bottom = QtWidgets.QAction(icon(file_), '', self)
        self.align_bottom.triggered.connect(method)
        self.align_bottom.setToolTip('Align to bottom')

        file_ = 'arrange_h.png'
        method = partial(self.arrangeRequested.emit, 'horizontal')
        self.arrange_horizontal = QtWidgets.QAction(icon(file_), '', self)
        self.arrange_horizontal.triggered.connect(method)
        self.arrange_horizontal.setToolTip('Distribute horizontally')

        file_ = 'arrange_v.png'
        method = partial(self.arrangeRequested.emit, 'vertical')
        self.arrange_vertical = QtWidgets.QAction(icon(file_), '', self)
        self.arrange_vertical.triggered.connect(method)
        self.arrange_vertical.setToolTip('Distribute vertically')

        self.toolbar = QtWidgets.QToolBar()
        self.toolbar.setIconSize(QtCore.QSize(24, 24))
        self.toolbar.addAction(self.delete)
        self.toolbar.addAction(self.copy)
        self.toolbar.addAction(self.paste)
        self.toolbar.addAction(self.copy_settings)
        self.toolbar.addAction(self.paste_settings)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.undo)
        self.toolbar.addAction(self.redo)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.search)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.lock_bg)
        self.toolbar.addAction(self.isolate)
        self.toolbar.addAction(self.hierarchy)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.snap)
        self.toolbar.addWidget(self.snapx)
        self.toolbar.addWidget(self.snapy)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.call_library)
        self.toolbar.addAction(self.addbutton)
        self.toolbar.addAction(self.addtext)
        self.toolbar.addAction(self.addbg)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.hsymmetry)
        self.toolbar.addAction(self.vsymmetry)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.onbottom)
        self.toolbar.addAction(self.movedown)
        self.toolbar.addAction(self.moveup)
        self.toolbar.addAction(self.ontop)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.align_left)
        self.toolbar.addAction(self.align_h_center)
        self.toolbar.addAction(self.align_right)
        self.toolbar.addAction(self.align_top)
        self.toolbar.addAction(self.align_v_center)
        self.toolbar.addAction(self.align_bottom)
        self.toolbar.addAction(self.arrange_horizontal)
        self.toolbar.addAction(self.arrange_vertical)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 10, 0)
        self.layout.addWidget(self.toolbar)

        self.load_ui_states()

    def toggle_display_hierarchy(self, state):
        save_optionvar(DISPLAY_HIERARCHY_IN_CANVAS, int(state))
        self.display_options.display_hierarchy = state
        self.display_options.options_changed.emit()

    def isolate_panel(self, state):
        self.display_options.isolate = state
        self.display_options.options_changed.emit()

    def _call_library(self):
        rect = self.toolbar.actionGeometry(self.call_library)
        point = self.toolbar.mapToGlobal(rect.bottomLeft())
        self.buttonLibraryRequested.emit(point)

    def load_ui_states(self):
        self.snap.setChecked(cmds.optionVar(query=SNAP_ITEMS))
        value = str(cmds.optionVar(query=SNAP_GRID_X))
        self.snapx.setText(value)
        value = str(cmds.optionVar(query=SNAP_GRID_Y))
        self.snapy.setText(value)
        self.lock_bg.setChecked(bool(cmds.optionVar(query=BG_LOCKED)))
        value = bool(cmds.optionVar(query=ISOLATE_CURRENT_PANEL_SHAPES))
        self.isolate.setChecked(value)

    def save_ui_states(self):
        save_optionvar(BG_LOCKED, int(self.lock_bg.isChecked()))
        save_optionvar(SNAP_ITEMS, int(self.snap.isChecked()))
        save_optionvar(SNAP_GRID_X, int(self.snapx.text()))
        save_optionvar(SNAP_GRID_Y, int(self.snapy.text()))
        value = int(self.isolate.isChecked())
        save_optionvar(ISOLATE_CURRENT_PANEL_SHAPES, value)

    def size_changed(self, *_):
        self.sizeChanged.emit()

    def edit_center_toggled(self):
        self.editCenterToggled.emit(self.editcenter.isChecked())

    def snap_toggled(self):
        self.useSnapToggled.emit(self.snap.isChecked())
        self.save_ui_states()

    def snap_values(self):
        x = int(self.snapx.text()) if self.snapx.text() else 1
        y = int(self.snapy.text()) if self.snapy.text() else 1
        x = x if x > 0 else 1
        y = y if y > 0 else 1
        return x, y

    def snap_value_changed(self, _):
        self.snapValuesChanged.emit()
        self.save_ui_states()
