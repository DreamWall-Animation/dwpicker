import imp
import json
import time

import dwpicker
imp.reload(dwpicker)
import dwpicker.scenedata
from maya import cmds
from dwpicker.namespace import maya_namespace


def shortname(fullname):
    return fullname.split('|')[-1].split(':')[-1]


def timeit(func):
    def wrapped(*args, **kwargs):
        started = time.perf_counter()
        value = func(*args, **kwargs)
        print(
            'Time for', func.__qualname__, ':', time.perf_counter() - started)
        return value
    return wrapped


def ensure_holder(parent, type, identifier, default_name):
    if parent:
        if identifier:
            for node in cmds.listRelatives(
                    parent, children=True, fullPath=True):
                if shortname(node) == shortname(identifier):
                    identifier = node
                    break
            else:
                default_name = identifier
                identifier = None
        if not identifier:
            identifier = cmds.createNode(
                type, name=default_name, parent=parent)
    if not cmds.objExists(identifier):
        identifier = cmds.createNode(type, name=identifier)
    if parent:
        identifier = parent + '|' + identifier.split('|')[-1]
    nodes = cmds.ls(identifier, long=True)
    assert len(nodes) == 1, (
        'Unexpected nodes found: {}, for {}'.format(
            nodes, identifier))
    return nodes[0]


def ensure_data(node, attribute, value):
    if not cmds.attributeQuery(attribute, node=node, exists=True):
        cmds.addAttr(node, longName=attribute, dataType='string')
    value = json.dumps(value)
    attribute = node + '.' + attribute
    if cmds.getAttr(attribute) != value:
        cmds.setAttr(attribute, value, type='string')


class SceneDagStorage:
    PICKER_HOLDER_NODE = 'DwPicker'

    def load(self):
        data = []
        for holder in cmds.ls('::' + self.PICKER_HOLDER_NODE):
            for picker_node in cmds.listRelatives(
                    holder, children=True, fullPath=True):
                picker = {
                    'general': {
                        # add corresponding scene node identifier, so storing
                        # picker data then will be into same node
                        'id': picker_node,
                    }, 'shapes': []}
                for attribute in cmds.listAttr(
                        picker_node, userDefined=True):
                    value = json.loads(cmds.getAttr(
                        picker_node + '.' + attribute))
                    if attribute == 'version':
                        picker[attribute] = value
                    else:
                        picker['general'][attribute] = value
                for shape in cmds.listRelatives(
                        picker_node, shapes=True, fullPath=True):
                    shape_data = {'id': shape}
                    for attribute in cmds.listAttr(
                            shape, userDefined=True):
                        value = json.loads(cmds.getAttr(
                            shape + '.' + attribute))
                        shape_data[attribute.replace('_', '.')] = value
                    picker['shapes'].append(shape_data)
                # some weird missing version in picker general section
                picker['general']['version'] = picker['version']
                data.append(picker)
        return data

    def store(self, pickers):
        for picker in pickers:
            picker_holder = picker.get('general', {}).get('id')
            if not picker_holder or not cmds.objExists(picker_holder):
                if not cmds.objExists(self.PICKER_HOLDER_NODE):
                    cmds.createNode(
                        'dagContainer', name=self.PICKER_HOLDER_NODE)
                picker_holder = ensure_holder(
                    self.PICKER_HOLDER_NODE, 'transform', picker_holder,
                    picker['general']['name'])
            ensure_data(picker_holder, 'version', picker['version'])
            for key, value in picker['general'].items():
                if key == 'id':
                    # scene identifier makes sense only in current scene
                    # context and should not be serialized
                    continue
                ensure_data(picker_holder, key, value)
            for shape in picker['shapes']:
                shape_holder = ensure_holder(
                    picker_holder, 'nurbsSurface', shape.get('id'), 'shape')
                for key, value in shape.items():
                    if key == 'id':
                        continue
                    assert '_' not in key
                    ensure_data(shape_holder, key.replace('.', '_'), value)

    def cleanup(self):
        pass


def node_namespace(name):
    # TODO dwpicker.namespace.node_namespace do not handle
    # nested namespaces
    return (name.rsplit(':', 1)[:-1] or [None])[-1]


class SceneDictDiffStorage:
    PICKER_HOLDER_NODE = 'DwPicker'
    PICKER_HOLDER_ATTRIBUTE = '_dwpicker_data'
    # LS_EXP = ["*." + PICKER_HOLDER_ATTRIBUTE, "*:*." + PICKER_HOLDER_ATTRIBUTE]
    LS_EXP = [PICKER_HOLDER_NODE, "*:" + PICKER_HOLDER_NODE]

    def _get_picker_holder_node(self):
        if cmds.objExists(self.PICKER_HOLDER_NODE):
            return self.PICKER_HOLDER_NODE
        return self._create_picker_holder_node()

    def _create_picker_holder_node(self):
        with maya_namespace(":"):
            node = cmds.createNode('dagContainer', name=self.PICKER_HOLDER_NODE, skipSelect=True)
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
        added_pickers = set()
        # start from root holders
        for node in sorted(nodes, key=lambda x: len(x)):
            for picker_node in cmds.listRelatives(node, children=True) or []:
                if picker_node in added_pickers:
                    continue
                namespace = node_namespace(picker_node)
                data = cmds.getAttr(picker_node + '.' + self.PICKER_HOLDER_ATTRIBUTE)
                data = dwpicker.scenedata.decode_data(data)
                data = dwpicker.scenedata.ensure_retro_compatibility(data)
                if namespace:
                    for s in data['shapes']:
                        s['action.targets'] = ['{}:{}'.format(namespace, n)
                                               for n in s['action.targets']]
                data['source_node'] = picker_node
                pickers.append(data)
                added_pickers.add(data['source_node'])
        return pickers

    def store(self, pickers):
        node = self._get_picker_holder_node()
        for picker_node in cmds.listRelatives(node, children=True) or []:
            cmds.delete(picker_node)
        for p in pickers:
            picker_node = p.get('source_node') or p.get('general', {}).get('name') or 'Picker'
            picker_node = cmds.createNode('dagContainer', name=picker_node, parent=node, skipSelect=True)
            if p.get('source_node') == picker_node:
                del p['source_node']
            cmds.addAttr(
                picker_node, longName=self.PICKER_HOLDER_ATTRIBUTE, dataType='string')
            data = dwpicker.scenedata.encode_data(p)
            cmds.setAttr(picker_node + '.' + self.PICKER_HOLDER_ATTRIBUTE, data, type='string')

    def cleanup(self):
        pass


# data = timeit(dwpicker.scenedata.DefaultSceneStorage().load)()
# data = timeit(SceneDagStorage().load)()
# SceneDagStorage().store(data)
# dwpicker.scenedata.DefaultSceneStorage().store(data)
# pprint.pprint(data)
# dwpicker.show(storage_class=SceneDagStorage)
# dwpicker.show(storage_class=dwpicker.scenedata.DefaultSceneStorage)
# import dwpicker.scenedata_dag
# dwpicker.show(storage_class=dwpicker.scenedata_dag.SceneDictDiffStorage)
