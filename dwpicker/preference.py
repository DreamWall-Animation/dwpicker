import os
from PySide6 import QtWidgets, QtCore
from maya import cmds
from dwpicker.hotkeyseditor import HotkeysEditor
from dwpicker.optionvar import (
    save_optionvar,
    AUTO_COLLAPSE_IMG_PATH_FROM_ENV, AUTO_FOCUS_BEHAVIOR,
    AUTO_RESIZE_NAMESPACE_COMBO, AUTO_SET_NAMESPACE, AUTO_FOCUS_BEHAVIORS,
    AUTO_SWITCH_TAB, CHECK_IMAGES_PATHS, CUSTOM_PROD_PICKER_DIRECTORY,
    CHECK_FOR_UPDATE, DISPLAY_QUICK_OPTIONS, DISABLE_IMPORT_CALLBACKS,
    OVERRIDE_PROD_PICKER_DIRECTORY_ENV, INSERT_TAB_AFTER_CURRENT,
    NAMESPACE_TOOLBAR, SYNCHRONYZE_SELECTION, TRIGGER_REPLACE_ON_MIRROR,
    USE_BASE64_DATA_ENCODING, USE_PROD_PICKER_DIR_AS_DEFAULT,
    USE_ICON_FOR_UNSAVED_TAB, WARN_ON_TAB_CLOSED, ZOOM_SENSITIVITY,
    ZOOM_BUTTON, ZOOM_BUTTONS)
from dwpicker.path import unix_path


MAX_SENSITIVITY = 500
AUTO_FOCUSES = {
    'Disable': AUTO_FOCUS_BEHAVIORS[0],
    'Bilateral': AUTO_FOCUS_BEHAVIORS[1],
    'From picker to Maya only': AUTO_FOCUS_BEHAVIORS[2]}


class PreferencesWindow(QtWidgets.QWidget):
    need_update_callbacks = QtCore.Signal()
    hotkey_changed = QtCore.Signal()

    def __init__(self, callback=None, parent=None):
        super(PreferencesWindow, self).__init__(parent, QtCore.Qt.Tool)
        self.setWindowTitle("Preferences")
        self.general_preferences = GeneralPreferences(callback)
        self.general_preferences.disable_import_callbacks.released.connect(
            self.need_update_callbacks.emit)
        self.hotkeys_editor = HotkeysEditor()
        self.hotkeys_editor.hotkey_changed.connect(self.hotkey_changed.emit)

        tab = QtWidgets.QTabWidget()
        tab.addTab(self.general_preferences, 'General')
        tab.addTab(self.hotkeys_editor, 'Hotkeys')

        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(tab)


