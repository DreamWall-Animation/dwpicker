
import uuid
from collections import defaultdict
from PySide2 import QtCore
from dwpicker.interactive import Shape
from dwpicker.templates import PICKER
from dwpicker.undo import UndoManager
from dwpicker.stack import count_panels


class PickerDocument(QtCore.QObject):
    shapes_changed = QtCore.Signal()
    # origin: str ["editor"|"picker"], key: str
    general_option_changed = QtCore.Signal(str, str)
    data_changed = QtCore.Signal()
    changed = QtCore.Signal()

    def __init__(self, data):
        super(PickerDocument, self).__init__()
        self.data = data
        self.filename = None
        self.modified_state = False
        self.undo_manager = UndoManager(self.data)

        self.shapes = []
        self.shapes_by_panel = {}
        self.shapes_by_id = {}
        self.shapes_by_layers = {}
        self.generate_shapes()

        self.shapes_changed.connect(self.emit_change)
        self.general_option_changed.connect(self.emit_change)
        self.data_changed.connect(self.emit_change)
        self.shapes_changed.connect(self.emit_change)

    def emit_change(self, *_):
        """
        Signal allways emitted when any data of the model changed.
        """
        self.changed.emit()

    @staticmethod
    def create():
        data = {
            'general': PICKER.copy(),
            'shapes': []}
        return PickerDocument(data)

    def record_undo(self):
        self.undo_manager.set_data_modified(self.data)

    def undo(self):
        if self.undo_manager.undo():
            self.data = self.undo_manager.data
            self.generate_shapes()
            self.data_changed.emit()

    def redo(self):
        if self.undo_manager.redo():
            self.data = self.undo_manager.data
            self.generate_shapes()
            self.data_changed.emit()

    def panel_count(self):
        return count_panels(self.data['general']['panels'])

    def set_shapes_data(self, data):
        self.data['shapes'] = data
        self.generate_shapes()

    def generate_shapes(self):
        self.shapes = [Shape(options) for options in self.data['shapes']]
        self.sync_shapes_caches()

    def sync_shapes_caches(self):
        self.shapes_by_panel = defaultdict(list)
        self.shapes_by_id = {}
        self.shapes_by_layers = defaultdict(list)
        for shape in self.shapes:
            self.shapes_by_panel[shape.options['panel']].append(shape)
            self.shapes_by_id[shape.options['id']] = shape
            layer = shape.options['visibility_layer']
            if layer:
                self.shapes_by_layers[layer].append(shape)

    def add_shapes(self, shapes_data, prepend=False):
        for options in shapes_data:
            options['id'] = str(uuid.uuid4())

        shapes = [Shape(options) for options in shapes_data]
        if prepend:
            for shape in reversed(shapes):
                self.shapes.insert(0, shape)
                self.data['shapes'].insert(0, shapes_data)
        else:
            self.shapes.extend(shapes)
            self.data['shapes'].extend(shapes_data)

        self.sync_shapes_caches()
        self.undo_manager.set_data_modified(self.data)

    def remove_shapes(self, shapes):
        removed_ids = [shape.options['id'] for shape in shapes]
        self.data['shapes'] = [
            s for s in self.data['shapes'] if s['id'] not in removed_ids]
        self.generate_shapes()
