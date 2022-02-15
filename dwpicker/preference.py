from PySide2 import QtWidgets, QtCore
from maya import cmds
from dwpicker.optionvar import (
    save_optionvar, AUTO_FOCUS_BEHAVIOR, DISPLAY_QUICK_OPTIONS,
    NAMESPACE_TOOLBAR, SYNCHRONYZE_SELECTION, TRIGGER_REPLACE_ON_MIRROR,
    USE_MAYA_COLOR_PICKER, ZOOM_SENSITIVITY, ZOOM_BUTTON)


MAX_SENSITIVITY = 200
AUTO_FOCUSES = {
    'Disable': 'off',
    'Bilateral': 'bilateral',
    'From picker to Maya only': 'pickertomaya'}


class PreferencesWindow(QtWidgets.QWidget):

    def __init__(self, callback=None, parent=None):
        super(PreferencesWindow, self).__init__(parent, QtCore.Qt.Tool)
        self.setWindowTitle("Preferences")
        self.callback = callback

        text = "Display namespace toolbar"
        self.namespace_toolbar = QtWidgets.QCheckBox(text)
        self.quick_options = QtWidgets.QCheckBox("Display quick options")
        self.sychronize = QtWidgets.QCheckBox("Synchronize picker selection")

        self.ui_group = QtWidgets.QGroupBox("Ui")
        self.ui_layout = QtWidgets.QVBoxLayout(self.ui_group)
        self.ui_layout.addWidget(self.namespace_toolbar)
        self.ui_layout.addWidget(self.quick_options)
        self.ui_layout.addWidget(self.sychronize)

        self.auto_focus = QtWidgets.QComboBox()
        self.auto_focus.addItems(list(AUTO_FOCUSES))

        self.focus_group = QtWidgets.QGroupBox("Auto-focus")
        self.focus_layout = QtWidgets.QFormLayout(self.focus_group)
        self.focus_layout.addRow("Behavior", self.auto_focus)

        msg = "Prompt search and replace after mirror"
        self.search_on_mirror = QtWidgets.QCheckBox(msg)
        msg = "Use Maya color picker"
        self.use_maya_color_picker = QtWidgets.QCheckBox(msg)
        self.advanced_group = QtWidgets.QGroupBox("Advanced editor")
        self.advanced_layout = QtWidgets.QVBoxLayout(self.advanced_group)
        self.advanced_layout.addWidget(self.search_on_mirror)
        self.advanced_layout.addWidget(self.use_maya_color_picker)

        self.zoom_sensitivity = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.zoom_sensitivity.setMaximum(MAX_SENSITIVITY)
        self.zoom_sensitivity.setMinimum(1)
        self.zoom_sensitivity.setSingleStep(1)
        self.zoom_button = QtWidgets.QComboBox()
        for item in ["left", "middle", "right"]:
            self.zoom_button.addItem(item)

        self.zoom_group = QtWidgets.QGroupBox("Zoom options")
        self.zoom_layout = QtWidgets.QFormLayout(self.zoom_group)
        self.zoom_layout.addRow("Sensitivity", self.zoom_sensitivity)
        self.zoom_layout.addRow("Mouse button", self.zoom_button)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.ui_group)
        self.layout.addWidget(self.focus_group)
        self.layout.addWidget(self.advanced_group)
        self.layout.addWidget(self.zoom_group)

        self.load_ui_states()

        self.namespace_toolbar.released.connect(self.save_ui_states)
        self.quick_options.released.connect(self.save_ui_states)
        self.auto_focus.currentIndexChanged.connect(self.save_ui_states)
        self.sychronize.released.connect(self.save_ui_states)
        self.search_on_mirror.released.connect(self.save_ui_states)
        self.zoom_sensitivity.valueChanged.connect(self.save_ui_states)
        self.zoom_button.currentIndexChanged.connect(self.save_ui_states)
        self.use_maya_color_picker.released.connect(self.save_ui_states)

    def load_ui_states(self):
        state = bool(cmds.optionVar(query=NAMESPACE_TOOLBAR))
        self.namespace_toolbar.setChecked(state)
        state = bool(cmds.optionVar(query=DISPLAY_QUICK_OPTIONS))
        self.quick_options.setChecked(state)
        state = bool(cmds.optionVar(query=SYNCHRONYZE_SELECTION))
        self.sychronize.setChecked(state)
        value = cmds.optionVar(query=AUTO_FOCUS_BEHAVIOR)
        text = {v: k for k, v in AUTO_FOCUSES.items()}[value]
        self.auto_focus.setCurrentText(text)
        state = cmds.optionVar(query=TRIGGER_REPLACE_ON_MIRROR)
        self.search_on_mirror.setChecked(state)
        state = cmds.optionVar(query=USE_MAYA_COLOR_PICKER)
        self.use_maya_color_picker.setChecked(state)
        value = MAX_SENSITIVITY - cmds.optionVar(query=ZOOM_SENSITIVITY)
        self.zoom_sensitivity.setSliderPosition(value)
        value = cmds.optionVar(query=ZOOM_BUTTON)
        self.zoom_button.setCurrentText(value)

    def save_ui_states(self, *_):
        value = int(self.namespace_toolbar.isChecked())
        save_optionvar(NAMESPACE_TOOLBAR, value)
        value = int(self.quick_options.isChecked())
        save_optionvar(DISPLAY_QUICK_OPTIONS, value)
        save_optionvar(SYNCHRONYZE_SELECTION, int(self.sychronize.isChecked()))
        value = AUTO_FOCUSES[self.auto_focus.currentText()]
        save_optionvar(AUTO_FOCUS_BEHAVIOR, value)
        value = int(self.search_on_mirror.isChecked())
        save_optionvar(TRIGGER_REPLACE_ON_MIRROR, value)
        value = int(self.use_maya_color_picker.isChecked())
        save_optionvar(USE_MAYA_COLOR_PICKER, value)
        save_optionvar(ZOOM_BUTTON, self.zoom_button.currentText())
        value = MAX_SENSITIVITY - int(self.zoom_sensitivity.value()) + 1
        save_optionvar(ZOOM_SENSITIVITY, value)
        if self.callback:
            self.callback()
