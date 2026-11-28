# P-001: what the models know about the installed public libraries (probe, no task data)

2026-11-28. Tool: `tools/lora/lib_probe.py`. Source of truth: the public libraries' own source in the task
environments, parsed with `ast` (one environment per repository family, 5 in all). No task text is read.

- **EXIST:** which of four names is defined in a given module (the three wrong ones are real names from other
  libraries). **PARAM:** which of four names is a parameter of a given function. Chance is 0.25. The answer is the
  highest next-token logit over the four letters, without thinking.

## E4B (job 68330, 3 min)

- **All libraries (50): EXIST 0.71 (n=1,363), PARAM 0.65 (n=827).**
- Web and data libraries the public tasks lean on: `starlette` 0.77 / 0.82, `pydantic` 0.83 / 0.62, `rich` 0.80 / 0.53,
  `click` 0.67 / 0.82, `typer` 0.70 / 0.59, `jinja2` 0.77 / 0.61, `sqlalchemy` 0.80 / 0.68, `uvicorn` 0.90 / 0.67,
  `anyio` 0.67 / 0.43, `yaml` 0.90 / 0.48.
- Lowest: `annotated_types` 0.26 (EXIST), `inline_snapshot` 0.31 / 0.55, `httpbin` 0.33 / 0.45, `jsonschema`
  0.52 / 0.53, `referencing` 0.53 / 0.33, `mistune` 0.60 / 0.38.
- Highest: `jwt` 0.90 / 0.93, `cryptography` 0.93 / 0.85, `itsdangerous` 0.82 / 0.86.

**Reading.** The E4B knows the common libraries well above chance but far from reliably: with three wrong options
shown, it picks a wrong parameter about one time in three, and for several widely used libraries (`rich`, `yaml`,
`anyio`, `typer`) about one time in two. Free recall inside a patch has no options to choose from and is harder.
Module-level names are known better than parameters.

## 31B

Job 68331 (3 GPUs) is held behind the evaluation queue; result appended here.
