import dwpicker
from dwpicker.namespace import detect_picker_namespace


picker = dwpicker.current()
if picker:
    namespace = detect_picker_namespace(picker.shapes)