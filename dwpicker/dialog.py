from functools import partial
import os

from PySide2 import QtWidgets, QtCore, QtGui
from maya import cmds

from dwpicker.designer.highlighter import get_highlighter
from dwpicker.optionvar import (
    save_optionvar, CHECK_FOR_UPDATE,
    SEARCH_FIELD_INDEX, LAST_IMAGE_DIRECTORY_USED, SETTINGS_GROUP_TO_COPY,
    SHAPES_FILTER_INDEX, SETTINGS_TO_COPY)
from dwpicker.languages import MEL, PYTHON
from dwpicker.path import get_image_directory
from dwpicker.qtutils import icon
from dwpicker.namespace import selected_namespace
from dwpicker.templates import BUTTON


SEARCH_AND_REPLACE_FIELDS = 'Targets', 'Label', 'Image path', 'Command'
SHAPES_FILTERS = 'All shapes', 'Selected shapes'


def warning(title, message, parent=None):
    return QtWidgets.QMessageBox.warning(
        parent,
        title,
        message,
        QtWidgets.QMessageBox.Ok,
        QtWidgets.QMessageBox.Ok)


def question(title, message, buttons=None, parent=None):
    buttons = buttons or QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel
    result = QtWidgets.QMessageBox.question(
        parent, title, message, buttons, QtWidgets.QMessageBox.Ok)
    return result == QtWidgets.QMessageBox.Ok


def get_image_path(parent=None):
    filename = QtWidgets.QFileDialog.getOpenFileName(
        parent, "Repath image...",
        get_image_directory(),
        filter="Images (*.jpg *.gif *.png *.tga)")[0]
    if not filename:
        return None
    directory = os.path.dirname(filename)
    save_optionvar(LAST_IMAGE_DIRECTORY_USED, directory)
    return filename


class NamespaceDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(NamespaceDialog, self).__init__(parent=parent)
        self.setWindowTitle('Select namespace ...')
        self.namespace_combo = QtWidgets.QComboBox()
        self.namespace_combo.setEditable(True)
        namespaces = [':'] + cmds.namespaceInfo(
            listOnlyNamespaces=True, recurse=True)
        self.namespace_combo.addItems(namespaces)
        self.namespace_combo.setCurrentText(selected_namespace())

        self.detect_selection = QtWidgets.QPushButton('Detect from selection')
        self.detect_selection.released.connect(self.call_detect_selection)
        self.ok = QtWidgets.QPushButton('Ok')
        self.ok.released.connect(self.accept)
        self.cancel = QtWidgets.QPushButton('Cancel')
        self.cancel.released.connect(self.reject)

        self.button_layout = QtWidgets.QHBoxLayout()
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        self.button_layout.addStretch(1)
        self.button_layout.addWidget(self.detect_selection)
        self.button_layout.addSpacing(16)
        self.button_layout.addWidget(self.ok)
        self.button_layout.addWidget(self.cancel)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.namespace_combo)
        self.layout.addLayout(self.button_layout)

    @property
    def namespace(self):
        return self.namespace_combo.currentText()

    def call_detect_selection(self):
        self.namespace_combo.setCurrentText(selected_namespace())


