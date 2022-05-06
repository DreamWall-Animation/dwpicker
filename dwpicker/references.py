

import os
from dwpicker.dialog import MissingImages


IMAGE_MISSING_WARNING = (
    '\nImage is not found.\nWould you like to set a new path ?')


def ensure_images_path_exists(pickers):
    """
    As images are stored as path in the picker, this function ensure the paths
    exists. If not, it proposes to set a new path. If more than an image is not
    found, it will automatically look up into directories given in previous
    repath to find the images.
    """
    missing_images = list_missing_images(pickers)
    if not missing_images:
        return
    dialog = MissingImages(missing_images)
    result = dialog.exec_()
    if result != dialog.Accepted:
        return
    for picker_data in pickers:
        for shape in picker_data['shapes']:
            path = os.path.expandvars(shape['image.path'])
            if path in missing_images:
                new_path = dialog.output(path)
                if not new_path:
                    continue
                shape['image.path'] = new_path
    return pickers


def list_missing_images(pickers_data):
    return sorted(list(set([
        shape['image.path']
        for picker_data in pickers_data
        for shape in picker_data['shapes'] if
        shape['image.path'] and not
        os.path.exists(os.path.expandvars(shape['image.path']))])))