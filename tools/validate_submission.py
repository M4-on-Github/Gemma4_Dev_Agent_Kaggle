#!/usr/bin/env python3
"""Validate a submission directory or submission.zip before upload.

Replicates, as far as community evidence allows, what the harness does at compile time
(root-config discovery, sandboxed `!include`, declared-tool / single-model / generation-config checks,
file-extension and size limits) and adds our own lint rules from plan.md §4.5 / §8.2:
forbidden strings, repo-agnostic prompts, eval_config worst-case run time, instruction placeholders.

Every rule is tagged in tools/submission_rules.py with the plan §3.4 question (VERIFY(Qn)) that confirms it.
When the official wheels are importable (`pip install --no-index --find-links data/wheelhouse adk-submission
swegemma`), `--official` additionally runs the harness's own validator/compiler and reports what it raises.

Usage:
    python tools/validate_submission.py submission/            # source tree
    python tools/validate_submission.py dist/submission.zip    # archive
    python tools/validate_submission.py submission/ --official --json
Exit status 0 = VALID, 1 = INVALID, 2 = usage error.
"""
from __future__ import annotations

import argparse
import ast
import re
import dataclasses
import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import submission_rules as R  # noqa: E402


class SubmissionError(Exception):
    """A structural problem that makes the submission uncompilable."""


# ----------------------------------------------------------------------------- report

@dataclasses.dataclass
class Report:
    errors: list[str] = dataclasses.field(default_factory=list)
    warnings: list[str] = dataclasses.field(default_factory=list)
    info: list[str] = dataclasses.field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def note(self, msg: str) -> None:
        self.info.append(msg)

    def extend(self, other: "Report") -> None:
        self.errors += other.errors
        self.warnings += other.warnings
        self.info += other.info

    def render(self) -> str:
        lines = [f"  info  {m}" for m in self.info]
        lines += [f"  WARN  {m}" for m in self.warnings]
        lines += [f"  ERROR {m}" for m in self.errors]
        lines.append(f"RESULT: {'VALID' if self.ok else 'INVALID'} "
                     f"({len(self.errors)} errors, {len(self.warnings)} warnings)")
        return "\n".join(lines)


# ----------------------------------------------------------------------------- sandboxed !include

@dataclasses.dataclass
class Loaded:
    data: Any
    includes: list[Path]   # every file pulled in through !include (recursively)


def _resolve_inside(root: Path, base_dir: Path, rel: str) -> Path:
    if not isinstance(rel, str) or not rel:
        raise SubmissionError("!include needs a non-empty relative path")
    if "\x00" in rel:
        raise SubmissionError(f"!include path contains a null byte: {rel!r}")
    pp = PurePosixPath(rel)
    if pp.is_absolute() or rel.startswith("\\"):
        raise SubmissionError(f"!include path must be relative: {rel}")
    target = (base_dir / rel)
    try:
        resolved = target.resolve(strict=True)
    except FileNotFoundError:
        raise SubmissionError(f"!include target not found: {rel} (from {base_dir.relative_to(root) or '.'})")
    root_resolved = root.resolve()
    if root_resolved not in resolved.parents and resolved != root_resolved:
        raise SubmissionError(f"!include escapes the submission root: {rel}")
    # VERIFY(Q2): '..' segments that still resolve inside the root (sub_agents/x.yaml -> ../prompts/x.md) are
    # used by the starter kit mirrors and community submissions, so they are accepted here.
    return resolved


def load_yaml(root: Path, path: Path, depth: int = 0, seen: tuple[Path, ...] = ()) -> Loaded:
    """Parse YAML with a sandboxed `!include` tag (relative to the including file)."""
    if depth > R.MAX_INCLUDE_DEPTH:
        raise SubmissionError(f"!include depth exceeds {R.MAX_INCLUDE_DEPTH}: {path}")
    if path in seen:
        raise SubmissionError(f"!include cycle at {path}")
    if path.stat().st_size > R.MAX_YAML_SIZE_BYTES:
        raise SubmissionError(f"YAML file exceeds 50 MiB: {path}")
    includes: list[Path] = []

    class Loader(yaml.SafeLoader):
        pass

    def include(loader: yaml.SafeLoader, node: yaml.Node) -> Any:
        rel = loader.construct_scalar(node)
        target = _resolve_inside(root, path.parent, rel)
        includes.append(target)
        suffix = target.suffix.lower()
        if suffix in (".md", ".txt"):
            return target.read_text(encoding="utf-8")
        if suffix in (".yaml", ".yml"):
            sub = load_yaml(root, target, depth + 1, seen + (path,))
            includes.extend(sub.includes)
            return sub.data
        raise SubmissionError(f"!include of unsupported file type: {rel}")

    Loader.add_constructor("!include", include)
    try:
        data = yaml.load(path.read_text(encoding="utf-8"), Loader=Loader)
    except yaml.YAMLError as exc:
        raise SubmissionError(f"{path.name}: YAML error: {exc}")
    return Loaded(data=data, includes=includes)


