import keyword
from PySide2 import QtGui, QtCore
from dwpicker.languages import PYTHON, MEL


MELKEYWORDS = [
    'if', 'else', 'int', 'float', 'double', 'string', 'array'
    'var', 'return', 'case', 'then', 'continue', 'break', 'global', 'proc']

TEXT_STYLES = {
    'keyword': {
        'color': 'white',
        'bold': True,
        'italic': False},
    'number': {
        'color': 'cyan',
        'bold': False,
        'italic': False},
    'comment': {
        'color': (0.7, 0.5, 0.5),
        'bold': False,
        'italic': False},
    'function': {
        'color': '#ff0571',
        'bold': False,
        'italic': True},
    'string': {
        'color': 'yellow',
        'bold': False,
        'italic': False},
    'boolean': {
        'color': '#a18852',
        'bold': True,
        'italic': False}}


PATTERNS = {
    PYTHON: {
        'keyword': r'\b|'.join(keyword.kwlist),
        'number': r'\b[+-]?[0-9]+[lL]?\b',
        'comment': r'#[^\n]*',
        'function': r'\b[A-Za-z0-9_]+(?=\()',
        'string': r'".*"|\'.*\'',
        'boolean': r'\bTrue\b|\bFalse\b'},
    MEL: {
        'keyword': r'\b|'.join(MELKEYWORDS),
        'number': r'\b[+-]?[0-9]+[lL]?\b',
        'comment': r'//[^\n]*',
        'function': r'\b[A-Za-z0-9_]+(?=\()',
        'string': r'".*"|\'.*\'',
        'boolean': r'\btrue\b|\bfalse\b'}
}


class Highlighter(QtGui.QSyntaxHighlighter):
    PATTERNS = []

    def __init__(self, parent=None):
        super(Highlighter, self).__init__(parent)
        self.rules = []
        for name, properties in TEXT_STYLES.items():
            if name not in self.PATTERNS:
                continue
            text_format = create_textcharformat(
                color=properties['color'],
                bold=properties['bold'],
                italic=properties['italic'])
            self.rules.append(
                (QtCore.QRegExp(self.PATTERNS[name]), text_format))

    def highlightBlock(self, text):
        for pattern, format_ in self.rules:
            expression = QtCore.QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format_)
                index = expression.indexIn(text, index + length)


class PythonHighlighter(Highlighter):
    PATTERNS = PATTERNS[PYTHON]


class MelHighlighter(Highlighter):
    PATTERNS = PATTERNS[MEL]


HIGHLIGHTERS = {
    PYTHON: PythonHighlighter,
    MEL: MelHighlighter}


def get_highlighter(language):
    return HIGHLIGHTERS.get(language, Highlighter)


def create_textcharformat(color, bold=False, italic=False):
    char_format = QtGui.QTextCharFormat()
    qcolor = QtGui.QColor()
    if isinstance(color, str):
        qcolor.setNamedColor(color)
    else:
        r, g, b = color
        qcolor.setRgbF(r, g, b)
    char_format.setForeground(qcolor)
    if bold:
        char_format.setFontWeight(QtGui.QFont.Bold)
    if italic:
        char_format.setFontItalic(True)
    return char_format
