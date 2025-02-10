import os
import sys
import uuid

import maya.OpenMayaUI as omui
from maya import cmds
from maya import mel

from dwpicker.capture import snap
from dwpicker.pyside import QtWidgets, QtCore, QtGui
from dwpicker.pyside import shiboken2
from dwpicker.qtutils import icon
from dwpicker.templates import BACKGROUND

if sys.version_info[0] == 3:
    long = int

IMAGE_SIZE_PRESETS = {
    "Default": {"width": 960, "height": 540},
    "1080x1080": {"width": 1080, "height": 1080},
    "720x1000": {"width": 720, "height": 1000},
    "720x1280": {"width": 720, "height": 1280},
    "1080x1350": {"width": 1080, "height": 1350},
    "1080x1920": {"width": 1080, "height": 1920},
    "1280x720": {"width": 1280, "height": 720},
    "1920x1080": {"width": 1920, "height": 1080},
    "Custom": {"width": None, "height": None}
}


class ViewportWidget(QtWidgets.QWidget):
    def __init__(self, editor, parent=None):
        super(ViewportWidget, self).__init__(parent)

        self.editor = editor

        self.setObjectName("ViewportWidget")
        self.resize(320, 620)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 0, 0, 0)
        self.main_layout.setObjectName("ViewportPickerLayout")

        layout = omui.MQtUtil.fullName(long(shiboken2.getCppPointer(
            self.main_layout)[0]))
        cmds.setParent(layout)
        panel_layout_name = cmds.paneLayout()

        ptr = omui.MQtUtil.findControl(panel_layout_name)
        self.panel_layout = shiboken2.wrapInstance(long(ptr),
                                                   QtWidgets.QWidget)

        cameras = cmds.ls(type="camera")
        cameras = [cmds.listRelatives(cam, parent=True)[0] for cam in
                   cameras]

        picker_model_name = "PickerModelPanel" + str(uuid.uuid4())[:4]
        self.camera_name = "front"

        if not self.camera_name in cameras:
            camera_ = cmds.camera(n=self.camera_name)[0]
            cmds.rename(camera_, self.camera_name)

        self.model_panel_name = cmds.modelPanel(picker_model_name, mbv=False)
        cmds.modelEditor(self.model_panel_name,
                         edit=True,
                         displayAppearance='smoothShaded',
                         cam=self.camera_name,
                         gr=True)

        ptr = omui.MQtUtil.findControl(self.model_panel_name)
        self.model_panel_widget = shiboken2.wrapInstance(long(ptr),
                                                         QtWidgets.QWidget)

        self.cam_label = QtWidgets.QLabel("Cam")

        camera_combo_box = QtWidgets.QComboBox()
        camera_combo_box.setToolTip("Cameras")
        camera_combo_box.addItems(cameras)
        camera_combo_box.currentTextChanged.connect(
            lambda: self.update_camera_viewport(camera_combo_box,
                                                picker_model_name))

        self.lock_toggle = QtWidgets.QAction(icon('lock.png'), '', self)
        self.lock_toggle.setToolTip("Toggle lock camera")
        self.lock_toggle.triggered.connect(
            lambda: toggle_camera_settings(picker_model_name,
                                           self.camera_name, "lock_camera"))

        self.camera_toggle = QtWidgets.QAction(icon('camera.png'), '', self)
        self.camera_toggle.setToolTip("Toggle orthographic view")
        self.camera_toggle.triggered.connect(
            lambda: toggle_camera_view(self.camera_name))

        self.grid_toggle = QtWidgets.QAction(icon('grid.png'), '', self)
        self.grid_toggle.setToolTip("Toggle grid view")
        self.grid_toggle.triggered.connect(
            lambda: toggle_grid_view(picker_model_name))

        self.field_toggle = QtWidgets.QAction(icon('fieldChart.png'), '', self)
        self.field_toggle.setToolTip("Toggle field chart")
        self.field_toggle.triggered.connect(
            lambda: toggle_camera_settings(picker_model_name,
                                           self.camera_name, "field_chart"))

        self.resolution_toggle = QtWidgets.QAction(icon('resolutionGate.png'),
                                                   '', self)
        self.resolution_toggle.setToolTip("Toggle resolution")
        self.resolution_toggle.triggered.connect(
            lambda: toggle_camera_settings(picker_model_name,
                                           self.camera_name, "resolution"))

        image_size_combo_box = QtWidgets.QComboBox(self)
        image_size_combo_box.setToolTip("Image sizes")
        image_size_combo_box.setMaximumWidth(85)
        for resolution in IMAGE_SIZE_PRESETS:
            image_size_combo_box.addItem(resolution)
        image_size_combo_box.currentTextChanged.connect(
            lambda: self.update_resolution_settings(image_size_combo_box,
                                                    IMAGE_SIZE_PRESETS))

        self.width_input = QtWidgets.QLineEdit()
        self.width_input.setMaximumWidth(35)
        self.width_input.setValidator(QtGui.QIntValidator(self))
        self.width_input.setVisible(False)
        self.height_input = QtWidgets.QLineEdit()
        self.height_input.setMaximumWidth(35)
        self.height_input.setValidator(QtGui.QIntValidator(self))
        self.height_input.setVisible(False)
        self.width_input.editingFinished.connect(
            lambda: self.update_resolution_settings(image_size_combo_box,
                                                    IMAGE_SIZE_PRESETS,
                                                    self.width_input,
                                                    self.height_input))
        self.height_input.editingFinished.connect(
            lambda: self.update_resolution_settings(image_size_combo_box,
                                                    IMAGE_SIZE_PRESETS,
                                                    self.width_input,
                                                    self.height_input))

        self.snapshot = QtWidgets.QAction(icon('snapshot.png'), '', self)
        self.snapshot.setToolTip("Capture snapshot")
        self.snapshot.triggered.connect(
            lambda: capture_snapshot(self, camera_combo_box))

        self.toolbar = QtWidgets.QToolBar()
        self.toolbar.setIconSize(QtCore.QSize(14, 14))
        toolbar_layout = self.toolbar.layout()
        toolbar_layout.setSpacing(0)
        self.toolbar.addWidget(self.cam_label)
        self.toolbar.addWidget(camera_combo_box)
        self.toolbar.addAction(self.lock_toggle)
        self.toolbar.addAction(self.camera_toggle)
        self.toolbar.addAction(self.grid_toggle)
        self.toolbar.addAction(self.field_toggle)
        self.toolbar.addAction(self.resolution_toggle)
        self.toolbar.addWidget(image_size_combo_box)
        self.width_action = self.toolbar.addWidget(self.width_input)
        self.height_action = self.toolbar.addWidget(self.height_input)
        self.toolbar.addAction(self.snapshot)

        self.main_layout.setSpacing(0)
        self.main_layout.addWidget(self.toolbar)
        self.main_layout.addWidget(self.panel_layout)

    def showEvent(self, event):
        super(ViewportWidget, self).showEvent(event)
        self.model_panel_widget.repaint()

    def add_snapshot_image(self, file=None):
        if os.path.exists(file):
            self.editor.create_shape(BACKGROUND, before=True, image=True,
                                     filepath=file)

    def update_camera_viewport(self, combo_box, panel):
        """
        Update the camera in the active panel when a new camera is selected from the combo box.
        """
        active_camera = combo_box.currentText()
        cmds.modelPanel(panel, edit=True, camera=active_camera)
        self.camera_name = active_camera

    def update_resolution_settings(self, combobox, image_size,
                                   custom_width=None,
                                   custom_height=None):
        resolution = combobox.currentText()

        if resolution == "Custom":
            self.width_action.setVisible(True)
            self.height_action.setVisible(True)
        else:
            self.width_action.setVisible(False)
            self.height_action.setVisible(False)

        width = image_size[resolution]["width"]
        height = image_size[resolution]["height"]

        if not (width and height):
            if not (custom_width and custom_height):
                return
            if not custom_width.text():
                return
            if not custom_height.text():
                return

            width = int(custom_width.text())
            height = int(custom_height.text())

        try:
            device_aspect_ratio = round(width / height, 3)
        except ZeroDivisionError:
            raise ZeroDivisionError("Height cannot be Zero")

        cmds.setAttr("defaultResolution.width", width)
        cmds.setAttr("defaultResolution.height", height)
        cmds.setAttr("defaultResolution.deviceAspectRatio",
                     device_aspect_ratio)
        cmds.setAttr("defaultResolution.pixelAspect", 1)