# ----------------------------------------------------------------------------- agent tree

@dataclasses.dataclass
class AgentNode:
    path: Path
    config: dict
    via: str                     # "root" | "agent_tool" | "sub_agent"
    includes: list[Path]


@dataclasses.dataclass
class AgentTree:
    root_dir: Path
    root_config: Path
    agents: list[AgentNode]
    skill_dirs: list[Path]
    adapter_dirs: list[Path]
    warnings: list[str]

    def reachable_files(self) -> set[Path]:
        files: set[Path] = {self.root_config.resolve()}
        for a in self.agents:
            files.add(a.path.resolve())
            files.update(p.resolve() for p in a.includes)
        for d in self.skill_dirs + self.adapter_dirs:
            for p in d.rglob("*"):
                if p.is_file() and "__pycache__" not in p.parts and not p.name.startswith("."):
                    files.add(p.resolve())
        ev = self.root_dir / "eval_config.yaml"
        if ev.is_file():
            files.add(ev.resolve())
        return files


def find_root_config(root: Path) -> Path:
    roots = [root / n for n in R.ROOT_CONFIG_NAMES if (root / n).is_file()]
    if not roots:
        raise SubmissionError(f"no root config ({', '.join(R.ROOT_CONFIG_NAMES)}) in {root}")
    if len(roots) > 1:
        raise SubmissionError(f"multiple root configs: {[r.name for r in roots]}")
    return roots[0]


def _config_path(root: Path, base: Path, rel: Any, what: str) -> Path:
    if not isinstance(rel, str) or not rel:
        raise SubmissionError(f"{what}: config_path must be a non-empty string")
    if ".." in PurePosixPath(rel).parts or PurePosixPath(rel).is_absolute():
        raise SubmissionError(f"{what}: config_path may not be absolute or contain '..': {rel}")
    # VERIFY(Q2): community source reading says config_path resolves against the submission ROOT and skills
    # paths are root-relative, while !include is relative to the including file. We accept both and warn.
    cand_root = root / rel
    cand_rel = base / rel
    if cand_root.is_file():
        return cand_root.resolve()
    if cand_rel.is_file():
        return cand_rel.resolve()
    raise SubmissionError(f"{what}: config_path not found: {rel}")


def load_agent_tree(root: Path) -> AgentTree:
    root = root.resolve()
    root_cfg = find_root_config(root)
    agents: list[AgentNode] = []
    skill_dirs: list[Path] = []
    adapter_dirs: list[Path] = []
    warnings: list[str] = []
    seen: set[Path] = set()

    def visit(path: Path, via: str, depth: int) -> None:
        if depth > 50:
            raise SubmissionError("sub-agent nesting deeper than 50")
        if path in seen:
            return
        seen.add(path)
        loaded = load_yaml(root, path)
        cfg = loaded.data
        if not isinstance(cfg, dict):
            raise SubmissionError(f"{path.relative_to(root)}: top level must be a mapping")
        agents.append(AgentNode(path=path, config=cfg, via=via, includes=loaded.includes))
        rel = path.relative_to(root).as_posix()
        for t in cfg.get("tools") or []:
            if isinstance(t, dict) and "agent_tool" in t and isinstance(t["agent_tool"], dict):
                sub = _config_path(root, path.parent, t["agent_tool"].get("config_path"), f"{rel}: agent_tool")
                visit(sub, "agent_tool", depth + 1)
        for s in cfg.get("sub_agents") or []:
            if isinstance(s, dict) and "config_path" in s:
                sub = _config_path(root, path.parent, s.get("config_path"), f"{rel}: sub_agents")
                visit(sub, "sub_agent", depth + 1)
        for sk in cfg.get("skills") or []:
            if isinstance(sk, str):
                if ".." in PurePosixPath(sk).parts or PurePosixPath(sk).is_absolute():
                    raise SubmissionError(f"{rel}: skills path may not be absolute or contain '..': {sk}")
                d = root / sk
                if not d.is_dir():
                    raise SubmissionError(f"{rel}: skill directory not found (root-relative): {sk}")
                if d.resolve() not in skill_dirs:
                    skill_dirs.append(d.resolve())
        ad = cfg.get("adapter")
        if isinstance(ad, str) and ad:
            d = root / "adapters" / ad
            if d.is_dir() and d.resolve() not in adapter_dirs:
                adapter_dirs.append(d.resolve())

    visit(root_cfg.resolve(), "root", 0)
    return AgentTree(root_dir=root, root_config=root_cfg.resolve(), agents=agents, skill_dirs=skill_dirs,
                     adapter_dirs=adapter_dirs, warnings=warnings)


