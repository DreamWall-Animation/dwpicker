"""
The multiple nested namespaces is currently not supported by the namespace
switch system. This can cause issue for picker having to support sub namespace
on part of the rig.
This piece of code allow to set manually a namespace through the selected
shapes"""


import dwpicker

namespace = 'write:nested:namespace:here'
picker = dwpicker.current()

## Edit Shapes from picker view selection

# selection = [s for s in picker.shapes if s.selected]
# for shape in selection:
#     targets = [namespace + ':' + t.split(':')[-1] for t in shape.targets()]
#     shape.options['action.targets'] = targets

# dwpicker._dwpicker.data_changed_from_picker(picker)

## Edit Shapes from advanced editor selection

index = dwpicker._dwpicker.pickers.index(picker)
editor = dwpicker._dwpicker.editors[index]
if editor is None:
    raise RuntimeWarning("Please open current picker's avanced editor")

selection = editor.shape_editor.selection
for shape in selection:
    targets = [namespace + ':' + t.split(':')[-1] for t in shape.targets()]
    shape.options['action.targets'] = targets

editor.set_data_modified()