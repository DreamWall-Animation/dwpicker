import maya.cmds as cmds
from functools import partial
from PySide2 import QtCore, QtWidgets

from dwpicker.languages import MEL, PYTHON
from dwpicker.qtutils import VALIGNS, HALIGNS
from dwpicker.designer.highlighter import get_highlighter
from dwpicker.widgets import (
    BoolCombo, BrowseEdit, ColorEdit, IntEdit, FloatEdit,
    TextEdit, Title, WidgetToggler)


LEFT_CELL_WIDTH = 80
SHAPE_TYPES = 'square', 'round', 'rounded_rect'
ACTION_TYPES = 'select', 'command'


class AttributeEditor(QtWidgets.QWidget):
    generalOptionSet = QtCore.Signal(str, object)
    imageModified = QtCore.Signal()
    optionSet = QtCore.Signal(str, object)
    rectModified = QtCore.Signal(str, float)

    def __init__(self, parent=None):
        super(AttributeEditor, self).__init__(parent)
        self.widget = QtWidgets.QWidget()

        self.generals = GeneralSettings()
        self.generals.optionModified.connect(self.generalOptionSet.emit)
        self.generals_toggler = WidgetToggler('Picker options', self.generals)

        self.shape = ShapeSettings()
        self.shape.optionSet.connect(self.optionSet.emit)
        self.shape.rectModified.connect(self.rectModified.emit)
        self.shape_toggler = WidgetToggler('Shape', self.shape)

        self.image = ImageSettings()
        self.image.optionSet.connect(self.image_modified)
        self.image_toggler = WidgetToggler('Image', self.image)

        self.appearence = AppearenceSettings()
        self.appearence.optionSet.connect(self.optionSet.emit)
        self.appearence_toggler = WidgetToggler('Appearence', self.appearence)

        self.text = TextSettings()
        self.text.optionSet.connect(self.optionSet.emit)
        self.text_toggler = WidgetToggler('Text', self.text)

        self.action = ActionSettings()
        self.action.set_languages([MEL, PYTHON])
        self.action.optionSet.connect(self.optionSet.emit)
        self.action_toggler = WidgetToggler('Action', self.action)

        self.layout = QtWidgets.QVBoxLayout(self.widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.generals_toggler)
        self.layout.addWidget(self.generals)
        self.layout.addWidget(self.shape_toggler)
        self.layout.addWidget(self.shape)
        self.layout.addWidget(self.image_toggler)
        self.layout.addWidget(self.image)
        self.layout.addWidget(self.appearence_toggler)
        self.layout.addWidget(self.appearence)
        self.layout.addWidget(self.text_toggler)
        self.layout.addWidget(self.text)
        self.layout.addWidget(self.action_toggler)
        self.layout.addWidget(self.action)
        self.layout.addStretch(1)

        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidget(self.widget)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.scroll_area)

        self.setFixedWidth(self.sizeHint().width() * 1.075)

    def set_generals(self, options):
        self.blockSignals(True)
        self.generals.set_options(options)
        self.blockSignals(False)

    def set_options(self, options):
        self.blockSignals(True)
        self.shape.set_options(options)
        self.image.set_options(options)
        self.appearence.set_options(options)
        self.text.set_options(options)
        self.action.set_options(options)
        self.blockSignals(False)

    def image_modified(self, option, value):
        self.optionSet.emit(option, value)
        self.imageModified.emit()


class GeneralSettings(QtWidgets.QWidget):
    optionModified = QtCore.Signal(str, object)

    def __init__(self, parent=None):
        super(GeneralSettings, self).__init__(parent)
        self.name = TextEdit()
        self.name.valueSet.connect(self.name_changed)
        self.zoom_locked = BoolCombo(False)
        self.zoom_locked.valueSet.connect(self.zoom_changed)

        self.layout = QtWidgets.QFormLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setHorizontalSpacing(5)
        self.layout.addRow('Name', self.name)
        self.layout.addRow('Zoom-locked', self.zoom_locked)

    def set_options(self, options):
        self.name.setText(options['name'])
        self.zoom_locked.setCurrentText(str(options['zoom_locked']))

    def name_changed(self, value):
        self.optionModified.emit('name', value)

    def zoom_changed(self, state):
        self.optionModified.emit('zoom_locked', state)


