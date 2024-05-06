
PYTHON = 'python'
MEL = 'mel'

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


def execute_code(language, code, deferred=False, compact_undo=False):
    return EXECUTORS[language](code, deferred, compact_undo)


def execute_python(code, deferred=False, compact_undo=False):
    if compact_undo:
        code = STACK_UNDO_PYTHON.format(code=code)
    if deferred:
        code = DEFERRED_PYTHON.format(code=code)
    exec(code, globals())


def execute_mel(code, deferred=False, compact_undo=False):
    from maya import mel
    if compact_undo:
        code = STACK_UNDO_MEL.format(code=code)
    if deferred:
        print('Eval deferred not supported for mel command.')
        # code = DEFERRED_MEL.format(code=code)
    mel.eval(code.replace(u'\u2029', '\n'))


EXECUTORS = {
    PYTHON: execute_python,
    MEL: execute_mel,
}
