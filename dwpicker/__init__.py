
from dwpicker.main import DwPicker, WINDOW_CONTROL_NAME
from dwpicker.optionvar import ensure_optionvars_exists
from dwpicker.qtutils import remove_workspace_control


_dwpicker = None


def show(editable=True, pickers=None, ignore_scene_pickers=False):
    ensure_optionvars_exists()
    global _dwpicker
    if not _dwpicker:
        _dwpicker = DwPicker()

    try:
        _dwpicker.show(dockable=True)
    except RuntimeError:
        # Workspace control already exists, UI restore as probably failed.
        remove_workspace_control(WINDOW_CONTROL_NAME)
        _dwpicker.show()

    _dwpicker.set_editable(editable)
    if not ignore_scene_pickers:
        _dwpicker.load_saved_pickers()

    if not pickers:
        return

    _dwpicker.clear()
    for filename in pickers:
        try:
            print(filename)
            _dwpicker.add_picker_from_file(filename)
        except BaseException:
            import traceback
            print("Not able to load: {}".format(filename))
            print(traceback.format_exc())


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


class disable():
    """
    This context manager temporarily disable the picker callbacks.
    This is usefull to decorate code which change the maya selection multiple
    times. This can lead constant refresh of the picker and lead performance
    issue. This should fix it.
    """
    def __enter__(self):
        if _dwpicker is None:
            return
        _dwpicker.unregister_callbacks()
        for i in range(_dwpicker.tab.count()):
            picker = _dwpicker.tab.widget(i)
            picker.unregister_callbacks()

    def __exit__(self, *_):
        if _dwpicker is None:
            return
        _dwpicker.register_callbacks()
        for i in range(_dwpicker.tab.count()):
            picker = _dwpicker.tab.widget(i)
            picker.register_callbacks()


def current():
    """
    Get the current picker widget visible in the main tab widget.
    """
    if not _dwpicker:
        return
    return _dwpicker.tab.currentWidget()


def refresh():
    """
    Trigger this function to refresh ui if the picker datas has been changed
    manually inside the scene.
    """
    if not _dwpicker:
        return
    _dwpicker.load_saved_pickers()
