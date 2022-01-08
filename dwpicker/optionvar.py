import os
import sys
from maya import cmds


AUTO_FOCUS_ENABLE = 'dwpicker_auto_focus_enable'
BG_LOCKED = 'dwpicker_designer_background_items_locked'
DISPLAY_QUICK_OPTIONS = 'dwpicker_display_quick_options'
DEFAULT_TEXT_COLOR = 'dwpicker_default_text_color'
DEFAULT_BG_COLOR = 'dwpicker_default_background_color'
DEFAULT_LABEL = 'dwpicker_default_label_color'
DEFAULT_WIDTH = 'dwpicker_default_width'
DEFAULT_HEIGHT = 'dwpicker_default_height'
LAST_OPEN_DIRECTORY = 'dwpicker_last_file_open_directory'
LAST_SAVE_DIRECTORY = 'dwpicker_last_file_save_directory'
LAST_IMPORT_DIRECTORY = 'dwpicker_last_file_import_directory'
LAST_COMMAND_LANGUAGE = 'dwpicker_last_command_language_used'
OPENED_FILES = 'dwpicker_opened_files'
RECENT_FILES = 'dwpicker_recent_files'
SEARCH_FIELD_INDEX = 'dwpicker_designer_search_field_index'
SHAPES_FILTER_INDEX = 'dwpicker_designer_shape_filter_index'
SNAP_ITEMS = 'dwpicker_designer_snap_items'
SNAP_GRID_X = 'dwpicker_designer_snap_x'
SNAP_GRID_Y = 'dwpicker_designer_snap_y'


OPTIONVARS = {
    AUTO_FOCUS_ENABLE: 0,
    BG_LOCKED: 1,
    DISPLAY_QUICK_OPTIONS: 1,
    DEFAULT_TEXT_COLOR: '000000',
    DEFAULT_BG_COLOR: '#777777',
    DEFAULT_LABEL: '',
    DEFAULT_WIDTH: 30,
    DEFAULT_HEIGHT: 20,
    LAST_OPEN_DIRECTORY: os.path.expanduser("~"),
    LAST_SAVE_DIRECTORY: os.path.expanduser("~"),
    LAST_IMPORT_DIRECTORY: os.path.expanduser("~"),
    LAST_COMMAND_LANGUAGE: 0, # 0 = python, 1 = mel
    OPENED_FILES: '',
    RECENT_FILES: '',
    SEARCH_FIELD_INDEX: 0,
    SHAPES_FILTER_INDEX: 0,
    SNAP_ITEMS: 0,
    SNAP_GRID_X: 10,
    SNAP_GRID_Y: 10,
}


TYPES = {
    int: 'intValue',
    float: 'floatValue',
    str: 'stringValue'}


# Ensure backward compatibility.
if sys.version_info[0] == 2:
    TYPES[unicode] = 'stringValue'


def ensure_optionvars_exists():
    for optionvar, default_value in OPTIONVARS.items():
        if cmds.optionVar(exists=optionvar):
            continue
        save_optionvar(optionvar, default_value)


def save_optionvar(optionvar, value):
    kwargs = {TYPES.get(type(value)): [optionvar, value]}
    cmds.optionVar(**kwargs)


def save_opened_filenames(filenames):
    save_optionvar(OPENED_FILES, ";".join(filenames))


def append_recent_filename(filename):
    filename = os.path.normpath(filename)
    stored_filenames = cmds.optionVar(query=RECENT_FILES)
    if not stored_filenames:
        cmds.optionVar(stringValue=[RECENT_FILES, filename + ';'])
        return

    # Just reorder list if the filename is already in the recent filenames.
    stored_filenames = stored_filenames.split(';')
    for stored_filename in stored_filenames:
        if os.path.normpath(stored_filename) == filename:
            stored_filenames.remove(stored_filename)
            stored_filenames.insert(0, filename)
            cmds.optionVar(
                stringValue=[RECENT_FILES, ';'.join(stored_filenames)])
            return

    # Append to list if new filename.
    if len(stored_filenames) >= 10:
        stored_filenames = stored_filenames[:9]
    stored_filenames.insert(0, filename)
    cmds.optionVar(stringValue=[RECENT_FILES, ';'.join(stored_filenames)])

