"""Competition constants shared by the dev tools.

Provenance: the HARNESS_README mirror and four community submissions (see experiments/README.md, Q1/Q2/Q9).
kaggle.com was unreachable from the build environment, so every value marked VERIFY(Qn) must be checked
against the official files (HARNESS_README.md, sample_submission/, the adk-submission / swegemma wheels)
once the dataset is downloaded. Nothing here was verified against official files.
"""
from __future__ import annotations

import re

# VERIFY(Q1): exact compile-time tool registry (9 names below + agent_tool entries). run_skill_script /
# load_skill_resource / load_skill / list_skills are added by ADK's SkillToolset when `skills:` is declared;
# one team reported ToolNotFoundError for run_skill_script, so do not rely on them.
HARNESS_TOOLS = frozenset({
    "run_command", "read_file", "edit_file", "write_file", "get_status", "submit_patch",
    "get_code_neighbors", "search_similar_code", "get_code_subgraph",
})
FREE_TOOLS = frozenset({"get_status", "submit_patch"})
SKILL_TOOLS = frozenset({"list_skills", "load_skill", "load_skill_resource", "run_skill_script"})

# VERIFY(Q2): model alias and provider prefixes (normalize_model_name strips the prefixes).
ALLOWED_MODEL_NAMES = frozenset({"gemma-4-31b-it-qat-w4a16-ct"})
MODEL_PROVIDER_PREFIXES = ("openai/", "google/", "hosted_vllm/", "custom/")

ROOT_CONFIG_NAMES = ("agent.yaml", "agent.yml", "root_agent.yaml", "root_agent.yml")
AGENT_CLASSES = frozenset({"LlmAgent", "SequentialAgent", "ParallelAgent", "LoopAgent"})
LLM_AGENT_KEYS = frozenset({
    "agent_class", "name", "model", "adapter", "description", "instruction", "global_instruction",
    "tools", "skills", "sub_agents", "output_key", "include_contents",
    "disallow_transfer_to_parent", "disallow_transfer_to_peers", "generate_content_config",
})
WORKFLOW_AGENT_KEYS = frozenset({"agent_class", "name", "description", "sub_agents", "max_iterations"})
AGENT_TOOL_KEYS = frozenset({"config_path", "skip_summarization"})

# VERIFY(Q2): generate_content_config field sets (HARNESS_README §2.4 mirror).
GENERATION_ALLOWED_FIELDS = frozenset({
    "temperature", "top_p", "top_k", "max_output_tokens", "presence_penalty", "frequency_penalty",
    "stop_sequences", "response_mime_type", "seed", "thinking_config",
})
GENERATION_FORBIDDEN_FIELDS = frozenset({
    "tools", "system_instruction", "http_options", "safety_settings", "response_schema",
})
THINKING_CONFIG_FIELDS = frozenset({"thinking_budget", "thinking_level", "include_thoughts"})
THINKING_LEVELS = frozenset({"MINIMAL", "LOW", "MEDIUM", "HIGH", "NONE"})
MAX_MODEL_LEN = 32_768

# VERIFY(Q2): eval_config.yaml schema: `evaluation:` mapping with exactly these keys; a missing key = no limit.
EVAL_CONFIG_KEYS = frozenset({"timeout_seconds", "max_tool_calls", "max_time_minutes", "max_turns"})
HARNESS_DEFAULT_TIME_MINUTES = 60.0
HARNESS_DEFAULT_TIMEOUT_SECONDS = 300
HARNESS_DEFAULT_TOOL_CALLS = 100
HARNESS_DEFAULT_TURNS = 500

# VERIFY(Q9): allowed extensions and size limits (swegemma/config.py per mirror).
ALLOWED_EXTENSIONS = frozenset({".yaml", ".yml", ".md", ".txt", ".py", ".json", ".safetensors"})
MAX_TOTAL_SIZE_BYTES = 3 * 1024 ** 3          # unpacked, adapters included
MAX_FILE_COUNT = 10_000
MAX_YAML_SIZE_BYTES = 50 * 1024 ** 2
MAX_SKILL_SIZE_BYTES = 50 * 1024 ** 2
MAX_INSTRUCTION_CHARS = 1_000_000
MAX_TOTAL_INSTRUCTION_CHARS = 10_000_000
MAX_AGENTS = 500
MAX_INCLUDE_DEPTH = 10
MAX_LOOP_ITERATIONS = 500
MAX_LORA_RANK = 128

# Session-state keys the harness sets (HARNESS_README §5.1 mirror). `hints` is absent on tasks without hints,
# so an instruction may only reference it as {hints?}. Any other {identifier} raises KeyError at runtime.
HARNESS_STATE_KEYS = frozenset({"problem_description"})
HARNESS_OPTIONAL_STATE_KEYS = frozenset({"hints"})
PLACEHOLDER_RE = re.compile(r"{+[^{}]*}+")   # same pattern ADK uses for instruction templating
IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

SKILL_FRONTMATTER_KEYS = frozenset({
    "name", "description", "license", "allowed-tools", "allowed_tools", "metadata", "compatibility",
})
SKILL_NAME_MAX = 64
SKILL_DESCRIPTION_MAX = 1024
SKILL_SUBDIRS = ("scripts", "references", "assets", "resources")

# Our own lint rules (plan §4.5 / §8.2), not harness rules.
# Strings that must not appear in shipped text: the sandbox is offline and the compiler is declarative, and
# community reports [M] say references to networking / package installs / MCP / subprocess get flagged.
FORBIDDEN_TEXT_PATTERNS = (
    (re.compile(r"\bpip3?\s+install\b", re.I), "pip install"),
    (re.compile(r"\bsubprocess\b", re.I), "subprocess"),
    (re.compile(r"\bmcp\b", re.I), "mcp"),
    (re.compile(r"https?://", re.I), "URL"),
    (re.compile(r"\bnetwork\b", re.I), "network"),
    (re.compile(r"\burllib\b|\bsocket\b|\brequests\.(get|post)\b", re.I), "network library"),
)
# Prompts must stay repo-agnostic (plan §8.2): the hidden set is private repositories.
PUBLIC_REPO_WORDS = (
    re.compile(r"\bfastapi\b", re.I), re.compile(r"\bstarlette\b", re.I), re.compile(r"\bpydantic\b", re.I),
    re.compile(r"\brich\.[a-z_]+\b"), re.compile(r"\bTextualize\b", re.I), re.compile(r"\bhttpx\b", re.I),
    re.compile(r"\bpsf/requests\b", re.I), re.compile(r"\brequests\.(sessions|adapters|models)\b"),
)

# Run-budget planning (plan §4.4).
RUN_BUDGET_HOURS = 12.0
PACK_GATE_HOURS = 11.0               # block packing if worst case exceeds this
EXPECTED_HIDDEN_TASKS = 120
ASSUMED_SETUP_MINUTES = 1.0          # VERIFY(Q8): measure setup_s on Kaggle; community says < 5 s, plan says 45-60 s
ASSUMED_SERVER_START_MINUTES = 15.0  # vLLM start on 4x L4, reported once per run [M]
ASSUMED_DECODE_TOK_S = 25.5          # VERIFY(Q10): one real trace implies >= 36 tok/s effective
ASSUMED_PER_CALL_OVERHEAD_S = 0.6    # VERIFY(Q10)


def normalize_model_name(model: str) -> str:
    for prefix in MODEL_PROVIDER_PREFIXES:
        if model.startswith(prefix):
            return model[len(prefix):]
    return model
