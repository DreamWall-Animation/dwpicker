
import os
import sys
from maya import cmds


if int(cmds.about(majorVersion=True)) >= 2025:
    print('>> PySide6 Maya version found. PySide2 remap activated.')
    sys.path.append(f'{os.path.dirname(__file__)}/qt_remapping')


from dwpicker.main import DwPicker, WINDOW_CONTROL_NAME
from dwpicker.optionvar import ensure_optionvars_exists
from dwpicker.qtutils import remove_workspace_control
from dwpicker.updatechecker import warn_if_update_available


_dwpicker = None


def show(editable=True, pickers=None, ignore_scene_pickers=False):
    """
    This is the dwpicker default startup function.
    editable: bool
        This allow users to do local edit on their picker. This is NOT
        affecting the original file.
    pickers: list[str]
        Path to pickers to open. If scene contains already pickers,
        they are going to be ignored.
    ignore_scene_pickers:
        This is loading the picker empty, ignoring the scene content.
    """
    ensure_optionvars_exists()
    global _dwpicker
    if not _dwpicker:
        warn_if_update_available()
        _dwpicker = DwPicker()

    try:
        _dwpicker.show(dockable=True)
    except RuntimeError:
        # Workspace control already exists, UI restore as probably failed.
        remove_workspace_control(WINDOW_CONTROL_NAME)
        _dwpicker.show()

    _dwpicker.set_editable(editable)
    if not ignore_scene_pickers and not pickers:
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
    _dwpicker.store_local_pickers_data()


def toggle():
    if not _dwpicker:
        return show()
    _dwpicker.setVisible(not _dwpicker.isVisible())


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


def open_picker_file(filepath):
    """
    Add programmatically a picker to the main UI.
    """
    if not _dwpicker:
        return cmds.warning('Please open picker first.')
    _dwpicker.add_picker_from_file(filepath)
    _dwpicker.store_local_pickers_data()