# ----------------------------------------------------------------------------- checks

def check_files(root: Path, report: Report, *, strict_tree: bool) -> None:
    total = count = 0
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root).as_posix()
        if p.is_symlink():
            report.error(f"symlink not allowed: {rel}")
            continue
        if not p.is_file():
            continue
        hidden = any(part.startswith(".") for part in PurePosixPath(rel).parts)
        if not strict_tree and (hidden or "__pycache__" in rel):
            continue   # source tree: tolerate editor/VCS droppings; the packer never ships them
        count += 1
        size = p.stat().st_size
        total += size
        if hidden:
            report.error(f"hidden file not allowed in submission: {rel}")
        elif "__pycache__" in rel:
            report.error(f"bytecode cache in submission: {rel}")
        elif p.suffix.lower() not in R.ALLOWED_EXTENSIONS:
            report.error(f"disallowed file extension: {rel} (allowed: {sorted(R.ALLOWED_EXTENSIONS)})")
        if size == 0:
            report.error(f"empty file (0 bytes): {rel} — zipping hard-linked files can produce these")
        # hard links: a file with st_nlink > 1 is copied by our packer, but warn so nobody zips with `zip -r`.
        if p.stat().st_nlink > 1:
            report.warn(f"hard-linked file (st_nlink>1): {rel}; use tools/pack_submission.py, not zip -r")
    if count > R.MAX_FILE_COUNT:
        report.error(f"too many files: {count} > {R.MAX_FILE_COUNT}")
    if total >= R.MAX_TOTAL_SIZE_BYTES:
        report.error(f"unpacked size {total} bytes >= 3 GiB limit")
    report.note(f"{count} files, {total / 1024:.1f} KiB unpacked")


def check_text_content(root: Path, path: Path, report: Report, *, is_prompt: bool) -> None:
    rel = path.relative_to(root).as_posix()
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        report.error(f"{rel}: not valid UTF-8")
        return
    for pat, label in R.FORBIDDEN_TEXT_PATTERNS:
        m = pat.search(text)
        if m:
            line = text.count("\n", 0, m.start()) + 1
            report.error(f"{rel}:{line}: forbidden reference ({label}): {m.group(0)!r}")
    if is_prompt:
        for pat in R.PUBLIC_REPO_WORDS:
            m = pat.search(text)
            if m:
                line = text.count("\n", 0, m.start()) + 1
                report.error(f"{rel}:{line}: prompt mentions a public dev-set repo ({m.group(0)!r}); "
                             "prompts must be repo-agnostic (plan §8.2)")


def check_instruction(where: str, text: Any, state_keys: set[str], report: Report) -> None:
    if text is None:
        return
    if not isinstance(text, str):
        report.error(f"{where}: instruction must be a string")
        return
    if len(text) > R.MAX_INSTRUCTION_CHARS:
        report.error(f"{where}: instruction exceeds {R.MAX_INSTRUCTION_CHARS} chars")
    for match in R.PLACEHOLDER_RE.findall(text):
        var = match.lstrip("{").rstrip("}").strip()
        optional = var.endswith("?")
        name = var[:-1] if optional else var
        if name.startswith("artifact."):
            report.error(f"{where}: artifact placeholder {match!r} needs an artifact service (unsupported)")
            continue
        if not R.IDENT_RE.match(name):
            report.warn(f"{where}: literal braces {match!r} in instruction (ADK leaves them; confusing for the model)")
            continue
        if optional:
            continue
        if name in R.HARNESS_OPTIONAL_STATE_KEYS:
            report.error(f"{where}: {match!r} raises KeyError on tasks without hints; write it as {{{name}?}}")
        elif name not in state_keys:
            report.error(f"{where}: placeholder {match!r} is not in session state -> KeyError at runtime")


