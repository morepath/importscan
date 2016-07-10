import sys

PY3 = sys.version_info[0] == 3

if PY3:
    def is_nonstr_iter(v):
        if isinstance(v, str):  # pragma: no cover
            return False
        return hasattr(v, '__iter__')
else:  # pragma: no cover
    def is_nonstr_iter(v):
        return hasattr(v, '__iter__')

if PY3:
    INT_TYPES = (int,)
else:  # pragma: no cover
    INT_TYPES = (int, long)
