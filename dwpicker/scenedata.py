import sys
import json
import base64

from maya import cmds

from dwpicker.compatibility import ensure_retro_compatibility
from dwpicker.optionvar import USE_BASE64_DATA_ENCODING
from dwpicker.namespace import maya_namespace


def encode_data(pickers):
    data = json.dumps(pickers)
    if not cmds.optionVar(query=USE_BASE64_DATA_ENCODING):
        return data
    # Ensure backward compatibility.
    if sys.version_info[0] == 2:
        return base64.b64encode(bytes(data))
    return base64.b64encode(bytes(data, "utf-8"))


def decode_data(data):
    try:
        return json.loads(data)
    except ValueError:  # Happe if data encoded is encoded as base 64 string.
        return json.loads(base64.b64decode(data))


class DefaultSceneStorage:
    PICKER_HOLDER_NODE = '_dwpicker_data'
    PICKER_HOLDER_ATTRIBUTE = '_dwpicker_data'
    LS_EXP = ["*." + PICKER_HOLDER_ATTRIBUTE, "*:*." + PICKER_HOLDER_ATTRIBUTE]

    def _get_picker_holder_node(self):
        if cmds.objExists(self.PICKER_HOLDER_NODE):
            return self.PICKER_HOLDER_NODE
        return self._create_picker_holder_node()

    def _create_picker_holder_node(self):
        with maya_namespace(":"):
            node = cmds.createNode('script', name=self.PICKER_HOLDER_NODE)
        cmds.setAttr(node + '.nodeState', 1)
        cmds.addAttr(
            node, longName=self.PICKER_HOLDER_ATTRIBUTE, dataType='string')
        return node

    def _list_picker_holder_nodes(self):
        """
        Look up in the scene all the nodes holding an attribute named
        "_dwpicker_holder" which are not set on the "_dwpicker_holder" node.
        This mignt happed if a node node is imported (creating a namespace or a
        incrementation).
        """
        return [node.split(".")[0] for node in cmds.ls(self.LS_EXP)]

    def load(self):
        nodes = self._list_picker_holder_nodes()
        pickers = []
        for node in nodes:
            data = cmds.getAttr(node + '.' + self.PICKER_HOLDER_ATTRIBUTE)
            data = decode_data(data)
            pickers.extend(ensure_retro_compatibility(p) for p in data)
        return pickers

    def store(self, pickers):
        data = encode_data(pickers)
        node = self._get_picker_holder_node()
        cmds.setAttr(
            node + '.' + self.PICKER_HOLDER_ATTRIBUTE, data, type='string')
        self.cleanup()

    def cleanup(self):
        """
        If the scene contains multiple picker holder nodes, we remove them
        automatically to avoid repeated pickers.
        """
        for node in self._list_picker_holder_nodes():
            if node == self.PICKER_HOLDER_NODE:
                continue
            try:
                cmds.delete(node)
            except:
                # Node is locked or in reference and cannot be removed.
                # As we cant remove it, we reset his data to avoid double 
                # pickers.
                cmds.setAttr(
                    node + "." + self.PICKER_HOLDER_ATTRIBUTE, "", 
                    dataType="string")
