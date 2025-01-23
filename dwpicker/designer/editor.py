from functools import partial
from copy import deepcopy

from PySide2 import QtWidgets, QtCore, QtGui
from maya import cmds

from dwpicker import clipboard
from dwpicker.align import align_shapes, arrange_horizontal, arrange_vertical
from dwpicker.arrayutils import (
    move_elements_to_array_end, move_elements_to_array_begin,
    move_up_array_elements, move_down_array_elements)
from dwpicker.dialog import (
    SearchAndReplaceDialog, warning, SettingsPaster, get_image_path)
from dwpicker.geometry import (
    rect_symmetry, path_symmetry, get_shapes_bounding_rects,
    rect_top_left_symmetry)
from dwpicker.optionvar import BG_LOCKED, TRIGGER_REPLACE_ON_MIRROR
from dwpicker.path import format_path
from dwpicker.qtutils import set_shortcut, get_cursor
from dwpicker.shape import Shape, get_shape_rect_from_options
from dwpicker.stack import count_panels
from dwpicker.templates import BUTTON, TEXT, BACKGROUND

from dwpicker.designer.editarea import ShapeEditArea
from dwpicker.designer.menu import MenuWidget
from dwpicker.designer.attributes import AttributeEditor


DIRECTION_OFFSETS = {
    'Left': (-1, 0), 'Right': (1, 0), 'Up': (0, -1), 'Down': (0, 1)}


