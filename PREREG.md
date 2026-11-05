# Pre-registration: judge-gated escalation from a small local model to a larger local model

Version: v2-proposed, written 2026-10-23 from v1-draft (2026-10-09), after the 20-task Gate 1 pilot and the switch to local-only models. **Status: proposal, not frozen.** It is frozen when Carson commits it to git together with `split_manifest.json` and `thresholds.json`, and optionally deposits it on OSF, before any test-split draw. The commit hash goes in the paper. Every later change is logged in `DEVIATIONS.md` with its date and reason, and the paper reports all deviations.

Fields marked **[set at Gate 1 v2]** are fixed from the Stage 1 calibration data only (section 2). They must be filled in before the freeze.

## 1. Question

A local model running on a consumer machine writes a draft solution, and an outcome-blind judge scores it without running anything. Can that judge decide when to accept the draft and when to escalate to a larger model on the same machine, keeping accuracy close to always using the larger model while using less compute? And after the judge rejects a draft, is it better to retry the local model or to escalate? Every model runs locally: no prompt or code leaves the owner's machines, and cost is measured in compute and time, not dollars. This extends Chen (2026), who found that no outcome-blind controller beat fixed escalation on MBPP+ with Qwen 7B and 14B.

## 2. Data

- **Main suites:** HumanEval+ v0.1.10 (164 problems) and MBPP+ v0.2.0 (378 problems), with the pinned release files fetched by `suites.py`, for 542 problems in total.
- **Split:** each task id is assigned by salted SHA-256 (`SALT = "tiered-llm-bench/prereg-v1"`, `CAL_FRACTION = 0.28`). The committed manifest gives 171 calibration tasks and 371 test tasks. The split manifest (`suites.py manifest`) and its hash are committed at the freeze.
- **Contamination check (exploratory):** the self-authored tasks in `tasks.py`, which number 10 now and are planned to reach at least 40, are scored locally. Both main suites are public and likely in the training data of every model used, so the paper treats them as a likely contamination risk. The contamination check only shows whether the conclusions change on unseen tasks.
- **Two-stage collection:**
  - **Stage 1 (before the freeze):** generate, score and judge the calibration split only, for every tier. Gate 1 v2 decisions and thresholds come from these rows.
  - **Stage 2 (after the freeze):** generate, score and judge the test split, blind, with identical settings. All models are pinned local builds (digests in section 3), so splitting collection in two cannot mix model versions. Any digest or Ollama version change between stages is a deviation.
  - The 20-task pilot of 2026-10-23 used different draw counts and ordering. Its rows informed only the design and are not reused.
- **Blinding:** test-split outcomes stay blind until `thresholds.json` is committed and `controllers.py test` runs. No command prints, summarizes or analyzes them before then:
  - bench.py prints `blind` for test rows;
  - test-split EvalPlus scoring discards the evaluator's console summary;
  - `controllers.py explore`, `power.py` and `style_bias.py` read calibration rows only.

## 3. Models and generation

| Role | Model | Where | Draws per task | Tasks | Temperature |
|---|---|---|---|---|---|
| Local (primary) | qwen2.5-coder:3b (digest f72c60cabf62) | MacBook Air M3 16 GB, Ollama 0.40.8 | 8 | all | 0.8 |
| Strong | qwen2.5-coder:14b (digest 9ec8897f747e) | same Mac | 5 | all | 0.8 |
| Local (secondary) | qwen2.5-coder:7b (digest dae161e27b0e) | same Mac | 8 | all | 0.8 |
| Local (secondary, wide gap) | qwen2.5-coder:1.5b (digest d7372fd82851) | same Mac | 8 | all | 0.8 |

All four generators are Qwen2.5-Coder Instruct builds, so model size is the only planned difference between tiers. The 7B->14B pair reproduces Chen; the 1.5B->14B pair covers a wide-gap regime. The Debian homelab orchestrates and scores; it generates nothing.

