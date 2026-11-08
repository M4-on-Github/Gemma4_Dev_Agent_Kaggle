"""EXP-054 analysis: applies section 4 of experiments/EXP-054-exact-copy-lora-train-eval-e4b.md to one run dir.

Run as: python -I -X utf8 experiments/EXP-054/analyze_copy_lora.py runs/EXP-054-copy-lora [--json out.json]

Reads run.json, eval.jsonl, probes.jsonl and train.json written by notebooks/exp054_copylora/copy_lora.py.
Prints ids, counts, rates, p-values and the reading that fires (first match wins). It never prints a call's
arguments or any file text: calls.jsonl is not read.
"""
import json
import math
import statistics
import sys
from collections import Counter
from pathlib import Path

DELTA = 0.10          # the paired effect the readings treat as a move (section 3)
ALPHA = 0.05
DECODE_DROP_MAX = 0.35
MIN_PAIRED = 60
MIN_PAIRS_TRAIN = 32


def jl(p: Path) -> list:
    return [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()] if p.exists() else []


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact McNemar p on the discordant counts (binomial, p = 0.5)."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def rate(xs) -> float | None:
    xs = list(xs)
    return sum(xs) / len(xs) if xs else None


def wilson(k: int, n: int, z: float = 1.96):
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(c - h, 3), round(c + h, 3))


def rows_by(rows, boot, arm, kind):
    return {r['pid']: r for r in rows if r.get('boot') == boot and r.get('arm') == arm and r.get('kind') == kind}


def mean_abs_diff(a: list, b: list):
    if not a or not b or len(a) != len(b):
        return None, None
    d = [abs(x - y) for x, y in zip(a, b) if x is not None and y is not None]
    return (statistics.mean(d), max(d)) if d else (None, None)


def logprob_drift(probes, boot, la, lb):
    """Mean and max per-token |delta logprob| over the two texts, label la against label lb."""
    by = {(p['label'], p['i']): p.get('logprobs') for p in probes
          if p.get('kind') == 'logprob' and p.get('boot') == boot and p.get('status') == 200}
    means, maxes = [], []
    for i in (0, 1):
        m, x = mean_abs_diff(by.get((la, i)) or [], by.get((lb, i)) or [])
        if m is not None:
            means.append(m); maxes.append(x)
    return (statistics.mean(means) if means else None, max(maxes) if maxes else None, len(means))


