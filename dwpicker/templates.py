from dwpicker.appinfos import VERSION


BUTTON = {
    'background': False,
    'visibility_layer': None,
    'shape': 'square',  # or round
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
    'image.height': 32,
    'image.width': 32}


TEXT = {
    'background': False,
    'visibility_layer': None,
    'shape': 'square',  # or round
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
    'image.height': 32,
    'image.width': 32}


BACKGROUND = {
    'background': True,
    'visibility_layer': None,
    'shape': 'square',  # or round or rounded_rect
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
    'image.fit': False,
    'image.height': 32,
    'image.width': 32}


COMMAND = {
    'enabled': True,
    'button': 'left',  # right
    'language': 'python',  # or mel
    'command': '',
    'ctrl': False,
    'shift': False,
    'deferred': False,
    'force_compact_undo': False,
}


MENU_COMMAND = {
    'caption': '',
    'language': 'python',  # or mel
    'command': '',
    'deferred': False,
    'force_compact_undo': False,
}


PICKER = {
    'name': 'Untitled',
    'version': VERSION,
    'zoom_locked': False,
}
