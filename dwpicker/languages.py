PYTHON = 'python'
MEL = 'mel'


def execute_code(language, code):
    return EXECUTORS[language](code)


def execute_python(code):
    exec(code, globals())


def execute_mel(code):
    from maya import mel
    mel.eval(code.replace(u'\u2029', '\n'))


EXECUTORS = {
    PYTHON: execute_python,
    MEL: execute_mel,
}