def check_generation_config(where: str, cfg: Any, report: Report) -> None:
    if cfg is None:
        report.warn(f"{where}: no generate_content_config (scorer defaults: thinking on, temperature 1.0, "
                    "max_output_tokens 16384)")
        return
    if not isinstance(cfg, dict):
        report.error(f"{where}: generate_content_config must be a mapping")
        return
    for key in cfg:
        if key in R.GENERATION_FORBIDDEN_FIELDS:
            report.error(f"{where}: generate_content_config.{key} is forbidden")
        elif key not in R.GENERATION_ALLOWED_FIELDS:
            report.error(f"{where}: unknown generate_content_config field {key!r}")
    mot = cfg.get("max_output_tokens")
    if mot is not None and not (isinstance(mot, int) and not isinstance(mot, bool) and 1 <= mot <= R.MAX_MODEL_LEN):
        report.error(f"{where}: max_output_tokens must be an int in 1..{R.MAX_MODEL_LEN}")
    elif isinstance(mot, int) and mot > 8192:
        report.warn(f"{where}: max_output_tokens={mot} > 8192 raises the risk of prompt+output > 32,768 (HTTP 400)")
    t = cfg.get("temperature")
    if t is not None and (isinstance(t, bool) or not isinstance(t, (int, float)) or t < 0):
        report.error(f"{where}: temperature must be a number >= 0")
    tp = cfg.get("top_p")
    if tp is not None and (isinstance(tp, bool) or not isinstance(tp, (int, float)) or not 0 <= tp <= 1):
        report.error(f"{where}: top_p must be in [0, 1]")
    tk = cfg.get("top_k")
    if tk is not None and (isinstance(tk, bool) or not isinstance(tk, int) or tk < 1):
        report.error(f"{where}: top_k must be an int >= 1")
    tc = cfg.get("thinking_config")
    if tc is None:
        return
    if not isinstance(tc, dict):
        report.error(f"{where}: thinking_config must be a mapping")
        return
    for key in tc:
        if key not in R.THINKING_CONFIG_FIELDS:
            report.error(f"{where}: unknown thinking_config field {key!r}")
    tb = tc.get("thinking_budget")
    if tb is not None and (isinstance(tb, bool) or not isinstance(tb, int) or not 0 <= tb <= R.MAX_MODEL_LEN):
        report.error(f"{where}: thinking_budget must be an int in 0..{R.MAX_MODEL_LEN}")
    lvl = tc.get("thinking_level")
    if lvl is not None:
        if str(lvl).upper() not in R.THINKING_LEVELS:
            report.error(f"{where}: invalid thinking_level {lvl!r}")
        report.warn(f"{where}: thinking_level maps to reasoning_effort and is dropped by litellm on vLLM; "
                    "use include_thoughts + thinking_budget")
    if isinstance(mot, int) and isinstance(tb, int) and tb >= mot:
        report.warn(f"{where}: thinking_budget ({tb}) >= max_output_tokens ({mot}); tool calls may be cut off")
    if tc.get("include_thoughts") is True:
        report.note(f"{where}: thinking ON (VERIFY(Q3): thinking_budget may not be enforced by the harness)")


