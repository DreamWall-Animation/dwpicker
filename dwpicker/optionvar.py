import os
import sys
from maya import cmds


AUTO_FOCUS_BEHAVIORS = ['off', 'bilateral', 'pickertomaya']
ZOOM_BUTTONS = ["left", "middle", "right"]


AUTO_FOCUS_BEHAVIOR = 'dwpicker_auto_focus_behavior'
AUTO_SWITCH_TAB = 'dwpicker_auto_switch_tab'
BG_LOCKED = 'dwpicker_designer_background_items_locked'
CHECK_IMAGES_PATHS = 'dwpicker_check_images_paths'
CHECK_FOR_UPDATE = 'dwpicker_check_for_update'
DEFAULT_BG_COLOR = 'dwpicker_default_background_color'
DEFAULT_LABEL = 'dwpicker_default_label_color'
DEFAULT_HEIGHT = 'dwpicker_default_height'
DEFAULT_TEXT_COLOR = 'dwpicker_default_text_color'
DEFAULT_WIDTH = 'dwpicker_default_width'
DISABLE_IMPORT_CALLBACKS = 'dwpicker_disable_import_callbacks'
DISPLAY_QUICK_OPTIONS = 'dwpicker_display_quick_options'
INSERT_TAB_AFTER_CURRENT = 'dwpicker_insert_tab_after_current'
LAST_COMMAND_LANGUAGE = 'dwpicker_last_command_language_used'
LAST_IMAGE_DIRECTORY_USED = 'dwpicker_last_directory_used'
LAST_IMPORT_DIRECTORY = 'dwpicker_last_file_import_directory'
LAST_OPEN_DIRECTORY = 'dwpicker_last_file_open_directory'
LAST_SAVE_DIRECTORY = 'dwpicker_last_file_save_directory'
OPENED_FILES = 'dwpicker_opened_files'
NAMESPACE_TOOLBAR = 'dwpicker_display_dwtoolbar'
RECENT_FILES = 'dwpicker_recent_files'
SEARCH_FIELD_INDEX = 'dwpicker_designer_search_field_index'
SETTINGS_GROUP_TO_COPY = 'dwpicker_settings_group_to_copy'
SETTINGS_TO_COPY = 'dwpicker_settings_to_copy'
SHAPES_FILTER_INDEX = 'dwpicker_designer_shape_filter_index'
SNAP_ITEMS = 'dwpicker_designer_snap_items'
SNAP_GRID_X = 'dwpicker_designer_snap_x'
SNAP_GRID_Y = 'dwpicker_designer_snap_y'
SYNCHRONYZE_SELECTION = 'dwpicker_synchronize_selection'
TRIGGER_REPLACE_ON_MIRROR = 'dwpicker_trigger_search_and_replace_on_mirror'
USE_BASE64_DATA_ENCODING = 'dwpicker_use_base64_data_encoding'
USE_ICON_FOR_UNSAVED_TAB = 'dwpicker_use_icon_for_unsaved_tab'
ZOOM_BUTTON = 'dwpicker_picker_zoom_mouse_button'
WARN_ON_TAB_CLOSED = 'dwpicker_warn_on_tab_closed'
ZOOM_SENSITIVITY = 'dwpicker_zoom_sensitivity'


OPTIONVARS = {
    AUTO_FOCUS_BEHAVIOR: AUTO_FOCUS_BEHAVIORS[-1],
    AUTO_SWITCH_TAB: 0,
    BG_LOCKED: 1,
    CHECK_IMAGES_PATHS: 1,
    CHECK_FOR_UPDATE: 1,
    DEFAULT_BG_COLOR: '#777777',
    DEFAULT_HEIGHT: 20,
    DEFAULT_LABEL: '',
    DEFAULT_TEXT_COLOR: '#000000',
    DEFAULT_WIDTH: 30,
    DISABLE_IMPORT_CALLBACKS: 1,
    DISPLAY_QUICK_OPTIONS: 1,
    INSERT_TAB_AFTER_CURRENT: 0,
    LAST_OPEN_DIRECTORY: os.path.expanduser("~"),
    LAST_SAVE_DIRECTORY: os.path.expanduser("~"),
    LAST_IMPORT_DIRECTORY: os.path.expanduser("~"),
    LAST_COMMAND_LANGUAGE: 0,  # 0 = python, 1 = mel
    LAST_IMAGE_DIRECTORY_USED: os.path.expanduser("~"),
    NAMESPACE_TOOLBAR: 0,
    OPENED_FILES: '',
    RECENT_FILES: '',
    SEARCH_FIELD_INDEX: 0,
    SHAPES_FILTER_INDEX: 0,
    SETTINGS_GROUP_TO_COPY: 'bordercolor;text;image;bgcolor;shape;borderwidth;border',
    SETTINGS_TO_COPY: (
        'bgcolor.clicked;bgcolor.hovered;bgcolor.normal;bgcolor.transparency;'
        'border;bordercolor.clicked;bordercolor.hovered;bordercolor.normal;'
        'bordercolor.transparency;borderwidth.clicked;borderwidth.hovered;'
        'borderwidth.normal;image.fit;image.height;image.width;shape;'
        'shape.cornersx;shape.cornersy;shape.height;shape.left;'
        'shape.top;shape.width;text.bold;text.color;text.halign;text.italic;'
        'text.size;text.valign'),
    SNAP_ITEMS: 0,
    SNAP_GRID_X: 10,
    SNAP_GRID_Y: 10,
    SYNCHRONYZE_SELECTION: 1,
    TRIGGER_REPLACE_ON_MIRROR: 0,
    USE_BASE64_DATA_ENCODING: 0,
    USE_ICON_FOR_UNSAVED_TAB: 1,
    WARN_ON_TAB_CLOSED: 0,
    ZOOM_BUTTON: ZOOM_BUTTONS[2],
    ZOOM_SENSITIVITY: 50
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