class GeneralPreferences(QtWidgets.QWidget):

    def __init__(self, callback=None, parent=None):
        super(GeneralPreferences, self).__init__(parent)
        self.callback = callback

        text = "Display namespace toolbar."
        self.namespace_toolbar = QtWidgets.QCheckBox(text)
        self.quick_options = QtWidgets.QCheckBox("Display quick options.")
        text = "Auto switch tab with selection."
        self.autoswitch_tab = QtWidgets.QCheckBox(text)
        text = "Auto switch namespace."
        self.autoswitch_namespace = QtWidgets.QCheckBox(text)
        self.sychronize = QtWidgets.QCheckBox("Synchronize picker selection.")
        text = "Auto resize namespace combo."
        self.auto_resize_namespace_combo = QtWidgets.QCheckBox(text)
        self.sychronize = QtWidgets.QCheckBox("Synchronize picker selection.")
        text = "Missing images warning."
        self.check_images_paths = QtWidgets.QCheckBox(text)
        text = "Disable callback at import time. (Use with Studio Library)"
        self.disable_import_callbacks = QtWidgets.QCheckBox(text)
        text = "Use icon to mark unsaved tab."
        self.unsaved_tab_icon = QtWidgets.QCheckBox(text)
        text = "Insert new tab after current tab."
        self.insert_after_current = QtWidgets.QCheckBox(text)
        text = "Warning before closing a tab."
        self.warn_on_tab_close = QtWidgets.QCheckBox(text)
        self.ui_group = QtWidgets.QGroupBox("Ui")
        self.ui_layout = QtWidgets.QVBoxLayout(self.ui_group)
        self.ui_layout.addWidget(self.namespace_toolbar)
        self.ui_layout.addWidget(self.quick_options)
        self.ui_layout.addWidget(self.disable_import_callbacks)
        self.ui_layout.addWidget(self.autoswitch_namespace)
        self.ui_layout.addWidget(self.auto_resize_namespace_combo)
        self.ui_layout.addWidget(self.autoswitch_tab)
        self.ui_layout.addWidget(self.sychronize)
        self.ui_layout.addWidget(self.check_images_paths)
        self.ui_layout.addWidget(self.unsaved_tab_icon)
        self.ui_layout.addWidget(self.insert_after_current)
        self.ui_layout.addWidget(self.warn_on_tab_close)

        notfound = "environment variable not found"
        text = '$DWPICKER_PROJECT_DIRECTORY:{}'.format(
            os.getenv("DWPICKER_PROJECT_DIRECTORY", notfound))
        self.project_dir_env = QtWidgets.QLineEdit(text)
        self.project_dir_env.setReadOnly(True)
        text = (
            "Auto-collapse path with environment "
            "variable $DWPICKER_PROJECT_DIRECTORY")
        self.auto_collapse_path = QtWidgets.QCheckBox(text)
        text = "Override $DWPICKER_PROJECT_DIRECTORY"
        self.override_variable = QtWidgets.QCheckBox(text)
        self.custom_prod_path = QtWidgets.QLineEdit()
        text = "Force file dialog to use this directory"
        self.force_file_dialog_directory = QtWidgets.QCheckBox(text)

        custom_path_layout = QtWidgets.QHBoxLayout()
        custom_path_layout.setContentsMargins(0, 0, 0, 0)
        custom_path_layout.addWidget(self.override_variable)
        custom_path_layout.addWidget(self.custom_prod_path)

        self.env_group = QtWidgets.QGroupBox("Environment Variables")
        self.env_layout = QtWidgets.QVBoxLayout(self.env_group)
        self.env_layout.addWidget(self.project_dir_env)
        self.env_layout.addWidget(self.auto_collapse_path)
        self.env_layout.addLayout(custom_path_layout)
        self.env_layout.addWidget(self.force_file_dialog_directory)

        text = "Encode in-scene data as base64."
        self.use_base64_encoding = QtWidgets.QCheckBox(text)

        self.data_group = QtWidgets.QGroupBox("Data")
        self.data_layout = QtWidgets.QVBoxLayout(self.data_group)
        self.data_layout.addWidget(self.use_base64_encoding)

        self.auto_focus = QtWidgets.QComboBox()
        self.auto_focus.addItems(list(AUTO_FOCUSES))

        self.focus_group = QtWidgets.QGroupBox("Auto-focus")
        self.focus_layout = QtWidgets.QFormLayout(self.focus_group)
        self.focus_layout.addRow("Behavior", self.auto_focus)

        msg = "Prompt search and replace after mirror."
        self.search_on_mirror = QtWidgets.QCheckBox(msg)
        self.advanced_group = QtWidgets.QGroupBox("Advanced editor")
        self.advanced_layout = QtWidgets.QVBoxLayout(self.advanced_group)
        self.advanced_layout.addWidget(self.search_on_mirror)

        self.zoom_sensitivity = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.zoom_sensitivity.setMaximum(MAX_SENSITIVITY)
        self.zoom_sensitivity.setMinimum(1)
        self.zoom_sensitivity.setSingleStep(1)
        self.zoom_button = QtWidgets.QComboBox()
        for item in ZOOM_BUTTONS:
            self.zoom_button.addItem(item)

        self.zoom_group = QtWidgets.QGroupBox("Zoom options")
        self.zoom_layout = QtWidgets.QFormLayout(self.zoom_group)
        self.zoom_layout.addRow("Sensitivity", self.zoom_sensitivity)
        self.zoom_layout.addRow("Mouse button", self.zoom_button)

        msg = "Check for new version at startup."
        self.check_for_update = QtWidgets.QCheckBox(msg)
        self.update_group = QtWidgets.QGroupBox("Update check")
        self.update_layout = QtWidgets.QVBoxLayout(self.update_group)
        self.update_layout.addWidget(self.check_for_update)

        central_widget = QtWidgets.QWidget()
        self.sublayout = QtWidgets.QVBoxLayout(central_widget)
        self.sublayout.addWidget(self.ui_group)
        self.sublayout.addWidget(self.env_group)
        self.sublayout.addWidget(self.data_group)
        self.sublayout.addWidget(self.focus_group)
        self.sublayout.addWidget(self.advanced_group)
        self.sublayout.addWidget(self.zoom_group)
        self.sublayout.addWidget(self.update_group)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(central_widget)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(scroll)

        self.load_ui_states()

        self.auto_collapse_path.released.connect(self.save_ui_states)
        self.autoswitch_tab.released.connect(self.save_ui_states)
        self.autoswitch_namespace.released.connect(self.save_ui_states)
        self.auto_resize_namespace_combo.released.connect(self.save_ui_states)
        self.auto_focus.currentIndexChanged.connect(self.save_ui_states)
        self.check_for_update.released.connect(self.save_ui_states)
        self.check_images_paths.released.connect(self.save_ui_states)
        self.custom_prod_path.textEdited.connect(self.save_ui_states)
        self.disable_import_callbacks.released.connect(self.save_ui_states)
        self.force_file_dialog_directory.released.connect(self.save_ui_states)
        self.override_variable.released.connect(self.save_ui_states)
        self.insert_after_current.released.connect(self.save_ui_states)
        self.quick_options.released.connect(self.save_ui_states)
        self.namespace_toolbar.released.connect(self.save_ui_states)
        self.use_base64_encoding.released.connect(self.save_ui_states)
        self.unsaved_tab_icon.released.connect(self.save_ui_states)
        self.sychronize.released.connect(self.save_ui_states)
        self.search_on_mirror.released.connect(self.save_ui_states)
        self.warn_on_tab_close.released.connect(self.save_ui_states)
        self.zoom_sensitivity.valueChanged.connect(self.save_ui_states)
        self.zoom_button.currentIndexChanged.connect(self.save_ui_states)

    def sizeHint(self):
        return QtCore.QSize(520, 600)

    def load_ui_states(self):
        state = bool(cmds.optionVar(query=AUTO_COLLAPSE_IMG_PATH_FROM_ENV))
        self.auto_collapse_path.setChecked(state)
        value = cmds.optionVar(query=AUTO_FOCUS_BEHAVIOR)
        text = {v: k for k, v in AUTO_FOCUSES.items()}[value]
        self.auto_focus.setCurrentText(text)
        state = bool(cmds.optionVar(query=AUTO_RESIZE_NAMESPACE_COMBO))
        self.auto_resize_namespace_combo.setChecked(state)
        state = bool(cmds.optionVar(query=AUTO_SET_NAMESPACE))
        self.autoswitch_namespace.setChecked(state)
        state = bool(cmds.optionVar(query=AUTO_SWITCH_TAB))
        self.autoswitch_tab.setChecked(state)
        state = bool(cmds.optionVar(query=DISABLE_IMPORT_CALLBACKS))
        self.disable_import_callbacks.setChecked(state)
        value = cmds.optionVar(query=CUSTOM_PROD_PICKER_DIRECTORY)
        self.custom_prod_path.setText(value)
        state = bool(cmds.optionVar(query=CHECK_IMAGES_PATHS))
        self.check_images_paths.setChecked(state)
        state = bool(cmds.optionVar(query=CHECK_FOR_UPDATE))
        self.check_for_update.setChecked(state)
        state = bool(cmds.optionVar(query=USE_PROD_PICKER_DIR_AS_DEFAULT))
        self.force_file_dialog_directory.setChecked(state)
        state = bool(cmds.optionVar(query=OVERRIDE_PROD_PICKER_DIRECTORY_ENV))
        self.override_variable.setChecked(state)
        self.custom_prod_path.setEnabled(state)
        state = bool(cmds.optionVar(query=NAMESPACE_TOOLBAR))
        self.namespace_toolbar.setChecked(state)
        state = bool(cmds.optionVar(query=DISPLAY_QUICK_OPTIONS))
        self.quick_options.setChecked(state)
        state = bool(cmds.optionVar(query=SYNCHRONYZE_SELECTION))
        self.sychronize.setChecked(state)
        state = bool(cmds.optionVar(query=USE_BASE64_DATA_ENCODING))
        self.use_base64_encoding.setChecked(state)
        state = bool(cmds.optionVar(query=USE_ICON_FOR_UNSAVED_TAB))
        self.unsaved_tab_icon.setChecked(state)
        state = bool(cmds.optionVar(query=WARN_ON_TAB_CLOSED))
        self.warn_on_tab_close.setChecked(state)
        state = bool(cmds.optionVar(query=INSERT_TAB_AFTER_CURRENT))
        self.insert_after_current.setChecked(state)
        state = bool(cmds.optionVar(query=TRIGGER_REPLACE_ON_MIRROR))
        self.search_on_mirror.setChecked(state)

        value = MAX_SENSITIVITY - cmds.optionVar(query=ZOOM_SENSITIVITY)
        self.zoom_sensitivity.setSliderPosition(value)
        value = cmds.optionVar(query=ZOOM_BUTTON)
        self.zoom_button.setCurrentText(value)

    def save_ui_states(self, *_):
        value = int(self.auto_collapse_path.isChecked())
        save_optionvar(AUTO_COLLAPSE_IMG_PATH_FROM_ENV, value)
        value = AUTO_FOCUSES[self.auto_focus.currentText()]
        save_optionvar(AUTO_FOCUS_BEHAVIOR, value)
        value = int(self.auto_resize_namespace_combo.isChecked())
        save_optionvar(AUTO_RESIZE_NAMESPACE_COMBO, value)
        value = int(self.autoswitch_namespace.isChecked())
        save_optionvar(AUTO_SET_NAMESPACE, value)
        value = int(self.autoswitch_tab.isChecked())
        save_optionvar(AUTO_SWITCH_TAB, value)
        value = int(self.check_images_paths.isChecked())
        save_optionvar(CHECK_IMAGES_PATHS, value)
        value = int(self.check_for_update.isChecked())
        save_optionvar(CHECK_FOR_UPDATE, value)
        value = unix_path(self.custom_prod_path.text())
        save_optionvar(CUSTOM_PROD_PICKER_DIRECTORY, value)
        value = int(self.insert_after_current.isChecked())
        save_optionvar(INSERT_TAB_AFTER_CURRENT, value)
        value = int(self.disable_import_callbacks.isChecked())
        save_optionvar(DISABLE_IMPORT_CALLBACKS, value)
        value = int(self.force_file_dialog_directory.isChecked())
        save_optionvar(USE_PROD_PICKER_DIR_AS_DEFAULT, value)
        value = self.override_variable.isChecked()
        save_optionvar(OVERRIDE_PROD_PICKER_DIRECTORY_ENV, int(value))
        self.custom_prod_path.setEnabled(value)
        value = int(self.quick_options.isChecked())
        save_optionvar(DISPLAY_QUICK_OPTIONS, value)
        value = int(self.namespace_toolbar.isChecked())
        save_optionvar(NAMESPACE_TOOLBAR, value)
        value = int(self.use_base64_encoding.isChecked())
        save_optionvar(USE_BASE64_DATA_ENCODING, value)
        value = int(self.unsaved_tab_icon.isChecked())
        save_optionvar(USE_ICON_FOR_UNSAVED_TAB, value)
        value = int(self.search_on_mirror.isChecked())
        save_optionvar(TRIGGER_REPLACE_ON_MIRROR, value)
        value = int(self.warn_on_tab_close.isChecked())
        save_optionvar(WARN_ON_TAB_CLOSED, value)
        save_optionvar(ZOOM_BUTTON, self.zoom_button.currentText())
        value = MAX_SENSITIVITY - int(self.zoom_sensitivity.value()) + 1
        save_optionvar(ZOOM_SENSITIVITY, value)
        if self.callback:
            self.callback()