def check_adapter(root: Path, where: str, adapter: Any, report: Report) -> None:
    if not isinstance(adapter, str) or not R.IDENT_RE.match(adapter.replace("-", "_")):
        report.error(f"{where}: invalid adapter name {adapter!r}")
        return
    adir = root / "adapters" / adapter
    if not adir.is_dir():
        report.error(f"{where}: adapter {adapter!r} not found at adapters/{adapter}/")
        return
    cfg, weights = adir / "adapter_config.json", adir / "adapter_model.safetensors"
    if not cfg.is_file():
        report.error(f"adapters/{adapter}: missing adapter_config.json")
    if not weights.is_file() or weights.stat().st_size < 1024:
        report.error(f"adapters/{adapter}: missing or placeholder adapter_model.safetensors")
    if cfg.is_file():
        try:
            data = json.loads(cfg.read_text(encoding="utf-8"))
            r = int(data.get("r", 0))
            if r > R.MAX_LORA_RANK:
                report.error(f"adapters/{adapter}: rank {r} > max_lora_rank {R.MAX_LORA_RANK}")
            elif r > 32:
                report.warn(f"adapters/{adapter}: rank {r} > 32 shrinks the KV cache on 4x L4 (plan §6.2)")
            if data.get("peft_type", "LORA") != "LORA":
                report.error(f"adapters/{adapter}: peft_type must be LORA")
        except (ValueError, TypeError) as exc:
            report.error(f"adapters/{adapter}: bad adapter_config.json: {exc}")
    report.warn(f"adapters/{adapter}: shipping an adapter; VERIFY(Q4) logprob canary must pass on the scorer stack")


def check_agents(tree: AgentTree, report: Report) -> None:
    root = tree.root_dir
    names: dict[str, str] = {}
    models: set[str] = set()
    adapters: set[str] = set()
    state_keys = set(R.HARNESS_STATE_KEYS)
    for node in tree.agents:
        ok = node.config.get("output_key")
        if isinstance(ok, str):
            state_keys.add(ok)
    total_instr = 0
    if len(tree.agents) > R.MAX_AGENTS:
        report.error(f"too many agents: {len(tree.agents)}")

    for node in tree.agents:
        cfg = node.config
        where = node.path.relative_to(root).as_posix()
        cls = cfg.get("agent_class", "LlmAgent")
        if cls not in R.AGENT_CLASSES:
            report.error(f"{where}: unsupported agent_class {cls!r}")
            continue
        allowed_keys = R.LLM_AGENT_KEYS if cls == "LlmAgent" else R.WORKFLOW_AGENT_KEYS
        for key in cfg:
            if key not in allowed_keys:
                report.error(f"{where}: unknown/unsupported key {key!r} for {cls}")
        name = cfg.get("name")
        if not isinstance(name, str) or not R.IDENT_RE.match(name):
            report.error(f"{where}: 'name' must be a valid identifier, got {name!r}")
        elif name in names:
            report.error(f"{where}: duplicate agent name {name!r} (also in {names[name]})")
        else:
            names[name] = where
        if name == "user":
            report.error(f"{where}: agent name 'user' is reserved by ADK")
        if cls == "LoopAgent":
            mi = cfg.get("max_iterations", 500)
            if not isinstance(mi, int) or not 1 <= mi <= R.MAX_LOOP_ITERATIONS:
                report.error(f"{where}: max_iterations must be 1..{R.MAX_LOOP_ITERATIONS}")
        if cls != "LlmAgent":
            if not cfg.get("sub_agents"):
                report.error(f"{where}: {cls} needs sub_agents")
            continue

        model = cfg.get("model")
        if not isinstance(model, str) or not model:
            report.error(f"{where}: LlmAgent requires 'model'")
        else:
            norm = R.normalize_model_name(model)
            models.add(norm)
            if norm not in R.ALLOWED_MODEL_NAMES:
                report.error(f"{where}: model {model!r} not allowed (only {sorted(R.ALLOWED_MODEL_NAMES)})")

        instr = cfg.get("instruction")
        check_instruction(where, instr, state_keys, report)
        check_instruction(f"{where} (global_instruction)", cfg.get("global_instruction"), state_keys, report)
        if isinstance(instr, str):
            total_instr += len(instr)
        elif instr is None:
            report.warn(f"{where}: agent has no instruction")
        if node.via != "root" and not cfg.get("description"):
            report.warn(f"{where}: sub-agent without description; the parent cannot tell when to use it")
        ic = cfg.get("include_contents")
        if ic is not None and ic not in ("default", "none"):
            report.error(f"{where}: include_contents must be 'default' or 'none'")
        check_generation_config(where, cfg.get("generate_content_config"), report)

        tools = cfg.get("tools")
        if tools is None:
            tools = []
            report.warn(f"{where}: no tools declared")
        if not isinstance(tools, list):
            report.error(f"{where}: tools must be a list")
            tools = []
        tool_names: list[str] = []
        for t in tools:
            if isinstance(t, str):
                if t not in R.HARNESS_TOOLS:
                    report.error(f"{where}: tool {t!r} is not provided by the harness (VERIFY(Q1) registry)")
                elif t in tool_names:
                    report.error(f"{where}: tool {t!r} listed twice")
                tool_names.append(t)
            elif isinstance(t, dict) and set(t) == {"agent_tool"} and isinstance(t["agent_tool"], dict):
                extra = set(t["agent_tool"]) - R.AGENT_TOOL_KEYS
                if extra:
                    report.error(f"{where}: unsupported agent_tool keys {sorted(extra)}")
                if "config_path" not in t["agent_tool"]:
                    report.error(f"{where}: agent_tool requires config_path")
            elif isinstance(t, dict) and "name" in t:
                report.error(f"{where}: tool entry {t!r} uses the {{name: ...}} form; use plain tool-name strings "
                             "or agent_tool: {config_path: ...} (VERIFY(Q2) against sample_submission)")
            else:
                report.error(f"{where}: unsupported tool entry {t!r}")

        if isinstance(instr, str):
            for t in sorted(R.HARNESS_TOOLS):
                if t not in tool_names and re.search(rf"\b{t}\b", instr):
                    report.warn(f"{where}: instruction mentions tool {t!r} but the agent does not declare it")
            for t in sorted(R.SKILL_TOOLS):
                if t in instr and not cfg.get("skills"):
                    report.warn(f"{where}: instruction mentions {t} but the agent declares no skills")
        if node.via == "root":
            if "submit_patch" not in tool_names:
                report.warn(f"{where}: root agent lacks submit_patch (harness falls back to git diff)")
            if not ({"edit_file", "write_file", "run_command"} & set(tool_names)):
                report.error(f"{where}: root agent has no way to modify files")
        elif "submit_patch" in tool_names:
            report.warn(f"{where}: sub-agent with submit_patch can end the session from inside a sub-call")
        for s in cfg.get("skills") or []:
            if not isinstance(s, str):
                report.error(f"{where}: skills entries must be relative path strings")
        for sub in cfg.get("sub_agents") or []:
            if not (isinstance(sub, dict) and "config_path" in sub):
                report.error(f"{where}: sub_agents entries must be {{config_path: ...}}")
        adapter = cfg.get("adapter")
        if adapter is not None:
            adapters.add(str(adapter))
            check_adapter(root, where, adapter, report)

    if len(models) > 1:
        report.error(f"multiple base models declared: {sorted(models)} (single-model rule)")
    if len(adapters) > 1:
        report.warn(f"{len(adapters)} adapters declared; community reports [M] recommend at most 1")
    if total_instr > R.MAX_TOTAL_INSTRUCTION_CHARS:
        report.error("total instruction size exceeds 10M chars")
    report.note(f"{len(tree.agents)} agent(s): {', '.join(sorted(names))}; "
                f"instruction chars: {total_instr}")


