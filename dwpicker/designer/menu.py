from functools import partial
from maya import cmds
from PySide2 import QtGui, QtWidgets, QtCore

from dwpicker.optionvar import (
    BG_LOCKED, SNAP_ITEMS, SNAP_GRID_X, SNAP_GRID_Y, save_optionvar)
from dwpicker.qtutils import icon


class MenuWidget(QtWidgets.QWidget):
    addBackgroundRequested = QtCore.Signal()
    addButtonRequested = QtCore.Signal()
    addTextRequested = QtCore.Signal()
    centerValuesChanged = QtCore.Signal(int, int)
    copyRequested = QtCore.Signal()
    deleteRequested = QtCore.Signal()
    editCenterToggled = QtCore.Signal(bool)
    lockBackgroundShapeToggled = QtCore.Signal(bool)
    moveDownRequested = QtCore.Signal()
    moveUpRequested = QtCore.Signal()
    onBottomRequested = QtCore.Signal()
    onTopRequested = QtCore.Signal()
    pasteRequested = QtCore.Signal()
    undoRequested = QtCore.Signal()
    searchAndReplaceRequested = QtCore.Signal()
    sizeChanged = QtCore.Signal()
    snapValuesChanged = QtCore.Signal()
    symmetryRequested = QtCore.Signal(bool)
    redoRequested = QtCore.Signal()
    useSnapToggled = QtCore.Signal(bool)

    def __init__(self, parent=None):
        super(MenuWidget, self).__init__(parent=parent)

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

        self.search = QtWidgets.QAction(icon('search.png'), '', self)
        self.search.triggered.connect(self.searchAndReplaceRequested.emit)
        self.search.setToolTip('Search and replace')

        icon_ = icon('lock-non-interactive.png')
        self.lock_bg = QtWidgets.QAction(icon_, '', self)
        self.lock_bg.setToolTip('Lock background items')
        self.lock_bg.setCheckable(True)
        self.lock_bg.triggered.connect(self.save_ui_states)
        self.lock_bg.toggled.connect(self.lockBackgroundShapeToggled.emit)

        validator = QtGui.QIntValidator()
        self.picker_width = QtWidgets.QLineEdit('600')
        self.picker_width.setFixedWidth(35)
        self.picker_width.setValidator(validator)
        self.picker_width.textEdited.connect(self.size_changed)
        self.picker_height = QtWidgets.QLineEdit('300')
        self.picker_height.setFixedWidth(35)
        self.picker_height.setValidator(validator)
        self.picker_height.textEdited.connect(self.size_changed)

        icon_ = icon('center.png')
        self.editcenter = QtWidgets.QAction(icon_, '', self)
        self.editcenter.setToolTip('Edit the picker focus center')
        self.editcenter.setCheckable(True)
        self.editcenter.triggered.connect(self.edit_center_toggled)
        validator = QtGui.QIntValidator()
        self.editcenterx = QtWidgets.QLineEdit('10')
        self.editcenterx.setFixedWidth(35)
        self.editcenterx.setValidator(validator)
        self.editcenterx.textEdited.connect(self.center_values_changed)
        self.editcentery = QtWidgets.QLineEdit('10')
        self.editcentery.setFixedWidth(35)
        self.editcentery.setValidator(validator)
        self.editcentery.textEdited.connect(self.center_values_changed)

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
        method = partial(self.symmetryRequested.emit, True)
        self.hsymmetry.triggered.connect(method)
        self.vsymmetry = QtWidgets.QAction(icon('v_symmetry.png'), '', self)
        method = partial(self.symmetryRequested.emit, False)
        self.vsymmetry.triggered.connect(method)

        self.toolbar = QtWidgets.QToolBar()
        self.toolbar.addAction(self.delete)
        self.toolbar.addAction(self.copy)
        self.toolbar.addAction(self.paste)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.undo)
        self.toolbar.addAction(self.redo)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.search)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.lock_bg)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.snap)
        self.toolbar.addWidget(self.snapx)
        self.toolbar.addWidget(self.snapy)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(QtWidgets.QLabel('size'))
        self.toolbar.addWidget(self.picker_width)
        self.toolbar.addWidget(self.picker_height)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.editcenter)
        self.toolbar.addWidget(self.editcenterx)
        self.toolbar.addWidget(self.editcentery)
        self.toolbar.addSeparator()
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

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 10, 0)
        self.layout.addWidget(self.toolbar)

        self.load_ui_states()

    def load_ui_states(self):
        self.snap.setChecked(cmds.optionVar(query=SNAP_ITEMS))
        value = str(cmds.optionVar(query=SNAP_GRID_X))
        self.snapx.setText(value)
        value = str(cmds.optionVar(query=SNAP_GRID_Y))
        self.snapy.setText(value)
        self.lock_bg.setChecked(bool(cmds.optionVar(query=BG_LOCKED)))

    def save_ui_states(self):
        save_optionvar(BG_LOCKED, int(self.lock_bg.isChecked()))
        save_optionvar(SNAP_ITEMS, int(self.snap.isChecked()))
        save_optionvar(SNAP_GRID_X, int(self.snapx.text()))
        save_optionvar(SNAP_GRID_Y, int(self.snapy.text()))

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

    def set_center_values(self, x, y):
        self.editcenterx.setText(str(x))
        self.editcentery.setText(str(y))

    def center_values_changed(self, _):
        x = int(self.editcenterx.text()) if self.editcenterx.text() else 0
        y = int(self.editcentery.text()) if self.editcentery.text() else 0
        self.centerValuesChanged.emit(x, y)

    def set_size_values(self, width, height):
        self.picker_width.setText(str(width))
        self.picker_height.setText(str(height))
        self.sizeChanged.emit()

    def get_size(self):
        width = int(self.picker_width.text()) if self.picker_width.text() else 1
        height = int(self.picker_height.text()) if self.picker_height.text() else 1
        return QtCore.QSize(width, height)
