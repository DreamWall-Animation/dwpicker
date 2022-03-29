# Example for td which would like to create a include a picker in a custom ui
# this is most simple case possible to have it functionnal without using the
# main application.

import json
from dwpicker.interactive import Shape
from dwpicker.picker import PickerView
from dwpicker.qtutils import set_shortcut
from PySide2 import QtCore

with open('-picker_file_path-', 'r') as f:
    data = json.load(f)
    shapes = [Shape(shape) for shape in data['shapes']]

view = PickerView(editable=False)
view.register_callbacks()
view.setWindowFlags(QtCore.Qt.Tool)
view.set_shapes(shapes)
set_shortcut('F', view, view.reset)

view.show()

