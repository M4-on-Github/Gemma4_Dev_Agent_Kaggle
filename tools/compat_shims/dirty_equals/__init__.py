"""Minimal, API-faithful stand-in for the real `dirty_equals` package.

Covers only the symbols fastapi's own test suite actually imports (`IsDict`, `IsPartialDict`,
`IsOneOf`, `HasRepr`), with real comparison semantics (including `|` for alternation between
matchers), not a trivially-always-pass stub. Verified against real fastapi test files
(fastapi_12942 snapshot) — see experiments/README.md §1j.
"""


class _DirtyBase:
    def __or__(self, other):
        return _Or(self, other)

    def __ror__(self, other):
        return _Or(other, self)

    def __hash__(self):
        return object.__hash__(self)


class _Or(_DirtyBase):
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def __eq__(self, other):
        return self.a == other or self.b == other

    def __repr__(self):
        return f'{self.a!r} | {self.b!r}'


class IsDict(_DirtyBase, dict):
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)

    def __eq__(self, other):
        if not isinstance(other, dict):
            return False
        return dict(other) == dict(self)


class IsPartialDict(_DirtyBase, dict):
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)

    def __eq__(self, other):
        if not isinstance(other, dict):
            return False
        _missing = object()
        return all(other.get(k, _missing) == v for k, v in self.items())


class IsOneOf(_DirtyBase):
    def __init__(self, *values):
        self.values = values

    def __eq__(self, other):
        return any(other == v for v in self.values)

    def __repr__(self):
        return f'IsOneOf({self.values!r})'


class HasRepr(_DirtyBase):
    def __init__(self, expected_repr):
        self.expected_repr = expected_repr

    def __eq__(self, other):
        return repr(other) == self.expected_repr

    def __repr__(self):
        return f'HasRepr({self.expected_repr!r})'
