# -*- coding: utf-8 -*-

from functools import partial
import inspect
import os
import json
import sys
import webbrowser

from PySide2 import QtWidgets, QtCore, QtGui

from maya import cmds
import maya.OpenMaya as om

import dwpicker.designer.editor
from dwpicker.designer.editor import PickerEditor
from dwpicker.dialog import (
    warning, question, CommandButtonDialog, NamespaceDialog)
from dwpicker.ingest import animschool
from dwpicker.interactive import Shape
from dwpicker.optionvar import (
    AUTO_FOCUS_BEHAVIOR, DISPLAY_QUICK_OPTIONS, LAST_OPEN_DIRECTORY,
    LAST_IMPORT_DIRECTORY, LAST_SAVE_DIRECTORY, NAMESPACE_TOOLBAR,
    save_optionvar, append_recent_filename, save_opened_filenames)

from dwpicker.picker import PickerView, detect_picker_namespace
from dwpicker.preference import PreferencesWindow
from dwpicker.qtutils import set_shortcut, icon, DockableBase
from dwpicker.quick import QuickOptions
from dwpicker.scenedata import (
    load_local_picker_data, store_local_picker_data,
    clean_stray_picker_holder_nodes)
from dwpicker.selection import switch_namespace
from dwpicker.templates import BUTTON, PICKER, BACKGROUND
from dwpicker.undo import UndoManager


__version__ = 0, 1, 1
WINDOW_TITLE = "DreamWall - Picker"
RELEASE_DATE = 'January 27th 2022'
DW_WEBSITE = 'https://fr.dreamwall.be/'
DW_GITHUB = 'https://github.com/DreamWall-Animation'
ABOUT = """\
DreamWall Picker
    Licence MIT
    Version: {version}
    Release date: {release}
    Authors: Lionel Brouyère, Olivier Evers
    Contributor(s): Herizoran

Features:
    Animation picker widget.
    Quick picker creation.
    Advanced picker editin.
    Read AnimSchoolPicker files (december 2021 version and latest)
    Free and open source, today and forever.

This tool is a fork of Hotbox Designer (Lionel Brouyère).
A menus, markmenu and hotbox designer cross DCC.
https://github.com/luckylyk/hotbox_designer
""".format(
    version=".".join(str(n) for n in __version__),
    release=RELEASE_DATE)
WINDOW_CONTROL_NAME = "dwPickerWindow"


def build_multiple_shapes(targets, override):
    shapes = [BUTTON.copy() for _ in range(len(targets))]
    for shape, target in zip(shapes, targets):
        if override:
            shape.update(override)
        shape['action.targets'] = [target]
    return [Shape(shape) for shape in shapes]


