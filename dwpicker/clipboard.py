

_clipboard_data = None


def set(data):
    global _clipboard_data
    _clipboard_data = data


def get():
    return _clipboard_data
