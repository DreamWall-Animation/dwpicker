
from PySide2 import QtWidgets, QtCore
from maya import cmds
from dwpicker.optionvar import (
    save_optionvar, AUTO_FOCUS_ENABLE, DISPLAY_QUICK_OPTIONS,
    NAMESPACE_TOOLBAR, ZOOM_SENSITIVITY, ZOOM_BUTTON)


MAX_SENSITIVITY = 200


class PreferencesWindow(QtWidgets.QWidget):

    def __init__(self, callback=None, parent=None):
        super(PreferencesWindow, self).__init__(parent, QtCore.Qt.Tool)
        self.setWindowTitle("Preferences")
        self.callback = callback

        text = "Display namespace toolbar"
        self.namespace_toolbar = QtWidgets.QCheckBox(text)
        self.quick_options = QtWidgets.QCheckBox("Display quick options")
        self.auto_focus = QtWidgets.QCheckBox("Auto-focus on picker")

        self.ui_group = QtWidgets.QGroupBox("Ui")
        self.ui_layout = QtWidgets.QVBoxLayout(self.ui_group)
        self.ui_layout.addWidget(self.namespace_toolbar)
        self.ui_layout.addWidget(self.quick_options)
        self.ui_layout.addWidget(self.auto_focus)

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
        self.layout.addWidget(self.zoom_group)

        self.load_ui_states()

        self.namespace_toolbar.released.connect(self.save_ui_states)
        self.quick_options.released.connect(self.save_ui_states)
        self.auto_focus.released.connect(self.save_ui_states)
        self.zoom_sensitivity.valueChanged.connect(self.save_ui_states)
        self.zoom_button.currentIndexChanged.connect(self.save_ui_states)

    def load_ui_states(self):
        state = bool(cmds.optionVar(query=NAMESPACE_TOOLBAR))
        self.namespace_toolbar.setChecked(state)
        state = bool(cmds.optionVar(query=DISPLAY_QUICK_OPTIONS))
        self.quick_options.setChecked(state)
        state = bool(cmds.optionVar(query=AUTO_FOCUS_ENABLE))
        self.auto_focus.setChecked(state)

        value = MAX_SENSITIVITY - cmds.optionVar(query=ZOOM_SENSITIVITY)
        self.zoom_sensitivity.setSliderPosition(value)
        value = cmds.optionVar(query=ZOOM_BUTTON)
        self.zoom_button.setCurrentText(value)

    def save_ui_states(self, *_):
        value = int(self.namespace_toolbar.isChecked())
        save_optionvar(NAMESPACE_TOOLBAR, value)
        value = int(self.quick_options.isChecked())
        save_optionvar(DISPLAY_QUICK_OPTIONS, value)
        save_optionvar(AUTO_FOCUS_ENABLE, int(self.auto_focus.isChecked()))
        save_optionvar(ZOOM_BUTTON, self.zoom_button.currentText())
        value = MAX_SENSITIVITY - int(self.zoom_sensitivity.value()) + 1
        save_optionvar(ZOOM_SENSITIVITY, value)
        if self.callback:
            self.callback()