def check_skill(root: Path, skill_dir: Path, report: Report) -> None:
    rel = skill_dir.relative_to(root).as_posix()
    md = skill_dir / "SKILL.md"
    if not md.is_file():
        report.error(f"{rel}: SKILL.md missing")
        return
    text = md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        report.error(f"{rel}/SKILL.md: must start with YAML frontmatter '---'")
        return
    parts = text.split("---", 2)
    if len(parts) < 3:
        report.error(f"{rel}/SKILL.md: frontmatter not closed with '---'")
        return
    try:
        fm = yaml.safe_load(parts[1])
    except yaml.YAMLError as exc:
        report.error(f"{rel}/SKILL.md: invalid frontmatter YAML: {exc}")
        return
    if not isinstance(fm, dict):
        report.error(f"{rel}/SKILL.md: frontmatter must be a mapping")
        return
    for key in fm:
        if key not in R.SKILL_FRONTMATTER_KEYS:
            report.error(f"{rel}/SKILL.md: unsupported frontmatter key {key!r}")
    name = fm.get("name")
    if not isinstance(name, str) or not R.KEBAB_RE.match(name) or len(name) > R.SKILL_NAME_MAX:
        report.error(f"{rel}/SKILL.md: name must be kebab-case <= {R.SKILL_NAME_MAX} chars, got {name!r}")
    elif name != skill_dir.name:
        report.error(f"{rel}/SKILL.md: name {name!r} must equal the directory name {skill_dir.name!r}")
    desc = fm.get("description")
    if not isinstance(desc, str) or not desc.strip():
        report.error(f"{rel}/SKILL.md: description required")
    elif len(desc) > R.SKILL_DESCRIPTION_MAX:
        report.error(f"{rel}/SKILL.md: description > {R.SKILL_DESCRIPTION_MAX} chars")
    size = 0
    for p in skill_dir.rglob("*"):
        if not p.is_file() or "__pycache__" in p.parts:
            continue
        size += p.stat().st_size
        sub = p.relative_to(skill_dir).as_posix()
        top = sub.split("/", 1)[0]
        if sub != "SKILL.md" and top not in R.SKILL_SUBDIRS:
            report.warn(f"{rel}/{sub}: outside {R.SKILL_SUBDIRS}; ADK will not load it")
        if top == "scripts":
            report.warn(f"{rel}/{sub}: skill scripts rely on run_skill_script (VERIFY(Q1): ToolNotFoundError reported)")
            if p.suffix != ".py":
                report.error(f"{rel}/{sub}: skill scripts must be .py")
        if p.suffix == ".py":
            try:
                ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
            except SyntaxError as exc:
                report.error(f"{rel}/{sub}: syntax error: {exc}")
        if p.suffix in (".md", ".txt", ".py"):
            check_text_content(root, p, report, is_prompt=True)
    if size > R.MAX_SKILL_SIZE_BYTES:
        report.error(f"{rel}: skill larger than 50 MiB")


