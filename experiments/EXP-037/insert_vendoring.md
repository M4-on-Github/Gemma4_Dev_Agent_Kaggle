## 0. Before step 1: two test-only packages
Some repositories' tests import `inline_snapshot` or `dirty_equals`, and this sandbox may lack them. A test file that cannot import one fails as a whole, even after a correct fix. Your first tool call is `cd /workspace && git grep -l -e inline_snapshot -e dirty_equals -- '*test*' | head -3`. If it prints nothing, go to step 1. If it prints a path, your second tool call is this `run_command`, copied exactly:
```
cd /workspace
if ! python -c 'import inline_snapshot' 2>/dev/null; then mkdir -p inline_snapshot; cat > inline_snapshot/__init__.py <<'EOF'
class Snapshot:
    __slots__ = ('_value',)
    def __init__(self, value=None): self._value = value
    def __class_getitem__(cls, item): return cls
    def __eq__(self, other): return self._value == other
    def __ne__(self, other): return not self.__eq__(other)
    def __repr__(self): return repr(self._value)
    def __hash__(self): return hash(self._value)
def snapshot(value=None): return Snapshot(value)
EOF
fi
if ! python -c 'import dirty_equals' 2>/dev/null; then mkdir -p dirty_equals; cat > dirty_equals/__init__.py <<'EOF'
class _B:
    def __or__(self, o): return _Or(self, o)
    def __ror__(self, o): return _Or(o, self)
    def __hash__(self): return object.__hash__(self)
class _Or(_B):
    def __init__(self, a, b): self.a, self.b = a, b
    def __eq__(self, o): return self.a == o or self.b == o
    def __repr__(self): return repr(self.a) + ' | ' + repr(self.b)
class IsDict(_B, dict):
    def __eq__(self, o): return isinstance(o, dict) and dict(o) == dict(self)
_M = object()
class IsPartialDict(_B, dict):
    def __eq__(self, o): return isinstance(o, dict) and all(o.get(k, _M) == v for k, v in self.items())
class IsOneOf(_B):
    def __init__(self, *v): self.values = v
    def __eq__(self, o): return any(o == v for v in self.values)
    def __repr__(self): return 'IsOneOf(' + repr(self.values) + ')'
class HasRepr(_B):
    def __init__(self, r): self.expected_repr = r
    def __eq__(self, o): return repr(o) == self.expected_repr
    def __repr__(self): return 'HasRepr(' + repr(self.expected_repr) + ')'
EOF
fi
git status --short | head -5
```
A new `inline_snapshot/` or `dirty_equals/` directory from that call is part of your fix and the one exception to the rules below on new files and files left in the repository: never edit or delete it, and keep it in your diff when you call `submit_patch`.

