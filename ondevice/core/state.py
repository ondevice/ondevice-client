""" stores non-persistent application state.

All functions in this module are thread safe """

import copy
import threading

_state = {}
_lock = threading.Lock()

def _getPath(path, create=False):
    global _state
    return _getPathRec(_state, path.split('.'), create)

def _getPathRec(state, path, create=False):
    if len(path) == 0:
        return state
    key = path[0]
    if not key in state:
        if create:
            state[key] = {}
        else:
            raise KeyError("State key not found: 'key'".format(key))

    return _getPathRec(state[key], path[1:], create)

def add(path, key, value):
    """ increment a state state value by a given integer (can be negative) """
    global _lock
    with _lock:
        parent = _getPath(path, True)
        if key not in parent:
            parent[key] = 0 # initialize with 0
        parent[key] += value
        return parent[key]

def getCopy():
    """ Returns a deep copy of the current state """
    global _lock, _state
    with _lock:
        return copy.deepcopy(_state)

def remove(path, key):
    global _lock
    with _lock:
        parent = _getPath(path, False)
        del parent[key]

def set(path, key, value):
    global _lock
    with _lock:
        parent = _getPath(path, True)
        parent[key] = value
