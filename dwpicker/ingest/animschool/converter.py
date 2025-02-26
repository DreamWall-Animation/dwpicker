import json
import os
from dwpicker.pyside import QtGui

from dwpicker.compatibility import ensure_retro_compatibility
from dwpicker.ingest.animschool.parser import parse_animschool_picker, save_png


PICKER = {
    'name': 'Untitled',
    'version': (0, 15, 3),
    'panels.as_sub_tab': False,
    'panels.orientation': 'vertical',
    'panels.zoom_locked': [False],
    'panels.colors': [None],
    'panels.names': ['Panel 1'],
    'menu_commands': [],
    'hidden_layers': [],
    'panels': [[1.0, [1.0]]]
}

BUTTON = {
    'background': False,
    'visibility_layer': None,
    'shape.ignored_by_focus': False,
    'panel': 0,
    'shape': 'square',  # or round or rounded_rect or custom
    'shape.space': 'world',  # or screen
    'shape.anchor': 'top_left',  # or bottom_left, top_right, bottom_right
    'shape.path' : [],
    'shape.left': 0.0,
    'shape.top': 0.0,
    'shape.width': 120.0,
    'shape.height': 25.0,
    'shape.cornersx': 4,
    'shape.cornersy': 4,
    'border': True,
    'borderwidth.normal': 1.0,
    'borderwidth.hovered': 1.25,
    'borderwidth.clicked': 2,
    'bordercolor.normal': '#000000',
    'bordercolor.hovered': '#393939',
    'bordercolor.clicked': '#FFFFFF',
    'bordercolor.transparency': 0,
    'bgcolor.normal': '#888888',
    'bgcolor.hovered': '#AAAAAA',
    'bgcolor.clicked': '#DDDDDD',
    'bgcolor.transparency': 0,
    'text.content': 'Button',
    'text.size': 12,
    'text.bold': False,
    'text.italic': False,
    'text.color': '#FFFFFF',
    'text.valign': 'center',  # or 'top' or bottom
    'text.halign': 'center',  # or 'left' or 'right'
    'action.targets': [],
    'action.commands': [],
    'action.menu_commands': [],
    'image.path': '',
    'image.fit': True,
    'image.ratio': True,
    'image.height': 32,
    'image.width': 32
}


TEXT = {
    'background': False,
    'visibility_layer': None,
    'shape.ignored_by_focus': False,
    'panel': 0,
    'shape': 'square',  # or round or rounded_rect or custom
    'shape.space': 'world',  # or screen
    'shape.anchor': 'top_left',  # or bottom_left, top_right, bottom_right
    'shape.path' : [],
    'shape.left': 0.0,
    'shape.top': 0.0,
    'shape.width': 200.0,
    'shape.height': 50.0,
    'shape.cornersx': 4,
    'shape.cornersy': 4,
    'border': False,
    'borderwidth.normal': 0,
    'borderwidth.hovered': 0,
    'borderwidth.clicked': 0,
    'bordercolor.normal': '#000000',
    'bordercolor.hovered': '#393939',
    'bordercolor.clicked': '#FFFFFF',
    'bordercolor.transparency': 0,
    'bgcolor.normal': '#888888',
    'bgcolor.hovered': '#AAAAAA',
    'bgcolor.clicked': '#DDDDDD',
    'bgcolor.transparency': 255,
    'text.content': 'Text',
    'text.size': 16,
    'text.bold': True,
    'text.italic': False,
    'text.color': '#FFFFFF',
    'text.valign': 'top',  # or 'top' or bottom
    'text.halign': 'left',  # or 'left' or 'right'
    'action.targets': [],
    'action.commands': [],
    'action.menu_commands': [],
    'image.path': '',
    'image.fit': False,
    'image.ratio': True,
    'image.height': 32,
    'image.width': 32,
}


BACKGROUND = {
    'background': True,
    'visibility_layer': None,
    'shape.ignored_by_focus': True,
    'panel': 0,
    'shape': 'square',  # or round or rounded_rect or custom
    'shape.space': 'world',  # or screen
    'shape.anchor': 'top_left',  # or bottom_left, top_right, bottom_right
    'shape.path' : [],
    'shape.left': 0.0,
    'shape.top': 0.0,
    'shape.width': 400.0,
    'shape.height': 400.0,
    'shape.cornersx': 4,
    'shape.cornersy': 4,
    'border': False,
    'borderwidth.normal': 0,
    'borderwidth.hovered': 0,
    'borderwidth.clicked': 0,
    'bordercolor.normal': '#888888',
    'bordercolor.hovered': '#888888',
    'bordercolor.clicked': '#888888',
    'bordercolor.transparency': 0,
    'bgcolor.normal': '#888888',
    'bgcolor.hovered': '#888888',
    'bgcolor.clicked': '#888888',
    'bgcolor.transparency': 0,
    'text.content': '',
    'text.size': 12,
    'text.bold': False,
    'text.italic': False,
    'text.color': '#FFFFFF',
    'text.valign': 'center',  # or 'top' or bottom
    'text.halign': 'center',  # or 'left' or 'right'
    'action.targets': [],
    'action.commands': [],
    'action.menu_commands': [],
    'image.path': '',
    'image.fit': True,
    'image.ratio': False,
    'image.height': 32,
    'image.width': 32,
}


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
    ensure_retro_compatibility(picker)
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