class DwPicker(DockableBase, QtWidgets.QWidget):
    def __init__(self):
        super(DwPicker, self).__init__(control_name=WINDOW_CONTROL_NAME)
        self.setWindowTitle(WINDOW_TITLE)
        set_shortcut("F", self, self.reset)
        set_shortcut("H", self, self.reset)

        # Set 'Ctrl-[n]': (n in [0-9]) key sequence to set binding to current zoom, centre
        # And set '[n]' key sequence to bind to recall preset that was set
        self.zoom_presets_slots={}
        for item in range(0,10):
            self.zoom_presets_slots[str(item)] =QtWidgets.QAction(self,str(item),self)
            self.zoom_presets_slots[str(item)].setData(str(item))
            self.zoom_presets_slots[str(item)].setText(str(item))
            keyseq="Ctrl+%d"%item
            self.zoom_presets_slots[str(item)].setShortcut(QtGui.QKeySequence(keyseq))
            # set preset setup
            set_shortcut(keyseq, self, self.set_preset)
            # get preset setup
            set_shortcut("%d"%item, self, self.get_preset)

        self.callbacks = []
        self.stored_focus = None
        self.editors = []
        self.generals = []
        self.undo_managers = []
        self.pickers = []
        self.filenames = []
        self.modified_states = []
        self.preferences_window = PreferencesWindow(
            callback=self.load_ui_states, parent=self)

        self.namespace_label = QtWidgets.QLabel("Namespace: ")
        self.namespace_combo = QtWidgets.QComboBox()
        self.namespace_combo.setFixedWidth(235)
        method = self.change_namespace_combo
        self.namespace_combo.currentIndexChanged.connect(method)
        self.namespace_refresh = QtWidgets.QPushButton("")
        self.namespace_refresh.setIcon(icon("reload.png"))
        self.namespace_refresh.setFixedSize(17, 17)
        self.namespace_refresh.setIconSize(QtCore.QSize(15, 15))
        self.namespace_refresh.released.connect(self.update_namespaces)
        self.namespace_widget = QtWidgets.QWidget()
        self.namespace_layout = QtWidgets.QHBoxLayout(self.namespace_widget)
        self.namespace_layout.setContentsMargins(10, 2, 2, 2)
        self.namespace_layout.setSpacing(0)
        self.namespace_layout.addWidget(self.namespace_label)
        self.namespace_layout.addSpacing(4)
        self.namespace_layout.addWidget(self.namespace_combo)
        self.namespace_layout.addSpacing(2)
        self.namespace_layout.addWidget(self.namespace_refresh)
        self.namespace_layout.addStretch(1)

        self.tab = QtWidgets.QTabWidget()
        self.tab.setTabsClosable(True)
        self.tab.setMovable(True)
        self.tab.tabBar().tabMoved.connect(self.tab_moved)
        self.tab.tabBar().tabBarDoubleClicked.connect(self.change_title)
        self.tab.currentChanged.connect(self.tab_index_changed)
        method = partial(self.close_tab, store=True)
        self.tab.tabCloseRequested.connect(method)

        self.quick_options = QuickOptions()

        self.menubar = DwPickerMenu()
        self.menubar.new.triggered.connect(self.call_new)
        self.menubar.new.setShortcut('CTRL+N')
        self.menubar.open.triggered.connect(self.call_open)
        self.menubar.open.setShortcut('CTRL+O')
        self.menubar.save.triggered.connect(self.call_save)
        self.menubar.save.setShortcut('CTRL+S')
        self.menubar.save_as.triggered.connect(self.call_save_as)
        self.menubar.exit.triggered.connect(self.close)
        self.menubar.exit.setShortcut('CTRL+Q')
        self.menubar.import_.triggered.connect(self.call_import)
        self.menubar.undo.triggered.connect(self.call_undo)
        self.menubar.undo.setShortcut('CTRL+Z')
        self.menubar.redo.triggered.connect(self.call_redo)
        self.menubar.redo.setShortcut('CTRL+Y')
        self.menubar.advanced_edit.triggered.connect(self.call_edit)
        self.menubar.advanced_edit.setShortcut('CTRL+E')
        self.menubar.preferences.triggered.connect(self.call_preferences)
        self.menubar.change_title.triggered.connect(self.change_title)
        method = self.change_namespace_dialog
        self.menubar.change_namespace.triggered.connect(method)
        self.menubar.add_background.triggered.connect(self.add_background)
        self.menubar.tools.triggered.connect(self.call_tools)
        self.menubar.dw.triggered.connect(self.call_dreamwall)
        self.menubar.about.triggered.connect(self.call_about)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.setMenuBar(self.menubar)
        self.layout.addWidget(self.namespace_widget)
        self.layout.addWidget(self.tab)
        self.layout.addWidget(self.quick_options)

        self.load_ui_states()

    def show(self, *args, **kwargs):
        super(DwPicker, self).show(*args, **kwargs)
        self.register_callbacks()
        self.load_saved_pickers()

    def update_namespaces(self, *_):
        namespaces = cmds.namespaceInfo(listOnlyNamespaces=True, recurse=True)
        self.namespace_combo.blockSignals(True)
        self.namespace_combo.clear()
        self.namespace_combo.addItem("*Root*")
        self.namespace_combo.addItems(namespaces)
        self.namespace_combo.blockSignals(False)

    def tab_index_changed(self, index):
        if not self.pickers:
            return
        picker = self.pickers[index]
        if not picker:
            return
        namespace = detect_picker_namespace(picker.shapes)
        self.namespace_combo.blockSignals(True)
        if self.namespace_combo.findText(namespace) == -1 and namespace:
            self.namespace_combo.addItem(namespace)
        if namespace:
            self.namespace_combo.setCurrentText(namespace)
        else:
            self.namespace_combo.setCurrentIndex(0)
        self.namespace_combo.blockSignals(False)

    def tab_moved(self, newindex, oldindex):
        lists = (
            self.editors,
            self.generals,
            self.pickers,
            self.filenames,
            self.modified_states)

        for l in lists:
            l.insert(newindex, l.pop(oldindex))

        self.store_local_pickers_data()

    def keyPressEvent(self, event):
        picker = self.tab.currentWidget()
        if not picker:
            return
        picker.keyPressEvent(event)

    def keyReleaseEvent(self, event):
        picker = self.tab.currentWidget()
        if not picker:
            return
        picker.keyReleaseEvent(event)

    def leaveEvent(self, _):
        mode = cmds.optionVar(query=AUTO_FOCUS_BEHAVIOR)
        if mode == 'off':
            return
        cmds.setFocus("MayaWindow")

    def enterEvent(self, _):
        mode = cmds.optionVar(query=AUTO_FOCUS_BEHAVIOR)
        if mode == 'bilateral':
            cmds.setFocus(self.objectName())

    def dockCloseEventTriggered(self):
        save_opened_filenames([fn for fn in self.filenames if fn])
        if not any(self.modified_states):
            return super(DwPicker, self).dockCloseEventTriggered()

        msg = (
            'Some picker have unsaved modification. \n'
            'Would you like to save them ?')
        result = QtWidgets.QMessageBox.question(
            None, 'Save ?', msg,
            buttons=(
                QtWidgets.QMessageBox.SaveAll |
                QtWidgets.QMessageBox.Close),
            button=QtWidgets.QMessageBox.SaveAll)

        if result == QtWidgets.QMessageBox.Close:
            return

        for i in range(self.tab.count()-1, -1, -1):
            self.save_tab(i)

        save_opened_filenames(self.filenames)
        return super(DwPicker, self).dockCloseEventTriggered()

    def register_callbacks(self):
        self.unregister_callbacks()
        callbacks = {
            om.MSceneMessage.kBeforeNew: [
                self.close_tabs, self.update_namespaces],
            om.MSceneMessage.kAfterOpen: [
                self.load_saved_pickers, self.update_namespaces],
            om.MSceneMessage.kAfterImport: [
                self.load_saved_pickers, self.update_namespaces],
            om.MSceneMessage.kAfterCreateReference: [
                self.load_saved_pickers, self.update_namespaces]}

        for event, methods in callbacks.items():
            for method in methods:
                callback = om.MSceneMessage.addCallback(event, method)
                self.callbacks.append(callback)
        for picker in self.pickers:
            picker.register_callbacks()

    def unregister_callbacks(self):
        for cb in self.callbacks:
            om.MMessage.removeCallback(cb)
            self.callbacks.remove(cb)
        for picker in self.pickers:
            picker.unregister_callbacks()

    def load_saved_pickers(self, *_, **__):
        self.clear()
        pickers = load_local_picker_data()
        for picker in pickers:
            self.add_picker(picker)
        clean_stray_picker_holder_nodes()

    def store_local_pickers_data(self):
        if not self.tab.count():
            store_local_picker_data([])
            return
        pickers = [self.picker_data(i) for i in range(self.tab.count())]
        store_local_picker_data(pickers)

    def save_tab(self, index):
        msg = (
            'Picker contain unsaved modification !\n'
            'Would you like to continue ?')
        result = QtWidgets.QMessageBox.question(
            None, 'Save ?', msg,
            buttons=(
                QtWidgets.QMessageBox.Save |
                QtWidgets.QMessageBox.Yes |
                QtWidgets.QMessageBox.Cancel),
            button=QtWidgets.QMessageBox.Cancel)

        if result == QtWidgets.QMessageBox.Cancel:
            return False
        elif result == QtWidgets.QMessageBox.Save and not self.call_save(index):
            return False
        return True

    def restore_session(self):
        self.load_saved_pickers()
        if self.tab.count():
            return
        # No data in the scene, try to set back old session, reopening last
        # used filenames.
        filenames = cmds.optionVar(query=OPENED_FILES).split(';')
        for filename in filenames:
            if not os.path.exists(filename):
                continue
            self.add_picker_from_file(filename)

    def close_tabs(self, *_):
        for i in range(self.tab.count()-1, -1, -1):
            self.close_tab(i)
        self.store_local_pickers_data()

    def clear(self):
        for i in range(self.tab.count()-1, -1, -1):
            self.close_tab(i, force=True)

    def close_tab(self, index, force=False, store=False):
        conditions = (
            self.modified_states[index]
            and force is False
            and not self.save_tab(index))
        if conditions:
            return

        editor = self.editors.pop(index)
        if editor:
            editor.close()
        picker = self.pickers.pop(index)
        picker.unregister_callbacks()
        picker.close()
        self.generals.pop(index)
        self.modified_states.pop(index)
        self.undo_managers.pop(index)
        self.filenames.pop(index)
        self.tab.removeTab(index)
        if store:
            self.store_local_pickers_data()

    def load_ui_states(self):
        value = bool(cmds.optionVar(query=DISPLAY_QUICK_OPTIONS))
        self.quick_options.setVisible(value)
        value = bool(cmds.optionVar(query=NAMESPACE_TOOLBAR))
        self.namespace_widget.setVisible(value)
        self.update_namespaces()

    def add_picker_from_file(self, filename):
        with open(filename, "r") as f:
            self.add_picker(json.load(f), filename=filename)
        append_recent_filename(filename)

    def reset(self):
        picker = self.tab.currentWidget()
        if picker:
            picker.reset()

    def get_preset(self):

        matched_key = None
        for item in range(0,10):
            if self.sender().key() == QtGui.QKeySequence("%d"%item):
                #print ("%s Matched:"% str(item))
                matched_key = "%d"%item

        if matched_key:
            picker = self.tab.currentWidget()
            if picker:
                picker.do_zoom_preset(matched_key)
        else:
            print ("No matched, not calling any presets")

    def set_preset(self):        
        matched_index = -1
        for item in range(0,10):
            if self.sender().key() == QtGui.QKeySequence("Ctrl+%d"%item):
                print ("Ctrl + %s Matched:"% str(item))
                matched_index = item

        picker = self.tab.currentWidget()
        if matched_index !=-1:
            # if it's not -1, assume value is in range (0,10)
            if picker:
                picker.set_preset(str(matched_index))

    def add_picker(self, data, filename=None, modified_state=False):
        picker = PickerView()
        picker.register_callbacks()
        picker.addButtonRequested.connect(self.add_button)
        picker.updateButtonRequested.connect(self.update_button)
        picker.deleteButtonRequested.connect(self.delete_buttons)
        method = partial(self.data_changed_from_picker, picker)
        picker.dataChanged.connect(method)
        shapes = [Shape(s) for s in data['shapes']]
        picker.set_shapes(shapes)
        center = [-data['general']['centerx'], -data['general']['centery']]
        picker.center = center

        # load presets if in json file
        if 'focus_presets' in data:
            focus_presets = data['focus_presets']
            picker.setFocusPresets(focus_presets)

        self.generals.append(data['general'])
        self.pickers.append(picker)
        self.editors.append(None)
        self.undo_managers.append(UndoManager(data))
        self.filenames.append(filename)
        self.modified_states.append(modified_state)

        self.tab.addTab(picker, data['general']['name'])
        self.tab.setCurrentIndex(self.tab.count() - 1)
        picker.reset()

    def call_open(self):
        filenames = QtWidgets.QFileDialog.getOpenFileNames(
            None, "Open a picker...",
            cmds.optionVar(query=LAST_OPEN_DIRECTORY),
            filter="Dreamwall Picker (*.json)")[0]
        if not filenames:
            return
        save_optionvar(LAST_OPEN_DIRECTORY, os.path.dirname(filenames[0]))
        for filename in filenames:
            self.add_picker_from_file(filename)
            self.filenames.append(filename)
        self.store_local_pickers_data()

    def call_preferences(self):
        self.preferences_window.show()

    def call_save(self, index=None):
        index = index if index is not None else self.tab.currentIndex()
        filename = self.filenames[index]
        if not filename:
            return self.call_save_as(index=index)
        self.save_picker(index, filename)

    def call_save_as(self, index=None):
        index = index if index is not None else self.tab.currentIndex()
        filename = QtWidgets.QFileDialog.getSaveFileName(
            None, "Save a picker ...",
            cmds.optionVar(query=LAST_SAVE_DIRECTORY),
            filter="Dreamwall Picker (*.json)")[0]

        if not filename:
            return False

        if os.path.exists(filename):
            msg = '{} already, exists. Do you want to erase it ?'
            if not question('File exist', msg.format(filename)):
                return False

        self.save_picker(index, filename)

    def call_undo(self):
        index = self.tab.currentIndex()
        if index < 0:
            return
        undo_manager = self.undo_managers[index]
        undo_manager.undo()
        self.data_changed_from_undo_manager(index)

    def call_redo(self):
        index = self.tab.currentIndex()
        if index < 0:
            return
        undo_manager = self.undo_managers[index]
        undo_manager.redo()
        self.data_changed_from_undo_manager(index)

    def save_picker(self, index, filename):
        self.filenames[index] = filename
        save_optionvar(LAST_SAVE_DIRECTORY, os.path.dirname(filename))
        append_recent_filename(filename)
        with open(filename, 'w') as f:
            json.dump(self.picker_data(index), f, indent=2)

        self.set_modified_state(index, False)
        return True

    def call_import(self):
        sources = QtWidgets.QFileDialog.getOpenFileNames(
            None, "Import a picker...",
            cmds.optionVar(query=LAST_IMPORT_DIRECTORY),
            filter="Anim School Picker (*.pkr)")[0]
        if not sources:
            return

        dst = QtWidgets.QFileDialog.getExistingDirectory(
            None,
            "Conversion destination",
            os.path.dirname(sources[0]),
            options=QtWidgets.QFileDialog.ShowDirsOnly)
        if not dst:
            return

        save_optionvar(LAST_IMPORT_DIRECTORY, os.path.dirname(sources[0]))
        for src in sources:
            filename = animschool.convert(src, dst)
            self.add_picker_from_file(filename)
            self.filenames.append(filename)

    def call_new(self):
        self.add_picker({
            'general': PICKER.copy(),
            'shapes': [],
        })
        self.filenames.append(None)
        self.store_local_pickers_data()

    def picker_data(self, index=None):
        index = index if index is not None else self.tab.currentIndex()
        picker = self.tab.widget(index)
        return {
            'version': __version__,
            'general': self.generals[index],
            'shapes': [shape.options for shape in picker.shapes],
            'focus_presets': picker.d_focus_presets,
        }

    def call_edit(self):
        index = self.tab.currentIndex()
        if index < 0:
            QtWidgets.QMessageBox.warning(self, "Warning", "No picker set")
            return
        if self.editors[index] is None:
            data = self.picker_data()
            undo_manager = self.undo_managers[index]
            editor = PickerEditor(
                picker_data=data,
                undo_manager=undo_manager,
                parent=self)
            picker = self.pickers[index]
            method = partial(self.data_changed_from_editor, picker=picker)
            editor.pickerDataModified.connect(method)
            self.editors[index] = editor

        self.editors[index].show()

    def set_modified_state(self, index, state):
        """
        Update the tab icon. Add a "save" icon if tab contains unsaved
        modifications.
        """
        if not self.filenames[index]:
            return
        self.modified_states[index] = state
        icon_ = icon('save.png') if state else QtGui.QIcon()
        self.tab.setTabIcon(index, icon_)

    def call_tools(self):
        webbrowser.open(DW_GITHUB)

    def call_dreamwall(self):
        webbrowser.open(DW_WEBSITE)

    def call_about(self):
        QtWidgets.QMessageBox.about(self, 'About', ABOUT)

    def sizeHint(self):
        return QtCore.QSize(500, 800)

    def add_button(self, x, y, button_type):
        targets = cmds.ls(sl=True)
        if not targets and button_type <= 1:
            return warning("Warning", "No targets selected")

        if button_type == 1:
            overrides = self.quick_options.values
            shapes = build_multiple_shapes(targets, overrides)
            if not shapes:
                return
            picker = self.tab.currentWidget()
            picker.drag_shapes = shapes
            return

        data = BUTTON.copy()
        data['shape.left'] = x
        data['shape.top'] = y
        data.update(self.quick_options.values)
        if button_type == 0:
            data['action.targets'] = targets
        else:
            dialog = CommandButtonDialog()
            result = dialog.exec_()
            if result != QtWidgets.QDialog.Accepted:
                return
            data.update(dialog.values)

        width = max([data['shape.width'], len(data['text.content']) * 7])
        data['shape.width'] = width
        self.add_shape_to_current_picker(Shape(data))

    def update_button(self, shape):
        picker = self.tab.currentWidget()
        shape.set_targets(cmds.ls(selection=True))
        self.data_changed_from_picker(picker)

    def delete_buttons(self):
        picker = self.tab.currentWidget()
        selected_shapes = [s for s in picker.shapes if s.selected]
        for shape in selected_shapes:
            picker.shapes.remove(shape)
        self.data_changed_from_picker(picker)

    def add_shape_to_current_picker(self, shape, prepend=False):
        picker = self.tab.currentWidget()
        if prepend:
            picker.shapes.insert(0, shape)
        else:
            picker.shapes.append(shape)
        self.data_changed_from_picker(picker)

    def data_changed_from_picker(self, picker):
        index = self.tab.indexOf(picker)
        data = self.picker_data(index)
        if self.editors[index]:
            self.editors[index].set_picker_data(data)
        self.set_modified_state(index, True)
        picker.repaint()
        self.undo_managers[index].set_data_modified(data)
        self.store_local_pickers_data()

    def data_changed_from_editor(self, data, picker):
        shapes = [Shape(s) for s in data['shapes']]
        picker.set_shapes(shapes)
        index = self.tab.indexOf(picker)
        self.generals[index] = data['general']
        center = [-data['general']['centerx'], -data['general']['centery']]
        picker.center = center
        self.set_modified_state(index, True)
        self.store_local_pickers_data()

    def data_changed_from_undo_manager(self, index):
        data = self.undo_managers[index].data
        if self.editors[index]:
            self.editors[index].set_picker_data(data)
        self.data_changed_from_editor(data, self.pickers[index])

    def change_title(self, index=None):
        index = index if index is not None else self.tab.currentIndex()
        if index < 0:
            return
        title, operate = QtWidgets.QInputDialog.getText(
            None, 'Change picker title', 'New title')

        if not operate:
            return

        self.generals[index]['name'] = title
        self.tab.setTabText(index, title)
        self.data_changed_from_picker(self.tab.widget(index))

    def change_namespace_dialog(self):
        dialog = NamespaceDialog()
        result = dialog.exec_()
        if result != QtWidgets.QDialog.Accepted:
            return
        namespace = dialog.namespace
        self.change_namespace(namespace)

    def change_namespace_combo(self):
        index = self.namespace_combo.currentIndex()
        text = self.namespace_combo.currentText()
        namespace = text if index else ":"
        self.change_namespace(namespace)

    def change_namespace(self, namespace):
        picker = self.tab.currentWidget()
        for shape in picker.shapes:
            if not shape.targets():
                continue
            targets = [switch_namespace(t, namespace) for t in shape.targets()]
            shape.options['action.targets'] = targets

        self.data_changed_from_picker(picker)

    def add_background(self):
        msg = 'Select image ..'
        filename = QtWidgets.QFileDialog.getOpenFileName(self, msg)[0]
        if not filename:
            return

        shape = BACKGROUND.copy()
        shape['image.path'] = filename
        image = QtGui.QImage(filename)
        shape['image.width'] = image.size().width()
        shape['image.height'] = image.size().height()
        shape['shape.width'] = image.size().width()
        shape['shape.height'] = image.size().height()
        shape['bgcolor.transparency'] = 255
        shape = Shape(shape)
        self.add_shape_to_current_picker(shape, prepend=True)


