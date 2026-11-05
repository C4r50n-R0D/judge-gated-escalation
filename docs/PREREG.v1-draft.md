# Pre-registration: judge-gated escalation from a local model to a hosted model

Version: v1-draft, written 2026-10-09, revised the same day after an independent code and methods review. **Status: draft.** It is frozen when committed to git, and optionally deposited on OSF, at Gate 1, before any main-collection draw. The commit hash goes in the paper. Every later change is logged in `DEVIATIONS.md` with its date and reason, and the paper reports all deviations.

Fields marked **[set at Gate 1]** are fixed using calibration-split pilot data only. They must be filled in before the freeze.

## 1. Question

A local model running on a consumer machine writes a draft solution, and an outcome-blind judge scores it without running anything. Can that judge decide when to accept the draft and when to escalate to a hosted model, keeping accuracy close to always using the hosted model while spending less? And after the judge rejects a draft, is it better to retry the local model or to escalate? This extends Chen (2026), who found that no outcome-blind controller beat fixed escalation on MBPP+ with Qwen 7B and 14B.

## 2. Data

- **Main suites:** HumanEval+ v0.1.10 (164 problems) and MBPP+ v0.2.0 (378 problems), with the pinned release files fetched by `suites.py`, for 542 problems in total.
- **Split:** each task id is assigned by salted SHA-256 (`SALT = "tiered-llm-bench/prereg-v1"`, `CAL_FRACTION = 0.28`). That gives about 150 calibration tasks and about 390 test tasks. The split manifest (`suites.py manifest`) and its hash are committed at the freeze.
- **Contamination check (exploratory):** the self-authored tasks in `tasks.py`, which number 10 now and are planned to reach at least 40, are scored locally. Both main suites are public and likely in the training data of every model used, so the paper treats them as a likely contamination risk. The contamination check only shows whether the conclusions change on unseen tasks.
- **Pilot:** at most 20 tasks, drawn from the calibration split only (`bench.py run --pilot 20`). Pilot data is used only for the Gate 1 decisions.
- **Blinding:** main collection generates, scores and judges all tasks in one pass, so that every draw comes from the same model versions. Test-split outcomes stay blind until `thresholds.json` is committed. No command prints, summarizes or analyzes them before then:
  - bench.py prints `blind` for test rows;
  - test-split EvalPlus scoring discards the evaluator's console summary;
  - `controllers.py explore`, `power.py` and `style_bias.py` read calibration rows only.

## 3. Models and generation

| Role | Model | Where | Draws per task | Temperature |
|---|---|---|---|---|
| Local (primary) | qwen2.5-coder:7b (record the exact Ollama digest) | MacBook Air M3 16 GB | 5 | 0.8 |
| Strong | claude-sonnet-5-5 (record the returned model string) | Anthropic API | 3 | 0.8 |
| Local (secondary, exploratory) | qwen2.5:3b-instruct | Debian homelab | 5, on a fixed 30% hash subset | 0.8 |

- **Prompts:** fixed, from `bench.py` (SYSTEM) and `suites.py` (PROMPT_WRAP), with `num_predict` set to 768. The generator sees the standard problem prompt. For MBPP+, that prompt includes its one example assert.
- **Seeds:** seed = base seed + rep.
- **Temperature:** one temperature for all local draws, so draws 2 to k are real resamples.
- **Resuming:** a run may resume into an existing output file only under identical generation settings: models, temperatures, seeds, draws, prompts and split. `bench.py` enforces this.

## 4. Scoring

- **EvalPlus suites:** scored by the official `evalplus.evaluate` (evalplus 0.3.1), run inside a container.
  - **visible:** the EvalPlus base tests (the original HumanEval or MBPP tests) pass.
  - **hidden:** both the base and plus tests pass. This is standard HumanEval+/MBPP+ correctness and is the outcome for every hypothesis.
  - **solution scored:** the problem's context prefix, meaning the imports and helper functions that come before the entry point in the prompt, followed by the model's code. A model is never failed for leaving out a helper the task already supplied.
- **Own suite:** hidden means the visible tests and the extra tests both pass, matching the EvalPlus definition.
  - **Isolation:** tests run in a network-less container (`BENCH_SANDBOX`).
  - **Pass check:** a run passes only on exit code 0 plus a random per-run sentinel, so early exits and printed markers cannot fake a pass.

