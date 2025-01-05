# Example for td which would like to create a include a picker in a custom ui
# this is most simple case possible to have it functionnal without using the
# main application.

import json
from dwpicker.interactive import Shape
from dwpicker.picker import PickerView
from dwpicker.qtutils import set_shortcut
from PySide2 import QtCore

view = PickerView(editable=False)
view.register_callbacks()
view.setWindowFlags(QtCore.Qt.Tool)
with open('-picker_file_path-', 'r') as f:
    data = json.load(f)
    view.set_picker_data(data)
view.reset()
set_shortcut('F', view, view.reset)

view.show()
