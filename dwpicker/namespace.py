
from contextlib import contextmanager
from maya import cmds


def detect_picker_namespace(shapes):
    targets = {target for shape in shapes for target in shape.targets()}
    namespaces = {ns for ns in [node_namespace(t) for t in targets] if ns}
    if len(namespaces) != 1:
        return None
    return list(namespaces)[0]


def pickers_namespaces(pickers):
    targets = {t for p in pickers for s in p.shapes for t in s.targets()}
    namespaces = {ns for ns in [node_namespace(t) for t in targets] if ns}
    return sorted(list(namespaces))


def node_namespace(node):
    basename = node.split("|")[-1]
    if ":" not in node:
        return None
    return basename.split(":")[0]


@contextmanager
def maya_namespace(
        namespace='', create_if_missing=True, restore_current_namespace=True):
    """Context manager to temporarily set a namespace"""
    initial_namespace = ':' + cmds.namespaceInfo(currentNamespace=True)
    if not namespace.startswith(':'):
        namespace = ':' + namespace
    try:
        if not cmds.namespace(absoluteName=True, exists=namespace):
            if create_if_missing:
                cmds.namespace(setNamespace=':')
                namespace = cmds.namespace(addNamespace=namespace)
            else:
                cmds.namespace(initial_namespace)
                raise ValueError(namespace + " doesn't exist.")
        cmds.namespace(setNamespace=namespace)
        yield namespace
    finally:
        if restore_current_namespace:
            cmds.namespace(setNamespace=initial_namespace)


def switch_namespace(name, namespace):
    basename = name.split("|")[-1]
    name = basename if ":" not in basename else basename.split(":")[-1]
    if not namespace:
        return name
    return namespace + ":" + name


def selected_namespace():
    selection = cmds.ls(selection=True)
    if not selection:
        return ":"
    node = selection[0]
    basename = node.split("|")[-1]
    if ":" not in node:
        return None
    return basename.split(":")[0]
