"""
This module contain a function to ingest picker done with older version.
If the structure changed, it can convert automatically the data to the new
version.
"""

from dwpicker.appinfos import VERSION


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
    return picker_data
