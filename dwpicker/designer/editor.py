from functools import partial
from math import ceil

from PySide2 import QtWidgets, QtCore
from maya import cmds

from dwpicker import clipboard
from dwpicker.align import align_shapes
from dwpicker.arrayutils import (
    move_elements_to_array_end, move_elements_to_array_begin,
    move_up_array_elements, move_down_array_elements)
from dwpicker.dialog import SearchAndReplaceDialog, warning, SettingsPaster
from dwpicker.interactive import Shape
from dwpicker.geometry import get_combined_rects, rect_symmetry
from dwpicker.optionvar import BG_LOCKED, TRIGGER_REPLACE_ON_MIRROR
from dwpicker.picker import frame_shapes
from dwpicker.qtutils import set_shortcut
from dwpicker.templates import BUTTON, TEXT, BACKGROUND

from dwpicker.designer.editarea import ShapeEditArea
from dwpicker.designer.menu import MenuWidget
from dwpicker.designer.attributes import AttributeEditor


DIRECTION_OFFSETS = {
    'Left': (-1, 0), 'Right': (1, 0), 'Up': (0, -1), 'Down': (0, 1)}


class PickerEditor(QtWidgets.QWidget):
    pickerDataModified = QtCore.Signal(object)

    def __init__(self, picker_data, undo_manager, parent=None):
        super(PickerEditor, self).__init__(parent, QtCore.Qt.Window)
        title = "Picker editor - " + picker_data['general']['name']
        self.setWindowTitle(title)
        self.options = picker_data['general']
        self.undo_manager = undo_manager

        self.shape_editor = ShapeEditArea(self.options)
        bg_locked = bool(cmds.optionVar(query=BG_LOCKED))
        self.shape_editor.set_lock_background_shape(bg_locked)
        self.set_picker_data(picker_data)
        self.shape_editor.selectedShapesChanged.connect(self.selection_changed)
        method = self.set_data_modified
        self.shape_editor.increaseUndoStackRequested.connect(method)
        self.scrollarea = QtWidgets.QScrollArea()
        alignment = QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter
        self.scrollarea.setFocusPolicy(QtCore.Qt.NoFocus)
        policy = QtWidgets.QSizePolicy.Expanding
        self.scrollarea.setSizePolicy(policy, policy)
        # HACK: Stupid hack to force scroll area to fix layout size.
        self.scrollarea.sizeHint = lambda: QtCore.QSize(10000, 10000)
        self.scrollarea.setAlignment(alignment)
        self.scrollarea.setWidget(self.shape_editor)

        self.menu = MenuWidget()
        self.menu.copyRequested.connect(self.copy)
        self.menu.copySettingsRequested.connect(self.copy_settings)
        self.menu.deleteRequested.connect(self.delete_selection)
        self.menu.frameShapes.connect(self.frame_shapes)
        self.menu.pasteRequested.connect(self.paste)
        self.menu.pasteSettingsRequested.connect(self.paste_settings)
        self.menu.sizeChanged.connect(self.editor_size_changed)
        self.menu.snapValuesChanged.connect(self.snap_value_changed)
        self.menu.useSnapToggled.connect(self.use_snap)

        method = self.shape_editor.set_lock_background_shape
        self.menu.lockBackgroundShapeToggled.connect(method)
        width, height = self.options['width'], self.options['height']
        self.menu.set_size_values(width, height)
        self.menu.undoRequested.connect(self.undo)
        self.menu.redoRequested.connect(self.redo)
        method = partial(self.create_shape, BUTTON)
        self.menu.addButtonRequested.connect(method)
        method = partial(self.create_shape, TEXT)
        self.menu.addTextRequested.connect(method)
        method = partial(self.create_shape, BACKGROUND, before=True)
        self.menu.addBackgroundRequested.connect(method)
        method = self.set_selection_move_down
        self.menu.moveDownRequested.connect(method)
        method = self.set_selection_move_up
        self.menu.moveUpRequested.connect(method)
        method = self.set_selection_on_top
        self.menu.onTopRequested.connect(method)
        method = self.set_selection_on_bottom
        self.menu.onBottomRequested.connect(method)
        self.menu.symmetryRequested.connect(self.do_symmetry)
        self.menu.searchAndReplaceRequested.connect(self.search_and_replace)
        self.menu.alignRequested.connect(self.align_selection)
        self.menu.load_ui_states()

        set_shortcut("Ctrl+Z", self.shape_editor, self.undo)
        set_shortcut("Ctrl+Y", self.shape_editor, self.redo)
        set_shortcut("Ctrl+C", self.shape_editor, self.copy)
        set_shortcut("Ctrl+V", self.shape_editor, self.paste)
        set_shortcut("Ctrl+R", self.shape_editor, self.search_and_replace)
        set_shortcut("del", self.shape_editor, self.delete_selection)
        set_shortcut("Ctrl+D", self.shape_editor, self.deselect_all)
        set_shortcut("Ctrl+A", self.shape_editor, self.select_all)
        set_shortcut("Ctrl+I", self.shape_editor, self.invert_selection)
        for direction in ['Left', 'Right', 'Up', 'Down']:
            method = partial(self.move_selection, direction)
            shortcut = set_shortcut(direction, self.shape_editor, method)
            shortcut.setAutoRepeat(True)

        self.attribute_editor = AttributeEditor()
        self.attribute_editor.set_generals(self.options)
        self.attribute_editor.generalOptionSet.connect(self.generals_modified)
        self.attribute_editor.optionSet.connect(self.option_set)
        self.attribute_editor.rectModified.connect(self.rect_modified)
        self.attribute_editor.imageModified.connect(self.image_modified)

        self.hlayout = QtWidgets.QHBoxLayout()
        self.hlayout.setSizeConstraint(QtWidgets.QLayout.SetMaximumSize)
        self.hlayout.setContentsMargins(0, 0, 0, 0)
        self.hlayout.addStretch(1)
        self.hlayout.addWidget(self.scrollarea)
        self.hlayout.addStretch(1)
        self.hlayout.addWidget(self.attribute_editor)

        self.vlayout = QtWidgets.QVBoxLayout(self)
        self.vlayout.setContentsMargins(0, 0, 0, 0)
        self.vlayout.setSpacing(0)
        self.vlayout.addWidget(self.menu)
        self.vlayout.addLayout(self.hlayout)

    def copy(self):
        clipboard.set([
            s.options.copy() for s in self.shape_editor.selection])

    def copy_settings(self):
        if len(self.shape_editor.selection) != 1:
            return warning('Copy settings', 'Please select only one shape')
        shape = self.shape_editor.selection[0]
        clipboard.set_settings(shape.options.copy())

    def sizeHint(self):
        return QtCore.QSize(1300, 750)

    def paste(self):
        clipboad_copy = [s.copy() for s in clipboard.get()]
        shape_datas = self.picker_data()['shapes'][:] + clipboad_copy
        picker_data = {
            'general': self.options,
            'shapes': shape_datas}
        self.set_picker_data(picker_data)
        self.undo_manager.set_data_modified(picker_data)
        self.pickerDataModified.emit(picker_data)
        # select new shapes
        shapes = self.shape_editor.shapes[-len(clipboard.get()):]
        self.shape_editor.selection.replace(shapes)
        self.shape_editor.update_selection()
        self.shape_editor.repaint()

    def paste_settings(self):
        dialog = SettingsPaster()
        result = dialog.exec_()
        if result != QtWidgets.QDialog.Accepted:
            return
        settings = clipboard.get_settings()
        settings = {k: v for k, v in settings.items() if k in dialog.settings}
        for shape in self.shape_editor.selection:
            shape.options.update(settings)
        self.shape_editor.repaint()
        self.pickerDataModified.emit(self.picker_data())

    def undo(self):
        result = self.undo_manager.undo()
        if result is False:
            return
        self.update_undo_manager()

    def redo(self):
        self.undo_manager.redo()
        self.update_undo_manager()

    def update_undo_manager(self):
        data = self.undo_manager.data
        self.set_picker_data(data)
        self.pickerDataModified.emit(self.picker_data())

    def deselect_all(self):
        self.shape_editor.selection.clear()
        self.shape_editor.update_selection()
        self.shape_editor.repaint()

    def select_all(self):
        shapes = self.shape_editor.list_shapes()
        self.shape_editor.selection.add(shapes)
        self.shape_editor.update_selection()
        self.shape_editor.repaint()

    def invert_selection(self):
        self.shape_editor.selection.invert(self.shape_editor.shapes)
        if self.menu.lock_bg.isChecked():
            shapes = [
                s for s in self.shape_editor.selection
                if not s.is_background()]
            self.shape_editor.selection.set(shapes)
        self.shape_editor.update_selection()
        self.shape_editor.repaint()

    def set_data_modified(self):
        self.undo_manager.set_data_modified(self.picker_data())
        self.pickerDataModified.emit(self.picker_data())

    def use_snap(self, state):
        snap = self.menu.snap_values() if state else None
        self.shape_editor.transform.snap = snap
        self.shape_editor.repaint()

    def snap_value_changed(self):
        self.shape_editor.transform.snap = self.menu.snap_values()
        self.set_data_modified()
        self.shape_editor.repaint()

    def generals_modified(self, key, value):
        self.options[key] = value
        if key == 'name':
            title = "Picker editor - " + self.options['name']
            self.setWindowTitle(title)
        self.pickerDataModified.emit(self.picker_data())

    def option_set(self, option, value):
        for shape in self.shape_editor.selection:
            shape.options[option] = value
        self.shape_editor.repaint()
        self.set_data_modified()

    def editor_size_changed(self):
        size = self.menu.get_size()
        self.shape_editor.setFixedSize(size)
        self.options['width'] = size.width()
        self.options['height'] = size.height()
        self.set_data_modified()

    def rect_modified(self, option, value):
        shapes = self.shape_editor.selection
        for shape in shapes:
            shape.options[option] = value
            if option == 'shape.height':
                shape.rect.setHeight(value)
                shape.synchronize_image()
                continue

            elif option == 'shape.width':
                shape.rect.setWidth(value)
                shape.synchronize_image()
                continue

            width = shape.rect.width()
            height = shape.rect.height()
            if option == 'shape.left':
                shape.rect.setLeft(value)
            else:
                shape.rect.setTop(value)
            shape.rect.setWidth(width)
            shape.rect.setHeight(height)
            shape.synchronize_image()

        self.update_manipulator_rect()
        self.set_data_modified()

    def selection_changed(self):
        shapes = self.shape_editor.selection
        options = [shape.options for shape in shapes]
        self.attribute_editor.set_options(options)

    def frame_shapes(self):
        shapes = self.shape_editor.shapes
        width = self.options['width']
        height = self.options['height']
        frame_shapes(shapes)
        width = int(ceil(max([max(s.rect.right() for s in shapes), width])))
        height = int(ceil(max([max(s.rect.bottom() for s in shapes), height])))
        self.shape_editor.repaint()
        self.update_manipulator_rect()
        # This mark data as changed, no need to repeat.
        self.menu.set_size_values(width, height)

    def create_shape(self, template, before=False):
        options = template.copy()
        shape = Shape(options)
        shape.rect.moveCenter(self.shape_editor.rect().center())
        shape.synchronize_rect()
        if before is True:
            self.shape_editor.shapes.insert(0, shape)
        else:
            self.shape_editor.shapes.append(shape)
        self.shape_editor.repaint()
        self.set_data_modified()

    def image_modified(self):
        for shape in self.shape_editor.selection:
            shape.synchronize_image()
        self.shape_editor.repaint()

    def set_selection_move_down(self):
        array = self.shape_editor.shapes
        elements = self.shape_editor.selection
        move_down_array_elements(array, elements)
        self.shape_editor.repaint()
        self.set_data_modified()

    def set_selection_move_up(self):
        array = self.shape_editor.shapes
        elements = self.shape_editor.selection
        move_up_array_elements(array, elements)
        self.shape_editor.repaint()
        self.set_data_modified()

    def set_selection_on_top(self):
        array = self.shape_editor.shapes
        elements = self.shape_editor.selection
        self.shape_editor.shapes = move_elements_to_array_end(array, elements)
        self.shape_editor.repaint()
        self.set_data_modified()

    def set_selection_on_bottom(self):
        array = self.shape_editor.shapes
        elements = self.shape_editor.selection
        shapes = move_elements_to_array_begin(array, elements)
        self.shape_editor.shapes = shapes
        self.shape_editor.repaint()
        self.set_data_modified()

    def delete_selection(self):
        for shape in reversed(self.shape_editor.selection.shapes):
            self.shape_editor.shapes.remove(shape)
            self.shape_editor.selection.remove(shape)
        self.update_manipulator_rect()
        self.set_data_modified()

    def update_manipulator_rect(self):
        rects = [shape.rect for shape in self.shape_editor.selection]
        rect = get_combined_rects(rects)
        self.shape_editor.manipulator.set_rect(rect)
        self.shape_editor.repaint()

    def picker_data(self):
        return {
            'general': self.options,
            'shapes': [shape.options for shape in self.shape_editor.shapes]}

    def set_picker_data(self, picker_data, reset_stacks=False):
        self.options = picker_data['general']
        self.shape_editor.options = self.options
        shapes = [Shape(options) for options in picker_data['shapes']]
        self.shape_editor.shapes = shapes
        self.shape_editor.manipulator.set_rect(None)
        self.shape_editor.repaint()
        if reset_stacks is True:
            self.undo_manager.reset_stacks()

    def do_symmetry(self, horizontal=True):
        shapes = self.shape_editor.selection.shapes
        for shape in shapes:
            rect_symmetry(
                rect=shape.rect,
                point=self.shape_editor.manipulator.rect.center(),
                horizontal=horizontal)
            shape.synchronize_rect()
        self.shape_editor.repaint()
        if not cmds.optionVar(query=TRIGGER_REPLACE_ON_MIRROR):
            self.set_data_modified()
            return
        if not self.search_and_replace():
            self.set_data_modified()

    def search_and_replace(self):
        dialog = SearchAndReplaceDialog()
        result = dialog.exec_()
        if result != QtWidgets.QDialog.Accepted:
            return False

        if dialog.filter == 0:  # Search on all shapes.
            shapes = self.shape_editor.shapes
        else:
            shapes = self.shape_editor.selection

        pattern = dialog.search.text()
        replace = dialog.replace.text()

        for s in shapes:
            if not dialog.field:  # Targets
                if not s.targets():
                    continue
                targets = [t.replace(pattern, replace) for t in s.targets()]
                s.options['action.targets'] = targets
                continue

            keys = (['text.content'],
                    ['action.left.command',
                    'action.right.command'],
                    ['image.path'])[dialog.field - 1]

            for key in keys:
                result = s.options[key].replace(pattern, replace)
                s.options[key] = result

        self.set_data_modified()
        self.shape_editor.repaint()
        return True

    def move_selection(self, direction):
        offset = DIRECTION_OFFSETS[direction]
        rects = (s.rect for s in self.shape_editor.selection)
        rects = (s.rect for s in self.shape_editor.selection)
        rect = self.shape_editor.manipulator.rect
        reference_rect = QtCore.QRect(rect)

        self.shape_editor.transform.set_rect(rect)
        self.shape_editor.transform.reference_rect = reference_rect
        self.shape_editor.transform.shift(rects, offset)
        self.shape_editor.manipulator.update_geometries()
        for shape in self.shape_editor.selection:
            shape.synchronize_rect()
        self.shape_editor.repaint()
        self.shape_editor.selectedShapesChanged.emit()
        self.pickerDataModified.emit(self.picker_data())

    def align_selection(self, direction):
        if not self.shape_editor.selection:
            return
        align_shapes(self.shape_editor.selection, direction)
        rects = [s.rect for s in self.shape_editor.selection]
        self.shape_editor.manipulator.set_rect(get_combined_rects(rects))
        self.shape_editor.manipulator.update_geometries()
        self.shape_editor.repaint()
        self.shape_editor.selectedShapesChanged.emit()
        self.pickerDataModified.emit(self.picker_data())