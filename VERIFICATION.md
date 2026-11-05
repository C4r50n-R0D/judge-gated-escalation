# What has been checked

All checks below were run by the study's own author and tools. **No independent party has reproduced this work yet.** Logs
are in `repro/stored/`.

## Clean-room rerun
Fresh Docker container from `Dockerfile.evalplus`, Python 3.11.17 (the study used 3.13.5), `--network none`, using only
this package.

| Check | Result |
|---|---|
| File checksums | all match |
| Unit tests | 0 failures |
| Frozen confirmatory analysis | report identical to `runs/T26_report.md` |
| Thresholds rederived from calibration data | identical to `thresholds.json` for all three judges |
| Independent recomputation, separate code | identical to the stored output |
| Exploratory analyses E2 to E14b, 18 outputs | 9 reports byte-identical; 9 JSON files equal to 1e-9 |
| Post hoc analyses (`pressure.py`, `pressure2.py`) | output byte-identical |

The 9 JSON files differ from the stored ones by at most 1.3e-11, in values up to the thousands. The cause is `sum()` on
floats, which changed in Python 3.12. Rerunning E4 and E5 on Python 3.13.5 gave byte-identical JSON.

The package was rebuilt after this run. Only `repro/exploratory.py`, `repro/run.sh` and `repro/scan_identifiers.py` changed,
and files were added or removed as `CHECKSUMS.sha256` shows; all data, analysis code and reference outputs have the same
sha256 as in the run above. Setup, tests, confirm, independent and all four `pressure` scripts were then rerun on the final
package, with the same results.

## Scoring
`repro/run.sh rescore 500`, run from the package with a fresh scorer cache: 500 of 500 random stored draws matched on both
the visible and the hidden verdict.

## Repeatability of generation and judging
`repro/stored/repeat_check.json`. Same machine, Ollama version, seeds and model digests. Run from this package's code,
at `localhost`.

| Item | Result |
|---|---|
| Draws | 21 of 21 byte-identical (3B 12, 1.5B 6, 14B 3) |
| llama judge | 8 of 8 exact |
| tev judge | 8 of 8 same verdict; largest probability difference 0.007069 |

## Integrity
- `controllers.py`, `PREREG.md`, `thresholds.json` and `split_manifest.json` are byte-identical to the freeze commit
  (`data_store/provenance.json`).
- `split_manifest.json` was recomputed from the benchmarks and matches.
- `repro/scan_identifiers.py` found no network addresses, personal paths, email addresses or keys, in text files or in
  compressed data rows. As a positive control, planted strings in a data row, a stored JSON file, a script and model-written
  code were all caught.

## Clean-up after the clean-room run
Code the study never used was then removed. The study repository keeps the original code.

Removed:
- Hosted-API paths: `gen_anthropic`, the `Jev` class, the spend cap and ledger in `bench.py` and `judge_label.py`.
- The sampled-vote judge `YesNoLLM` and `parse_vote`, which no reported judge used.
- The task-variant framework for experiments designed but not run: `variants/__main__.py`, `variants/transforms.py`,
  `variants/quality.py`, the framework in `variants/__init__.py`, `ext/variants/`, `ext/E11/prompts.py`,
  `tools/variant_selfcheck.sh`, and the `variant:` branches in `suites.py` and `evalplus_io.py`.
- `style_bias.py`, an analysis that was not run, and `tools/stage_status.py` and `tools/t13_timing.py`, which only monitored
  collection.
- The matching tests and mock-server endpoints, and unused imports in scripts outside the analyses below.

Kept on purpose: `controllers.py`, `judgestats.py`, `jsonl.py`, and every script that computed a reported number are
byte-identical to the clean-room run. That leaves one unused variable in `judgestats.py`, unused imports in
`ext/E3/analyze.py`, `ext/E14/e14.py` and `ext/E14b/e14b.py`, and one lint finding in the frozen `controllers.py`.
`variants/codemods.py` stays because it produced the E4 to E6 data. `config.study.json` keeps its original keys as a record.

Rerun on the final package: checksums, unit tests, the mock pipeline, the frozen report, the independent recomputation, all four
`pressure` scripts, `rescore 500` and the identifier scan, all with the same results as above. Thresholds and the exploratory
analyses were not rerun, because no file they use changed.

`gen_ollama`, `tier_run`, `extract_code`, `http_json` and `load_config` have identical syntax trees before and after. Using
the final code, the original sample again gave 21 of 21 byte-identical draws and 16 of 16 labels with the same verdict, with
the same largest difference, 0.007069 (`repro/stored/repeat_check.json`).

