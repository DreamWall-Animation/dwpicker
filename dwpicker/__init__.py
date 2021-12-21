
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
    This context manager is providen to decorated user code loop on maya
    selection edits. This can leadperformance issue.
    Apply that context ensure a safe context to run that code.
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