class SettingsPaster(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(SettingsPaster, self).__init__(parent)
        self.setWindowTitle('Paste settings')
        self.groups = {}
        self.categories = {}
        enable_settings = cmds.optionVar(query=SETTINGS_TO_COPY).split(';')
        for setting in sorted(BUTTON.keys()):
            text = ' '.join(setting.split('.')[1:]).capitalize()
            checkbox = QtWidgets.QCheckBox(text or setting.capitalize())
            checkbox.setting = setting
            checkbox.setChecked(setting in enable_settings)
            checkbox.stateChanged.connect(self.updated)
            name = setting.split('.')[0]
            self.categories.setdefault(name, []).append(checkbox)
        enable_groups = cmds.optionVar(query=SETTINGS_GROUP_TO_COPY).split(';')

        groups_layout = QtWidgets.QVBoxLayout()
        self.group_layouts = QtWidgets.QHBoxLayout()
        checkboxes_count = 0
        for category, checkboxes in self.categories.items():
            if checkboxes_count > 12:
                checkboxes_count = 0
                groups_layout.addStretch(1)
                self.group_layouts.addLayout(groups_layout)
                groups_layout = QtWidgets.QVBoxLayout()
            group = QtWidgets.QGroupBox(category)
            group.setCheckable(True)
            group.setChecked(category in enable_groups)
            group.toggled.connect(self.updated)
            group_layout = QtWidgets.QVBoxLayout(group)
            for checkbox in checkboxes:
                group_layout.addWidget(checkbox)
            self.groups[category] = group
            groups_layout.addWidget(group)
            checkboxes_count += len(checkboxes)
        groups_layout.addStretch(1)
        self.group_layouts.addLayout(groups_layout)

        self.paste = QtWidgets.QPushButton('Paste')
        self.paste.released.connect(self.accept)
        self.cancel = QtWidgets.QPushButton('Cancel')
        self.cancel.released.connect(self.reject)
        self.buttons_layout = QtWidgets.QHBoxLayout()
        self.buttons_layout.addStretch(1)
        self.buttons_layout.addWidget(self.paste)
        self.buttons_layout.addWidget(self.cancel)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addLayout(self.group_layouts)
        self.layout.addLayout(self.buttons_layout)

    @property
    def settings(self):
        return [
            cb.setting for category, checkboxes in self.categories.items()
            for cb in checkboxes if cb.isChecked() and
            self.groups[category].isChecked()]

    def updated(self, *_):
        cat = ';'.join([c for c, g in self.groups.items() if g.isChecked()])
        save_optionvar(SETTINGS_GROUP_TO_COPY, cat)
        save_optionvar(SETTINGS_TO_COPY, ';'.join(self.settings))


class SearchAndReplaceDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(SearchAndReplaceDialog, self).__init__(parent=parent)
        self.setWindowTitle('Search and replace in shapes')
        self.sizeHint = lambda: QtCore.QSize(320, 80)

        self.filters = QtWidgets.QComboBox()
        self.filters.addItems(SHAPES_FILTERS)
        self.filters.setCurrentIndex(cmds.optionVar(query=SHAPES_FILTER_INDEX))
        function = partial(save_optionvar, SHAPES_FILTER_INDEX)
        self.filters.currentIndexChanged.connect(function)
        self.fields = QtWidgets.QComboBox()
        self.fields.addItems(SEARCH_AND_REPLACE_FIELDS)
        self.fields.setCurrentIndex(cmds.optionVar(query=SEARCH_FIELD_INDEX))
        function = partial(save_optionvar, SEARCH_FIELD_INDEX)
        self.fields.currentIndexChanged.connect(function)
        self.search = QtWidgets.QLineEdit()
        self.replace = QtWidgets.QLineEdit()

        self.ok = QtWidgets.QPushButton('Replace')
        self.ok.released.connect(self.accept)
        self.cancel = QtWidgets.QPushButton('Cancel')
        self.cancel.released.connect(self.reject)

        self.options = QtWidgets.QFormLayout()
        self.options.setContentsMargins(0, 0, 0, 0)
        self.options.addRow('Apply on: ', self.filters)
        self.options.addRow('Field to search: ', self.fields)
        self.options.addRow('Search: ', self.search)
        self.options.addRow('Replace by: ', self.replace)

        self.button_layout = QtWidgets.QHBoxLayout()
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        self.button_layout.addStretch(1)
        self.button_layout.addWidget(self.ok)
        self.button_layout.addWidget(self.cancel)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addLayout(self.options)
        self.layout.addLayout(self.button_layout)

    @property
    def field(self):
        '''
        0 = Targets
        1 = Label
        2 = Command
        3 = Image path
        '''
        return self.fields.currentIndex()

    @property
    def filter(self):
        '''
        0 = Apply on all shapes
        1 = Apply on selected shapes
        '''
        return self.filters.currentIndex()


class MissingImages(QtWidgets.QDialog):
    def __init__(self, paths, parent=None):
        super(MissingImages, self).__init__(parent)
        self.setWindowTitle('Missing images')
        self.model = PathModel(paths)
        self.paths = QtWidgets.QTableView()
        self.paths.setAlternatingRowColors(True)
        self.paths.setShowGrid(False)
        self.paths.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        mode = QtWidgets.QHeaderView.ResizeToContents
        self.paths.verticalHeader().resizeSections(mode)
        self.paths.verticalHeader().hide()
        self.paths.horizontalHeader().show()
        self.paths.horizontalHeader().resizeSections(mode)
        self.paths.horizontalHeader().setStretchLastSection(True)
        mode = QtWidgets.QAbstractItemView.ScrollPerPixel
        self.paths.setHorizontalScrollMode(mode)
        self.paths.setVerticalScrollMode(mode)
        self.paths.setModel(self.model)

        self.browse = QtWidgets.QPushButton(icon('mini-open.png'))
        self.browse.setFixedWidth(30)
        self.browse.released.connect(self.call_browse)
        self.update = QtWidgets.QPushButton('Update')
        self.update.released.connect(self.accept)
        self.skip = QtWidgets.QPushButton('Skip')
        self.skip.released.connect(self.reject)
        self.validators = QtWidgets.QHBoxLayout()
        self.validators.addStretch(1)
        self.validators.addWidget(self.browse)
        self.validators.addWidget(self.update)
        self.validators.addWidget(self.skip)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.paths)
        self.layout.addLayout(self.validators)

    def output(self, path):
        for p, output in zip(self.model.paths, self.model.outputs):
            if p == path:
                return output

    @property
    def outputs(self):
        return self.model.outputs

    def resizeEvent(self, _):
        mode = QtWidgets.QHeaderView.ResizeToContents
        self.paths.verticalHeader().resizeSections(mode)
        self.paths.horizontalHeader().resizeSections(mode)

    def call_browse(self):
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select image folder")
        if not directory:
            return
        filenames = os.listdir(directory)
        self.model.layoutAboutToBeChanged.emit()
        for i, path in enumerate(self.model.paths):
            filename = os.path.basename(path)
            if filename in filenames:
                filepath = os.path.join(directory, filename)
                self.model.outputs[i] = filepath
        self.model.layoutChanged.emit()


