

_clipboard_data = None
_clipboard_settings_data = None


def set(data):
    global _clipboard_data
    _clipboard_data = data


def get():
    return _clipboard_data


def set_settings(settings):
    global _clipboard_settings_data
    _clipboard_settings_data = settings


def get_settings():
    return _clipboard_settings_data or {}
