
from PySide2 import QtWidgets, QtCore, QtGui
from dwpicker.hotkeys import get_hotkeys_config, save_hotkey_config


class HotkeysEditor(QtWidgets.QWidget):
    hotkey_changed = QtCore.Signal()

    def __init__(self, parent=None):
        super(HotkeysEditor, self).__init__(parent)
        self.model = HotkeysTableModel()
        self.model.hotkey_changed.connect(self.hotkey_changed.emit)
        self.table = QtWidgets.QTableView()
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setModel(self.model)
        self.table.selectionModel().selectionChanged.connect(
            self.selection_changed)
        self.hotkey_editor = HotkeyEditor()
        self.hotkey_editor.hotkey_edited.connect(self.update_hotkeys)
        self.clear = QtWidgets.QPushButton('Clear')
        self.clear.released.connect(self.do_clear)

        hotkey_layout = QtWidgets.QVBoxLayout()
        hotkey_layout.setContentsMargins(0, 0, 0, 0)
        hotkey_layout.addWidget(self.hotkey_editor)
        hotkey_layout.addWidget(self.clear)
        hotkey_layout.addStretch(1)

        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(self.table)
        layout.addLayout(hotkey_layout)

    def do_clear(self):
        self.hotkey_editor.clear_values()
        self.update_hotkeys()
        self.hotkey_changed.emit()

    def update_hotkeys(self):
        self.model.set_keysequence(
            self.hotkey_editor.function_name,
            self.hotkey_editor.key_sequence())

    def selection_changed(self, *_):
        indexes = self.table.selectionModel().selectedIndexes()
        if not indexes:
            self.hotkey_editor.clear()
            return
        row = indexes[0].row()
        function_name = sorted(list(self.model.config))[row]
        data = self.model.config[function_name]
        self.hotkey_editor.set_key_sequence(
            function_name, data['key_sequence'])


class HotkeyEditor(QtWidgets.QWidget):
    hotkey_edited = QtCore.Signal()

    def __init__(self, parent=None):
        super(HotkeyEditor, self).__init__(parent)
        self.function_name = None
        self.function_name_label = QtWidgets.QLabel()
        self.alt = QtWidgets.QCheckBox('Alt')
        self.alt.released.connect(self.emit_hotkey_edited)
        self.ctrl = QtWidgets.QCheckBox('Ctrl')
        self.ctrl.released.connect(self.emit_hotkey_edited)
        self.shift = QtWidgets.QCheckBox('Shift')
        self.shift.released.connect(self.emit_hotkey_edited)
        self.string = KeyField()
        self.string.changed.connect(self.hotkey_edited.emit)

        modifiers = QtWidgets.QHBoxLayout()
        modifiers.addWidget(self.alt)
        modifiers.addWidget(self.ctrl)
        modifiers.addWidget(self.shift)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.function_name_label)
        layout.addLayout(modifiers)
        layout.addWidget(self.string)

    def clear(self):
        self.function_name = None
        self.clear_values()
        self.function_name_label.setText('')

    def clear_values(self):
        self.ctrl.setChecked(False)
        self.alt.setChecked(False)
        self.shift.setChecked(False)
        self.string.setText('')

    def emit_hotkey_edited(self, *_):
        self.hotkey_edited.emit()

    def key_sequence(self):
        if not self.string.text():
            return None
        sequence = []
        if self.ctrl.isChecked():
            sequence.append('CTRL')
        if self.alt.isChecked():
            sequence.append('ALT')
        if self.shift.isChecked():
            sequence.append('SHIFT')
        sequence.append(self.string.text())
        return '+'.join(sequence)

    def set_key_sequence(self, function_name, key_sequence):
        self.function_name = function_name
        self.function_name_label.setText(function_name.title())
        if key_sequence is None:
            self.ctrl.setChecked(False)
            self.alt.setChecked(False)
            self.shift.setChecked(False)
            self.string.setText('')
            return
        self.ctrl.setChecked('ctrl' in key_sequence.lower())
        self.alt.setChecked('alt' in key_sequence.lower())
        self.shift.setChecked('shift' in key_sequence.lower())
        self.string.setText(key_sequence.split('+')[-1])


class KeyField(QtWidgets.QLineEdit):
    changed = QtCore.Signal()

    def __init__(self, parent=None):
        super(KeyField, self).__init__(parent)
        self.setReadOnly(True)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Shift:
            return
        self.setText(QtGui.QKeySequence(event.key()).toString())
        self.changed.emit()


class HotkeysTableModel(QtCore.QAbstractTableModel):
    HEADERS = 'Function', 'Key sequence'
    hotkey_changed = QtCore.Signal()

    def __init__(self, parent=None):
        super(HotkeysTableModel, self).__init__(parent)
        self.config = get_hotkeys_config()

    def rowCount(self, *_):
        return len(self.config)

    def columnCount(self, *_):
        return len(self.HEADERS)

    def set_keysequence(self, function_name, key_sequence):
        self.layoutAboutToBeChanged.emit()
        self.config[function_name]['key_sequence'] = key_sequence
        if key_sequence is None:
            self.config[function_name]['enabled'] = False
        save_hotkey_config(self.config)
        self.layoutChanged.emit()
        self.hotkey_changed.emit()

    def flags(self, index):
        flags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        if index.column() == 0:
            flags |= QtCore.Qt.ItemIsUserCheckable
        return flags

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Vertical or role != QtCore.Qt.DisplayRole:
            return
        return self.HEADERS[section]

    def setData(self, index, value, role):

        if role != QtCore.Qt.CheckStateRole or index.column() != 0:
            return
        function = sorted(list(self.config))[index.row()]
        self.config[function]['enabled'] = value
        save_hotkey_config(self.config)
        self.hotkey_changed.emit()
        return True

    def data(self, index, role):
        if not index.isValid():
            return

        function = sorted(list(self.config))[index.row()]
        data = self.config[function]
        if role == QtCore.Qt.DisplayRole:
            if index.column() == 0:
                return function.title()
            else:
                return data['key_sequence']
        if role == QtCore.Qt.CheckStateRole and index.column() == 0:
            return (
                QtCore.Qt.Checked if data['enabled'] else QtCore.Qt.Unchecked)
