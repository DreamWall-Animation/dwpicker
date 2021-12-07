import json
from maya import cmds
from dwpicker.selection import maya_namespace


PICKER_HOLDER_NODE = '_dwpicker_data'
PICKER_HOLDER_ATTRIBUTE = '_dwpicker_data'
LS_EXP = ["*." + PICKER_HOLDER_ATTRIBUTE, "*:*." + PICKER_HOLDER_ATTRIBUTE]


def get_picker_holder_node():
    if cmds.objExists(PICKER_HOLDER_NODE):
        return PICKER_HOLDER_NODE
    return create_picker_holder_node()


def create_picker_holder_node():
    with maya_namespace(":"):
        node = cmds.createNode('script', name=PICKER_HOLDER_NODE)
    cmds.setAttr(node + '.nodeState', 1)
    cmds.addAttr(node, longName=PICKER_HOLDER_ATTRIBUTE, dataType='string')
    return node


def store_local_picker_data(pickers):
    data = json.dumps(pickers)
    node = get_picker_holder_node()
    cmds.setAttr(node + '.' + PICKER_HOLDER_ATTRIBUTE, data, type='string')
    clean_stray_picker_holder_nodes()


def load_local_picker_data():
    nodes = list_picker_holder_nodes()
    pickers = []
    for node in nodes:
        data = cmds.getAttr(node + '.' + PICKER_HOLDER_ATTRIBUTE)
        pickers.extend(json.loads(data))
    return pickers


def list_picker_holder_nodes():
    """
    Look up in the scene all the nodes holding an attribute named
    "_dwpicker_holder" which are not set on the "_dwpicker_holder" node.
    This mignt happed if a node node is imported (creating a namespace or a
    incrementation).
    """
    return [n for n in [node.split(".")[0] for node in cmds.ls(LS_EXP)]]


def clean_stray_picker_holder_nodes():
    """
    If the scene contains multiple picker holder nodes, we remove them
    automatically to avoid repeated pickers.
    """
    for node in list_picker_holder_nodes():
        if node == PICKER_HOLDER_NODE:
            continue
        try:
            cmds.delete(node)
        except:
            # Node is locked or in reference and cannot be removed.
            # As we cant remove it, we reset his data to avoid double pickers.
            cmds.setAttr(
                node + "." + PICKER_HOLDER_ATTRIBUTE, "", dataType="string")