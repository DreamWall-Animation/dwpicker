from copy import deepcopy

PYTHON = 'python'
MEL = 'mel'


PYTHON_TARGETS_VARIABLE = """\
import dwpicker
__targets__ = [{targets}]
if dwpicker.get_shape('{shape_id}'):
    __shape__ = dwpicker.get_shape('{shape_id}').options
else:
    __shape__ = None
{code}
"""


MEL_TARGETS_VARIABLE = """\
string $targets[] = {{{targets}}};
{code}
"""


DEFERRED_PYTHON = """\
from maya import cmds
cmds.evalDeferred(\"\"\"{code}\"\"\", lowestPriority=True)
"""

DEFERRED_MEL = """\
evalDeferred "{code}" -lowestPriority;"""

STACK_UNDO_PYTHON = """\
from maya import cmds
cmds.undoInfo(openChunk=True)
{code}
cmds.undoInfo(closeChunk=True)
"""

STACK_UNDO_MEL = """\
undoInfo -openChunk;
{code}
undoInfo -closeChunk;
"""


EXECUTION_WARNING = """\
Code execution failed for {object}: "{name}"
{error}.
"""


def execute_code(
        language, code, shape=None, deferred=False, compact_undo=False):
    return EXECUTORS[language](code, shape, deferred, compact_undo)


def execute_python(
        code, shape=None, deferred=False, compact_undo=False):
    if compact_undo:
        code = STACK_UNDO_PYTHON.format(code=code)
    if deferred:
        code = DEFERRED_PYTHON.format(code=code)
    targets = (shape.targets() or []) if shape else []
    targets = ', '.join(('"{}"'.format(target) for target in targets))
    shape_id = shape.options['id'] if shape else None
    code = PYTHON_TARGETS_VARIABLE.format(
        targets=targets, shape_id=shape_id, code=code)
    exec(code, globals())


def execute_mel(code, shape=None, deferred=False, compact_undo=False):
    from maya import mel
    if compact_undo:
        code = STACK_UNDO_MEL.format(code=code)
    if deferred:
        print('Eval deferred not supported for mel command.')
        # code = DEFERRED_MEL.format(code=code)
    targets = (shape.targets() or []) if shape else []
    if targets:
        targets = ', '.join(
            '"{}"'.format(target) for target in shape.targets())
        code = MEL_TARGETS_VARIABLE.format(targets=targets, code=code)
    mel.eval(code.replace(u'\u2029', '\n'))


EXECUTORS = {
    PYTHON: execute_python,
    MEL: execute_mel,
}
