"""Offline compile of agent trees with stub tools, to check sub-agent and agent_tool wiring before a GPU job.

  apptainer exec --bind $PWD/.. env/harness.sif python3 -I tools/compile_check.py trees/<a> [trees/<b> ...]

Prints the compiled agent tree (class, name, tools, include_contents). No model is called.
"""
import sys
from adk_submission.compiler import compile_submission
from adk_submission.registry import ModelRegistry
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import FunctionTool
def mk(n):
    def f(**kw): return {}
    f.__name__ = n
    return FunctionTool(f)
names = ["run_command","read_file","edit_file","write_file","get_status","submit_patch"]
tools = {n: mk(n) for n in names}
for d in sys.argv[1:]:
    models = ModelRegistry()
    for m in ["gemma-4-31b-it-qat-w4a16-ct","gemma-4-e4b-it-qat-w4a16-ct"]:
        models.register(m, LiteLlm(model="openai/"+m, api_base="http://127.0.0.1:1/v1", api_key="EMPTY"))
    a = compile_submission(submission_dir=d, tool_registry=tools, model_registry=models)
    def show(x, ind=0):
        tl = [getattr(t,'name',type(t).__name__) for t in getattr(x,'tools',[]) or []]
        print(" "*ind + f"{type(x).__name__} {x.name} tools={tl} out={getattr(x,'output_key',None)} inc={getattr(x,'include_contents',None)}")
        for t in getattr(x,'tools',[]) or []:
            if type(t).__name__=="AgentTool": print(" "*ind+"  agent_tool skip_summ=",t.skip_summarization); show(t.agent, ind+4)
        for s in x.sub_agents: show(s, ind+2)
    print("==", d); show(a)
