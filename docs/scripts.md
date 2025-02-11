# Scripts



### Reload Picker

A developper hack to reload the Dreamwall picker without having to restart
Maya each time.


```python
# If the picker is not in a known PYTHONPATH.
import sys
sys.path.insert(0, "<dwpicker path>")

# Code to clean modules and relaunch a Dreamwall picker with updated code.
try:
    # Important step to not let some callbacks left behind.
    dwpicker.close()
except:
    pass

for module in list(sys.modules):
    if "dwpicker" in module:
        print("deleted: " + module)
        del sys.modules[module]

import dwpicker
dwpicker.show()
```


### Create buttons to picker programmaticaly.

```python
from maya import cmds
import dwpicker
from dwpicker.templates import BUTTON


def add_button(options, refresh_ui=True):
    """
    @param dict options:
        This is a dictionnary of the shape options. List of possible options
        are can be found here dwpicker.templates.BUTTON
        (too much very many long to be documented here ;) )
    @param bool refresh_ui:
        this update the ui. Can be disabled for loop purpose.
    """
    button = BUTTON.copy()
    button.update(options)
    picker = dwpicker.current()
    if picker is None:
        cmds.warning('No picker found')
        return

    picker.document.add_shapes([button])

    if refresh_ui:
        picker.document.changed.emit()


options = {
    'text.content': 'Button',
    'shape.left': 250,
    'shape.top': 150,
    'shape.width': 120.0,
    'shape.height': 25.0,
}
add_button(options)
```


### Embeb custom picker widget.

Example for a TD who wants to include a picker in a custom UI:
This is the simplest possible setup to make it functional without relying on the main application.

```python
import json
from dwpicker.interactive import Shape
from dwpicker.document import PickerDocument
from dwpicker.picker import PickerStackedView
from dwpicker.qtutils import set_shortcut
from PySide2 import QtCore

with open('-picker_file_path-', 'r') as f:
    data = json.load(f)
document = PickerDocument(data)
view = PickerStackedView(document=document editable=False)
view.register_callbacks()
view.setWindowFlags(QtCore.Qt.Tool)
view.reset()
set_shortcut('F', view, view.reset)

view.show()
```