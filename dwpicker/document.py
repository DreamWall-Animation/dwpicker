
import uuid
from copy import deepcopy
from collections import defaultdict
from PySide2 import QtCore
from dwpicker.shape import Shape
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
        self.shapes_by_layer = {}
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
            'general': deepcopy(PICKER),
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
        self.shapes_by_layer = defaultdict(list)
        for shape in self.shapes:
            self.shapes_by_panel[shape.options['panel']].append(shape)
            self.shapes_by_id[shape.options['id']] = shape
            layer = shape.options['visibility_layer']
            if layer:
                self.shapes_by_layer[layer].append(shape)

    def add_shapes(self, shapes_data, prepend=False, hierarchize=False):
        for options in shapes_data:
            options['id'] = str(uuid.uuid4())
            options['children'] = []

        shapes = []
        parent_shape = None
        for options in shapes_data:
            shape = Shape(options)
            shapes.append(shape)
            if parent_shape and hierarchize:
                parent_shape.options['children'].append(shape.options['id'])
            parent_shape = shape

        if prepend:
            for shape in reversed(shapes):
                self.shapes.insert(0, shape)
                self.data['shapes'].insert(0, shape.options)
        else:
            self.shapes.extend(shapes)
            self.data['shapes'].extend(shapes_data)

        self.sync_shapes_caches()
        return shapes

    def remove_shapes(self, shapes):
        removed_ids = [shape.options['id'] for shape in shapes]
        self.data['shapes'] = [
            s for s in self.data['shapes'] if s['id'] not in removed_ids]
        self.generate_shapes()

    def all_children(self, id_):
        if id_ not in self.shapes_by_id:
            return []

        shape = self.shapes_by_id[id_]
        result = []
        to_visit = [id_]
        visited = set()

        while to_visit:
            current_id = to_visit.pop(0)

            if current_id in visited:
                continue

            visited.add(current_id)
            shape = self.shapes_by_id.get(current_id)

            if shape:
                result.append(shape)
                children = shape.options.get('children', [])
                to_visit.extend(c for c in children if c not in visited)

        return result