def analyze(run_dir: Path) -> dict:
    run = json.loads((run_dir / 'run.json').read_text(encoding='utf-8')) if (run_dir / 'run.json').exists() else {}
    rows = jl(run_dir / 'eval.jsonl')
    probes = jl(run_dir / 'probes.jsonl')
    train = json.loads((run_dir / 'train.json').read_text(encoding='utf-8')) if (run_dir / 'train.json').exists() else {}
    out: dict = {'status': run.get('status'), 'stopped_why': (run.get('stages', {}).get('stopped') or {}).get('why'),
                 'elapsed_s': run.get('elapsed_s'), 'paths': run.get('paths'), 'data': run.get('data'),
                 'train_data': run.get('train_data'), 'render_check': run.get('render_check')}
    out['train'] = {k: train.get(k) for k in ('weights', 'rank_world', 'L_ok', 'n_seqs_fit', 'n_pairs_fit', 'steps',
                                              'total_steps_planned', 'seqs_seen', 'stopped', 'train_s',
                                              'peak_train_gib', 'b_norm_total', 'n_tensors', 'n_lora_modules')}
    hist = train.get('history') or []
    for key in ('pair_loss', 'anchor_loss'):
        v = [h[key] for h in hist if h.get(key) is not None]
        out['train'][key + '_first5'] = round(statistics.mean(v[:5]), 4) if v else None
        out['train'][key + '_last5'] = round(statistics.mean(v[-5:]), 4) if v else None

    # paired edit prompts on boot 1, greedy
    b1, ad = rows_by(rows, 'boot1', 'base1', 'edit'), rows_by(rows, 'boot1', 'adapter', 'edit')
    b0 = rows_by(rows, 'boot0', 'base0', 'edit')
    adapter_all = [r for r in rows if r.get('arm') == 'adapter']
    out['adapter_requests'] = len(adapter_all)
    out['adapter_non200_share'] = rate(r.get('status') != 200 for r in adapter_all)
    out['adapter_resp_models'] = dict(Counter(r.get('resp_model') for r in adapter_all if r.get('status') == 200))
    pids = sorted(p for p in b1 if p in ad and b1[p].get('status') == 200 and ad[p].get('status') == 200)
    n = len(pids)
    out['n_paired'] = n
    e_b = [b1[p].get('cls') == 'E' for p in pids]
    e_a = [ad[p].get('cls') == 'E' for p in pids]
    bb = sum(1 for x, y in zip(e_a, e_b) if x and not y)
    cc = sum(1 for x, y in zip(e_a, e_b) if y and not x)
    out['exact_base1'] = rate(e_b); out['exact_adapter'] = rate(e_a)
    out['exact_base1_ci'] = wilson(sum(e_b), n); out['exact_adapter_ci'] = wilson(sum(e_a), n)
    out['discordant_adapter_only'] = bb; out['discordant_base1_only'] = cc
    out['delta_exact'] = (out['exact_adapter'] - out['exact_base1']) if n else None
    out['p_mcnemar'] = mcnemar_exact(bb, cc)
    p0 = [p for p in pids if p in b0 and b0[p].get('status') == 200]
    out['n_with_base0'] = len(p0)
    out['exact_base0_on_paired'] = rate(b0[p].get('cls') == 'E' for p in p0)
    out['exact_adapter_on_base0_ids'] = rate(ad[p].get('cls') == 'E' for p in p0)
    out['boot_agreement_exact_base0_base1'] = rate((b0[p].get('cls') == 'E') == (b1[p].get('cls') == 'E') for p in p0)
    for arm, d in (('base1', b1), ('adapter', ad)):
        rs = [d[p] for p in pids]
        out[f'classes_{arm}'] = dict(Counter(r.get('cls') for r in rs))
        out[f'edit_call_rate_{arm}'] = rate(r.get('tool') == 'edit_file' for r in rs)
        out[f'correct_ast_{arm}'] = rate(bool(r.get('correct_ast')) for r in rs)
        out[f'correct_strict_{arm}'] = rate(bool(r.get('correct_strict')) for r in rs)
        calls = [r for r in rs if r.get('tool') == 'edit_file']
        out[f'exact_given_edit_{arm}'] = rate(r.get('cls') == 'E' for r in calls)
        out[f'by_kind_exact_{arm}'] = {k: rate(r.get('cls') == 'E' for r in rs if r.get('edit_kind') == k)
                                       for k in ('K1', 'K2', 'K3')}
    out['class_disagreement'] = rate(b1[p].get('cls') != ad[p].get('cls') for p in pids)

    # T = 1 subset (shipped sampling), secondary
    t1b, t1a = rows_by(rows, 'boot1', 'base1', 't1'), rows_by(rows, 'boot1', 'adapter', 't1')
    tp = sorted(p for p in t1b if p in t1a and t1b[p].get('status') == 200 and t1a[p].get('status') == 200)
    tb = [t1b[p].get('cls') == 'E' for p in tp]; ta = [t1a[p].get('cls') == 'E' for p in tp]
    out['t1'] = {'n': len(tp), 'exact_base1': rate(tb), 'exact_adapter': rate(ta),
                 'p_mcnemar': mcnemar_exact(sum(1 for x, y in zip(ta, tb) if x and not y),
                                            sum(1 for x, y in zip(ta, tb) if y and not x))}

    # drift gate
    d1, da = rows_by(rows, 'boot1', 'base1', 'drift'), rows_by(rows, 'boot1', 'adapter', 'drift')
    d0 = rows_by(rows, 'boot0', 'base0', 'drift')
    dp = sorted(p for p in d1 if p in da and d1[p].get('status') == 200 and da[p].get('status') == 200)
    dp0 = [p for p in dp if p in d0 and d0[p].get('status') == 200]
    agree_ab = rate(d1[p].get('tool') == da[p].get('tool') for p in dp)
    agree_01 = rate(d1[p].get('tool') == d0[p].get('tool') for p in dp0)
    g = {'n_drift_paired': len(dp), 'n_drift_with_base0': len(dp0), 'tool_agree_adapter_base1': agree_ab,
         'tool_agree_base0_base1': agree_01,
         'first_tools_base1': dict(Counter(d1[p].get('tool') for p in dp)),
         'first_tools_adapter': dict(Counter(da[p].get('tool') for p in dp))}
    g['G1'] = (agree_ab is not None and agree_ab >= 0.70 and (agree_01 is None or agree_ab >= agree_01 - 0.10))
    pooled = [(b1[p], ad[p]) for p in pids] + [(d1[p], da[p]) for p in dp]
    nocall_b = rate(x.get('tool') is None for x, _ in pooled)
    nocall_a = rate(y.get('tool') is None for _, y in pooled)
    g['no_call_base1'] = nocall_b; g['no_call_adapter'] = nocall_a
    g['G2'] = nocall_a is not None and nocall_b is not None and nocall_a - nocall_b <= 0.10
    ct_b = [d1[p].get('completion_tokens') or 0 for p in dp]; ct_a = [da[p].get('completion_tokens') or 0 for p in dp]
    both = [p for p in dp if d1[p].get('call_tokens') and da[p].get('call_tokens')]
    g['completion_token_ratio'] = (statistics.mean(ct_a) / statistics.mean(ct_b)) if dp and statistics.mean(ct_b) else None
    g['call_token_ratio'] = (statistics.mean(da[p]['call_tokens'] for p in both) /
                             statistics.mean(d1[p]['call_tokens'] for p in both)) if both else None
    g['n_call_token_pairs'] = len(both)
    g['G3'] = (g['completion_token_ratio'] is not None and 0.67 <= g['completion_token_ratio'] <= 1.5
               and g['call_token_ratio'] is not None and 0.8 <= g['call_token_ratio'] <= 1.25)
    lp_mean, lp_max, lp_n = logprob_drift(probes, 'boot1', 'adapter', 'base1')
    fl_mean, fl_max, _ = logprob_drift(probes, 'boot1', 'base1_repeat', 'base1')
    b01_mean, b01_max, _ = logprob_drift(probes, 'boot0', 'base0_repeat', 'base0')
    g.update(logprob_mean_abs=lp_mean, logprob_max_abs=lp_max, logprob_texts=lp_n, floor_boot1_mean=fl_mean,
             floor_boot1_max=fl_max, floor_boot0_mean=b01_mean)
    g['G4'] = lp_mean is not None and lp_mean <= 0.15
    ca, cb = out['correct_ast_adapter'], out['correct_ast_base1']
    g['G5'] = ca is not None and cb is not None and ca >= cb - 0.05
    g['passed'] = all(g[k] for k in ('G1', 'G2', 'G3', 'G4', 'G5'))
    out['drift_gate'] = g

    # decode speed on the idle boot-1 server
    dec = [p for p in probes if p.get('kind') == 'decode' and p.get('boot') == 'boot1' and p.get('status') == 200
           and p.get('tok_s')]
    tb_ = [p['tok_s'] for p in dec if p['label'] == 'base1']; ta_ = [p['tok_s'] for p in dec if p['label'] == 'adapter']
    out['decode'] = {'base1_tok_s': statistics.mean(tb_) if tb_ else None, 'adapter_tok_s': statistics.mean(ta_) if ta_ else None,
                     'n_base1': len(tb_), 'n_adapter': len(ta_)}
    out['decode']['drop'] = (1 - out['decode']['adapter_tok_s'] / out['decode']['base1_tok_s']) if tb_ and ta_ else None
    out['routing'] = run.get('routing')
    out['v1_models_boot1'] = (run.get('boot1') or {}).get('v1_models')
    out['reading'] = read(out, run)
    return out


