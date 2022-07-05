import imp
import json
import time

import dwpicker
imp.reload(dwpicker)
import dwpicker.scenedata
from maya import cmds


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

#data = timeit(dwpicker.scenedata.DefaultSceneStorage().load)()
#data = timeit(SceneDagStorage().load)()
#SceneDagStorage().store(data)
#dwpicker.scenedata.DefaultSceneStorage().store(data)
#pprint.pprint(data)
#dwpicker.show(storage_class=SceneDagStorage)
#dwpicker.show(storage_class=dwpicker.scenedata.DefaultSceneStorage)