class NotificationWidget(QtWidgets.QLabel):
    def __init__(self, parent=None, message="Notification", duration=2000):
        super(NotificationWidget, self).__init__(parent)
        self.setText(message)
        self.setStyleSheet("""
            background-color: grey;
            color: white;
            border-radius: 4px; 
            font-size: 14px;
            font-weight: bold;
        """)
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(140, 30)

        parent_rect = parent.rect()
        self.move(
            (parent_rect.width() - self.width()) // 2,
            140
        )

        self.timer = QtCore.QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.deleteLater)

        self.show()
        self.timer.start(duration)

    @staticmethod
    def show_notification(parent, message="Notification", duration=2000):
        NotificationWidget(parent, message, duration)


def ui_delete_callback():
    panels = cmds.getPanel(type="modelPanel")
    for panel in panels:
        if panel.startswith('PickerModelPanel') and cmds.modelPanel(
                panel,
                exists=True):
            cmds.deleteUI(panel, panel=True)


def toggle_grid_view(panel):
    current_grid_state = cmds.modelEditor(panel, query=True, grid=True)
    set_state = not current_grid_state
    cmds.modelEditor(panel, edit=True, grid=set_state)


def toggle_camera_view(camera_name):
    """
    Adjusts the camera view based on its type (perspective or orthographic).

    Args:
        camera_name (str): The name of the camera to adjust.
    """
    is_perspective = not cmds.camera(camera_name, query=True,
                                     orthographic=True)
    up_dir = cmds.camera(camera_name, query=True, worldUp=True)

    camera_view = {"o": True} if is_perspective else {"p": True}
    cmds.viewPlace(camera_name, up=(up_dir[0], up_dir[1], up_dir[2]),
                   **camera_view)


