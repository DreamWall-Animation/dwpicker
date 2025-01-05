from functools import partial
from copy import deepcopy

from PySide2 import QtWidgets, QtCore
from maya import cmds

from dwpicker import clipboard
from dwpicker.align import align_shapes, arrange_horizontal, arrange_vertical
from dwpicker.arrayutils import (
    move_elements_to_array_end, move_elements_to_array_begin,
    move_up_array_elements, move_down_array_elements)
from dwpicker.dialog import SearchAndReplaceDialog, warning, SettingsPaster
from dwpicker.interactive import Shape, get_shape_rect_from_options
from dwpicker.geometry import get_combined_rects, rect_symmetry, path_symmetry
from dwpicker.optionvar import BG_LOCKED, TRIGGER_REPLACE_ON_MIRROR
from dwpicker.qtutils import set_shortcut, get_cursor
from dwpicker.stack import count_splitters
from dwpicker.templates import BUTTON, TEXT, BACKGROUND

from dwpicker.designer.editarea import ShapeEditArea
from dwpicker.designer.menu import MenuWidget
from dwpicker.designer.attributes import AttributeEditor


DIRECTION_OFFSETS = {
    'Left': (-1, 0), 'Right': (1, 0), 'Up': (0, -1), 'Down': (0, 1)}


