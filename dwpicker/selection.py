
from maya import cmds


class NameclashError(BaseException):
    def __init__(self, nodes=None):
        self.clashes = [node for node in nodes or [] if len(cmds.ls(node)) > 1]
        message = 'Some nodes exists more than once:\n'
        nodes = '\n  - '.join(self.clashes)
        super(NameclashError, self).__init__(message + nodes)


def select_targets(shapes, selection_mode='replace'):
    shapes = [s for s in shapes if s.targets()]
    hovered = [s for s in shapes if s.hovered]
    targets = [t for s in hovered for t in s.targets() if cmds.objExists(t)]
    targets = list(dict.fromkeys(targets))

    current_selection = cmds.ls(selection=True, long=True)
    targets_selection = cmds.ls(targets, long=True)

    if len(set(targets_selection)) != len(set(targets)):
        raise NameclashError(targets)
    if selection_mode == 'add':
        new_selection = list(
            dict.fromkeys(current_selection + targets_selection))
    elif selection_mode == 'replace':
        new_selection = targets_selection
    elif selection_mode == 'invert':
        new_selection = current_selection[:]
        for target in targets_selection:
            if target not in new_selection:
                new_selection.append(target)
            else:
                new_selection.remove(target)
    elif selection_mode == 'remove':
        new_selection = [
            s for s in current_selection if s not in targets_selection]
    else:
        raise NotImplementedError(
            'Unsupported selection mode {}'.format(selection_mode))

    # Only call cmds.select if it will actually change the selection.
    # This is needed to prevent "empty undoes", where Maya will register an
    # undo for all calls to cmds.select.
    # SEE: https://forums.autodesk.com/t5/maya-ideas/consolidate-undo-steps-for-selection/idi-p/13331011
    if current_selection != new_selection:
        cmds.select(new_selection)


def select_shapes_from_selection(shapes):
    selection = cmds.ls(sl=True)
    for shape in shapes:
        if not shape.targets():
            shape.selected = False
            continue
        for target in shape.targets():
            if target not in selection:
                shape.selected = False
                break
        else:
            shape.selected = True


class Selection():
    def __init__(self, document=None):
        self.document = document
        self.ids = []
        self.mode = 'replace'

    def set(self, shapes):
        if self.mode == 'add':
            if shapes is None:
                return
            return self.add(shapes)
        elif self.mode == 'replace':
            if shapes is None:
                return self.clear()
            return self.replace(shapes)
        elif self.mode == 'invert':
            if shapes is None:
                return
            return self.invert(shapes)
        elif self.mode == 'remove':
            if shapes is None:
                return
            for shape in shapes:
                if shape in self.shapes:
                    self.remove(shape)

    def replace(self, shapes):
        self.ids = [s.options['id'] for s in shapes]

    def add(self, shapes):
        self.ids.extend([s.options['id'] for s in shapes if s not in self])

    def remove(self, shape):
        self.ids.remove(shape.options['id'])

    def invert(self, shapes):
        for shape in shapes:
            if shape.options['id'] not in self.ids:
                self.add([shape])
            else:
                self.remove(shape)

    @property
    def shapes(self):
        shapes = [self.document.shapes_by_id.get(id_) for id_ in self.ids]
        return [shape for shape in shapes if shape is not None]

    def clear(self):
        self.ids = []

    def __len__(self):
        return len(self.ids)

    def __bool__(self):
        return bool(self.ids)

    __nonzero__ = __bool__

    def __getitem__(self, i):
        return self.document.shapes_by_id[self.ids[i]]

    def __iter__(self):
        return self.shapes.__iter__()


def get_selection_mode(ctrl, shift):
    if not ctrl and not shift:
        return 'replace'
    elif ctrl and shift:
        return 'invert'
    elif shift:
        return 'add'
    return 'remove'
