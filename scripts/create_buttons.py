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