"""
Shared storage for passing data between GhPython components.
Since GhPython 3 in Rhino 8 serializes objects on wires (converting dicts to strings),
we store data in this module's global dict. All components import this same module,
so they share the same data.
"""

_store = {}


def put(key, value):
    _store[key] = value


def get(key, default=None):
    return _store.get(key, default)


def clear():
    _store.clear()
