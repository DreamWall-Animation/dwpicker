from copy import deepcopy
from PySide2 import QtWidgets, QtCore
from dwpicker.templates import COMMAND, MENU_COMMAND
from dwpicker.qtutils import icon
from dwpicker.dialog import CommandEditorDialog, MenuCommandEditorDialog


class CommandItemWidget(QtWidgets.QWidget):
    editRequested = QtCore.Signal(object)
    deletedRequested = QtCore.Signal(object)

    def __init__(self, command, parent=None):
        super(CommandItemWidget, self).__init__(parent)

        self.command = command
        self.label = QtWidgets.QLabel(self.get_label())
        self.edit = QtWidgets.QPushButton(icon('edit2.png'), '')
        self.edit.released.connect(lambda: self.editRequested.emit(self))
        self.edit.setFixedSize(25, 25)
        self.delete = QtWidgets.QPushButton(icon('delete2.png'), '')
        self.delete.setFixedSize(25, 25)
        self.delete.released.connect(lambda: self.deletedRequested.emit(self))
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.edit)
        layout.addWidget(self.delete)
        layout.addSpacing(10)
        layout.addWidget(self.label)

    def get_label(self):
        language = '<a style="color: #FFFF00"><i>({0})</i></a>'.format(
            self.command['language'])
        touchs = [self.command['button'] + 'Click']
        touchs.extend([m for m in ('ctrl', 'shift') if self.command[m]])
        return '{} {}'.format('+'.join(touchs), language)

    def update_label(self):
        self.label.setText(self.get_label())


class MenuCommandItemWidget(CommandItemWidget):

    def get_label(self):
        language = '<a style="color: #FFFF00"><i>({0})</i></a>'.format(
            self.command['language'])
        return '{} {}'.format(self.command['caption'], language)


class CommandsEditor(QtWidgets.QWidget):
    valueSet = QtCore.Signal(object)
    edit_dialog_constructor = CommandEditorDialog
    picker_command_key = 'action.commands'
    template = COMMAND
    item_constructor = CommandItemWidget

    def __init__(self, parent=None):
        super(CommandsEditor, self).__init__(parent)
        self.warning = QtWidgets.QLabel('Select only one shape')

        self.commands = QtWidgets.QListWidget()
        self.commands.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.commands.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.commands.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff)

        self.add_command = QtWidgets.QPushButton('Add command')
        self.add_command.released.connect(self.call_create_command)
        self.add_command.setEnabled(False)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.warning)
        layout.addWidget(self.commands)
        layout.addWidget(self.add_command)

    def set_options(self, options):
        self.commands.clear()
        if len(options) != 1:
            self.warning.setVisible(True)
            self.add_command.setEnabled(False)
            return
        self.warning.setVisible(False)
        self.add_command.setEnabled(True)
        for command in options[0][self.picker_command_key]:
            self.call_add_command(command)

    def call_create_command(self):
        command = deepcopy(self.template)
        dialog = self.edit_dialog_constructor(command)
        if not dialog.exec_():
            return
        self.call_add_command(dialog.command_data())
        self.valueSet.emit(self.commands_data())

    def call_add_command(self, command=None):
        widget = self.item_constructor(command)
        widget.editRequested.connect(self.edit_command)
        widget.deletedRequested.connect(self.delete_command)
        item = QtWidgets.QListWidgetItem()
        item.widget = widget
        item.setSizeHint(
            QtCore.QSize(
                self.commands.width() -
                self.commands.verticalScrollBar().width(),
                widget.sizeHint().height()))
        self.commands.addItem(item)
        self.commands.setItemWidget(item, widget)

    def edit_command(self, widget):
        for r in range(self.commands.count()):
            item = self.commands.item(r)
            if item.widget != widget:
                continue
            dialog = self.edit_dialog_constructor(item.widget.command)
            if not dialog.exec_():
                return
            widget.command = dialog.command_data()
            widget.update_label()
            self.valueSet.emit(self.commands_data())

    def delete_command(self, widget):
        for r in range(self.commands.count()):
            item = self.commands.item(r)
            if item.widget != widget:
                continue
            self.commands.takeItem(r)
            self.valueSet.emit(self.commands_data())
            return

    def commands_data(self):
        return [
            self.commands.item(r).widget.command
            for r in range(self.commands.count())]


class MenuCommandsEditor(CommandsEditor):
    edit_dialog_constructor = MenuCommandEditorDialog
    picker_command_key = 'action.menu_commands'
    template = MENU_COMMAND
    item_constructor = MenuCommandItemWidget


class GlobalCommandsEditor(CommandsEditor):
    edit_dialog_constructor = MenuCommandEditorDialog
    picker_command_key = 'menu_commands'
    template = MENU_COMMAND
    item_constructor = MenuCommandItemWidget

    def __init__(self, parent=None):
        super(GlobalCommandsEditor, self).__init__(parent)
        self.warning.hide()
        self.add_command.setEnabled(True)

    def set_options(self, options):
        self.commands.clear()
        for command in options[self.picker_command_key]:
            self.call_add_command(command)