- **Prompts:** fixed, from `bench.py` (SYSTEM) and `suites.py` (PROMPT_WRAP), with `num_predict` set to 768. The generator sees the standard problem prompt. For MBPP+, that prompt includes its one example assert.
- **Seeds:** seed = base seed + rep.
- **Temperature:** one temperature for all draws, so draws 2 to k are real resamples.
- **Log-probabilities:** every draft records its mean and minimum token log-probability (Ollama `logprobs`), for the selfconf baseline in section 5.
- **Collection order:** tasks in a fixed random order (seeded), processed in blocks of about 20 tasks; within each block every tier runs in turn (chunked round-robin). This spreads heat and power state across tiers without a model swap on every task.
- **Ollama settings (fixed after T13, 2026-10-23):** Ollama 0.40.8 on the Mac, `OLLAMA_KEEP_ALIVE=30m`, `OLLAMA_MAX_LOADED_MODELS=1`, `OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_KV_CACHE_TYPE=q8_0`, fixed for the whole study.
- **Cooldown guard:** a tier pauses (240 s, re-probing, up to 30 min) when the median decode speed of its last 10 drafts falls below 0.7 x its cool reference speed (1.5B 70, 3B 38, 7B 11.5, 14B 8.0 tok/s). Pauses are logged and excluded from seconds.
- **Hardware log:** every batch records power source (mains or battery) and the macOS thermal and performance warning state. Collection runs on mains power only.
- **Resuming:** a run may resume into an existing output file only under identical generation settings: models, temperatures, seeds, draws, prompts and split. `bench.py` enforces this.

## 4. Scoring

- **EvalPlus suites:** scored by the official `evalplus.evaluate` (evalplus 0.3.1), run inside a container with no network, a 6 GB memory limit, `EVALPLUS_MAX_MEMORY_BYTES=8589934592` and `--parallel 1` (the settings that passed the T3 selfcheck). Scoring never runs while generation is running.
  - **visible:** the EvalPlus base tests (the original HumanEval or MBPP tests) pass.
  - **hidden:** both the base and plus tests pass. This is standard HumanEval+/MBPP+ correctness and is the outcome for every hypothesis.
  - **solution scored:** the problem's context prefix, meaning the imports and helper functions that come before the entry point in the prompt, followed by the model's code. A model is never failed for leaving out a helper the task already supplied.
  - **Known always-fail tasks:** HumanEval/32 (an EvalPlus find_zero bug) and Mbpp/255 (its reference runs close to its time limit) fail even for the canonical solution. They stay in the data, and the paper notes them.
- **Own suite:** hidden means the visible tests and the extra tests both pass, matching the EvalPlus definition.
  - **Isolation:** tests run in a network-less container (`BENCH_SANDBOX`).
  - **Pass check:** a run passes only on exit code 0 plus a random per-run sentinel, so early exits and printed markers cannot fake a pass.

## 5. Judges

A judge sees only the task text and the candidate code. The task text is the problem prompt with any `assert` lines removed, because MBPP+ prompts embed one base test. The judge never sees tests, test output, other drafts, or the strong model's answer.

- **Empty code:** gets probability 0 without calling the judge.
- **YES/NO parsing:** P(YES) sums the first-token probabilities of every spelling of YES and of NO (case, punctuation, markdown) among the top 20 tokens, then renormalises over YES+NO. If neither appears, the label counts as NO and is reported as unparseable.
- **Caching:** labels are cached per judge configuration, so changing model or prompt never reuses old labels.
- **Coverage:** every tier's drafts (1.5B, 3B, 7B, 14B) are judged by tev and llama; selfconf applies to every tier.

| Judge | Backend | Probability |
|---|---|---|
| tev | Together AI's Tev1 4B (digest 4d24c6f6d61a), served by Ollama's `/v1/systemone` | Tev1's `noul` probability |
| llama | llama3.1:8b (digest 46e0c10c039e), a different model family from every generator, asked YES/NO once at temperature 0 | P(YES) from first-token log-probabilities |
| selfconf | the generator's own confidence, no judge call | exp(mean token log-probability of the draft) |

Verified facts (2026-10-23): the Ollama model page states that Tev1 is "a family of experimental decision models from Together AI, fine-tuned from Qwen3.5", served at `/v1/systemone`, which "follows TypeSafe's Jev API", and needs Ollama 0.35 or later. `ollama show tev1:4b` reports architecture qwen35 and an Apache-2.0 license; the page itself states no weight license (only that the dataset builders and training scripts are MIT). Live calls on 2026-10-22 returned `answers.is_correct.noul` and token usage without a cost field. Tev1 therefore shares a family lineage with the Qwen generators; llama does not.

selfconf is a baseline: a judge that cannot beat the generator's own confidence is not earning its time.

