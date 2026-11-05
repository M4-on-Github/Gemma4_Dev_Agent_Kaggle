"""EXP-040 check (b): the instruction-template path for {cands?} and {vote_NN?}.

Two layers, both run by: python -m pytest experiments/EXP-040/test_template_relay.py -q -rs

1. Real ADK. Imports data/src/google_adk/google/adk/utils/instructions_utils.py with a fake context that carries only
   session.state. If google.adk or a dependency does not import here (it does not on this machine: no opentelemetry),
   these tests are skipped and say why.
2. Port. A line-for-line port of the substitution (instructions_utils.py:70-124 and 127-149, the artifact branch dropped
   because no EXP-040 template uses it) that runs everywhere. The port is data copied by hand, not an import of the
   vendored file, so it proves the prompts against the source's logic, not against the installed package.
"""

import asyncio
import re
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
ADK_SRC = ROOT / "data" / "src" / "google_adk"
ACTOR = ROOT / "experiments" / "EXP-040" / "candidate-v1" / "prompts" / "actor.md"
VOTER = ROOT / "experiments" / "EXP-040" / "candidate-v1" / "prompts" / "voter.md"
PREFIXES = ["app:", "user:", "temp:"]  # State.APP_PREFIX, USER_PREFIX, TEMP_PREFIX


def _is_valid_state_name(var_name):  # port of instructions_utils.py:127-149
    parts = var_name.split(":")
    if len(parts) == 1:
        return var_name.isidentifier()
    if len(parts) == 2:
        if (parts[0] + ":") in PREFIXES:
            return parts[1].isidentifier()
    return False


def port_inject(template, state):  # port of instructions_utils.py:70-124
    def replace(match):
        var_name = match.group().lstrip("{").rstrip("}").strip()
        optional = False
        if var_name.endswith("?"):
            optional = True
            var_name = var_name.removesuffix("?")
        if not _is_valid_state_name(var_name):
            return match.group()
        if var_name in state:
            value = state[var_name]
            if value is None:
                return ""
            return str(value)
        if optional:
            return ""
        raise KeyError(f"Context variable not found: `{var_name}`.")

    result, last_end = [], 0
    for m in re.finditer(r"{+[^{}]*}+", template):
        result.append(template[last_end : m.start()])
        result.append(replace(m))
        last_end = m.end()
    result.append(template[last_end:])
    return "".join(result)


try:
    sys.path.insert(0, str(ADK_SRC))
    from google.adk.utils.instructions_utils import inject_session_state
except Exception as exc:
    inject_session_state = None
    IMPORT_ERROR = repr(exc)
else:
    IMPORT_ERROR = ""


def real_inject(template, state):
    ctx = SimpleNamespace(_invocation_context=SimpleNamespace(session=SimpleNamespace(state=state), artifact_service=None))
    return asyncio.run(inject_session_state(template, ctx))


needs_adk = pytest.mark.skipif(inject_session_state is None, reason="google.adk does not import here: " + IMPORT_ERROR)

CANDS = "ISSUE: fix {x} in f\nA. edit a.py {y}\nB. edit b.py"


def _filled():
    state = {"cands": CANDS}
    state.update({"vote_%02d" % i: "PICK: B" for i in range(1, 17)})
    state["vote_03"] = None  # a None value renders as empty
    return state


def check_empty(render):
    out = render(ACTOR.read_text(encoding="utf-8"), {})
    assert "{" not in out and "}" not in out
    assert "Reader report:\n\n" in out
    assert "voter 1: \n" in out and "voter 16: \n" in out
    assert "{" not in render(VOTER.read_text(encoding="utf-8"), {})


def check_filled(render):
    out = render(ACTOR.read_text(encoding="utf-8"), _filled())
    assert CANDS in out  # braces inside an injected value survive: a single pass, no re-templating
    assert "voter 1: PICK: B\n" in out and "voter 3: \n" in out and "voter 16: PICK: B\n" in out
    assert len(re.findall(r"PICK: B", out)) == 15
    assert CANDS in render(VOTER.read_text(encoding="utf-8"), _filled())


def test_port_empty_state():
    check_empty(port_inject)


def test_port_filled_state():
    check_filled(port_inject)


def test_every_placeholder_is_optional_and_a_valid_name():
    names = re.findall(r"\{([^{}]*)\}", ACTOR.read_text(encoding="utf-8") + VOTER.read_text(encoding="utf-8"))
    assert names and all(n.endswith("?") for n in names)
    assert all(_is_valid_state_name(n[:-1]) for n in names)
    assert len([n for n in names if n.startswith("vote_")]) == 16
    assert len(re.findall(r"{+[^{}]*}+", ACTOR.read_text(encoding="utf-8"))) == 17  # cands and sixteen votes, no stray braces


def test_a_required_key_would_raise_in_the_port():
    with pytest.raises(KeyError):
        port_inject("x {cands} y", {})


@needs_adk
def test_real_adk_empty_state():
    check_empty(real_inject)


@needs_adk
def test_real_adk_filled_state():
    check_filled(real_inject)
