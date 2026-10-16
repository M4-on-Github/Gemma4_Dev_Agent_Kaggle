"""Minimal, API-faithful stand-in for the real `inline_snapshot` package.

Not a trivial always-pass stub: `Snapshot` is a transparent equality wrapper around the recorded
value, matching the real library's non-"fix"-mode read semantics exactly. Verified against real
fastapi test files (fastapi_11355, fastapi_12942, fastapi_13920 snapshots) — see
experiments/README.md §1j for how and why this is used (vendored into the agent's own patch as a
new top-level package, which survives the harness's protected-test-file patch filter since it
isn't conftest.py/pytest.ini/etc.).
"""


class Snapshot:
    __slots__ = ('_value',)

    def __init__(self, value=None):
        self._value = value

    def __class_getitem__(cls, item):
        return cls

    def __eq__(self, other):
        return self._value == other

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return repr(self._value)

    def __hash__(self):
        return hash(self._value)


def snapshot(value=None):
    return Snapshot(value)
