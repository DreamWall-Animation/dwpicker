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