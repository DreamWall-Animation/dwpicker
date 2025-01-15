"""
This module contain a function to ingest picker done with older version.
If the structure changed, it can convert automatically the data to the new
version.
"""

from dwpicker.appinfos import VERSION
from dwpicker.stack import count_splitters


def ensure_retro_compatibility(picker_data):
    """
    This function ensure retro compatibility.
    """
    # If a new release involve a data structure change in the picker, implement
    # the way to update the data here using this pattern:
    #
    # if version < (youre version number):
    #     picker_data = your code update
    version = picker_data['general'].get('version') or (0, 0, 0)
    picker_data['general']['version'] = VERSION

    if tuple(version) < (0, 3, 0):
        # Add new options added to version 0, 3, 0.
        picker_data['general']['zoom_locked'] = False

    if tuple(version) < (0, 4, 0):
        picker_data['general'].pop('centerx')
        picker_data['general'].pop('centery')

    if tuple(version) < (0, 10, 0):
        for shape in picker_data['shapes']:
            shape['visibility_layer'] = None

    if tuple(version) < (0, 11, 0):
        for shape in picker_data['shapes']:
            update_shape_actions_for_v0_11_0(shape)

    if tuple(version) < (0, 11, 3):
        for shape in picker_data['shapes']:
            shape['background'] = not (
                any(cmd['enabled'] for cmd in shape['action.commands']) or
                shape['action.targets'])

    if tuple(version) < (0, 12, 0):
        for shape in picker_data['shapes']:
            shape['action.menu_commands'] = []

    if tuple(version) < (0, 12, 1):
        picker_data['general'].pop('width')
        picker_data['general'].pop('height')

    if tuple(version) < (0, 14, 0):
        for shape in picker_data['shapes']:
            shape['shape.path'] = []

    if tuple(version) < (0, 14, 1):
        picker_data['general']['menu_commands'] = []

    if tuple(version) < (0, 15, 0):
        picker_data['general']['panels'] = [[1.0, [1.0]]]
        picker_data['general']['panels.orientation'] = 'vertical'
        zoom_locked = picker_data['general']['zoom_locked']
        picker_data['general']['panels.zoom_locked'] = [zoom_locked]
        del picker_data['general']['zoom_locked']
        for shape in picker_data['shapes']:
            shape['panel'] = 0
            shape['shape.space'] = 'world'
            shape['shape.anchor'] = 'top_left'

    if tuple(version) < (0, 15, 2):
        picker_data['general']['hidden_layers'] = []

    if tuple(version) < (0, 15, 3):
        picker_data['general']['panels.as_sub_tab'] = False
        picker_data['general']['panels.colors'] = [None]
        picker_data['general']['panels.names'] = ['Panel 1']
        ensure_general_options_sanity(picker_data['general'])

    return picker_data


def ensure_general_options_sanity(options):
    split_count = count_splitters(options['panels'])
    while split_count > len(options['panels.zoom_locked']):
        options['panels.zoom_locked'].append(False)
    while split_count > len(options['panels.colors']):
        options['panels.colors'].append(None)
    while split_count > len(options['panels.names']):
        name = 'Panel' + str(len(options["panels.names"]))
        options['panels.names'].append(name)


def update_shape_actions_for_v0_11_0(shape):
    """
    With release 0.11.0 comes a new configurable action system.
    """
    if 'action.namespace' in shape:
        del shape['action.namespace']
    if 'action.type' in shape:
        del shape['action.type']

    shape['action.commands'] = []

    if shape['action.left.command']:
        shape['action.commands'].append({
            'enabled': shape['action.left'],
            'button': 'left',
            'language': shape['action.left.language'],
            'command': shape['action.left.command'],
            'alt': False,
            'ctrl': False,
            'shift': False,
            'deferred': False,
            'force_compact_undo': False})

    if shape['action.right.command']:
        shape['action.commands'].append({
            'enabled': shape['action.right'],
            'button': 'left',
            'language': shape['action.right.language'],
            'command': shape['action.right.command'],
            'alt': False,
            'ctrl': False,
            'shift': False,
            'deferred': False,
            'force_compact_undo': False})

    keys_to_clear = (
        'action.left', 'action.left.language',
        'action.left.command', 'action.right', 'action.right.language',
        'action.right.command')

    for key in keys_to_clear:
        del shape[key]