def read(o: dict, run: dict) -> dict:
    """Section 4, first match wins. Returns the row and the conditions that put it there."""
    status = o.get('status')
    td = o.get('train_data') or {}
    tr = o.get('train') or {}
    boot1 = run.get('boot1') or {}
    # R0 infrastructure
    r0 = []
    if status in (None, 'started', 'infrastructure'):
        r0.append(f'run status {status} ({o.get("stopped_why")})')
    if (td.get('n_pairs') or 0) < MIN_PAIRS_TRAIN and status != 'boot1_failed':
        r0.append(f'training pairs {td.get("n_pairs")} < {MIN_PAIRS_TRAIN}')
    if status == 'complete' and o['n_paired'] < MIN_PAIRED:
        r0.append(f'paired edit prompts {o["n_paired"]} < {MIN_PAIRED}')
    if r0:
        return {'row': 'R0', 'why': r0}
    # R1 adapter not applied
    r1 = []
    if status == 'boot1_failed' or not boot1.get('started'):
        r1.append('boot 1 failed')
    else:
        if 'copy_lora' not in (o.get('v1_models_boot1') or []):
            r1.append('copy_lora not in /v1/models')
        if (o.get('adapter_non200_share') or 0) > 0.5:
            r1.append(f'adapter non-200 share {o["adapter_non200_share"]:.2f}')
        am = str((o.get('routing') or {}).get('agent_model') or '')
        if not am.endswith('copy_lora'):
            r1.append(f'routing: agent model does not name the adapter ({am or "none"})')
        if o.get('adapter_resp_models') and set(o['adapter_resp_models']) != {'copy_lora'}:
            r1.append(f'adapter responses name {sorted(map(str, o["adapter_resp_models"]))}')
    if r1:
        return {'row': 'R1', 'why': r1}
    # R2 near-zero adapter
    g = o['drift_gate']
    floor = max(2 * (g.get('floor_boot1_mean') or 0.0), 0.005)
    r2 = []
    if not tr.get('steps'):
        r2.append('0 optimizer steps')
    if not tr.get('b_norm_total'):
        r2.append('B norm 0')
    if (g.get('logprob_mean_abs') is not None and g['logprob_mean_abs'] <= floor
            and (o.get('class_disagreement') or 0) <= 0.05):
        r2.append(f'logprob drift {g["logprob_mean_abs"]:.4f} <= {floor:.4f} and class disagreement '
                  f'{o.get("class_disagreement"):.3f} <= 0.05')
    if r2:
        return {'row': 'R2', 'why': r2}
    d, p = o['delta_exact'], o['p_mcnemar']
    xplus = d is not None and d >= DELTA and p < ALPHA
    xminus = d is not None and d <= -DELTA and p < ALPHA
    drop = (o.get('decode') or {}).get('drop')
    base0_ok = (o.get('exact_adapter_on_base0_ids') is not None and o.get('exact_base0_on_paired') is not None
                and o['exact_adapter_on_base0_ids'] >= o['exact_base0_on_paired'])
    why = [f'delta {d:+.3f}, McNemar p {p:.4f}', f'drift gate {"passed" if g["passed"] else "failed"} '
           f'({", ".join(k for k in ("G1", "G2", "G3", "G4", "G5") if not g[k]) or "all pass"})',
           f'decode drop {drop if drop is None else round(drop, 3)}', f'adapter >= base0 on the same ids: {base0_ok}']
    if xplus:
        if g['passed'] and drop is not None and drop <= DECODE_DROP_MAX and base0_ok:
            return {'row': 'R3', 'why': why}
        return {'row': 'R4', 'why': why}
    if xminus:
        return {'row': 'R6', 'why': why}
    return {'row': 'R5', 'why': why}


