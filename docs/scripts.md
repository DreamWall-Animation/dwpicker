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
import dwpicker
from dwpicker.scenedata import load_local_picker_data, store_local_picker_data
from dwpicker.templates import BUTTON


def add_button(index, options, refresh_ui=True):
    """
    This works with pick closed as well.
    @param int index: the tab position of the dwpicker.
    @param dict options:
        This is a dictionnary of the shape options. List of possible options
        are can be found here dwpicker.templates.BUTTON
        (too much very many long to be documented here ;) )
    @param bool refresh_ui:
        this update the ui. Can be disabled for loop purpose.
    """
    pickers = load_local_picker_data()
    button = BUTTON.copy()
    button.update(options)
    pickers[index]['shapes'].append(button)
    store_local_picker_data(pickers)
    if refresh_ui:
        dwpicker.refresh()


options = {
    'text.content': 'Button',
    'shape.left': 250,
    'shape.top': 150,
    'shape.width': 120.0,
    'shape.height': 25.0,
}
add_button(0, options)
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