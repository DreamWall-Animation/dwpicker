import json
import os
from PySide2 import QtGui

from dwpicker.templates import PICKER, BUTTON, BACKGROUND
from dwpicker.ingest.animschool.parser import parse_animschool_picker, save_png


def rgb_to_hex(r, g, b):
    return '#{r:02x}{g:02x}{b:02x}'.format(r=r, g=g, b=b)


def _label_width(text):
    width = 0
    for letter in text:
        if letter == " ":
            width += 3
        elif letter.isupper():
            width += 7
        else:
            width += 6
    return width


def convert_to_picker_button(button):
    if len(button['label']):
        button['w'] = max((button['w'], _label_width(button['label'])))
    delta = {
        'text.content': button['label'],
        'shape.left': button['x'] - (button['w'] // 2),
        'shape.top': button['y'] - (button['h'] // 2),
        'shape.width': button['w'],
        'shape.height': button['h']}

    if button['action'] == 'select':
        delta['action.targets'] = button['targets']
        if len(button['targets']) > 1:
            delta['shape'] = 'rounded_square' if button['label'] else 'round'
            delta['shape.cornersx'] = delta['shape.width'] / 10
            delta['shape.cornersy'] = delta['shape.height'] / 10

    else:
        delta['action.left.language'] = button['lang']
        delta['action.left.command'] = button['targets'][0]

    delta['bgcolor.normal'] = rgb_to_hex(*button['bgcolor'])
    delta['text.color'] = rgb_to_hex(*button['txtcolor'])
    delta['border'] = button['action'] == 'command'
    delta['border'] = button['action'] == 'command'

    picker_button = BUTTON.copy()
    picker_button.update(delta)
    return picker_button


def frame_picker_buttons(picker):
    shapes = picker['shapes']
    offset_x = min(shape['shape.left'] for shape in shapes)
    offset_y = min(shape['shape.top'] for shape in shapes)
    offset = -min([offset_x, 0]), -min([offset_y, 0])

    for shape in shapes:
        shape['shape.left'] += offset[0]
        shape['shape.top'] += offset[1]


def fit_picker_to_content(picker):
    shapes = picker['shapes']
    width = max(s['shape.left'] + s['shape.width'] for s in shapes)
    height = max(s['shape.top'] + s['shape.height'] for s in shapes)
    picker['general']['width'] = int(width)
    picker['general']['height'] = int(height)


def image_to_background_shape(imagepath):
    shape = BACKGROUND.copy()
    shape['image.path'] = imagepath
    image = QtGui.QImage(imagepath)
    shape['image.width'] = image.size().width()
    shape['image.height'] = image.size().height()
    shape['shape.width'] = image.size().width()
    shape['shape.height'] = image.size().height()
    shape['bgcolor.transparency'] = 255
    return shape


def build_picker_from_pkr(title, buttons, imagepath, dst):
    picker = {
        'general': PICKER.copy(),
        'shapes': [convert_to_picker_button(b) for b in buttons]}
    picker['general']['name'] = title
    if imagepath:
        picker['shapes'].insert(0, image_to_background_shape(imagepath))
    frame_picker_buttons(picker)
    fit_picker_to_content(picker)
    with open(dst, "w") as f:
        json.dump(picker, f, indent=2)


def convert(filepath, directory=None):
    directory = directory or os.path.dirname(filepath)
    title, buttons, png_data = parse_animschool_picker(filepath)
    picker_filename = os.path.splitext(os.path.basename(filepath))[0]
    png_path = unique_filename(directory, picker_filename, 'png')
    png_path = png_path if png_data else None
    dst = unique_filename(directory, picker_filename, 'json')
    if png_path:
        save_png(png_data, png_path)
    build_picker_from_pkr(title, buttons, png_path, dst)
    return dst


def unique_filename(directory, filename, extension):
    filepath = os.path.join(directory, filename) + '.' + extension
    i = 0
    while os.path.exists(filepath):
        filepath = '{base}.{index}.{extension}'.format(
            base=os.path.join(directory, filename),
            index=str(i).zfill(3),
            extension=extension)
        i += 1
    return filepath
