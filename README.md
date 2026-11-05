# Replication package: judge-gated escalation between local code models

For the paper "Does an Outcome-Blind Judge Save Compute? A Pre-Registered Study of Escalation Between Local Code
Models". This package reruns every analysis in the paper from stored data, and can regenerate draws from scratch.

All commands run on one machine. Nothing needs an account, an API key or a hosted service. Models are reached only at
`http://localhost:11434`. The study's own machines and network are not needed and are not referenced.

## Quick start

You need Python 3.11 or later. The first four commands use only the standard library.

```sh
sh repro/run.sh setup        # check all checksums, unpack the data (seconds)
sh repro/run.sh tests        # unit tests (seconds)
sh repro/run.sh confirm      # the frozen confirmatory analysis, compared with runs/T26_report.md (under 2 minutes)
sh repro/run.sh independent  # main results from separate code, exact expectations (under 2 minutes)
```

## Everything else

Times are from a 4-thread Intel i3-7100U; most machines will be faster.

| Command | What it checks | Needs | Time |
|---|---|---|---|
| `sh repro/run.sh thresholds` | Rederives the frozen thresholds from calibration data | Python | about 40 minutes |
| `sh repro/run.sh exploratory` | Reruns the follow-up analyses and compares outputs | Python | about 4 hours |
| `sh repro/run.sh fetch` | Downloads the two benchmarks, checked by sha256 | Network, once | seconds |
| `sh repro/run.sh pressure` | Post hoc robustness analyses and the back-test from the paper's section 4.3 | numpy, `fetch` | about 2 minutes |
| `sh repro/run.sh rescore 500` | Official scorer on a random sample, in a container with no network | Docker, `fetch` | about 5 minutes |
| `sh repro/run.sh repeat` | Regenerates sampled draws and labels, then compares them | Ollama, models, `fetch` | minutes |
| `sh repro/run.sh scan` | Confirms the package holds no addresses, personal paths or keys | Python | seconds |

`exploratory` requires Markdown reports to match byte for byte and JSON files to match in structure with numbers equal to
1e-9. On Python older than 3.12 the JSON files differ in their last digits, because `sum()` on floats changed in 3.12.
`exploratory --compare DIR` compares outputs you already have, without rerunning.

`pressure` covers sections 4.2 and 4.3 and compares its output with `repro/pressure/stored/`. Two scoring checks are not
rerun by it, because they execute model-written code and need extra packages: `repro/pressure/strip.py` and `mods.py`. Their
outputs are in `repro/pressure/stored/`, and `pressure` reads them. To rerun them, use containers with `--network none`.

On macOS with Python from python.org, `fetch` needs that build's "Install Certificates" command to have been run once.

Before `rescore`, build the scorer once. Its first run needs network to cache the dataset.

```sh
docker build -f Dockerfile.evalplus -t evalplus:0.3.1 .
docker run --rm -v evalplus-cache:/root/.cache/evalplus evalplus:0.3.1 python -c "from evalplus.data import get_human_eval_plus as h, get_mbpp_plus as m; h(); m()"
```

Before `repeat`, pull the models named in `ENVIRONMENT.md` and check their digests with `ollama list`. A draw made within
seconds of a model load can differ from the stored one and then match on a later run; see `VERIFICATION.md`. The script refuses
a model whose digest differs, and refuses any Ollama that is not on this machine unless you pass `--allow-remote`.

## Regenerating the whole study

`config.study.json` holds the study's settings with addresses set to `localhost`. A full rerun generates 15,718 draws. That
took about 44 hours on the generation machine in `ENVIRONMENT.md`, plus judging. We have not rerun the whole study from this
package; `repeat` checks a sample.

```sh
sh repro/run.sh fetch
export BENCH_SANDBOX="docker run --rm -i --network none --memory 512m --cpus 1 python:3.11-slim timeout 10 python -I -"
python3 bench.py run config.study.json runs/cal.jsonl --split cal
python3 bench.py run config.study.json runs/test.jsonl --split test
```

Generation with the same seeds, digests and Ollama version returned byte-identical drafts in our sample, on the same
hardware. Expect differences on other hardware or Ollama versions, and on the tev judge, whose probabilities move
slightly between runs. `tools/exprun.py` and each `ext/E*/spec.json` give the commands for the follow-up experiments.
Model-written code runs only in containers started with `--network none`.

## What is here

| Path | Contents |
|---|---|
| `PREREG.md`, `docs/PREREG.v1-draft.md` | Frozen pre-registration, and the first draft it replaced |
| `thresholds.json`, `split_manifest.json` | Frozen thresholds and task split |
| `DEVIATIONS.md` | Deviations from the pre-registration |
| `controllers.py`, `bench.py`, `judge.py`, `suites.py`, `evalplus_io.py` | Pipeline and analysis |
| `data_store/` | Compressed draws, labels and scorer results, a mains or battery flag per test draw, plus provenance |
| `runs/` | Reports from the study; `setup` unpacks the data here too |
| `ext/E*/` | Each follow-up: specification and written predictions, code, result, outputs |
| `repro/` | The scripts in this README; `repro/stored/` holds the logs behind `VERIFICATION.md` |
| `VERIFICATION.md` | What has already been checked, and the results |
| `ENVIRONMENT.md` | Hardware, software, settings and model digests |

## Provenance and integrity

`controllers.py`, `PREREG.md`, `thresholds.json` and `split_manifest.json` are byte-identical to the versions at the
freeze commit. `data_store/provenance.json` gives their sha256 and git blob IDs, so `git hash-object FILE` can be compared
directly. `data_store/commit_log.txt` lists the study's commits with their dates.

Data rows are unchanged. Only run-metadata lines were altered, to replace addresses and host names, and
`data_store/row_hashes.json` records a hash over the unchanged rows. `data_store/scrubbed_files.txt` lists the text files
whose addresses or network wording were replaced; no logic changed. The git repository itself is private because its
history records the study's network settings; it is available to the editor on request.

Commit dates are self-reported. There is no third-party registry deposit, as the paper states.

## What is not here

The hosted-API code from the first draft of the pre-registration was never used by the study and has been removed, along
with code for the follow-up experiments that were designed but not run. `ext/E1`, `E7`, `E8`, `E10` and `E11` keep their
specifications only. `VERIFICATION.md` lists exactly what was removed and how the result was checked.
