

import os
from maya import cmds
from dwpicker.optionvar import (
    AUTO_COLLAPSE_IMG_PATH_FROM_ENV, CUSTOM_PROD_PICKER_DIRECTORY,
    OVERRIDE_PROD_PICKER_DIRECTORY_ENV)


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
    path = unix_path(path)
    if not cmds.optionVar(query=AUTO_COLLAPSE_IMG_PATH_FROM_ENV):
        return path
    if cmds.optionVar(query=OVERRIDE_PROD_PICKER_DIRECTORY_ENV):
        root = unix_path(cmds.optionVar(query=CUSTOM_PROD_PICKER_DIRECTORY))
    else:
        root = unix_path(os.getenv('DWPICKER_PROJECT_DIRECTORY'))
    if not root or not path.lower().startswith(root.lower()):
        return path
    return '$DWPICKER_PROJECT_DIRECTORY/{}'.format(
        path[len(root):].lstrip('/'))


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
