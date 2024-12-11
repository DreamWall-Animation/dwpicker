from copy import deepcopy

PYTHON = 'python'
MEL = 'mel'


PYTHON_TARGETS_VARIABLE = """\
targets = [{targets}]
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
        language, code, targets=None, deferred=False, compact_undo=False):
    return EXECUTORS[language](code, targets, deferred, compact_undo)


def execute_python(
        code, targets=None, deferred=False, compact_undo=False):
    if compact_undo:
        code = STACK_UNDO_PYTHON.format(code=code)
    if deferred:
        code = DEFERRED_PYTHON.format(code=code)
    if targets is not None:
        targets = ', '.join((f'"{target}"' for target in targets))
        code = PYTHON_TARGETS_VARIABLE.format(targets=targets, code=code)
    exec(code, globals())


def execute_mel(code, targets=None, deferred=False, compact_undo=False):
    from maya import mel
    if compact_undo:
        code = STACK_UNDO_MEL.format(code=code)
    if deferred:
        print('Eval deferred not supported for mel command.')
        # code = DEFERRED_MEL.format(code=code)
    if targets is not None:
        targets = ', '.join((f'"{target}"' for target in targets))
        code = MEL_TARGETS_VARIABLE.format(targets=targets, code=code)
    mel.eval(code.replace(u'\u2029', '\n'))


EXECUTORS = {
    PYTHON: execute_python,
    MEL: execute_mel,
}