A second sample gave 6 of 7 identical (`repro/stored/repeat_check_second_sample.json`). The exception, Mbpp/632 rep 4,
happens within seconds of a model load. It differed in 6 of 6 trials right after unloading the model, for the code before
and after the clean-up alike, and matched the stored draw in every trial once the model had run longer, whichever prompt came
before it. We did not establish the mechanism. Repeatability therefore holds for a warmed model, and a single warm-up draw
does not always guarantee it.

## Back-test
`repro/pressure/backtest.py`, written without the pipeline's code, rebuilds the main results from raw rows and then cuts them
in ways the analysis did not (`repro/pressure/stored/backtest.out`).

| Cut | tev gate against strong-only | Visible gate against strong-only |
|---|---|---|
| All 371 test tasks | -0.4 points, +119, fails on cost | +1.4 points, -1,932, passes |
| Disjoint draws, half 1 | +0.5, +83, fails on cost | +1.5, -1,988, passes |
| Disjoint draws, half 2 | -1.1, +156, fails on cost | +1.2, -1,878, passes |
| No battery draws (319 tasks) | -0.6, +173, fails on cost | +1.0, -1,846, passes |
| No draws with over 0.1 s of model load | -0.5, +120, fails on cost | +1.3, -1,931, passes |
| Calibration split at frozen thresholds | +0.8, -201 [-466, +53], fails on cost | +3.8, -2,118, passes |

Two results go against a simple reading. tev's calibration estimate was a saving that did not carry over to test. Across
quartiles of collection order, about 93 tasks each, the visible gate failed the accuracy bound in two of four, so the pooled
pass should not be read as a pass on every small subset. A random gate at tev's accept rate lost 6.4 points.

## Timing sensitivity in scoring
Scoring has a time limit, so a stalled machine can turn a pass into a timeout.
- One rerun of `rescore 500` gave 499 of 500: Mbpp/116, 7B draft 1, a one-line function, was recorded as a timeout while the
  evaluator reported a stall. A fresh rerun gave 500 of 500. The stored verdict was correct.
- `evalplus.evaluate` silently reuses an existing results file, so repeating `rescore` used to report the old result. `run.sh`
  now deletes those files first.
- 13 of the 16,000 stored evaluations recorded a timeout (12 distinct drafts, 22 draws). Rescoring them three times changed one
  verdict: a Mbpp/255 draft stored as failed passed all three times. The pre-registration already notes that this task's
  reference runs close to its time limit. Correcting its three draws (14B reps 0 and 1, 7B rep 5) moves 14B accuracy from 0.752 to
  0.753 and tev from -0.4 to -0.5 points, and changes no verdict. Another Mbpp/255 draft varied between fail and timeout, so
  this task stays noisy. Stored data are unchanged.

## Claim and source audit
- Every number in the paper's body and appendices appears in a stored source file (786 of 786). That test alone is weak, so
  each exploratory section was also read against its `RESULT.md`, Table 7 was compared cell by cell with `results.json`
  (48 of 48), and the deviation counts were recomputed from the draws (96, 1 and 739 battery draws, 836 in all).
- Power, the break-even rejection rate and the comparison register (42) were recomputed by hand.
- All 23 arXiv references resolve, with title and author lists matching the arXiv record. Each attributed claim was checked
  against the source text, not only its abstract. The Tev1 page, the EvalPlus venue and all nine model digests were also checked.
- Corrected in the paper as a result: the Chen comparison had called different model builds "the same pair" and treated
  controllers that choose between two actions as if they were escalation gates; the test-execution sentence mixed a confidence
  bound with a point estimate; the TRIAGE result is now marked post hoc; "differs in" became "combining", since other cited
  work also pre-registers; a missing reference (Bouchard) was added, including a finding that runs against the three-tier
  cascade.
- `ext/E6/RESULT.md` words attack success loosely. As `ext/E6/analyze.py` computes it, the denominator is wrong drafts rejected
  clean, which is what the paper states.

## Not checked
- The whole study has not been regenerated from this package. Repeatability rests on the sample above.
- Generation has not been repeated on other hardware or other Ollama versions. Expect differences there.
- `repeat` has run only on the original generation machine.
- The author's first name appears in the frozen `PREREG.md`, in `DEVIATIONS.md` and in code comments, and `LICENSE` names
  the author. This package is not anonymous, and it cannot be made so without changing frozen files.
- Commit dates are self-reported. There is no third-party registry deposit.