class ShapeSettings(QtWidgets.QWidget):
    optionSet = QtCore.Signal(str, object)
    rectModified = QtCore.Signal(str, float)

    def __init__(self, parent=None):
        super(ShapeSettings, self).__init__(parent)
        self.shape = QtWidgets.QComboBox()
        self.shape.addItems(SHAPE_TYPES)
        self.shape.currentIndexChanged.connect(self.shape_changed)

        self.left = IntEdit(minimum=0)
        method = partial(self.rectModified.emit, 'shape.left')
        self.left.valueSet.connect(method)
        self.top = IntEdit(minimum=0)
        method = partial(self.rectModified.emit, 'shape.right')
        self.top.valueSet.connect(method)
        self.width = IntEdit(minimum=0)
        method = partial(self.rectModified.emit, 'shape.width')
        self.width.valueSet.connect(method)
        self.height = IntEdit(minimum=0)
        method = partial(self.rectModified.emit, 'shape.height')
        self.height.valueSet.connect(method)
        self.cornersx = IntEdit(minimum=0)
        method = partial(self.optionSet.emit, 'shape.cornersx')
        self.cornersx.valueSet.connect(method)
        self.cornersy = IntEdit(minimum=0)
        method = partial(self.optionSet.emit, 'shape.cornersy')
        self.cornersy.valueSet.connect(method)

        self.layout = QtWidgets.QFormLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setHorizontalSpacing(5)
        self.layout.addRow('Shape', self.shape)
        self.layout.addItem(QtWidgets.QSpacerItem(0, 8))
        self.layout.addRow(Title('Dimensions'))
        self.layout.addRow('left', self.left)
        self.layout.addRow('top', self.top)
        self.layout.addRow('width', self.width)
        self.layout.addRow('height', self.height)
        self.layout.addRow('roundness x', self.cornersx)
        self.layout.addRow('roundness y', self.cornersy)
        for label in self.findChildren(QtWidgets.QLabel):
            if not isinstance(label, Title):
                label.setFixedWidth(LEFT_CELL_WIDTH)

    def shape_changed(self, _):
        self.optionSet.emit('shape', self.shape.currentText())

    def set_options(self, options):
        values = list({option['shape'] for option in options})
        value = values[0] if len(values) == 1 else '...'
        self.shape.setCurrentText(value)

        values = list({int(round((option['shape.left']))) for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.left.setText(value)

        values = list({option['shape.top'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.top.setText(value)

        values = list({option['shape.width'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.width.setText(value)

        values = list({option['shape.height'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.height.setText(value)

        values = list({option['shape.cornersx'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.cornersx.setText(value)

        values = list({option['shape.cornersy'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.cornersy.setText(value)


class ImageSettings(QtWidgets.QWidget):
    optionSet = QtCore.Signal(str, object)

    def __init__(self, parent=None):
        super(ImageSettings, self).__init__(parent)
        self.path = BrowseEdit()
        self.path.valueSet.connect(partial(self.optionSet.emit, 'image.path'))

        self.fit = BoolCombo(True)
        self.fit.valueSet.connect(partial(self.optionSet.emit, 'image.fit'))

        self.width = FloatEdit()
        method = partial(self.optionSet.emit, 'image.width')
        self.width.valueSet.connect(method)

        self.height = FloatEdit()
        method = partial(self.optionSet.emit, 'image.height')
        self.height.valueSet.connect(method)

        self.layout = QtWidgets.QFormLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setHorizontalSpacing(5)
        self.layout.addRow('Path', self.path)
        self.layout.addRow('Fit to shape', self.fit)
        self.layout.addRow('Width', self.width)
        self.layout.addRow('Height', self.height)
        for label in self.findChildren(QtWidgets.QLabel):
            if not isinstance(label, Title):
                label.setFixedWidth(LEFT_CELL_WIDTH)

    def set_options(self, options):
        values = list({option['image.path'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.path.set_value(value)

        values = list({option['image.fit'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.fit.setCurrentText(value)

        values = list({option['image.width'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.width.setText(value)

        values = list({option['image.height'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.height.setText(value)


class AppearenceSettings(QtWidgets.QWidget):
    optionSet = QtCore.Signal(str, object)

    def __init__(self, parent=None):
        super(AppearenceSettings, self).__init__(parent)

        self.border = BoolCombo(True)
        method = partial(self.optionSet.emit, 'border')
        self.border.valueSet.connect(method)

        self.borderwidth_normal = FloatEdit(minimum=0.0)
        method = partial(self.optionSet.emit, 'borderwidth.normal')
        self.borderwidth_normal.valueSet.connect(method)

        self.borderwidth_hovered = FloatEdit(minimum=0.0)
        method = partial(self.optionSet.emit, 'borderwidth.hovered')
        self.borderwidth_hovered.valueSet.connect(method)

        self.borderwidth_clicked = FloatEdit(minimum=0.0)
        method = partial(self.optionSet.emit, 'borderwidth.clicked')
        self.borderwidth_clicked.valueSet.connect(method)

        self.bordercolor_normal = ColorEdit()
        method = partial(self.optionSet.emit, 'bordercolor.normal')
        self.bordercolor_normal.valueSet.connect(method)

        self.bordercolor_hovered = ColorEdit()
        method = partial(self.optionSet.emit, 'bordercolor.hovered')
        self.bordercolor_hovered.valueSet.connect(method)

        self.bordercolor_clicked = ColorEdit()
        method = partial(self.optionSet.emit, 'bordercolor.clicked')
        self.bordercolor_clicked.valueSet.connect(method)

        self.bordercolor_transparency = FloatEdit(minimum=0, maximum=255)
        method = partial(self.optionSet.emit, 'bordercolor.transparency')
        self.bordercolor_transparency.valueSet.connect(method)

        self.backgroundcolor_normal = ColorEdit()
        method = partial(self.optionSet.emit, 'bgcolor.normal')
        self.backgroundcolor_normal.valueSet.connect(method)

        self.backgroundcolor_hovered = ColorEdit()
        method = partial(self.optionSet.emit, 'bgcolor.hovered')
        self.backgroundcolor_hovered.valueSet.connect(method)

        self.backgroundcolor_clicked = ColorEdit()
        method = partial(self.optionSet.emit, 'bgcolor.clicked')
        self.backgroundcolor_clicked.valueSet.connect(method)

        self.backgroundcolor_transparency = FloatEdit(minimum=0, maximum=255)
        method = partial(self.optionSet.emit, 'bgcolor.transparency')
        self.backgroundcolor_transparency.valueSet.connect(method)

        self.layout = QtWidgets.QFormLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setHorizontalSpacing(5)
        self.layout.addRow('border visible', self.border)
        self.layout.addRow(Title('Border width (pxf)'))
        self.layout.addRow('normal', self.borderwidth_normal)
        self.layout.addRow('hovered', self.borderwidth_hovered)
        self.layout.addRow('clicked', self.borderwidth_clicked)
        self.layout.addItem(QtWidgets.QSpacerItem(0, 8))
        self.layout.addRow(Title('Border color'))
        self.layout.addRow('normal', self.bordercolor_normal)
        self.layout.addRow('hovered', self.bordercolor_hovered)
        self.layout.addRow('clicked', self.bordercolor_clicked)
        self.layout.addRow('transparency', self.bordercolor_transparency)
        self.layout.addItem(QtWidgets.QSpacerItem(0, 8))
        self.layout.addRow(Title('Background color'))
        self.layout.addRow('normal', self.backgroundcolor_normal)
        self.layout.addRow('hovered', self.backgroundcolor_hovered)
        self.layout.addRow('clicked', self.backgroundcolor_clicked)
        self.layout.addRow('transparency', self.backgroundcolor_transparency)
        for label in self.findChildren(QtWidgets.QLabel):
            if not isinstance(label, Title):
                label.setFixedWidth(LEFT_CELL_WIDTH)

    def set_options(self, options):
        values = list({option['border'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.border.setCurrentText(value)

        values = list({option['borderwidth.normal'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.borderwidth_normal.setText(value)

        values = list({option['borderwidth.hovered'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.borderwidth_hovered.setText(value)

        values = list({option['borderwidth.clicked'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.borderwidth_clicked.setText(value)

        values = list({option['bordercolor.normal'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.bordercolor_normal.set_color(value)

        values = list({option['bordercolor.hovered'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.bordercolor_hovered.set_color(value)

        values = list({option['bordercolor.clicked'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.bordercolor_clicked.set_color(value)

        values = list({option['bordercolor.transparency'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.bordercolor_transparency.setText(value)

        values = list({option['bgcolor.normal'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.backgroundcolor_normal.set_color(value)

        values = list({option['bgcolor.hovered'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.backgroundcolor_hovered.set_color(value)

        values = list({option['bgcolor.clicked'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.backgroundcolor_clicked.set_color(value)

        values = list({option['bgcolor.transparency'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.backgroundcolor_transparency.setText(value)


class ActionSettings(QtWidgets.QWidget):
    optionSet = QtCore.Signal(str, object)

    def __init__(self, parent=None):
        super(ActionSettings, self).__init__(parent)
        self._targets = QtWidgets.QLineEdit()
        self._targets.returnPressed.connect(self.targets_changed)

        self._lactive = BoolCombo(False)
        method = partial(self.optionSet.emit, 'action.left')
        self._lactive.valueSet.connect(method)
        self._lactive.valueSet.connect(self.set_left_enabled)


        self._llanguage = QtWidgets.QComboBox()
        method = partial(self.language_changed, 'left')
        self._llanguage.currentIndexChanged.connect(method)
        self._lcommand = QtWidgets.QPlainTextEdit()
        self._lcommand.setFixedHeight(100)
        self._lsave = QtWidgets.QPushButton('save command')
        self._lsave.released.connect(partial(self.save_command, 'left'))

        self._ractive = BoolCombo(False)
        method = partial(self.optionSet.emit, 'action.right')
        self._ractive.valueSet.connect(method)
        self._ractive.valueSet.connect(self.set_right_enabled)

        self._rlanguage = QtWidgets.QComboBox()
        method = partial(self.language_changed, 'right')
        self._rlanguage.currentIndexChanged.connect(method)
        self._rcommand = QtWidgets.QPlainTextEdit()
        self._rcommand.setFixedHeight(100)
        self._rsave = QtWidgets.QPushButton('save command')
        self._rsave.released.connect(partial(self.save_command, 'right'))

        self._add_targets = QtWidgets.QPushButton('Add')
        self._remove_targets = QtWidgets.QPushButton('Remove')
        self._replace_targets = QtWidgets.QPushButton('Replace')
        self._targets_layout = QtWidgets.QHBoxLayout()
        self._targets_layout.addWidget(self._add_targets)
        self._targets_layout.addWidget(self._remove_targets)
        self._targets_layout.addWidget(self._replace_targets)

        self._add_targets.clicked.connect(self.call_add_targets)
        self._remove_targets.clicked.connect(self.call_remove_targets)
        self._replace_targets.clicked.connect(self.call_replace_targets)

        self.layout = QtWidgets.QFormLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setHorizontalSpacing(5)
        self.layout.addRow(Title('Selection'))
        self.layout.addRow('Targets', self._targets)
        self.layout.addRow('Add Selected', self._targets_layout)

        self.layout.addRow(Title('Left click'))
        self.layout.addRow('Has command', self._lactive)
        self.layout.addRow('Language', self._llanguage)
        self.layout.addRow(self._lcommand)
        self.layout.addRow(self._lsave)
        self.layout.addRow(Title('Right click'))
        self.layout.addRow('Has command', self._ractive)
        self.layout.addRow('Language', self._rlanguage)
        self.layout.addRow(self._rcommand)
        self.layout.addRow(self._rsave)
        for label in self.findChildren(QtWidgets.QLabel):
            if not isinstance(label, Title):
                label.setFixedWidth(LEFT_CELL_WIDTH)

    def targets(self):
        targets = str(self._targets.text())
        try:
            return [t.strip(" ") for t in targets.split(',')]
        except ValueError:
            return []

    def call_add_targets(self):
        selection = cmds.ls(selection=True, flatten=True)
        if not selection:
            return
        targets = self.targets()
        edits = [item for item in selection if item not in targets]
        targets = targets if targets != [''] else []
        self._targets.setText(', '.join(targets + edits))
        self._targets.setFocus()
        self.targets_changed()

    def call_remove_targets(self):
        selection = cmds.ls(selection=True, flatten=True)
        if not selection:
            return

        targets = [item for item in self.targets() if item not in selection]
        self._targets.setText(', '.join(targets))
        self._targets.setFocus()
        self.targets_changed()

    def call_replace_targets(self):
        selection = cmds.ls(selection=True, flatten=True)
        if not selection:
            return

        self._targets.setText(', '.join(selection))
        self._targets.setFocus()
        self.targets_changed()

    def targets_changed(self):
        if not self._targets.text():
            self.optionSet.emit('action.targets', [])
            return
        values = [t.strip(" ") for t in self._targets.text().split(",")]
        self.optionSet.emit('action.targets', values)

    def set_languages(self, languages):
        self.blockSignals(True)
        self._llanguage.addItems(languages)
        self._rlanguage.addItems(languages)
        self.blockSignals(False)

    def language_changed(self, side, *_):
        option = 'action.' + side + '.language'
        combo = self._llanguage if side == 'left' else self._rlanguage
        text_edit = self._lcommand if side == 'left' else self._rcommand
        language = combo.currentText()
        highlighter = get_highlighter(language)
        highlighter(text_edit.document())
        self.optionSet.emit(option, language)

    def save_command(self, side):
        text_edit = self._lcommand if side == 'left' else self._rcommand
        option = 'action.' + side + '.command'
        self.optionSet.emit(option, text_edit.toPlainText())

    def set_options(self, options):
        values = list({o for opt in options for o in opt['action.targets']})
        value = values[0] if len(values) == 1 else ""
        self._targets.setText(", ".join(sorted(values)))

        values = list({option['action.left'] for option in options})
        value = values[0] if len(values) == 1 else None
        self._lactive.setCurrentText(str(value))
        self.set_left_enabled(bool(value))

        values = list({option['action.left.language'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self._llanguage.setCurrentText(value)

        if not options or len(options) > 1 or not options[0]['action.left']:
            self._lcommand.setPlainText('')
            self._lcommand.setEnabled(False)
            self._lsave.setEnabled(False)
        else:
            self._lcommand.setPlainText(options[0]['action.left.command'])
            self._lcommand.setEnabled(True)
            self._lsave.setEnabled(True)

        values = list({option['action.right'] for option in options})
        value = values[0] if len(values) == 1 else None
        self._ractive.setCurrentText(str(value))
        self.set_right_enabled(bool(value))
        values = list({option['action.right.language'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self._rlanguage.setCurrentText(value)

        if not options or len(options) > 1 or not options[0]['action.right']:
            self._rcommand.setPlainText('')
            self._rcommand.setEnabled(False)
            self._rsave.setEnabled(False)
        else:
            self._rcommand.setPlainText(options[0]['action.right.command'])
            self._rcommand.setEnabled(True)
            self._rsave.setEnabled(True)

    def set_left_enabled(self, state):
        self._llanguage.setEnabled(state)
        self._lcommand.setEnabled(state)
        self._lsave.setEnabled(state)

    def set_right_enabled(self, state):
        self._rlanguage.setEnabled(state)
        self._rcommand.setEnabled(state)
        self._rsave.setEnabled(state)


class TextSettings(QtWidgets.QWidget):
    optionSet = QtCore.Signal(str, object)

    def __init__(self, parent=None):
        super(TextSettings, self).__init__(parent)
        self.text = TextEdit()
        method = partial(self.optionSet.emit,'text.content')
        self.text.valueSet.connect(method)

        self.size = FloatEdit(minimum=0.0)
        self.size.valueSet.connect(partial(self.optionSet.emit, 'text.size'))

        self.bold = BoolCombo()
        self.bold.valueSet.connect(partial(self.optionSet.emit, 'text.bold'))

        self.italic = BoolCombo()
        method = partial(self.optionSet.emit, 'text.italic')
        self.italic.valueSet.connect(method)

        self.color = ColorEdit()
        self.color.valueSet.connect(partial(self.optionSet.emit, 'text.color'))

        self.halignement = QtWidgets.QComboBox()
        self.halignement.addItems(HALIGNS.keys())
        self.halignement.currentIndexChanged.connect(self.halign_changed)
        self.valignement = QtWidgets.QComboBox()
        self.valignement.addItems(VALIGNS.keys())
        self.valignement.currentIndexChanged.connect(self.valign_changed)

        self.layout = QtWidgets.QFormLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setHorizontalSpacing(5)
        self.layout.addRow('Content', self.text)
        self.layout.addItem(QtWidgets.QSpacerItem(0, 8))
        self.layout.addRow(Title('Options'))
        self.layout.addRow('Size', self.size)
        self.layout.addRow('Bold', self.bold)
        self.layout.addRow('Italic', self.italic)
        self.layout.addRow('Color', self.color)
        self.layout.addItem(QtWidgets.QSpacerItem(0, 8))
        self.layout.addRow(Title('Alignement'))
        self.layout.addRow('Horizontal', self.halignement)
        self.layout.addRow('Vertical', self.valignement)
        for label in self.findChildren(QtWidgets.QLabel):
            if not isinstance(label, Title):
                label.setFixedWidth(LEFT_CELL_WIDTH)

    def valign_changed(self):
        self.optionSet.emit('text.valign', self.valignement.currentText())

    def halign_changed(self):
        self.optionSet.emit('text.halign', self.halignement.currentText())

    def set_options(self, options):
        values = list({option['text.content'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.text.setText(value)

        values = list({option['text.size'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.size.setText(value)

        values = list({option['text.bold'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.bold.setCurrentText(value)

        values = list({option['text.italic'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.italic.setCurrentText(value)

        values = list({option['text.color'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.color.set_color(value)

        values = list({option['text.halign'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.halignement.setCurrentText(value)

        values = list({option['text.valign'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.valignement.setCurrentText(value)