class PathModel(QtCore.QAbstractTableModel):
    HEADERS = 'filename', 'directory'

    def __init__(self, paths, parent=None):
        super(PathModel, self).__init__(parent)
        self.paths = paths
        self.outputs = paths[:]

    def rowCount(self, *_):
        return len(self.paths)

    def columnCount(self, *_):
        return 2

    def flags(self, index):
        flags = super(PathModel, self).flags(index)
        if index.column() == 1:
            flags |= QtCore.Qt.ItemIsEditable
        return flags

    def headerData(self, position, orientation, role):
        if orientation != QtCore.Qt.Horizontal:
            return

        if role != QtCore.Qt.DisplayRole:
            return

        return self.HEADERS[position]

    def data(self, index, role):
        if not index.isValid():
            return

        row, col = index.row(), index.column()
        if role == QtCore.Qt.DisplayRole:
            if col == 0:
                return os.path.basename(self.outputs[row])
            if col == 1:
                return os.path.dirname(self.outputs[row])

        elif role == QtCore.Qt.BackgroundColorRole:
            if not os.path.exists(self.outputs[row]):
                return QtGui.QColor(QtCore.Qt.darkRed)


class UpdateAvailableDialog(QtWidgets.QDialog):
    def __init__(self, version, parent=None):
        super(UpdateAvailableDialog, self).__init__(parent=parent)
        self.setWindowTitle('Update available')

        # Widgets
        text = '\n    New DreamWall Picker version "{0}" is available !    \n'
        label = QtWidgets.QLabel(text.format(version))

        ok_btn = QtWidgets.QPushButton('Open GitHub page')
        ok_btn.released.connect(self.accept)

        cancel_btn = QtWidgets.QPushButton('Close')
        cancel_btn.released.connect(self.reject)

        self.check_cb = QtWidgets.QCheckBox('Check for update at startup')
        self.check_cb.stateChanged.connect(
            self.change_check_for_update_preference)
        self.check_cb.setChecked(cmds.optionVar(query=CHECK_FOR_UPDATE))

        # Layouts
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)

        cb_layout = QtWidgets.QHBoxLayout()
        cb_layout.addStretch(1)
        cb_layout.addWidget(self.check_cb)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(label)
        layout.addLayout(cb_layout)
        layout.addLayout(button_layout)

    def change_check_for_update_preference(self):
        save_optionvar(CHECK_FOR_UPDATE, int(self.check_cb.isChecked()))


