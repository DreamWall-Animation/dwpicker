

import os
import uuid
from maya import cmds
from dwpicker.pyside import QtWidgets
from dwpicker.optionvar import (
    AUTO_COLLAPSE_IMG_PATH_FROM_ENV, CUSTOM_PROD_PICKER_DIRECTORY,
    LAST_IMPORT_DIRECTORY, LAST_IMAGE_DIRECTORY_USED, LAST_OPEN_DIRECTORY,
    OVERRIDE_PROD_PICKER_DIRECTORY_ENV, USE_PROD_PICKER_DIR_AS_DEFAULT,
    save_optionvar)



def unix_path(path, isroot=False):
    path = path.replace('\\', '/')
    condition = (
        os.name == 'nt' and
        isroot and
        path.startswith('/') and
        not path.startswith('//'))

    if condition:
        path = '/' + path

    path = path.rstrip(r'\/')
    return path


def format_path(path):
    if path is None:
        return
    path = unix_path(path)
    if not cmds.optionVar(query=AUTO_COLLAPSE_IMG_PATH_FROM_ENV):
        return path
    root = get_picker_project_directory()
    if not root or not path.lower().startswith(root.lower()):
        return path
    return '$DWPICKER_PROJECT_DIRECTORY/{}'.format(
        path[len(root):].lstrip('/'))


def get_picker_project_directory():
    if cmds.optionVar(query=OVERRIDE_PROD_PICKER_DIRECTORY_ENV):
        path = cmds.optionVar(query=CUSTOM_PROD_PICKER_DIRECTORY)
        return unix_path(path) if path else None
    path = os.getenv('DWPICKER_PROJECT_DIRECTORY')
    return unix_path(path) if path else None


def expand_path(path):
    backup = None
    if cmds.optionVar(query=OVERRIDE_PROD_PICKER_DIRECTORY_ENV):
        root = unix_path(cmds.optionVar(query=CUSTOM_PROD_PICKER_DIRECTORY))
        backup = os.getenv('DWPICKER_PROJECT_DIRECTORY')
        os.environ['DWPICKER_PROJECT_DIRECTORY'] = root
    result = os.path.expandvars(path)
    if backup:
        os.environ['DWPICKER_PROJECT_DIRECTORY'] = backup
    return result


def get_open_directory():
    if cmds.optionVar(query=USE_PROD_PICKER_DIR_AS_DEFAULT):
        directory = get_picker_project_directory()
        if directory:
            return directory
    return cmds.optionVar(query=LAST_OPEN_DIRECTORY)


def get_import_directory():
    if cmds.optionVar(query=USE_PROD_PICKER_DIR_AS_DEFAULT):
        directory = get_picker_project_directory()
        if directory:
            return directory
    return cmds.optionVar(query=LAST_IMPORT_DIRECTORY)


def get_image_directory():
    if cmds.optionVar(query=USE_PROD_PICKER_DIR_AS_DEFAULT):
        directory = get_picker_project_directory()
        if directory:
            return directory
    return cmds.optionVar(query=LAST_IMAGE_DIRECTORY_USED)

def get_filename():
    folder_path = get_picker_project_directory()
    if not folder_path:
        folder_path = QtWidgets.QFileDialog.getExistingDirectory(None,
                                                                 "Select Directory",
                                                                 "")
        if folder_path:
            save_optionvar(LAST_IMAGE_DIRECTORY_USED, folder_path)
        else:
            folder_path = cmds.optionVar(query=LAST_IMAGE_DIRECTORY_USED)

    filename = os.path.join(folder_path, "dwpicker-" + str(uuid.uuid4()))

    return filename