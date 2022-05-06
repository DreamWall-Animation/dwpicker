

import os
from dwpicker.dialog import get_image_path, question


IMAGE_MISSING_WARNING = (
    '\nImage is not found.\nWould you like to set a new path ?')


def ensure_images_path_exists(picker_data):
    """
    As images are stored as path in the picker, this function ensure the paths
    exists. If not, it proposes to set a new path. If more than an image is not
    found, it will automatically look up into directories given in previous
    repath to find the images.
    """
    possible_directories = []
    for shape in picker_data['shapes']:
        path = os.path.expandvars(shape['image.path'])
        if path and not os.path.exists(path):
            basename = os.path.basename(path)
            for directory in possible_directories:
                possible_path = os.path.join(directory, basename)
                if os.path.exists(possible_path):
                    shape['image.path'] = possible_path
                    break
            else:
                msg = shape['image.path'] + IMAGE_MISSING_WARNING
                result = question('Repath image: ' + basename, msg)
                image_path = get_image_path() if result else ''
                if image_path:
                    shape['image.path'] = image_path
                    possible_directories.append(os.path.dirname(image_path))
    return picker_data
