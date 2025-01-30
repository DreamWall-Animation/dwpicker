from dwpicker.pyside import QtWidgets, QtCore
from maya import cmds
from dwpicker.optionvar import ZOOM_BUTTON


class InteractionManager:
    FLY_OVER = 'fly_over'
    SELECTION = 'selection'
    NAVIGATION = 'navigation'
    DRAGGING = 'dragging'
    ZOOMING = 'zooming'

    def __init__(self):
        self.shapes = []
        self.left_click_pressed = False
        self.right_click_pressed = False
        self.middle_click_pressed = False
        self.mouse_ghost = None
        self.has_shape_hovered = False
        self.dragging = False
        self.anchor = None
        self.zoom_anchor = None

    @property
    def ctrl_pressed(self):
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        return modifiers == (modifiers | QtCore.Qt.ControlModifier)

    @property
    def shift_pressed(self):
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        return modifiers == (modifiers | QtCore.Qt.ShiftModifier)

    @property
    def alt_pressed(self):
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        return modifiers == (modifiers | QtCore.Qt.AltModifier)

    def update(
            self,
            event,
            pressed=False,
            has_shape_hovered=False,
            dragging=False):

        self.dragging = dragging
        self.has_shape_hovered = has_shape_hovered
        self.update_mouse(event, pressed)

    def update_mouse(self, event, pressed):
        if event.button() == QtCore.Qt.LeftButton:
            self.left_click_pressed = pressed
            self.anchor = event.pos() if self.dragging else None
        elif event.button() == QtCore.Qt.RightButton:
            self.right_click_pressed = pressed
        elif event.button() == QtCore.Qt.MiddleButton:
            self.middle_click_pressed = pressed
        if self.zoom_button_pressed:
            self.zoom_anchor = event.pos() if pressed else None

    @property
    def mode(self):
        if self.dragging:
            return InteractionManager.DRAGGING
        elif self.zoom_button_pressed and self.alt_pressed:
            return InteractionManager.ZOOMING
        elif self.middle_click_pressed:
            return InteractionManager.NAVIGATION
        elif self.left_click_pressed:
            return InteractionManager.SELECTION
        self.mouse_ghost = None
        return InteractionManager.FLY_OVER

    def mouse_offset(self, position):
        result = position - self.mouse_ghost if self.mouse_ghost else None
        self.mouse_ghost = position
        return result or None

    @property
    def zoom_button_pressed(self):
        button = cmds.optionVar(query=ZOOM_BUTTON)
        return any((
            button == 'left' and self.left_click_pressed,
            button == 'middle' and self.middle_click_pressed,
            button == 'right' and self.right_click_pressed))