**Primary judge (set at Gate 1 v2, 2026-10-24):** tev. Rule: tev or llama, whichever has the higher AUROC on the Stage 1 calibration drafts of the primary local model (tev 0.793 [0.739, 0.843], llama 0.673 [0.619, 0.725], 171 tasks, 1,368 drafts); selfconf is never primary.

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
- **Simulation:** each task's expected accuracy, cost and seconds come from 200 Monte Carlo replicates over its stored draws. Local drafts are drawn without replacement and strong draws with replacement.
- **Unjudged drafts:** a draft the judge did not label, because of a judge error, counts as a rejection, which is what a deployed system would do. It is not dropped, because dropping mostly-wrong drafts would flatter the judge. Counts are reported per judge.
- **Costs:**
  - **Primary cost: token-compute.** Model parameters (billions) x (prompt tokens + generated tokens), summed over every generator and judge call (parameter counts from `ollama show`: 1.5, 3.1, 7.6 and 14.8 for the generators, 4.2 for tev, 8.0 for llama; selfconf adds nothing). It does not depend on hardware, heat or power state. It decides the cheapest tau (section 7) and H2's savings test, and is frozen in `thresholds.json`. Chosen at Gate 1 v2 (Carson, 2026-10-24) because Stage 1 showed wall seconds varying with heat and power state on the fanless Mac (section 9).
  - **Secondary cost: seconds per task.** Wall time measured by the orchestrator for generation and judge calls, net of any model load Ollama reports; raw wall time is kept too. Reported for every controller (H5) and frozen in `thresholds.json` as the secondary metric.
  - Every tier is local, so USD is $0 throughout and is reported only for completeness.
  - Visible-test execution is charged as 0 seconds and 0 token-compute.
  - selfconf adds no time or compute: its log-probabilities come with generation.

## 7. Threshold rule (calibration split only)

For each judge, every distinct probability value is a candidate tau. Infinity is also a candidate, meaning always reroute.

- **Feasible:** a tau is feasible if the 2.5th percentile of a task-cluster bootstrap (1,000 resamples) of the calibration accuracy difference, gate->reroute minus strong-only, is at least -delta/2.
- **Choice:** the cheapest feasible tau, by the primary cost (token-compute). If none is feasible, the most accurate tau.

Requiring a bootstrap lower bound, not a point estimate, guards against the optimism of choosing the best of many thresholds on about 170 tasks. The independent reviewer's simulation (synthetic data, 20 replications) found:

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
- the primary and secondary cost metrics;
- a hash of the calibration data;
- calibration coverage.

That file is committed before `controllers.py test` runs. `test` takes every setting from the file and refuses to run if any command-line value differs or if the calibration data has changed since the freeze.

## 8. Hypotheses and decision rules (test split)

Confidence intervals come from a cluster bootstrap over tasks (2,000 resamples, paired across controllers). Hypotheses use the primary local model (3B) and the strong model (14B).

- **H1 (discrimination):** for each judge, the AUROC of its probability against hidden correctness of local drafts is above 0.5. Supported if the lower 95% bound is above 0.5. Confirmatory for the primary judge only. A within-task AUROC, which compares only correct and wrong drafts of the same task, is also reported because pooled AUROC can reward recognizing easy tasks.
- **H2 (primary; savings at near-equal accuracy):** for the primary judge, gate->reroute against strong-only has two parts:
  - **Non-inferiority:** the lower 95% bound of the accuracy difference is above -delta, with delta = 0.03 (set at Gate 1 v2, 2026-10-24: Stage 1 per-task sd 0.169, SE 0.0088 for 371 test tasks; power 0.93 if the true difference is 0, 0.40 if it is -delta/2).
  - **Savings:** the upper 95% bound of the token-compute-per-task difference is below 0. The seconds difference is reported next to it.

  Both parts are required. The same comparison is reported for the other judges, the visible gate and the oracle, as secondary results.
- **H3 (Chen replication):** at the frozen tau, gate->reroute accuracy minus gate->resample(3) accuracy has a lower 95% bound above 0. Also reported is whether the hybrid's gain over reroute has an upper bound below delta.
- **H4 (stopping debt):** a task is "hard" if the local model's hidden pass rate across its draws is at most 1/3. The judge's false-accept rate among wrong drafts is higher on hard tasks than on other tasks, judged by the lower 95% bound of the difference. Also reported is how often the strong model would have been right on wrongly accepted tasks.
- **H5 (latency, descriptive):** seconds per task for every controller, with CIs. Timings come from one fanless laptop; run order, power source, thermal state and timestamps are recorded, and seconds are also reported split by power source (mains or battery) as a sensitivity analysis.

The only confirmatory test is H2 with the primary judge. Everything else is labeled secondary or exploratory, without multiplicity correction.

### Pre-registered secondary comparisons
- **S1 (what the judge adds):** for the primary judge, gate->reroute minus local-only, in accuracy (with CI), token-compute and seconds. H2 is always reported together with S1.
- **S2 (judges vs the free baseline):** for each judge, the paired AUROC difference judge minus selfconf (task-cluster bootstrap CI), and the accuracy and token-compute of judge:J->reroute minus selfconf->reroute at their frozen taus.