def fmt(x):
    return round(x, 4) if isinstance(x, float) else x


def main() -> None:
    run_dir = Path(sys.argv[1])
    o = analyze(run_dir)
    keys = ['status', 'stopped_why', 'elapsed_s', 'n_paired', 'exact_base1', 'exact_adapter', 'exact_base1_ci',
            'exact_adapter_ci', 'delta_exact', 'discordant_adapter_only', 'discordant_base1_only', 'p_mcnemar',
            'n_with_base0', 'exact_base0_on_paired', 'exact_adapter_on_base0_ids', 'boot_agreement_exact_base0_base1',
            'classes_base1', 'classes_adapter', 'edit_call_rate_base1', 'edit_call_rate_adapter',
            'correct_ast_base1', 'correct_ast_adapter', 'correct_strict_base1', 'correct_strict_adapter',
            'exact_given_edit_base1', 'exact_given_edit_adapter', 'by_kind_exact_base1', 'by_kind_exact_adapter',
            'class_disagreement', 'adapter_requests', 'adapter_non200_share', 'adapter_resp_models']
    for k in keys:
        v = o.get(k)
        print(f'{k}: {json.dumps({a: fmt(b) for a, b in v.items()} if isinstance(v, dict) else fmt(v), default=str)}')
    for k in ('t1', 'drift_gate', 'decode', 'train', 'train_data', 'render_check', 'paths', 'data'):
        v = o.get(k) or {}
        print(f'{k}: {json.dumps({a: fmt(b) for a, b in v.items()}, default=str)}')
    print('READING', o['reading']['row'], '|', '; '.join(o['reading']['why']))
    if '--json' in sys.argv:
        Path(sys.argv[sys.argv.index('--json') + 1]).write_text(json.dumps(o, indent=1, default=str), encoding='utf-8')


if __name__ == '__main__':
    main()