class CommandEditorDialog(QtWidgets.QDialog):

    def __init__(self, command, parent=None):
        super(CommandEditorDialog, self).__init__(parent)
        self.setWindowTitle('Edit/Create command')
        self.languages = QtWidgets.QComboBox()
        self.languages.addItems([MEL, PYTHON])
        self.languages.setCurrentText(command['language'])
        self.languages.currentIndexChanged.connect(self.language_changed)

        self.button = QtWidgets.QComboBox()
        self.button.addItems(['left', 'right'])
        self.button.setCurrentText(command['button'])

        self.enabled = QtWidgets.QCheckBox('Enabled')
        self.enabled.setChecked(command['enabled'])

        self.ctrl = QtWidgets.QCheckBox('Ctrl')
        self.ctrl.setChecked(command['ctrl'])
        self.shift = QtWidgets.QCheckBox('Shift')
        self.shift.setChecked(command['shift'])
        self.eval_deferred = QtWidgets.QCheckBox('Eval deferred (python only)')
        self.eval_deferred.setChecked(command['deferred'])
        self.unique_undo = QtWidgets.QCheckBox('Unique undo')
        self.unique_undo.setChecked(command['force_compact_undo'])

        self.command = QtWidgets.QTextEdit()
        self.command.setFixedHeight(100)
        self.command.setPlainText(command['command'])

        self.ok = QtWidgets.QPushButton('Ok')
        self.ok.released.connect(self.accept)
        self.cancel = QtWidgets.QPushButton('Cancel')
        self.cancel.released.connect(self.reject)

        form = QtWidgets.QFormLayout()
        form.setSpacing(0)
        form.addRow('Language', self.languages)
        form.addRow('Mouse button', self.button)

        modifiers_group = QtWidgets.QGroupBox('Modifiers')
        modifiers_layout = QtWidgets.QVBoxLayout(modifiers_group)
        modifiers_layout.addWidget(self.ctrl)
        modifiers_layout.addWidget(self.shift)

        options_group = QtWidgets.QGroupBox('Options')
        options_layout = QtWidgets.QVBoxLayout(options_group)
        options_layout.addWidget(self.eval_deferred)
        options_layout.addWidget(self.unique_undo)
        options_layout.addLayout(form)

        code = QtWidgets.QGroupBox('Code')
        code_layout = QtWidgets.QVBoxLayout(code)
        code_layout.setSpacing(0)
        code_layout.addWidget(self.command)

        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(self.ok)
        buttons_layout.addWidget(self.cancel)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(options_group)
        layout.addWidget(modifiers_group)
        layout.addWidget(code)
        layout.addLayout(buttons_layout)
        self.language_changed()

    def language_changed(self, *_):
        language = self.languages.currentText()
        highlighter = get_highlighter(language)
        highlighter(self.command.document())

    def command_data(self):
        return {
            'enabled': self.enabled.isChecked(),
            'button': self.button.currentText(),
            'language': self.languages.currentText(),
            'command': self.command.toPlainText(),
            'ctrl': self.ctrl.isChecked(),
            'shift': self.shift.isChecked(),
            'deferred': self.eval_deferred.isChecked(),
            'force_compact_undo': self.unique_undo.isChecked()}


class MenuCommandEditorDialog(QtWidgets.QDialog):

    def __init__(self, command, parent=None):
        super(MenuCommandEditorDialog, self).__init__(parent)
        self.setWindowTitle('Edit/Create command')
        self.languages = QtWidgets.QComboBox()
        self.languages.addItems([MEL, PYTHON])
        self.languages.setCurrentText(command['language'])
        self.languages.currentIndexChanged.connect(self.language_changed)

        self.eval_deferred = QtWidgets.QCheckBox('Eval deferred (python only)')
        self.eval_deferred.setChecked(command['deferred'])
        self.unique_undo = QtWidgets.QCheckBox('Unique undo')
        self.unique_undo.setChecked(command['force_compact_undo'])

        self.caption = QtWidgets.QLineEdit()
        self.caption.setText(command['caption'])

        self.command = QtWidgets.QTextEdit()
        self.command.setFixedHeight(100)
        self.command.setPlainText(command['command'])

        self.ok = QtWidgets.QPushButton('Ok')
        self.ok.released.connect(self.accept)
        self.cancel = QtWidgets.QPushButton('Cancel')
        self.cancel.released.connect(self.reject)

        form = QtWidgets.QFormLayout()
        form.setSpacing(0)
        form.addRow('Caption', self.caption)
        form.addRow('Language', self.languages)

        options_group = QtWidgets.QGroupBox('Options')
        options_layout = QtWidgets.QVBoxLayout(options_group)
        options_layout.addWidget(self.eval_deferred)
        options_layout.addWidget(self.unique_undo)
        options_layout.addLayout(form)

        code = QtWidgets.QGroupBox('Code')
        code_layout = QtWidgets.QVBoxLayout(code)
        code_layout.setSpacing(0)
        code_layout.addWidget(self.command)

        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(self.ok)
        buttons_layout.addWidget(self.cancel)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(options_group)
        layout.addWidget(code)
        layout.addLayout(buttons_layout)
        self.language_changed()

    def language_changed(self, *_):
        language = self.languages.currentText()
        highlighter = get_highlighter(language)
        highlighter(self.command.document())

    def command_data(self):
        return {
            'caption': self.caption.text(),
            'language': self.languages.currentText(),
            'command': self.command.toPlainText(),
            'deferred': self.eval_deferred.isChecked(),
            'force_compact_undo': self.unique_undo.isChecked()}