class DwPickerMenu(QtWidgets.QMenuBar):
    def __init__(self, parent=None):
        super(DwPickerMenu, self).__init__(parent)

        self.new = QtWidgets.QAction('&New', self)
        self.open = QtWidgets.QAction('&Open', self)
        self.import_ = QtWidgets.QAction('&Import', self)
        self.save = QtWidgets.QAction('&Save', self)
        self.save_as = QtWidgets.QAction('&Save as', self)
        self.exit = QtWidgets.QAction('Exit', self)

        self.undo = QtWidgets.QAction('Undo', self)
        self.redo = QtWidgets.QAction('Redo', self)

        self.advanced_edit = QtWidgets.QAction('Advanced &editing', self)
        self.preferences = QtWidgets.QAction('Preferences', self)
        self.change_title = QtWidgets.QAction('Change picker title', self)
        self.change_namespace = QtWidgets.QAction('Change namespace', self)
        self.add_background = QtWidgets.QAction('Add background item', self)

        self.tools = QtWidgets.QAction('Other DreamWall &tools', self)
        self.dw = QtWidgets.QAction('&About DreamWall', self)
        self.about = QtWidgets.QAction('&About DwPicker', self)

        self.file = QtWidgets.QMenu('&File', self)
        self.file.addAction(self.new)
        self.file.addAction(self.open)
        self.file.addAction(self.import_)
        self.file.addSeparator()
        self.file.addAction(self.save)
        self.file.addAction(self.save_as)
        self.file.addSeparator()
        self.file.addAction(self.exit)

        self.edit = QtWidgets.QMenu('&Edit', self)
        self.edit.addAction(self.undo)
        self.edit.addAction(self.redo)
        self.edit.addSeparator()
        self.edit.addAction(self.advanced_edit)
        self.edit.addAction(self.preferences)
        self.edit.addSeparator()
        self.edit.addAction(self.change_title)
        self.edit.addSeparator()
        self.edit.addAction(self.change_namespace)
        self.edit.addAction(self.add_background)

        self.help = QtWidgets.QMenu('&Help', self)
        self.help.addAction(self.tools)
        self.help.addAction(self.dw)
        self.help.addSeparator()
        self.help.addAction(self.about)

        self.addMenu(self.file)
        self.addMenu(self.edit)
        self.addMenu(self.help)