def worst_case_hours(max_time_minutes: float, *, tasks: int = R.EXPECTED_HIDDEN_TASKS,
                     setup_minutes: float = R.ASSUMED_SETUP_MINUTES) -> float:
    return tasks * (max_time_minutes + setup_minutes) / 60.0


def check_eval_config(root: Path, report: Report) -> None:
    path = root / "eval_config.yaml"
    if not path.is_file():
        report.error("no eval_config.yaml: the harness default of 60 min/task would exceed the 12 h run budget")
        return
    try:
        data = load_yaml(root, path).data
    except SubmissionError as exc:
        report.error(f"eval_config.yaml: {exc}")
        return
    if not isinstance(data, dict) or not isinstance(data.get("evaluation"), dict):
        report.error("eval_config.yaml: must contain an 'evaluation:' mapping (VERIFY(Q2))")
        return
    ev = data["evaluation"]
    for key, val in ev.items():
        if key not in R.EVAL_CONFIG_KEYS:
            report.error(f"eval_config.yaml: unknown key evaluation.{key} (known: {sorted(R.EVAL_CONFIG_KEYS)})")
        elif isinstance(val, bool) or not isinstance(val, (int, float)) or val <= 0:
            report.error(f"eval_config.yaml: evaluation.{key} must be a positive number")
    minutes = ev.get("max_time_minutes")
    if minutes is None:
        report.error("eval_config.yaml: max_time_minutes missing -> no per-task cap (harness default 60 min)")
    elif isinstance(minutes, (int, float)) and not isinstance(minutes, bool):
        hours = worst_case_hours(float(minutes))
        msg = (f"worst case {R.EXPECTED_HIDDEN_TASKS} x ({minutes} + {R.ASSUMED_SETUP_MINUTES} setup) min = "
               f"{hours:.2f} h (gate {R.PACK_GATE_HOURS} h, limit {R.RUN_BUDGET_HOURS} h)")
        if hours > R.PACK_GATE_HOURS + 1e-9:
            report.error("eval_config.yaml: " + msg + " -> EXCEEDS the packing gate")
        else:
            report.note("eval_config.yaml: " + msg)
    for key in ("max_tool_calls", "max_turns"):
        if ev.get(key) is None:
            report.warn(f"eval_config.yaml: {key} missing -> harness default applies")
    ts = ev.get("timeout_seconds")
    if ts is None:
        report.warn("eval_config.yaml: timeout_seconds missing -> harness default 300 s")
    elif isinstance(ts, (int, float)) and ts < 300:
        report.warn(f"eval_config.yaml: timeout_seconds={ts} < 300 may also cap the grading pytest run (VERIFY(Q2))")


