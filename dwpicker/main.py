# -*- coding: utf-8 -*-
import os
import json
import webbrowser
from copy import deepcopy
from functools import partial

from dwpicker.pyside import QtWidgets, QtCore, QtGui

from maya import cmds
import maya.OpenMaya as om

from dwpicker.appinfos import (
    VERSION, RELEASE_DATE, DW_GITHUB, DW_WEBSITE, PICKER_DOCUMENTATION)
from dwpicker.compatibility import ensure_retro_compatibility
from dwpicker.document import PickerDocument
from dwpicker.designer.editor import PickerEditor
from dwpicker.dialog import (
    question, get_image_path, NamespaceDialog)
from dwpicker.ingest import animschool
from dwpicker.hotkeys import get_hotkeys_config
from dwpicker.namespace import (
    switch_namespace, selected_namespace, detect_picker_namespace,
    pickers_namespaces)
from dwpicker.optionvar import (
    AUTO_FOCUS_BEHAVIOR, AUTO_SWITCH_TAB, AUTO_RESIZE_NAMESPACE_COMBO,
    CHECK_IMAGES_PATHS, AUTO_SET_NAMESPACE, DISABLE_IMPORT_CALLBACKS,
    DISPLAY_HIERARCHY_IN_PICKER, DISPLAY_QUICK_OPTIONS,
    INSERT_TAB_AFTER_CURRENT, LAST_OPEN_DIRECTORY, LAST_IMPORT_DIRECTORY,
    LAST_SAVE_DIRECTORY, NAMESPACE_TOOLBAR, USE_ICON_FOR_UNSAVED_TAB,
    WARN_ON_TAB_CLOSED, save_optionvar, append_recent_filename,
    save_opened_filenames)
from dwpicker.path import get_import_directory, get_open_directory, format_path
from dwpicker.picker import PickerStackedView, list_targets
from dwpicker.preference import PreferencesWindow
from dwpicker.qtutils import set_shortcut, icon, maya_main_window, DockableBase
from dwpicker.quick import QuickOptions
from dwpicker.references import ensure_images_path_exists
from dwpicker.scenedata import (
    load_local_picker_data, store_local_picker_data,
    clean_stray_picker_holder_nodes)
from dwpicker.templates import PICKER, BACKGROUND
from dwpicker.designer.viewportwidget import ui_delete_callback


ABOUT = """\
DreamWall Picker
    Licence MIT
    Version: {version}
    Release date: {release}
    Authors: Lionel Brouyère, Olivier Evers
    Contributor(s):
        Herizo Ran, fabiencollet, c-morten, kalemas (Konstantin Maslyuk),
        Markus Ng, Jerome Drese

Features:
    Animation picker widget.
    Quick picker creation.
    Advanced picker editing.
    Read AnimSchoolPicker files (december 2021 version and latest)
    Free and open source, today and forever.

This tool is a fork of Hotbox Designer (Lionel Brouyère).
A menus, markmenu and hotbox designer cross DCC.
https://github.com/luckylyk/hotbox_designer
""".format(
    version=".".join(str(n) for n in VERSION),
    release=RELEASE_DATE)
WINDOW_TITLE = "DreamWall - Picker"
WINDOW_CONTROL_NAME = "dwPickerWindow"
CLOSE_CALLBACK_COMMAND = "import dwpicker;dwpicker._dwpicker.close_event()"
CLOSE_TAB_WARNING = """\
Close the tab will remove completely the picker data from the scene.
Are you sure to continue ?"""