### Interpretation of a small tier gap
The 20-task pilot showed a 3B-to-14B gap of about 5 points, with a standard error near 4.5 points. If the test-split gap is small, H2 can be met by a threshold that rarely escalates, because the 3B alone is nearly as accurate as the 14B. The paper therefore reads H2 only alongside S1: savings at near-equal accuracy count as evidence about judging only if gate->reroute also beats local-only. The observed gap and its CI are reported for every local tier (1.5B, 3B, 7B), and the 1.5B arm shows how the controllers behave when the gap is wide.

## 9. Gate 1 v2 rules (Stage 1 calibration data only)

### Power rule
`power.py pilot` runs on the Stage 1 calibration rows. It picks tau with the section 7 rule, then measures the across-task standard deviation (sd) of the per-task accuracy difference, gate->reroute minus strong-only. The mean is deliberately not shown. With SE = sd / sqrt(371 test tasks):

- delta = max(0.03, the smallest multiple of 0.01 that is at least 2.8 x SE). That gives 80% power for the one-sided non-inferiority test if the true difference is 0.
- If that delta exceeds 0.05, H2 is reported as an estimate with its CI, not as a hypothesis test.
- Power when the true difference is -delta/2 is lower. It is also printed and reported in the paper.

This decision is recorded in this file before the freeze and is never revisited after any test-split data exists.

### Other Gate 1 v2 rules
- **Ceiling or floor:**
  - If the primary local model passes hidden tests on more than 90% of its Stage 1 drafts, there are too few wrong drafts: the primary becomes qwen2.5-coder:1.5b.
  - If it passes on under 15%, the gate has nothing to accept: the primary becomes qwen2.5-coder:7b.
- **Timing conditions (Stage 1 finding):** 63% of Stage 1 draws ran on battery and mains periods coincided with charging, which ran hotter (14B: 24.9 s per draft on mains vs 16.4 s on battery). Stage 2 runs on mains power; power source is logged per draw.
- **Budget:**
  - If measured time is more than twice the estimate, first cut draws to 5 (local) and 3 (strong), then drop the 1.5B arm.
  - The primary analysis (3B and 14B) is never cut.

## 10. Exclusions and missing data

- **Generation errors:** retried by resuming, at most 3 attempts per draw. A draw still failing after that is excluded and counted.
- **Missing tiers:** a task without at least one usable draw from both the 3B and the 14B is excluded and counted. Gate 2 fails if more than 5% of planned rows are missing. Missing rows in the 1.5B or 7B arms are counted and reported but do not exclude the task.
- **Judge errors:** retried. Drafts still unjudged count as rejections (section 6), and the count is reported.
- **Coverage:** `calibrate` and `test` compare usable tasks with the committed split manifest and refuse to run if more than 5% of a split's tasks are missing. Error rows and unscored rows are counted in the report.
- **Spend:** none; no hosted model is used. (The spend ledger in the code stays empty.)
- **EvalPlus placeholders:** placeholders for problems not covered in a run are ignored.

## 11. Sensitivity and exploratory analyses (reported, not confirmatory)

- A two-stage bootstrap that resamples tasks and draws within tasks, for the primary H2 comparison.
- The contamination-check suite.
- H1 to H4 for the 7B->14B pair (Chen's pair) and the 1.5B->14B pair.
- H2 and H3 with each non-primary judge and the visible gate.
- Judge style bias: on hidden-correct solutions only, compare judge probabilities for drafts written by the 1.5B, 3B, 7B and 14B.
- **Extension program:** every further experiment (other models, languages, prompt variants, prompt injection, judge stress tests) is exploratory by rule. Each has a committed `SPEC.md` with written predictions before any run, reports effect sizes with CIs and no significance claims, is counted in `ext/COMPARISONS.md`, and never feeds back into H1 to H5 or any frozen setting. Variants of test-split tasks count as test-split data and are not run before the confirmatory analysis.

## 12. What would change the conclusions (stated in advance)

- **Visible gate beats every judge:** the paper says that tests should gate escalation when tests exist, and that judges matter only where tests do not.
- **Primary judge AUROC CI includes 0.5:** H2 and H3 for that judge are reported but not interpreted as evidence about judging.
- **selfconf matches or beats the primary judge (S2):** the paper says the generator's own confidence is enough at no cost, and that the judge result is not evidence that a separate judge is needed.
- **H2 passes but S1 does not:** reported as "the larger model was not needed", not as evidence for the judge.
- **Model digest or Ollama version changes between stages:** the affected rows are re-collected, or the analysis is split by version, and the change is logged in DEVIATIONS.md.
