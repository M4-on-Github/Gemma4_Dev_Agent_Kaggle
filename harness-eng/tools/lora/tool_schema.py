"""Dump the exact OpenAI-style tool list the served model sees, for rendering LoRA training samples.

  apptainer exec env/harness.sif python3 -I tools/lora/tool_schema.py --out /data/mmyatmau/gemma4-lora/schema/tools.json

Builds the harness's own tools (swegemma.tools.create_tools) on a dummy context, wraps them as ADK FunctionTools
and converts each declaration with ADK's LiteLlm converter, the same path a served request takes. No model, no
sandbox and no task data are touched.
"""
import argparse
import json
from types import SimpleNamespace

from google.adk.models.lite_llm import _function_declaration_to_tool_param
from google.adk.tools import FunctionTool
from swegemma.tools import create_tools

SIX = ["run_command", "read_file", "edit_file", "write_file", "get_status", "submit_patch"]

p = argparse.ArgumentParser()
p.add_argument("--out", required=True)
a = p.parse_args()
fns = create_tools(SimpleNamespace(harness=SimpleNamespace()))
out = {}
for n in SIX:
    decl = FunctionTool(fns[n])._get_declaration()
    out[n] = _function_declaration_to_tool_param(decl)
json.dump(out, open(a.out, "w"), indent=1)
for n, t in out.items():
    print(n, sorted(t["function"]["parameters"].get("properties", {})), t["function"].get("parameters", {}).get("required"))