## 5. Judges

A judge sees only the task text and the candidate code. The task text is the problem prompt with any `assert` lines removed, because MBPP+ prompts embed one base test. The judge never sees tests, test output, other drafts, or the strong model's answer.

- **Empty code:** gets probability 0 without calling the judge.
- **Vote parsing:** YES/NO votes are parsed tolerantly (case, punctuation, markdown), and unparseable votes count as NO and are reported.
- **Caching:** labels are cached per judge configuration, so changing votes, model or prompt never reuses old labels.

| Judge | Backend | Probability |
|---|---|---|
| jev | TypeSafe Jev via OpenRouter (`typesafe/jev-1.13`; record the dated snapshot it returns) | Jev's `noul` probability |
| haiku | claude-haiku-5-5, asked YES/NO | share of YES in 5 votes at temperature 0.7 |
| local | qwen2.5:7b-instruct, a different model from the generator, asked YES/NO | share of YES in 3 votes at temperature 0.7 [votes set at Gate 1 from measured speed] |

**Primary judge [set at Gate 1]:** Jev if it passes Gate 1 (access works, the response parses, and cost per label is at most 5 times Haiku's), otherwise haiku. All local drafts are judged by every judge.

## 6. Controllers (`controllers.py`)

At the decision point, the local model writes a draft, and a gate either accepts it or rejects it.

- **Gates:**
  - `judge:J`: accept if J's probability is at least tau_J.
  - `visible`: accept if the visible tests pass. This is the practical baseline when tests exist.
  - `oracle`: accept if the hidden tests pass. This is an upper bound only.
- **Controllers:**
  - `local-only`
  - `strong-only`
  - `gate->reroute`: after a rejection, take one strong draw. This is Chen's fixed reroute.
  - `gate->resample(k=3)`: take up to 3 local drafts and accept the first that passes. If none passes, keep the best-scored draft.
  - `gate->resample(3)->reroute`: as above, but escalate if none passes. This one is exploratory.
- **Simulation:** each task's expected accuracy, USD and seconds come from 200 Monte Carlo replicates over its stored draws. Local drafts are drawn without replacement and strong draws with replacement.
- **Unjudged drafts:** a draft the judge did not label, because of a judge error or the spend cap, counts as a rejection, which is what a deployed system would do. It is not dropped, because dropping mostly-wrong drafts would flatter the judge. Counts are reported per judge.
- **Costs and timing:**
  - Judge cost and latency are charged for every draft the judge scores.
  - Local generation costs $0.
  - Visible-test execution is charged as 0 seconds.
- **Cost metric:** USD covers API spend only. Latency is reported next to it (H5), so a cheaper-but-slower result is visible.

## 7. Threshold rule (calibration split only)

For each judge, every distinct probability value is a candidate tau. Infinity is also a candidate, meaning always reroute.

- **Feasible:** a tau is feasible if the 2.5th percentile of a task-cluster bootstrap (1,000 resamples) of the calibration accuracy difference, gate->reroute minus strong-only, is at least -delta/2.
- **Choice:** the cheapest feasible tau. If none is feasible, the most accurate tau.

Requiring a bootstrap lower bound, not a point estimate, guards against the optimism of choosing the best of many thresholds on about 150 tasks. The independent reviewer's simulation (synthetic data, 20 replications) found:

| Threshold rule | H2 passed |
|---|---|
| point estimate at -delta/2 (first draft) | 10 of 20 |
| calibration parity | 15 of 20 |
| this lower-bound rule | 20 of 20 |

These numbers come from one synthetic world and do not predict real results.

`controllers.py calibrate` writes `thresholds.json`. It needs `--primary-judge` and `--manifest`, and records:
- tau for each judge;
- the primary judge;
- delta, k, Monte Carlo replicates, seed, and the hard-task cut-off;
- a hash of the calibration data;
- calibration coverage.

That file is committed before `controllers.py test` runs. `test` takes every setting from the file and refuses to run if any command-line value differs or if the calibration data has changed since the freeze.

## 8. Hypotheses and decision rules (test split)

Confidence intervals come from a cluster bootstrap over tasks (2,000 resamples, paired across controllers).

- **H1 (discrimination):** for each judge, the AUROC of its probability against hidden correctness of local drafts is above 0.5. Supported if the lower 95% bound is above 0.5. Confirmatory for the primary judge only. A within-task AUROC, which compares only correct and wrong drafts of the same task, is also reported because pooled AUROC can reward recognizing easy tasks.
- **H2 (primary; savings at near-equal accuracy):** for the primary judge, gate->reroute against strong-only has two parts:
  - **Non-inferiority:** the lower 95% bound of the accuracy difference is above -delta, with delta = 0.03 [revisable once at Gate 1, see section 9].
  - **Savings:** the upper 95% bound of the USD difference is below 0.

  Both parts are required. The same comparison is reported for the other judges, the visible gate and the oracle, as secondary results.
- **H3 (Chen replication):** at the frozen tau, gate->reroute accuracy minus gate->resample(3) accuracy has a lower 95% bound above 0. Also reported is whether the hybrid's gain over reroute has an upper bound below delta.
- **H4 (stopping debt):** a task is "hard" if the local model's hidden pass rate across its draws is at most 1/3. The judge's false-accept rate among wrong drafts is higher on hard tasks than on other tasks, judged by the lower 95% bound of the difference. Also reported is how often the strong model would have been right on wrongly accepted tasks.
- **H5 (latency, descriptive):** seconds per task for every controller, with CIs.

The only confirmatory test is H2 with the primary judge. Everything else is labeled secondary or exploratory, without multiplicity correction.

## 9. Power rule (Gate 1, calibration pilot only)

`power.py pilot` uses calibration pilot rows only. It picks tau with the section 7 rule, then measures the across-task standard deviation (sd) of the per-task accuracy difference, gate->reroute minus strong-only. The mean is deliberately not shown. With SE = sd / sqrt(number of test tasks):

- delta = max(0.03, the smallest multiple of 0.01 that is at least 2.8 x SE). That gives 80% power for the one-sided non-inferiority test if the true difference is 0.
- If that delta exceeds 0.05, H2 is reported as an estimate with its CI, not as a hypothesis test.
- Power when the true difference is -delta/2 is lower. It is also printed and reported in the paper.

This decision is recorded in this file before the freeze and is never revisited after any test-split data exists.

### Other Gate 1 rules (calibration pilot only)
- **Ceiling or floor:**
  - If the primary local model passes hidden tests on more than 90% of pilot drafts, there are too few wrong drafts. Replace it with a weaker local model, named here before the freeze.
  - If it passes on under 15%, the gate has nothing to accept, and the same replacement rule applies in the other direction.
- **Budget:**
  - If measured cost or time is more than twice the estimate, cut local draws from 5 to 4 and drop the 3B arm.
  - The primary analysis is never cut.
- **Local judge:** votes are set from measured speed, at most 5 and at least 1, and recorded in section 5.

## 10. Exclusions and missing data

- **Generation errors:** retried by resuming, at most 3 attempts per draw. A draw still failing after that is excluded and counted.
- **Missing tiers:** a task without at least one usable draw from both the local and strong tiers is excluded and counted. Gate 2 fails if more than 5% of planned rows are missing.
- **Judge errors:** retried. Drafts still unjudged count as rejections (section 6), and the count is reported.
- **Coverage:** `calibrate` and `test` compare usable tasks with the committed split manifest and refuse to run if more than 5% of a split's tasks are missing. Error rows and unscored rows are counted in the report.
- **Spend:** generation and judge spend are capped through a global ledger shared by all runs.
- **EvalPlus placeholders:** placeholders for problems not covered in a run are ignored.

## 11. Sensitivity and exploratory analyses (reported, not confirmatory)

- A two-stage bootstrap that resamples tasks and draws within tasks, for the primary H2 comparison.
- The contamination-check suite.
- The 3B local tier.
- H2 and H3 with each non-primary judge and the visible gate.
- Judge style bias: on hidden-correct solutions only, compare judge probabilities for drafts written by the 7B, the 3B and Claude. This needs those drafts judged; Claude drafts are judged by haiku and local only, to limit spend.

## 12. What would change the conclusions (stated in advance)

- **Visible gate beats every judge:** the paper says that tests should gate escalation when tests exist, and that judges matter only where tests do not.
- **Primary judge AUROC CI includes 0.5:** H2 and H3 for that judge are reported but not interpreted as evidence about judging.
- **Strong model version changes mid-collection:** the affected rows are re-collected, or the analysis is split by version.
