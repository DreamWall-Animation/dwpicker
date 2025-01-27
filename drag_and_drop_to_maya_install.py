import os
import shiboken2
import shutil
from PySide2 import QtWidgets, QtCore

from maya import cmds, mel
import maya.OpenMayaUI as omui


RELATIVE_INSTALL_COMMAND = """
import os
import sys
from maya import cmds

if not os.path.exists(r'{path}'):
    message = (
        "DreamWall Picker folder is missing!\\n"
        "Did you moved the installation folder ?\\n"
        "Please re-install.")
    cmds.confirmDialog(message=message, button=["ok"])
    raise FileNotFoundError('DreamWall Picker is gone :/')

if r'{path}' not in sys.path:
    sys.path.insert(0, r'{path}')

import dwpicker
dwpicker.show()
"""


def get_maya_window():
    if os.name == 'posix':
        return None
    ptr = omui.MQtUtil.mainWindow()
    if ptr is not None:
        return shiboken2.wrapInstance(int(ptr), QtWidgets.QWidget)


def list_shelves():
    shelf_layout = "ShelfLayout"
    if cmds.layout(shelf_layout, exists=True):
        shelves = cmds.layout(shelf_layout, query=True, childArray=True)
        return shelves
    else:
        return []


def get_active_shelf():
    if cmds.shelfTabLayout("ShelfLayout", exists=True):
        active_shelf = cmds.shelfTabLayout(
            "ShelfLayout", query=True, selectTab=True)
        return active_shelf
    else:
        return None


def get_user_scripts_dir():
    user_dir = cmds.internalVar(userAppDir=True)
    scripts_dir = os.path.join(
        user_dir, cmds.about(majorVersion=True), "scripts")
    return scripts_dir


class InstallOptions(QtWidgets.QDialog):
    def __init__(self):
        super(InstallOptions, self).__init__(get_maya_window())
        self.setWindowTitle('Install DreamWall Picker')
        self.mayafolder = QtWidgets.QRadioButton('Into Maya scripts folder.')
        self.mayafolder.setChecked(True)
        self.relative = QtWidgets.QRadioButton('From current folder.')

        self.button_group = QtWidgets.QButtonGroup()
        self.button_group.addButton(self.relative, 0)
        self.button_group.addButton(self.mayafolder, 1)

        self.shelves = QtWidgets.QListWidget()
        self.add_shelves()
        self.shelf_name = QtWidgets.QLineEdit()
        self.shelf_name.setEnabled(False)
        self.shelf_name.setText('DWPicker')

        self.add_to_existing_shelf = QtWidgets.QRadioButton('Add to Shelf')
        self.add_to_existing_shelf.setChecked(True)
        self.add_to_existing_shelf.toggled.connect(self.shelves.setEnabled)
        self.create_shelf = QtWidgets.QRadioButton('Create Shelf')
        self.create_shelf.toggled.connect(self.shelf_name.setEnabled)

        self.button_group2 = QtWidgets.QButtonGroup()
        self.button_group2.addButton(self.add_to_existing_shelf, 0)
        self.button_group2.addButton(self.create_shelf, 1)

        install = QtWidgets.QPushButton('Install')
        install.released.connect(self.accept)
        cancel = QtWidgets.QPushButton('Cancel')
        cancel.released.connect(self.reject)

        group = QtWidgets.QGroupBox('Location')
        radios = QtWidgets.QVBoxLayout(group)
        radios.addWidget(self.mayafolder)
        radios.addWidget(self.relative)

        group_2 = QtWidgets.QGroupBox('Shelf')
        shelf_options = QtWidgets.QVBoxLayout(group_2)
        shelf_options.addWidget(self.add_to_existing_shelf)
        shelf_options.addWidget(self.shelves)
        shelf_options.addWidget(self.create_shelf)
        shelf_options.addWidget(self.shelf_name)

        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(install)
        buttons.addWidget(cancel)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(group)
        layout.addWidget(group_2)
        layout.addLayout(buttons)

    def add_shelves(self):
        shelves = list_shelves()
        if not shelves:
            return

        self.shelves.addItems(shelves)
        active_shelf = get_active_shelf()
        if not active_shelf and 'Custom' in shelves:
            active_shelf = 'Custom'
        elif not active_shelf:
            active_shelf = shelves[0]
        items = self.shelves.findItems(active_shelf, QtCore.Qt.MatchExactly)
        self.shelves.setCurrentItem(items[0])

    def is_relative_install(self):
        return self.relative.isChecked()

    def is_create_shelf(self):
        return self.create_shelf.isChecked()

    def get_shelf_name(self):
        if self.is_create_shelf():
            return self.shelf_name.text()
        return self.shelves.selectedItems()[0].text()


def onMayaDroppedPythonFile(*_):
    dwpicker_directory = os.path.join(os.path.dirname(__file__))
    dwpicker_directory = os.path.normpath(dwpicker_directory)
    dialog = InstallOptions()
    if not dialog.exec_():
        return

    if dialog.is_relative_install():
        command = RELATIVE_INSTALL_COMMAND.format(path=dwpicker_directory)
        icon_path = os.path.join(
            dwpicker_directory, 'dwpicker/icons/dreamwallpicker.png')

    else:
        destination = os.path.join(get_user_scripts_dir(), 'dwpicker')
        source = os.path.join(dwpicker_directory, 'dwpicker')
        if os.path.exists(destination):
            result = QtWidgets.QMessageBox.question(
                get_maya_window(), 'Warning',
                ('DwPicker seems already installed,'
                 '\nWould you like to replace it ?'))
            if result == QtWidgets.QMessageBox.No:
                return
            shutil.rmtree(destination)
        shutil.copytree(source, destination)
        command = "import dwpicker;dwpicker.show()"
        icon_path = os.path.join(destination, 'icons/dreamwallpicker.png')

    shelf_name = dialog.get_shelf_name()
    if dialog.is_create_shelf():
        cmds.shelfLayout(shelf_name, parent='ShelfLayout')

    # shelf = mel.eval('$gShelfTopLevel=$gShelfTopLevel')
    cmds.shelfButton(
        command=command,
        image=icon_path,
        sourceType='python',
        annotation='DreamWall Picker',
        parent=shelf_name)
    cmds.shelfTabLayout('ShelfLayout', edit=True, selectTab=shelf_name)
