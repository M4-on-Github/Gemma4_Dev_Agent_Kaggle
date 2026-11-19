"""Write a Turing-safe copy of vLLM 0.19.1's Triton unified-attention op for pleiades-1-10.

Why: on the Quadro RTX 6000 (sm_75, 64 KB shared memory per block) vLLM's only usable attention backend for
Gemma 4 is TRITON_ATTN. FlashAttention needs sm_80, FlashInfer stops at head size 256, and FlexAttention has no
KV sharing, which the E4B uses. At the global layers' head size 512, the 2D kernel's 32-wide tile with Triton's
default 3 pipeline stages needs 96 KB, so the engine dies in CUDA-graph profiling (R-009, job 59472).

Change, applied only when the device's compute capability is below 8.0:
  - every kernel launch gets num_stages=1;
  - tiles are 16 wide for head sizes above 256.
On sm_80+ the patched file runs exactly as the original. eval.sbatch binds it over the image's copy only on
Quadro RTX 6000 nodes. Nothing is installed; the output goes to env/ (gitignored), and the source is read from
the image each time so no vLLM code is committed.

    apptainer exec --containall env/harness.sif python3 -I tools/turing_patches/make_triton_attn_patch.py \
        env/turing_patches/triton_unified_attention.py
"""
import sys
from pathlib import Path

SRC = Path("/usr/local/lib/python3.12/dist-packages/vllm/v1/attention/ops/triton_unified_attention.py")

text = SRC.read_text()

helper = '''

# ---- Turing patch (harness-eng tools/turing_patches/make_triton_attn_patch.py) ----
import functools as _functools


@_functools.cache
def _small_smem() -> bool:
    return torch.cuda.get_device_capability()[0] < 8


def _launch_kw() -> dict:
    return {"num_stages": 1} if _small_smem() else {}
# ---- end Turing patch ----

'''

edits = [
    # 1. helper after the imports
    ("from vllm.triton_utils import tl, triton\n", "from vllm.triton_utils import tl, triton\n" + helper),
    # 2. 16-wide tiles for head sizes above 256 on small-smem devices
    ('    """Select tile size with Gemma3-specific optimization.\n',
     '    """Select tile size with Gemma3-specific optimization.\n'),
    ("    if _is_gemma3_attention(head_size, sliding_window):\n",
     "    if _small_smem() and head_size > 256:\n        return 16\n"
     "    if _is_gemma3_attention(head_size, sliding_window):\n"),
    # 3. num_stages on the three launches
    ("            BLOCK_M=BLOCK_M,\n            USE_FP8=output_scale is not None,\n        )\n",
     "            BLOCK_M=BLOCK_M,\n            USE_FP8=output_scale is not None,\n            **_launch_kw(),\n        )\n"),
    ("            NUM_SEGMENTS_PER_SEQ=num_par_softmax_segments,\n        )\n        reduce_segments",
     "            NUM_SEGMENTS_PER_SEQ=num_par_softmax_segments,\n            **_launch_kw(),\n        )\n        reduce_segments"),
    ("            NUM_SEGMENTS_PER_SEQ=num_par_softmax_segments,\n            USE_FP8=output_scale is not None,\n        )\n",
     "            NUM_SEGMENTS_PER_SEQ=num_par_softmax_segments,\n            USE_FP8=output_scale is not None,\n            **_launch_kw(),\n        )\n"),
]
for old, new in edits:
    n = text.count(old)
    if n != 1:
        sys.exit(f"patch anchor found {n} times, expected 1 (vLLM version changed?):\n{old!r}")
    text = text.replace(old, new)

out = Path(sys.argv[1])
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(text)
print(f"wrote {out} ({len(text)} bytes)")
