from functools import partial
import os

from PySide2 import QtWidgets, QtCore, QtGui
from maya import cmds

from dwpicker.optionvar import (
    save_optionvar, LAST_COMMAND_LANGUAGE, SEARCH_FIELD_INDEX,
    LAST_IMAGE_DIRECTORY_USED, SETTINGS_GROUP_TO_COPY, SHAPES_FILTER_INDEX,
    SETTINGS_TO_COPY)
from dwpicker.namespace import selected_namespace
from dwpicker.templates import BUTTON


SEARCH_AND_REPLACE_FIELDS = 'Targets', 'Label', 'Command', 'Image path'
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
        cmds.optionVar(query=LAST_IMAGE_DIRECTORY_USED),
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


class CommandButtonDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(CommandButtonDialog, self).__init__(parent=parent)
        self.setWindowTitle('Create command button')
        self.label = QtWidgets.QLineEdit()

        self.python = QtWidgets.QRadioButton('Python')
        self.mel = QtWidgets.QRadioButton('Mel')
        self.language = QtWidgets.QWidget()
        self.language_layout = QtWidgets.QVBoxLayout(self.language)
        self.language_layout.setContentsMargins(0, 0, 0, 0)
        self.language_layout.addWidget(self.python)
        self.language_layout.addWidget(self.mel)

        self.language_buttons = QtWidgets.QButtonGroup()
        self.language_buttons.buttonReleased.connect(self.change_state)
        self.language_buttons.addButton(self.python, 0)
        self.language_buttons.addButton(self.mel, 1)

        self.command = QtWidgets.QPlainTextEdit()

        self.options_layout = QtWidgets.QFormLayout()
        self.options_layout.addRow('Label: ', self.label)
        self.options_layout.addRow('Language: ', self.language)
        self.options_layout.addRow('Command: ', self.command)

        self.ok = QtWidgets.QPushButton('Ok')
        self.ok.released.connect(self.accept)
        self.cancel = QtWidgets.QPushButton('Cancel')
        self.cancel.released.connect(self.reject)

        self.button_layout = QtWidgets.QHBoxLayout()
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        self.button_layout.addStretch(1)
        self.button_layout.addWidget(self.ok)
        self.button_layout.addWidget(self.cancel)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addLayout(self.options_layout)
        self.layout.addLayout(self.button_layout)

        self.set_ui_states()

    def set_ui_states(self):
        index = cmds.optionVar(query=LAST_COMMAND_LANGUAGE)
        button = self.language_buttons.button(index)
        button.setChecked(True)

    @property
    def values(self):
        language = 'python' if self.python.isChecked() else 'mel'
        return {
            'action.left.language': language,
            'text.content': self.label.text(),
            'action.left.command': self.command.toPlainText(),
        }

    def change_state(self, *_):
        save_optionvar(
            LAST_COMMAND_LANGUAGE,
            self.language_buttons.checkedId())


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
            group.toggled.connect(self.updated)
            group.setCheckable(True)
            group.setChecked(category in enable_groups)
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

        self.browse = QtWidgets.QPushButton('B')
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