class DwPicker(DockableBase, QtWidgets.QWidget):
    def __init__(
            self,
            replace_namespace_function=None,
            list_namespaces_function=None):
        super(DwPicker, self).__init__(control_name=WINDOW_CONTROL_NAME)
        self.setWindowTitle(WINDOW_TITLE)
        self.shortcuts = {}
        self.replace_namespace_custom_function = replace_namespace_function
        self.list_namespaces_function = list_namespaces_function

        self.editable = True
        self.callbacks = []
        self.stored_focus = None
        self.editors = []
        self.pickers = []
        self.preferences_window = PreferencesWindow(
            callback=self.load_ui_states, parent=maya_main_window())
        self.preferences_window.need_update_callbacks.connect(
            self.reload_callbacks)
        self.preferences_window.hotkey_changed.connect(self.register_shortcuts)

        self.sub_panels_view = QtWidgets.QToolButton()
        self.sub_panels_view.setCheckable(True)
        self.sub_panels_view.setChecked(True)
        self.sub_panels_view.setIcon(icon("panels.png"))
        self.sub_panels_view.setFixedSize(17, 17)
        self.sub_panels_view.released.connect(self.update_panels_display_mode)
        self.sub_tabs_view = QtWidgets.QToolButton()
        self.sub_tabs_view.setCheckable(True)
        self.sub_tabs_view.setIcon(icon("tabs.png"))
        self.sub_tabs_view.setFixedSize(17, 17)
        self.sub_tabs_view.released.connect(self.update_panels_display_mode)

        self.panel_buttons = QtWidgets.QButtonGroup()
        self.panel_buttons.addButton(self.sub_panels_view, 0)
        self.panel_buttons.addButton(self.sub_tabs_view, 1)

        self.namespace_label = QtWidgets.QLabel("Namespace: ")
        self.namespace_combo = QtWidgets.QComboBox()
        self.namespace_combo.setMinimumWidth(200)
        method = self.change_namespace_combo
        self.namespace_combo.currentIndexChanged.connect(method)
        self.namespace_refresh = QtWidgets.QPushButton("")
        self.namespace_refresh.setIcon(icon("reload.png"))
        self.namespace_refresh.setFixedSize(17, 17)
        self.namespace_refresh.setIconSize(QtCore.QSize(15, 15))
        self.namespace_refresh.released.connect(self.update_namespaces)
        self.namespace_picker = QtWidgets.QPushButton("")
        self.namespace_picker.setIcon(icon("picker.png"))
        self.namespace_picker.setFixedSize(17, 17)
        self.namespace_picker.setIconSize(QtCore.QSize(15, 15))
        self.namespace_picker.released.connect(self.pick_namespace)
        self.namespace_widget = QtWidgets.QWidget()
        self.namespace_layout = QtWidgets.QHBoxLayout(self.namespace_widget)
        self.namespace_layout.setContentsMargins(10, 2, 2, 2)
        self.namespace_layout.setSpacing(0)
        self.namespace_layout.addWidget(self.namespace_label)
        self.namespace_layout.addSpacing(4)
        self.namespace_layout.addWidget(self.namespace_combo)
        self.namespace_layout.addSpacing(2)
        self.namespace_layout.addWidget(self.namespace_refresh)
        self.namespace_layout.addWidget(self.namespace_picker)
        self.namespace_layout.addStretch(1)
        self.namespace_layout.addWidget(self.sub_panels_view)
        self.namespace_layout.addWidget(self.sub_tabs_view)

        self.tab = QtWidgets.QTabWidget()
        self.tab.setTabsClosable(True)
        self.tab.setMovable(True)
        self.tab.tabBar().tabMoved.connect(self.tab_moved)
        self.tab.tabBar().tabBarDoubleClicked.connect(self.change_title)
        self.tab.currentChanged.connect(self.tab_index_changed)
        method = partial(self.close_tab, store=True)
        self.tab.tabCloseRequested.connect(method)

        self.quick_options = QuickOptions()

        self.menubar = DwPickerMenu(parent=self)
        self.menubar.new.triggered.connect(self.call_new)
        self.menubar.open.triggered.connect(self.call_open)
        self.menubar.save.triggered.connect(self.call_save)
        self.menubar.save_as.triggered.connect(self.call_save_as)
        self.menubar.exit.triggered.connect(self.close)
        self.menubar.import_.triggered.connect(self.call_import)
        self.menubar.undo.triggered.connect(self.call_undo)
        self.menubar.redo.triggered.connect(self.call_redo)
        self.menubar.advanced_edit.triggered.connect(self.call_edit)
        self.menubar.preferences.triggered.connect(self.call_preferences)
        self.menubar.change_title.triggered.connect(self.change_title)
        self.menubar.toggle_display.triggered.connect(self.toggle_display_mode)
        method = self.toggle_hierarchy_display
        self.menubar.toggle_hierarchy_display.triggered.connect(method)
        method = self.change_namespace_dialog
        self.menubar.change_namespace.triggered.connect(method)
        self.menubar.add_background.triggered.connect(self.add_background)
        self.menubar.tools.triggered.connect(self.call_tools)
        self.menubar.documentation.triggered.connect(self.call_documentation)
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
        self.register_shortcuts()

    def register_shortcuts(self):
        # Unregister all shortcuts before create new ones
        function_names_actions = {
            'focus': (self.reset, None),
            'new': (self.call_new, self.menubar.new),
            'open': (self.call_open, self.menubar.open),
            'save': (self.call_save, self.menubar.save),
            'close': (self.close, self.menubar.exit),
            'undo': (self.call_undo, self.menubar.undo),
            'redo': (self.call_redo, self.menubar.redo),
            'edit': (self.call_edit, self.menubar.advanced_edit),
            'next_tab': (self.call_next_tab, None),
            'previous_tab': (self.call_previous_tab, None),
            'toggle_display': (
                self.toggle_display_mode, self.menubar.toggle_display),
            'display_hierarchy': (
                self.toggle_hierarchy_display,
                self.menubar.toggle_hierarchy_display)
            }
        for function_name, sc in self.shortcuts.items():
            sc.activated.disconnect(function_names_actions[function_name][0])
            seq = QtGui.QKeySequence()
            action = function_names_actions[function_name][1]
            if not action:
                continue
            action.setShortcut(seq)

        self.shortcuts = {}
        shortcut_context = QtCore.Qt.WidgetWithChildrenShortcut
        for function_name, data in get_hotkeys_config().items():
            if not data['enabled']:
                continue
            method = function_names_actions[function_name][0]
            ks = data['key_sequence']
            if ks is None:
                continue
            sc = set_shortcut(ks, self, method, shortcut_context)
            self.shortcuts[function_name] = sc
            # HACK: Need to implement twice the shortcut to display key
            # sequence in the menu and keep it active when the view is docked.
            action = function_names_actions[function_name][1]
            if action is None:
                continue
            action.setShortcut(ks)
            action.setShortcutContext(shortcut_context)

    def show(self, *args, **kwargs):
        super(DwPicker, self).show(
            closeCallback=CLOSE_CALLBACK_COMMAND, *args, **kwargs)
        self.register_callbacks()

    def close_event(self):
        ui_delete_callback()
        self.preferences_window.close()

    def list_scene_namespaces(self):
        if self.list_namespaces_function:
            ns = self.list_namespaces_function()
        else:
            ns = cmds.namespaceInfo(listOnlyNamespaces=True, recurse=True)
            ns = ns or []
        namespaces = ns + pickers_namespaces(self.pickers)
        return sorted(list(set(namespaces)))

    def update_namespaces(self, *_):
        self.namespace_combo.blockSignals(True)
        self.namespace_combo.clear()
        self.namespace_combo.addItem("*Root*")
        namespaces = self.list_scene_namespaces()
        self.namespace_combo.addItems(namespaces)
        self.namespace_combo.blockSignals(False)

        # Auto update namespace combo to namespace size.
        if not cmds.optionVar(query=AUTO_RESIZE_NAMESPACE_COMBO):
            self.namespace_combo.setSizePolicy(
                QtWidgets.QSizePolicy.MinimumExpanding,
                QtWidgets.QSizePolicy.Minimum)
            self.namespace_combo.setMinimumWidth(200)
            return
        max_width = 0
        for i in range(self.namespace_combo.count()):
            t = self.namespace_combo.itemText(i)
            width = self.namespace_combo.fontMetrics().horizontalAdvance(t)
            max_width = max(max_width, width)
        width = max_width + 20 # padding
        self.namespace_combo.setFixedWidth(max((200, width)))

    def toggle_display_mode(self):
        index = int(not bool(self.panel_buttons.checkedId()))
        self.panel_buttons.button(index).setChecked(True)
        self.update_panels_display_mode()
        self.setFocus()

    def toggle_hierarchy_display(self):
        state = not bool(cmds.optionVar(query=DISPLAY_HIERARCHY_IN_PICKER))
        save_optionvar(DISPLAY_HIERARCHY_IN_PICKER, int(state))
        self.update()
        self.setFocus()

    def update_panels_display_mode(self, *_):
        state = bool(self.panel_buttons.checkedId())
        picker = self.tab.currentWidget()
        if picker is None:
            return
        focused_panel = picker.reset()
        picker.as_sub_tab = state
        picker.create_pickers()
        picker.create_panels(panel=focused_panel)
        QtCore.QTimer.singleShot(10, partial(picker.reset, force_all=True))
        picker.update()

    def tab_index_changed(self, index):
        if not self.pickers:
            return
        picker = self.pickers[index]
        index = int(picker.as_sub_tab)
        self.panel_buttons.button(index).setChecked(True)
        if not picker:
            return
        namespace = detect_picker_namespace(picker.document.shapes)
        self.namespace_combo.blockSignals(True)
        if self.namespace_combo.findText(namespace) == -1 and namespace:
            self.namespace_combo.addItem(namespace)
        if namespace:
            self.namespace_combo.setCurrentText(namespace)
        else:
            self.namespace_combo.setCurrentIndex(0)
        self.namespace_combo.blockSignals(False)

    def tab_moved(self, newindex, oldindex):

        for l in (self.editors, self.pickers):
            l.insert(newindex, l.pop(oldindex))

        self.store_local_pickers_data()

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
        save_opened_filenames([
            p.document.filename for p in self.pickers
            if p.document.filename])

        modified = [p.document.modified_state for p in self.pickers]
        if not any(modified):
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

        save_opened_filenames([p.document.filename for p in self.pickers])
        return super(DwPicker, self).dockCloseEventTriggered()

    def reload_callbacks(self):
        self.unregister_callbacks()
        self.register_callbacks()

    def register_callbacks(self):
        self.unregister_callbacks()
        callbacks = {
            om.MSceneMessage.kBeforeNew: [
                self.close_tabs, self.update_namespaces],
            om.MSceneMessage.kAfterOpen: [
                self.load_saved_pickers, self.update_namespaces],
            om.MSceneMessage.kAfterCreateReference: [
                self.load_saved_pickers, self.update_namespaces]}
        if not cmds.optionVar(query=DISABLE_IMPORT_CALLBACKS):
            callbacks[om.MSceneMessage.kAfterImport] = [
                self.load_saved_pickers, self.update_namespaces]

        for event, methods in callbacks.items():
            for method in methods:
                callback = om.MSceneMessage.addCallback(event, method)
                self.callbacks.append(callback)

        method = self.auto_switch_tab
        cb = om.MEventMessage.addEventCallback('SelectionChanged', method)
        self.callbacks.append(cb)
        method = self.auto_switch_namespace
        cb = om.MEventMessage.addEventCallback('SelectionChanged', method)
        self.callbacks.append(cb)

        for picker in self.pickers:
            picker.register_callbacks()

    def unregister_callbacks(self):
        for cb in self.callbacks:
            om.MMessage.removeCallback(cb)
            self.callbacks.remove(cb)
        for picker in self.pickers:
            picker.unregister_callbacks()

    def auto_switch_namespace(self, *_, **__):
        if not cmds.optionVar(query=AUTO_SET_NAMESPACE):
            return
        self.pick_namespace()

    def auto_switch_tab(self, *_, **__):
        if not cmds.optionVar(query=AUTO_SWITCH_TAB):
            return
        nodes = cmds.ls(selection=True)
        if not nodes:
            return
        picker = self.tab.currentWidget()
        if not picker:
            return
        targets = list_targets(picker.document.shapes)
        if nodes[-1] in targets:
            return
        for i, picker in enumerate(self.pickers):
            if nodes[-1] in list_targets(picker.document.shapes):
                self.tab.setCurrentIndex(i)
                return

    def load_saved_pickers(self, *_, **__):
        self.clear()
        pickers = load_local_picker_data()
        if cmds.optionVar(query=CHECK_IMAGES_PATHS):
            ensure_images_path_exists(pickers)
        for picker in pickers:
            self.add_picker(picker)
        clean_stray_picker_holder_nodes()

    def store_local_pickers_data(self):
        if not self.editable:
            return

        if not self.tab.count():
            store_local_picker_data([])
            return

        pickers = [self.document(i).data for i in range(self.tab.count())]
        store_local_picker_data(pickers)

    def save_tab(self, index):
        msg = (
            'Picker contain unsaved modification !\n'
            'Woud you like to continue ?')
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

    def close_tabs(self, *_):
        for i in range(self.tab.count()-1, -1, -1):
            self.close_tab(i)
        self.store_local_pickers_data()

    def clear(self):
        for i in range(self.tab.count()-1, -1, -1):
            self.close_tab(i, force=True)

    def close_tab(self, index, force=False, store=False):
        if self.document(index).modified_state and force is False:
            if not self.save_tab(index):
                return

        elif (cmds.optionVar(query=WARN_ON_TAB_CLOSED) and
              not question('Warning', CLOSE_TAB_WARNING)):
            return

        editor = self.editors.pop(index)
        if editor:
            editor.close()
        picker = self.pickers.pop(index)
        picker.unregister_callbacks()
        picker.close()
        self.tab.removeTab(index)
        if store:
            self.store_local_pickers_data()

    def load_ui_states(self):
        value = bool(cmds.optionVar(query=DISPLAY_QUICK_OPTIONS))
        self.quick_options.setVisible(value)
        value = bool(cmds.optionVar(query=NAMESPACE_TOOLBAR))
        self.namespace_widget.setVisible(value)
        self.update_namespaces()
        self.update_modified_states()

    def add_picker_from_file(self, filename):
        with open(filename, "r") as f:
            data = ensure_retro_compatibility(json.load(f))
            ensure_images_path_exists([data])
            self.add_picker(data, filename=filename)
        append_recent_filename(filename)

    def reset(self):
        picker = self.tab.currentWidget()
        if picker:
            picker.reset()

    def general_changed(self, origin, option):
        if option == 'name' and origin != 'main_window':
            self.update_names()
        if option == 'panels.as_sub_tab' and origin != 'main_window':
            index = int(self.document().data['general']['panels.as_sub_tab'])
            self.panel_buttons.button(index).setChecked(True)

    def update_names(self):
        for i in range(self.tab.count()):
            self.set_title(i, self.document(i).data['general']['name'])

    def create_picker(self, data):
        document = PickerDocument(data)
        document.changed.connect(self.store_local_pickers_data)
        document.general_option_changed.connect(self.general_changed)
        document.data_changed.connect(self.update_names)
        document.changed.connect(self.update_modified_states)
        picker = PickerStackedView(document, self.editable)
        picker.register_callbacks()
        return picker

    def add_picker(self, data, filename=None, modified_state=False):
        picker = self.create_picker(data)
        picker.document.filename = filename
        picker.document.modified_state = modified_state
        insert = cmds.optionVar(query=INSERT_TAB_AFTER_CURRENT)
        if not insert or self.tab.currentIndex() == self.tab.count() - 1:
            self.pickers.append(picker)
            self.editors.append(None)
            self.tab.addTab(picker, data['general']['name'])
            self.tab.setCurrentIndex(self.tab.count() - 1)
        else:
            index = self.tab.currentIndex() + 1
            self.pickers.insert(index, picker)
            self.editors.insert(index, None)
            self.tab.insertTab(index, picker, data['general']['name'])
            self.tab.setCurrentIndex(index)
        picker.reset(force_all=True)

    def call_open(self):
        filenames = QtWidgets.QFileDialog.getOpenFileNames(
            None, "Open a picker...",
            get_open_directory(),
            filter="Dreamwall Picker (*.json)")[0]
        if not filenames:
            return
        save_optionvar(LAST_OPEN_DIRECTORY, os.path.dirname(filenames[0]))
        for filename in filenames:
            self.add_picker_from_file(filename)
        self.store_local_pickers_data()

    def call_preferences(self):
        self.preferences_window.show()

    def call_save(self, index=None):
        index = self.tab.currentIndex() if type(index) is not int else index
        filename = self.document(index).filename
        if not filename:
            return self.call_save_as(index=index)
        return self.save_picker(index, filename)

    def call_save_as(self, index=None):
        index = self.tab.currentIndex() if type(index) is not int else index
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
        self.document(index).undo()
        self.document(index).changed.emit()

    def call_redo(self):
        index = self.tab.currentIndex()
        if index < 0:
            return
        self.document(index).redo()
        self.document(index).changed.emit()

    def save_picker(self, index, filename):
        self.document(index).filename = filename
        save_optionvar(LAST_SAVE_DIRECTORY, os.path.dirname(filename))
        append_recent_filename(filename)
        with open(filename, 'w') as f:
            json.dump(self.document(index).data, f, indent=2)

        self.set_modified_state(index, False)
        return True

    def call_import(self):
        sources = QtWidgets.QFileDialog.getOpenFileNames(
            None, "Import a picker...",
            get_import_directory(),
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

    def call_new(self):
        self.add_picker({
            'general': deepcopy(PICKER),
            'shapes': []})
        self.store_local_pickers_data()

    def document(self, index=None):
        index = self.tab.currentIndex() if type(index) is not int else index
        if index < 0:
            return None
        picker = self.tab.widget(index)
        return picker.document

    def call_edit(self):
        index = self.tab.currentIndex()
        if index < 0:
            QtWidgets.QMessageBox.warning(self, "Warning", "No picker set")
            return
        if self.editors[index] is None:
            document = self.document()
            editor = PickerEditor(
                document,
                parent=self)
            self.editors[index] = editor

        self.editors[index].show()
        self.editors[index].shape_canvas.focus()

    def call_next_tab(self):
        index = self.tab.currentIndex() + 1
        if index == self.tab.count():
            index = 0
        self.tab.setCurrentIndex(index)

    def call_previous_tab(self):
        index = self.tab.currentIndex() - 1
        if index < 0:
            index = self.tab.count() - 1
        self.tab.setCurrentIndex(index)

    def set_editable(self, state):
        self.editable = state
        self.menubar.set_editable(state)
        for picker in self.pickers:
            picker.editable = state

    def update_modified_states(self):
        for index, picker in enumerate(self.pickers):
            state = picker.document.modified_state
            use_icon = cmds.optionVar(query=USE_ICON_FOR_UNSAVED_TAB)
            icon_ = icon('save.png') if state and use_icon else QtGui.QIcon()
            self.tab.setTabIcon(index, icon_)
            title = self.document(index).data['general']['name']
            title = "*" + title if state and not use_icon else title
            self.tab.setTabText(index, title)

    def set_modified_state(self, index, state):
        """
        Update the tab icon. Add a "save" icon if tab contains unsaved
        modifications.
        """
        if not self.document(index).filename:
            return
        self.document(index).modified_state = state
        use_icon = cmds.optionVar(query=USE_ICON_FOR_UNSAVED_TAB)
        icon_ = icon('save.png') if state and use_icon else QtGui.QIcon()
        self.tab.setTabIcon(index, icon_)
        title = self.document(index).data['general']['name']
        title = "*" + title if state and not use_icon else title
        self.tab.setTabText(index, title)

    def call_tools(self):
        webbrowser.open(DW_GITHUB)

    def call_dreamwall(self):
        webbrowser.open(DW_WEBSITE)

    def call_documentation(self):
        webbrowser.open(PICKER_DOCUMENTATION)

    def call_about(self):
        QtWidgets.QMessageBox.about(self, 'About', ABOUT)

    def sizeHint(self):
        return QtCore.QSize(500, 800)

    def change_title(self, index=None):
        if not self.editable:
            return
        index = (
            self.tab.currentIndex() if not isinstance(index, int) else index)
        if index < 0:
            return
        title, operate = QtWidgets.QInputDialog.getText(
            None, 'Change picker title', 'New title',
            text=self.document(index).data['general']['name'])

        if not operate:
            return
        self.set_title(index, title)
        index = (
            self.tab.currentIndex() if not isinstance(index, int) else index)
        if index < 0:
            return
        document = self.document(index)
        document.data['general']['name'] = title
        document.general_option_changed.emit('main_window', 'name')
        self.document(index).record_undo()
        self.set_title(index, title)

    def set_title(self, index=None, title=''):
        use_icon = cmds.optionVar(query=USE_ICON_FOR_UNSAVED_TAB)
        if not use_icon and self.document(index).modified_state:
            title = "*" + title
        self.tab.setTabText(index, title)

    def change_namespace_dialog(self):
        dialog = NamespaceDialog()
        if not dialog.exec_():
            return
        namespace = dialog.namespace
        self.change_namespace(namespace)

    def change_namespace_combo(self):
        index = self.namespace_combo.currentIndex()
        text = self.namespace_combo.currentText()
        namespace = text if index else ":"
        self.change_namespace(namespace)

    def pick_namespace(self):
        namespace = selected_namespace()
        self.namespace_combo.setCurrentText(namespace)

    def change_namespace(self, namespace):
        document = self.document()
        if not document:
            return
        switch_namespace_function = (
            self.replace_namespace_custom_function or switch_namespace)
        for shape in document.shapes:
            if not shape.targets():
                continue
            targets = [
                switch_namespace_function(t, namespace)
                for t in shape.targets()]
            shape.options['action.targets'] = targets
        document.record_undo()
        document.shapes_changed.emit()

    def add_background(self):
        filename = get_image_path(self)
        if not filename:
            return

        filename = format_path(filename)
        shape = deepcopy(BACKGROUND)
        shape['image.path'] = filename
        image = QtGui.QImage(filename)
        shape['image.width'] = image.size().width()
        shape['image.height'] = image.size().height()
        shape['shape.width'] = image.size().width()
        shape['shape.height'] = image.size().height()
        shape['bgcolor.transparency'] = 255
        self.document().add_shapes([shape], prepend=True)
        self.document().record_undo()
        self.document().shapes_changed.emit()


class DwPickerMenu(QtWidgets.QMenuBar):
    def __init__(self, parent=None):
        super(DwPickerMenu, self).__init__(parent)
        self.new = QtWidgets.QAction('&New', parent)
        self.open = QtWidgets.QAction('&Open', parent)
        self.import_ = QtWidgets.QAction('&Import', parent)
        self.save = QtWidgets.QAction('&Save', parent)
        self.save_as = QtWidgets.QAction('&Save as', parent)
        self.exit = QtWidgets.QAction('Exit', parent)

        self.undo = QtWidgets.QAction('Undo', parent)
        self.redo = QtWidgets.QAction('Redo', parent)

        self.advanced_edit = QtWidgets.QAction('Advanced &editing', parent)
        self.preferences = QtWidgets.QAction('Preferences', parent)
        text = 'Toggle panel display mode'
        self.toggle_display = QtWidgets.QAction(text, parent)
        text = 'Toggle hierarchy display'
        self.toggle_hierarchy_display = QtWidgets.QAction(text, parent)
        self.change_title = QtWidgets.QAction('Change picker title', parent)
        self.change_namespace = QtWidgets.QAction('Change namespace', parent)
        self.add_background = QtWidgets.QAction('Add background item', parent)

        self.documentation = QtWidgets.QAction('Documentation', parent)
        self.tools = QtWidgets.QAction('Other DreamWall &tools', parent)
        self.dw = QtWidgets.QAction('&About DreamWall', parent)
        self.about = QtWidgets.QAction('&About DwPicker', parent)

        self.file = QtWidgets.QMenu('&File', parent)
        self.file.addAction(self.new)
        self.file.addAction(self.open)
        self.file.addAction(self.import_)
        self.file.addSeparator()
        self.file.addAction(self.save)
        self.file.addAction(self.save_as)
        self.file.addSeparator()
        self.file.addAction(self.exit)

        self.edit = QtWidgets.QMenu('&Edit', parent)
        self.edit.addAction(self.undo)
        self.edit.addAction(self.redo)
        self.edit.addSeparator()
        self.edit.addAction(self.advanced_edit)
        self.edit.addAction(self.preferences)
        self.edit.addSeparator()
        self.edit.addAction(self.toggle_display)
        self.edit.addAction(self.toggle_hierarchy_display)
        self.edit.addSeparator()
        self.edit.addAction(self.change_title)
        self.edit.addSeparator()
        self.edit.addAction(self.change_namespace)
        self.edit.addAction(self.add_background)

        self.help = QtWidgets.QMenu('&Help', parent)
        self.help.addAction(self.documentation)
        self.help.addSeparator()
        self.help.addAction(self.tools)
        self.help.addAction(self.dw)
        self.help.addSeparator()
        self.help.addAction(self.about)

        self.addMenu(self.file)
        self.addMenu(self.edit)
        self.addMenu(self.help)

    def set_editable(self, state):
        self.undo.setEnabled(state)
        self.redo.setEnabled(state)
        self.change_title.setEnabled(state)
        self.advanced_edit.setEnabled(state)
        self.add_background.setEnabled(state)