def check_official(root: Path, report: Report) -> None:
    """Run the harness's own validator/compiler when the wheelhouse packages are importable (VERIFY(Q1/Q2))."""
    try:
        import adk_submission  # type: ignore
    except ImportError as exc:
        report.note(f"official adk-submission validator not importable ({exc}); install from the wheelhouse to enable")
        return
    ran = False
    for fn_name in ("validate_directory", "validate_submission", "compile_submission"):
        fn = getattr(adk_submission, fn_name, None)
        if fn is None:
            continue
        ran = True
        try:
            fn(str(root))
            report.note(f"official adk_submission.{fn_name}: OK")
        except Exception as exc:  # noqa: BLE001
            report.error(f"official adk_submission.{fn_name} raised {type(exc).__name__}: {exc}")
    try:
        from swegemma.models.discovery import validate_single_declared_model  # type: ignore
        report.note(f"official validate_single_declared_model: {validate_single_declared_model(str(root))}")
        ran = True
    except ImportError:
        pass
    except Exception as exc:  # noqa: BLE001
        report.error(f"official validate_single_declared_model raised {type(exc).__name__}: {exc}")
    if not ran:
        report.warn("adk_submission imported but no known validator entry point found; inspect the wheel")


# ----------------------------------------------------------------------------- entry points

def validate_dir(root: Path, *, strict_tree: bool = True, official: bool = False) -> Report:
    report = Report()
    root = root.resolve()
    if not root.is_dir():
        report.error(f"not a directory: {root}")
        return report
    check_files(root, report, strict_tree=strict_tree)
    try:
        tree = load_agent_tree(root)
    except SubmissionError as exc:
        report.error(str(exc))
        return report
    for w in tree.warnings:
        report.warn(w)
    check_agents(tree, report)
    for skill_dir in sorted(tree.skill_dirs):
        check_skill(root, skill_dir, report)
    check_eval_config(root, report)
    reachable = tree.reachable_files()
    for p in sorted(reachable):
        if p.suffix.lower() in (".md", ".txt", ".yaml", ".yml", ".py"):
            is_prompt = p.suffix.lower() in (".md", ".txt")
            check_text_content(root, p, report, is_prompt=is_prompt)
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.resolve() not in reachable and not p.name.startswith(".") and "__pycache__" not in p.parts:
            rel = p.relative_to(root).as_posix()
            if strict_tree:
                report.warn(f"unreferenced file shipped: {rel}")
            else:
                report.note(f"unreferenced (not shipped by the packer): {rel}")
    if official:
        check_official(root, report)
    return report


def validate_zip(zip_path: Path, *, official: bool = False) -> Report:
    report = Report()
    if not zip_path.is_file():
        report.error(f"archive not found: {zip_path}")
        return report
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        bad = zf.testzip()
        if bad:
            report.error(f"corrupt archive member: {bad}")
        for info in zf.infolist():
            n = info.filename
            pp = PurePosixPath(n)
            if pp.is_absolute() or ".." in pp.parts or "\\" in n:
                report.error(f"unsafe archive member path: {n}")
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                report.error(f"symlink inside archive: {n}")
            if not n.endswith("/") and info.file_size == 0:
                report.error(f"0-byte member: {n}")
        roots = [n for n in names if n in R.ROOT_CONFIG_NAMES]
        if not roots:
            nested = [n for n in names if PurePosixPath(n).name in R.ROOT_CONFIG_NAMES]
            hint = f" (found nested: {nested}; zip the CONTENTS of submission/, not the folder)" if nested else ""
            report.error("agent.yaml is not at the archive root" + hint)
        if report.errors:
            return report
        with tempfile.TemporaryDirectory() as td:
            zf.extractall(td)
            inner = validate_dir(Path(td), strict_tree=True, official=official)
    report.extend(inner)
    report.note(f"archive {zip_path.name}: {len(names)} members, {zip_path.stat().st_size / 1024:.1f} KiB")
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", type=Path, help="submission directory or submission.zip")
    ap.add_argument("--official", action="store_true", help="also run the harness's own validator if importable")
    ap.add_argument("--strict", action="store_true",
                    help="treat the directory as the exact zip contents (hidden files/unreferenced files are errors/warnings)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    if args.target.suffix.lower() == ".zip":
        report = validate_zip(args.target, official=args.official)
    else:
        report = validate_dir(args.target, strict_tree=args.strict, official=args.official)
    if args.json:
        print(json.dumps(dataclasses.asdict(report), indent=2))
    else:
        print(report.render())
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