def toggle_camera_settings(panel, camera_name="persp", option="resolution"):
    """
    Toggles the camera settings based on the option specified.

    - 'resolution' toggles the camera resolution (displayResolution and overscan).
    - 'field_chart' toggles the field chart display.
    """

    if option == "lock_camera":
        mel.eval("changeCameraLockStatus" + " %s;" % panel)

    if option == "resolution":
        display_resolution = cmds.camera(camera_name, query=True,
                                         displayResolution=True)
        overscan_value = cmds.camera(camera_name, query=True, overscan=True)

        if display_resolution and overscan_value == 1.3:
            cmds.camera(camera_name, edit=True, displayFilmGate=False,
                        displayResolution=False, overscan=1.0)
            return
        cmds.camera(camera_name, edit=True, displayFilmGate=False,
                    displayResolution=True, overscan=1.3)

    elif option == "field_chart":
        field_chart_display = cmds.camera(camera_name, query=True,
                                          displayFieldChart=True)
        if field_chart_display:
            cmds.camera(camera_name, edit=True, displayFieldChart=False)
            return
        cmds.camera(camera_name, edit=True, displayFieldChart=True)


def capture_snapshot(cls, combo_box):
    """
    snapshot args:
    off_screen: boolean (Process in the background when True)
    show_ornaments: boolean (Hide Axis and camera names,... when False)
    """
    active_camera = combo_box.currentText()
    folder_path = QtWidgets.QFileDialog.getExistingDirectory(None,
                                                             "Select Directory",
                                                             "")
    if not folder_path:
        return

    filename = os.path.join(folder_path, str(uuid.uuid4()))

    snap(active_camera,
         off_screen=True,
         filename=filename,
         frame_padding=0,
         show_ornaments=False,
         # clipboard=True,
         maintain_aspect_ratio=True,
         camera_options={"displayFieldChart": False})

    NotificationWidget.show_notification(cls, "Snapshot done!")

    cls.add_snapshot_image(filename + ".0.png")
