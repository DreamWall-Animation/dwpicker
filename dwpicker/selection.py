
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

    if selection_mode in ('add', 'replace', 'invert'):
        try:
            return cmds.select(list(targets), add=selection_mode == 'add')
        except ValueError:
            raise NameclashError(targets)
    elif selection_mode == 'remove':
        selection = [n for n in cmds.ls(sl=True) if n not in targets]
        try:
            return cmds.select(selection)
        except ValueError:
            raise NameclashError(targets)

    # Invert selection
    selected = [s for s in shapes if s.selected]
    to_select = [s for s in shapes if s in hovered and s not in selected]
    # List targets unaffected by selection
    targets = {
        t for s in selected for t in s.targets()
        if cmds.objExists(t) and not s.hovered}
    # List targets in reversed selection
    invert_t = {t for s in to_select for t in s.targets() if cmds.objExists(t)}
    targets.union(invert_t)
    try:
        cmds.select(targets)
    except ValueError:
        raise NameclashError(targets)
    return


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
