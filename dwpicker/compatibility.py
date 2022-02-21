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
    # version = picker_data['version']
    # if version < (youre version number):
    #     picker_data = your code update
    print("retro comp: ", picker_data)
    picker_data['version'] = VERSION
    return picker_data
