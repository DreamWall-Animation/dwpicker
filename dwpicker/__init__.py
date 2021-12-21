
from dwpicker.main import DwPicker
from dwpicker.optionvar import ensure_optionvars_exists
from contextlib import contextmanager


_dwpicker = None


def show():
    ensure_optionvars_exists()
    global _dwpicker
    if not _dwpicker:
        _dwpicker = DwPicker()
    _dwpicker.show(dockable=True)
    _dwpicker.register_callbacks()
    _dwpicker.load_saved_pickers()


def close():
    global _dwpicker
    if not _dwpicker:
        return

    _dwpicker.unregister_callbacks()
    for i in range(_dwpicker.tab.count()):
        picker = _dwpicker.tab.widget(i)
        picker.unregister_callbacks()

    _dwpicker.close()
    _dwpicker = None


@contextmanager
def disable():
    '''
    This context manager temporarily disable the picker callbacks.
    This is usefull to decorate code which change the maya selection multiple
    times. This can lead constant refresh of the picker and lead performance
    issue. This should fix it.
    '''
    try:
        if _dwpicker:
            _dwpicker.unregister_callbacks()
            for i in range(_dwpicker.tab.count()):
                picker = _dwpicker.tab.widget(i)
                picker.unregister_callbacks()
        yield
    finally:
        if _dwpicker is None:
            return
        _dwpicker.register_callbacks()
        for i in range(_dwpicker.tab.count()):
            picker = _dwpicker.tab.widget(i)
            picker.register_callbacks()