class PickerEditor(QtWidgets.QWidget):
    pickerDataModified = QtCore.Signal(object)
    panelsResized = QtCore.Signal(object)
    panelsChanged = QtCore.Signal(object)

    def __init__(self, picker_data, undo_manager, parent=None):
        super(PickerEditor, self).__init__(parent, QtCore.Qt.Window)
        title = "Picker editor - " + picker_data['general']['name']
        self.setWindowTitle(title)
        self.options = picker_data['general']
        self.undo_manager = undo_manager

        self.shape_editor = ShapeEditArea(self.options)
        self.shape_editor.callContextMenu.connect(self.call_context_menu)
        bg_locked = bool(cmds.optionVar(query=BG_LOCKED))
        self.shape_editor.set_lock_background_shape(bg_locked)
        self.set_picker_data(picker_data)
        self.shape_editor.selectedShapesChanged.connect(self.selection_changed)
        method = self.set_data_modified
        self.shape_editor.increaseUndoStackRequested.connect(method)

        self.menu = MenuWidget()
        self.menu.copyRequested.connect(self.copy)
        self.menu.copySettingsRequested.connect(self.copy_settings)
        self.menu.deleteRequested.connect(self.delete_selection)
        self.menu.isolateCurrentPanel.connect(self.isolate_shapes)
        self.menu.pasteRequested.connect(self.paste)
        self.menu.pasteSettingsRequested.connect(self.paste_settings)
        self.menu.snapValuesChanged.connect(self.snap_value_changed)
        self.menu.useSnapToggled.connect(self.use_snap)
        method = self.shape_editor.set_lock_background_shape
        self.menu.lockBackgroundShapeToggled.connect(method)
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
        self.menu.arrangeRequested.connect(self.arrange_selection)
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
        set_shortcut("F", self.shape_editor, self.shape_editor.focus)
        for direction in ['Left', 'Right', 'Up', 'Down']:
            method = partial(self.move_selection, direction)
            shortcut = set_shortcut(direction, self.shape_editor, method)
            shortcut.setAutoRepeat(True)

        self.attribute_editor = AttributeEditor()
        self.attribute_editor.panelsChanged.connect(self.panels_changed)
        self.attribute_editor.panelsResized.connect(self.panels_resized)
        self.attribute_editor.set_generals(self.options)
        self.attribute_editor.generals.set_shapes(self.shape_editor.shapes)
        self.attribute_editor.generalOptionSet.connect(self.generals_modified)
        self.attribute_editor.optionSet.connect(self.option_set)
        self.attribute_editor.optionsSet.connect(self.options_set)
        self.attribute_editor.rectModified.connect(self.rect_modified)
        self.attribute_editor.imageModified.connect(self.image_modified)
        self.attribute_editor.removeLayer.connect(self.remove_layer)
        self.attribute_editor.selectLayerContent.connect(self.select_layer)
        self.attribute_editor.panelSelected.connect(
            self.shape_editor.set_current_panel)
        self.attribute_editor.panelDoubleClicked.connect(
            self.shape_editor.select_panel_shapes)

        self.hlayout = QtWidgets.QHBoxLayout()
        self.hlayout.setSizeConstraint(QtWidgets.QLayout.SetMaximumSize)
        self.hlayout.setContentsMargins(0, 0, 0, 0)
        self.hlayout.addWidget(self.shape_editor)
        self.hlayout.addWidget(self.attribute_editor)

        self.vlayout = QtWidgets.QVBoxLayout(self)
        self.vlayout.setContentsMargins(0, 0, 0, 0)
        self.vlayout.setSpacing(0)
        self.vlayout.addWidget(self.menu)
        self.vlayout.addLayout(self.hlayout)

    def isolate_shapes(self, state):
        self.shape_editor.isolate = state
        self.shape_editor.update()

    def panels_changed(self, panels):
        self.options['panels'] = panels
        self.panelsChanged.emit(self.picker_data())

    def panels_resized(self, panels):
        self.options['panels'] = panels
        self.panelsResized.emit(self.picker_data())

    def copy(self):
        clipboard.set([
            deepcopy(s.options) for s in self.shape_editor.selection])

    def copy_settings(self):
        if len(self.shape_editor.selection) != 1:
            return warning('Copy settings', 'Please select only one shape')
        shape = self.shape_editor.selection[0]
        clipboard.set_settings(deepcopy(shape.options))

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
        self.shape_editor.update()

    def paste_settings(self):
        dialog = SettingsPaster()
        if not dialog.exec_():
            return
        settings = clipboard.get_settings()
        settings = {k: v for k, v in settings.items() if k in dialog.settings}
        for shape in self.shape_editor.selection:
            shape.options.update(settings)
            shape.rect = get_shape_rect_from_options(shape.options)
            shape.synchronize_image()
        self.set_data_modified()
        self.selection_changed()
        self.shape_editor.update_selection()
        self.shape_editor.update()

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
        self.attribute_editor.generals.set_shapes(self.shape_editor.shapes)

    def deselect_all(self):
        self.shape_editor.selection.clear()
        self.shape_editor.update_selection()
        self.shape_editor.update()

    def select_all(self):
        shapes = self.shape_editor.list_shapes()
        self.shape_editor.selection.add(shapes)
        self.shape_editor.update_selection()
        self.shape_editor.update()

    def invert_selection(self):
        self.shape_editor.selection.invert(self.shape_editor.shapes)
        if self.menu.lock_bg.isChecked():
            shapes = [
                s for s in self.shape_editor.selection
                if not s.is_background()]
            self.shape_editor.selection.set(shapes)
        self.shape_editor.update_selection()
        self.shape_editor.update()

    def set_data_modified(self):
        self.undo_manager.set_data_modified(self.picker_data())
        self.pickerDataModified.emit(self.picker_data())

    def use_snap(self, state):
        snap = self.menu.snap_values() if state else None
        self.shape_editor.transform.snap = snap
        self.shape_editor.update()

    def snap_value_changed(self):
        self.shape_editor.transform.snap = self.menu.snap_values()
        self.set_data_modified()
        self.shape_editor.update()

    def generals_modified(self, key, value):
        self.options[key] = value
        if key == 'name':
            title = "Picker editor - " + self.options['name']
            self.setWindowTitle(title)
        self.pickerDataModified.emit(self.picker_data())

    def options_set(self, options, rect_update):
        for shape in self.shape_editor.selection:
            shape.options.update(options)
            if rect_update:
                shape.rect = QtCore.QRectF(
                    options['shape.left'],
                    options['shape.top'],
                    options['shape.width'],
                    options['shape.height'])
                shape.update_path()
        self.shape_editor.update()
        self.update_manipulator_rect()
        self.set_data_modified()

    def option_set(self, option, value):
        for shape in self.shape_editor.selection:
            shape.options[option] = value
        self.shape_editor.update()
        self.set_data_modified()
        if option == 'visibility_layer':
            self.attribute_editor.generals.set_shapes(self.shape_editor.shapes)

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

    def create_shape(
            self, template, before=False, position=None, targets=None):
        options = template.copy()
        options['panel'] = max((self.shape_editor.current_panel, 0))
        shape = Shape(options)
        if not position:
            center = self.shape_editor.rect().center()
            center = self.shape_editor.viewportmapper.to_units_coords(center)
            shape.rect.moveCenter(center)
        else:
            tl = self.shape_editor.viewportmapper.to_units_coords(position)
            shape.rect.moveTopLeft(tl)
        if targets:
            shape.set_targets(targets)
        shape.synchronize_rect()
        shape.update_path()
        if before is True:
            self.shape_editor.shapes.insert(0, shape)
        else:
            self.shape_editor.shapes.append(shape)
        self.shape_editor.update()
        self.set_data_modified()

    def update_targets(self, shape):
        shape.set_targets(cmds.ls(selection=True))
        self.shape_editor.update()
        self.set_data_modified()

    def image_modified(self):
        for shape in self.shape_editor.selection:
            shape.synchronize_image()
        self.shape_editor.update()

    def set_selection_move_down(self):
        array = self.shape_editor.shapes
        elements = self.shape_editor.selection
        move_down_array_elements(array, elements)
        self.shape_editor.update()
        self.set_data_modified()

    def set_selection_move_up(self):
        array = self.shape_editor.shapes
        elements = self.shape_editor.selection
        move_up_array_elements(array, elements)
        self.shape_editor.update()
        self.set_data_modified()

    def set_selection_on_top(self):
        array = self.shape_editor.shapes
        elements = self.shape_editor.selection
        self.shape_editor.shapes = move_elements_to_array_end(array, elements)
        self.shape_editor.update()
        self.set_data_modified()

    def set_selection_on_bottom(self):
        array = self.shape_editor.shapes
        elements = self.shape_editor.selection
        shapes = move_elements_to_array_begin(array, elements)
        self.shape_editor.shapes = shapes
        self.shape_editor.update()
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
        self.shape_editor.update()

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
        self.shape_editor.update()
        if reset_stacks is True:
            self.undo_manager.reset_stacks()

    def do_symmetry(self, horizontal=True):
        shapes = self.shape_editor.selection.shapes
        for shape in shapes:
            rect_symmetry(
                rect=shape.rect,
                point=self.shape_editor.manipulator.rect.center(),
                horizontal=horizontal)
            path_symmetry(
                path=shape.options['shape.path'],
                center=self.shape_editor.manipulator.rect.center(),
                horizontal=horizontal)
            shape.synchronize_rect()
            shape.update_path()
        self.shape_editor.update()
        if not cmds.optionVar(query=TRIGGER_REPLACE_ON_MIRROR):
            self.set_data_modified()
            return
        if not self.search_and_replace():
            self.set_data_modified()

    def search_and_replace(self):
        dialog = SearchAndReplaceDialog()
        if not dialog.exec_():
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

            if dialog.field <= 2:
                key = ('text.content', 'image.path')[dialog.field - 1]
                result = s.options[key].replace(pattern, replace)
                s.options[key] = result
            else:  # Command code
                for command in s.options['action.commands']:
                    result = command['command'].replace(pattern, replace)
                    command['command'] = result

        self.set_data_modified()
        self.shape_editor.update()
        return True

    def move_selection(self, direction):
        offset = DIRECTION_OFFSETS[direction]
        rect = self.shape_editor.manipulator.rect
        reference_rect = QtCore.QRect(rect)

        self.shape_editor.transform.set_rect(rect)
        self.shape_editor.transform.reference_rect = reference_rect
        self.shape_editor.transform.shift(
            self.shape_editor.selection.shapes, offset)
        self.shape_editor.manipulator.update_geometries()
        for shape in self.shape_editor.selection:
            shape.synchronize_rect()
            shape.update_path()
        self.shape_editor.update()
        self.shape_editor.selectedShapesChanged.emit()
        self.pickerDataModified.emit(self.picker_data())

    def align_selection(self, direction):
        if not self.shape_editor.selection:
            return
        align_shapes(self.shape_editor.selection, direction)
        rects = [s.rect for s in self.shape_editor.selection]
        self.shape_editor.manipulator.set_rect(get_combined_rects(rects))
        self.shape_editor.manipulator.update_geometries()
        self.shape_editor.update()
        self.shape_editor.selectedShapesChanged.emit()
        self.pickerDataModified.emit(self.picker_data())

    def arrange_selection(self, direction):
        if not self.shape_editor.selection:
            return
        if direction == 'horizontal':
            arrange_horizontal(self.shape_editor.selection)
        else:
            arrange_vertical(self.shape_editor.selection)
        rects = [s.rect for s in self.shape_editor.selection]
        self.shape_editor.manipulator.set_rect(get_combined_rects(rects))
        self.shape_editor.manipulator.update_geometries()
        self.shape_editor.update()
        self.shape_editor.selectedShapesChanged.emit()
        self.pickerDataModified.emit(self.picker_data())

    def call_context_menu(self, position):
        targets = cmds.ls(selection=True)
        button = QtWidgets.QAction('Add selection button', self)
        method = partial(
            self.create_shape, BUTTON.copy(),
            position=position, targets=targets)
        button.triggered.connect(method)
        template = BUTTON.copy()
        template.update(clipboard.get_settings())
        method = partial(
            self.create_shape, template,
            position=position, targets=targets)
        text = 'Add selection button (using settings clipboard)'
        button2 = QtWidgets.QAction(text, self)
        button2.triggered.connect(method)

        cursor = get_cursor(self.shape_editor)
        s = self.shape_editor.get_hovered_shape(cursor)
        method = partial(self.update_targets, s)
        text = 'Update targets'
        button3 = QtWidgets.QAction(text, self)
        button3.setEnabled(bool(s))
        button3.triggered.connect(method)

        menu = QtWidgets.QMenu()
        menu.addAction(button)
        menu.addAction(button2)
        menu.addAction(button3)
        menu.addSection('Visibility Layers')

        layers = sorted(list({
            s.visibility_layer()
            for s in self.shape_editor.shapes
            if s.visibility_layer()}))

        add_selection = QtWidgets.QMenu('Assign to layer', self)
        add_selection.setEnabled(bool(layers))
        menu.addMenu(add_selection)
        for layer in layers:
            action = QtWidgets.QAction(layer, self)
            action.triggered.connect(partial(self.set_visibility_layer, layer))
            add_selection.addAction(action)

        remove_selection = QtWidgets.QAction('Remove assigned layer', self)
        remove_selection.setEnabled(bool(self.shape_editor.selection.shapes))
        remove_selection.triggered.connect(self.set_visibility_layer)
        menu.addAction(remove_selection)

        create_layer = QtWidgets.QAction('Create layer from selection', self)
        create_layer.triggered.connect(self.create_visibility_layer)
        create_layer.setEnabled(bool(self.shape_editor.selection.shapes))
        menu.addAction(create_layer)

        menu.addSeparator()
        assign_to_panel = QtWidgets.QMenu('Assign to panel', self)
        for i in range(count_splitters(self.options['panels'])):
            action = QtWidgets.QAction(str(i + 1), self)
            action.triggered.connect(partial(self.assign_to_panel, i))
            assign_to_panel.addAction(action)
        menu.addMenu(assign_to_panel)

        menu.exec_(self.shape_editor.mapToGlobal(position))

    def set_visibility_layer(self, layer=''):
        for shape in self.shape_editor.selection:
            shape.options['visibility_layer'] = layer
        self.layers_modified()

    def assign_to_panel(self, panel):
        for shape in self.shape_editor.selection:
            shape.options['panel'] = panel
        self.set_data_modified()

    def layers_modified(self):
        self.set_data_modified()
        self.attribute_editor.generals.set_shapes(self.shape_editor.shapes)
        self.selection_changed()

    def create_visibility_layer(self):
        text, result = QtWidgets.QInputDialog.getText(
            self, 'Create visibility layer', 'Layer name')
        if not text or not result:
            return

        for shape in self.shape_editor.selection:
            shape.options['visibility_layer'] = text
        self.layers_modified()

    def select_layer(self, layer):
        shapes = [
            shape for shape in self.shape_editor.shapes
            if shape.visibility_layer() == layer]
        self.shape_editor.selection.set(shapes)
        self.shape_editor.update_selection()
        self.shape_editor.update()
        self.selection_changed()

    def remove_layer(self, layer):
        for shape in self.shape_editor.shapes:
            if shape.visibility_layer() == layer:
                shape.options['visibility_layer'] = None
        self.layers_modified()