class PickerEditor(QtWidgets.QWidget):

    def __init__(self, document, parent=None):
        super(PickerEditor, self).__init__(parent, QtCore.Qt.Window)
        title = "Picker editor - " + document.data['general']['name']
        self.setWindowTitle(title)

        self.document = document
        self.document.shapes_changed.connect(self.update)
        self.document.general_option_changed.connect(self.generals_modified)
        self.document.data_changed.connect(self.update)

        self.shape_editor = ShapeEditArea(self.document)
        self.shape_editor.callContextMenu.connect(self.call_context_menu)
        bg_locked = bool(cmds.optionVar(query=BG_LOCKED))
        self.shape_editor.set_lock_background_shape(bg_locked)
        self.shape_editor.selectedShapesChanged.connect(self.selection_changed)

        self.menu = MenuWidget()
        self.menu.copyRequested.connect(self.copy)
        self.menu.copySettingsRequested.connect(self.copy_settings)
        self.menu.deleteRequested.connect(self.shape_editor.delete_selection)
        self.menu.isolateCurrentPanel.connect(self.isolate_shapes)
        self.menu.pasteRequested.connect(self.paste)
        self.menu.pasteSettingsRequested.connect(self.paste_settings)
        self.menu.snapValuesChanged.connect(self.snap_value_changed)
        self.menu.useSnapToggled.connect(self.use_snap)
        method = self.shape_editor.set_lock_background_shape
        self.menu.lockBackgroundShapeToggled.connect(method)
        self.menu.undoRequested.connect(self.document.undo)
        self.menu.redoRequested.connect(self.document.redo)
        method = partial(self.create_shape, BUTTON)
        self.menu.addButtonRequested.connect(method)
        method = partial(self.create_shape, TEXT)
        self.menu.addTextRequested.connect(method)
        method = partial(self.create_shape, BACKGROUND, before=True, image=True)
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

        set_shortcut("Ctrl+Z", self.shape_editor, self.document.undo)
        set_shortcut("Ctrl+Y", self.shape_editor, self.document.redo)
        set_shortcut("Ctrl+C", self.shape_editor, self.copy)
        set_shortcut("Ctrl+V", self.shape_editor, self.paste)
        set_shortcut("Ctrl+R", self.shape_editor, self.search_and_replace)
        set_shortcut("del", self.shape_editor, self.shape_editor.delete_selection)
        set_shortcut("Ctrl+D", self.shape_editor, self.deselect_all)
        set_shortcut("Ctrl+A", self.shape_editor, self.select_all)
        set_shortcut("Ctrl+I", self.shape_editor, self.invert_selection)
        set_shortcut("F", self.shape_editor, self.shape_editor.focus)
        for direction in ['Left', 'Right', 'Up', 'Down']:
            method = partial(self.move_selection, direction)
            shortcut = set_shortcut(direction, self.shape_editor, method)
            shortcut.setAutoRepeat(True)

        self.attribute_editor = AttributeEditor(self.document)
        self.attribute_editor.optionSet.connect(self.option_set)
        self.attribute_editor.optionsSet.connect(self.options_set)
        self.attribute_editor.imageModified.connect(self.image_modified)
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
        self.shape_editor.update_selection(False)
        self.shape_editor.update()

    def panels_changed(self, panels):
        self.document.data['general']['panels'] = panels

    def panels_resized(self, panels):
        self.document.data['general']['panels'] = panels

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
        clipboad_copy = [deepcopy(s) for s in clipboard.get()]
        shapes = self.document.add_shapes(clipboad_copy)
        self.shape_editor.selection.replace(shapes)
        self.shape_editor.update_selection()
        self.document.record_undo()
        self.document.shapes_changed.emit()

    def paste_settings(self):
        dialog = SettingsPaster()
        if not dialog.exec_():
            return
        settings = clipboard.get_settings()
        settings = {k: v for k, v in settings.items() if k in dialog.settings}
        for shape in self.shape_editor.selection:
            shape.options.update(deepcopy(settings))
            shape.rect = get_shape_rect_from_options(shape.options)
            shape.synchronize_image()
            shape.update_path()
        self.document.record_undo()
        self.document.shapes_changed.emit()
        self.selection_changed()
        self.shape_editor.update_selection()
        self.shape_editor.update()

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

    def use_snap(self, state):
        snap = self.menu.snap_values() if state else None
        self.shape_editor.transform.snap = snap
        self.shape_editor.update()

    def snap_value_changed(self):
        self.shape_editor.transform.snap = self.menu.snap_values()
        self.shape_editor.update()

    def generals_modified(self, _, key):
        if key == 'name':
            title = "Picker editor - " + self.document.data['general']['name']
            self.setWindowTitle(title)

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
        self.document.record_undo()
        self.document.shapes_changed.emit()

    def option_set(self, option, value):
        update_geometries = False
        update_selection = False
        rect_options = (
            'shape.top', 'shape.width', 'shape.height', 'shape.left')

        for shape in self.shape_editor.selection:
            shape.options[option] = value
            if option in ('shape.path', 'shape'):
                if value == 'custom' and not shape.options['shape.path']:
                    update_selection = True
                shape.update_path()
                shape.synchronize_image()
                update_geometries = True

            if option in rect_options:
                shape.rect = QtCore.QRectF(
                    shape.options['shape.left'],
                    shape.options['shape.top'],
                    shape.options['shape.width'],
                    shape.options['shape.height'])
                shape.update_path()
                shape.synchronize_image()
                update_geometries = True

        if update_selection:
            self.selection_changed()
        if update_geometries:
            self.update_manipulator_rect()

        if option == 'visibility_layer':
            self.layers_modified()
        else:
            self.document.shapes_changed.emit()
            self.document.record_undo()
        self.shape_editor.update()

    def selection_changed(self):
        shapes = self.shape_editor.selection
        options = [shape.options for shape in shapes]
        self.attribute_editor.set_options(options)

    def create_shapes(self, targets, use_clipboard_data=False):
        shapes = []
        for target in targets:
            template = deepcopy(BUTTON)
            if use_clipboard_data:
                template.update(deepcopy(clipboard.get_settings()))
            template['action.targets'] = [target]
            shapes.append(Shape(template))
        self.shape_editor.drag_shapes = shapes

    def create_shape(
            self, template, before=False, position=None, targets=None,
            image=False):

        options = deepcopy(template)
        options['panel'] = max((self.shape_editor.current_panel, 0))
        if image:
            filename = get_image_path(self, "Select background image.")
            if filename:
                filename = format_path(filename)
                options['image.path'] = filename
                qimage = QtGui.QImage(filename)
                options['image.width'] = qimage.size().width()
                options['image.height'] = qimage.size().height()
                options['shape.width'] = qimage.size().width()
                options['shape.height'] = qimage.size().height()
                options['bgcolor.transparency'] = 255

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
        self.document.add_shapes([shape.options], prepend=before)
        self.document.shapes_changed.emit()
        self.document.record_undo()

    def update_targets(self, shape):
        shape.set_targets(cmds.ls(selection=True))
        self.shape_editor.update()
        self.document.shapes_changed.emit()
        self.document.record_undo()

    def image_modified(self):
        for shape in self.shape_editor.selection:
            shape.synchronize_image()
        self.shape_editor.update()

    def set_selection_move_on_stack(self, function, inplace=True):
        selected_ids = [s.options['id'] for s in self.shape_editor.selection]
        all_ids = list(self.document.shapes_by_id)
        result = function(all_ids, selected_ids)
        if inplace:
            result = all_ids
        data = [self.document.shapes_by_id[id_].options for id_ in result]
        self.document.set_shapes_data(data)
        self.document.record_undo()
        self.document.shapes_changed.emit()
        self.shape_editor.update()

    def set_selection_move_down(self):
        self.set_selection_move_on_stack(move_down_array_elements, True)

    def set_selection_move_up(self):
        self.set_selection_move_on_stack(move_up_array_elements, True)

    def set_selection_on_top(self):
        self.set_selection_move_on_stack(move_elements_to_array_end, False)

    def set_selection_on_bottom(self):
        self.set_selection_move_on_stack(move_elements_to_array_begin, False)

    def update_manipulator_rect(self):
        rect = get_shapes_bounding_rects(self.shape_editor.selection)
        self.shape_editor.manipulator.set_rect(rect)
        self.shape_editor.update()

    def do_symmetry(self, horizontal=True):
        shapes = self.shape_editor.selection.shapes
        for shape in shapes:
            if shape.options['shape'] == 'custom':
                path_symmetry(
                    path=shape.options['shape.path'],
                    horizontal=horizontal)
                rect_top_left_symmetry(
                    rect=shape.rect,
                    point=self.shape_editor.manipulator.rect.center(),
                    horizontal=horizontal)
                shape.synchronize_rect()
                shape.update_path()
            else:
                rect_symmetry(
                    rect=shape.rect,
                    point=self.shape_editor.manipulator.rect.center(),
                    horizontal=horizontal)
                shape.synchronize_rect()
        self.shape_editor.update()
        self.document.shapes_changed.emit()
        if not cmds.optionVar(query=TRIGGER_REPLACE_ON_MIRROR):
            self.document.record_undo()
            return
        if not self.search_and_replace():
            self.document.record_undo()
        self.attribute_editor.update()
        self.update_manipulator_rect()

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

        self.document.shape_changed.emit()
        self.document.record_undo()
        self.shape_editor.update()
        return True

    def move_selection(self, direction):
        offset = DIRECTION_OFFSETS[direction]
        rect = self.shape_editor.manipulator.rect
        reference_rect = QtCore.QRectF(rect)

        self.shape_editor.transform.set_rect(rect)
        self.shape_editor.transform.reference_rect = reference_rect
        self.shape_editor.transform.shift(
            self.shape_editor.selection.shapes, offset)
        for shape in self.shape_editor.selection:
            shape.synchronize_rect()
            shape.update_path()
        self.shape_editor.update()
        self.selection_changed()
        self.document.record_undo()
        self.document.shapes_changed.emit()

    def align_selection(self, direction):
        if not self.shape_editor.selection:
            return
        align_shapes(self.shape_editor.selection, direction)
        rect = get_shapes_bounding_rects(self.shape_editor.selection)
        self.shape_editor.manipulator.set_rect(rect)
        self.shape_editor.update()
        self.selection_changed()
        self.document.record_undo()
        self.document.shapes_changed.emit()

    def arrange_selection(self, direction):
        if not self.shape_editor.selection:
            return
        if direction == 'horizontal':
            arrange_horizontal(self.shape_editor.selection)
        else:
            arrange_vertical(self.shape_editor.selection)
        rect = get_shapes_bounding_rects(self.shape_editor.selection)
        self.shape_editor.manipulator.set_rect(rect)
        self.shape_editor.update()
        self.selection_changed()
        self.document.record_undo()
        self.document.shapes_changed.emit()

    def call_context_menu(self, position):
        targets = cmds.ls(selection=True)
        button = QtWidgets.QAction('Add selection button', self)
        method = partial(
            self.create_shape, deepcopy(BUTTON),
            position=position, targets=targets)
        button.triggered.connect(method)

        template = deepcopy(BUTTON)
        template.update(clipboard.get_settings())
        method = partial(
            self.create_shape, template,
            position=position, targets=targets)
        text = 'Add selection button (using settings clipboard)'
        button2 = QtWidgets.QAction(text, self)
        button2.triggered.connect(method)

        button3 = QtWidgets.QAction('Add selection multiple buttons', self)
        button3.triggered.connect(partial(self.create_shapes, targets))
        button3.setEnabled(len(targets) > 1)

        text = 'Add selection multiple buttons (using settings clipboard)'
        button4 = QtWidgets.QAction(text, self)
        button4.triggered.connect(partial(self.create_shapes, targets, True))
        button4.setEnabled(len(targets) > 1)

        cursor = get_cursor(self.shape_editor)
        s = self.shape_editor.get_hovered_shape(cursor)
        method = partial(self.update_targets, s)
        text = 'Update targets'
        button5 = QtWidgets.QAction(text, self)
        button5.setEnabled(bool(s))
        button5.triggered.connect(method)

        menu = QtWidgets.QMenu()
        menu.addAction(button)
        menu.addAction(button2)
        menu.addAction(button3)
        menu.addAction(button4)
        menu.addAction(button5)
        menu.addSection('Visibility Layers')

        layers = sorted(list({
            s.visibility_layer()
            for s in self.document.shapes
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
        for i in range(count_panels(self.document.data['general']['panels'])):
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
        self.document.shapes_changed.emit()
        self.document.record_undo()
        self.document.sync_shapes_caches()
        self.shape_editor.update_selection(False)

    def layers_modified(self):
        self.selection_changed()
        model = self.attribute_editor.generals.layers.model
        model.layoutAboutToBeChanged.emit()
        self.document.sync_shapes_caches()
        self.document.record_undo()
        self.document.shapes_changed.emit()
        model.layoutChanged.emit()

    def create_visibility_layer(self):
        text, result = QtWidgets.QInputDialog.getText(
            self, 'Create visibility layer', 'Layer name')
        if not text or not result:
            return

        for shape in self.shape_editor.selection:
            shape.options['visibility_layer'] = text
        self.layers_modified()

    def select_layer(self, layer):
        self.shape_editor.selection.set(self.document.shapes_by_layer[layer])
        self.shape_editor.update_selection()
        self.shape_editor.update()
        self.selection_changed()
