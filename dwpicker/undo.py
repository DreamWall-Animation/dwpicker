
from copy import deepcopy


class UndoManager():
    def __init__(self, data):
        self._current_state = data
        self._modified = False
        self._undo_stack = []
        self._redo_stack = []

    @property
    def data(self):
        return deepcopy(self._current_state)

    def undo(self):
        if not self._undo_stack:
            print('No undostack.')
            return False
        self._redo_stack.append(deepcopy(self._current_state))
        self._current_state = deepcopy(self._undo_stack[-1])
        del self._undo_stack[-1]
        return True

    def redo(self):
        if not self._redo_stack:
            return False

        self._undo_stack.append(deepcopy(self._current_state))
        self._current_state = deepcopy(self._redo_stack[-1])
        del self._redo_stack[-1]
        return True

    def set_data_modified(self, data):
        self._redo_stack = []
        self._undo_stack.append(deepcopy(self._current_state))
        self._current_state = deepcopy(data)
        self._modified = True

    def set_data_saved(self):
        self._modified = False

    @property
    def data_saved(self):
        return not self._modified

    def reset_stacks(self):
        self._undo_stack = []
        self._redo_stack = []
