# Limitations, exclusions and caveats (running list)

Started 2026-10-23 during KICKOFF2 Phase 1-2. Every verification failure, excluded suite or language, and timing
caveat goes here, with the date and what was done about it.

## Scoring
- HumanEval/32 (EvalPlus find_zero bug) and Mbpp/255 (reference close to its time limit) fail even for the canonical
  solution. Kept in the data by Carson's T3 decision; selfchecks report them as known always-fail.
- EvalPlus 0.3.1 caps each test process at 4 GB of address space; the scoring worker already holds about 4.5 GB, so
  correct code failed at random until scoring used `--memory 6g`, `EVALPLUS_MAX_MEMORY_BYTES=8589934592`, `--parallel 1` (T3).
- evalplus.evaluate silently reuses an existing `<samples>_eval_results.json`; every scoring path now deletes it first
  (found in T18 when an import refused a stale file).

## Timing (seconds cost)
- Fanless MacBook Air: heat slowed decoding up to 2.4x (3B) and 1.2x (14B) in T13. macOS reported no thermal warning
  throughout, so decode speed is the only usable throttle signal. A cooldown guard pauses a tier below 0.7 x its cool
  reference speed; pauses are logged. Early Stage 1: pauses took about 60% of wall time.
- Charging the battery during a run adds heat (T13 ran while charging 41% -> 100%).
- The 7B decodes at about 11.5 tok/s under Ollama 0.40.8 vs 18.1 tok/s measured once under 0.32.5; not explained.
- Wall times are measured by the homelab orchestrator over a private network and include network latency.

## Infrastructure
- The homelab's Wi-Fi dropped for about 14 minutes on 2026-10-23 (13:57-14:11 UTC). Stage 1 lost nothing (it was
  paused); bench.py now retries draws through network outages instead of writing error rows.
- tmux is not installed on the homelab; long runs use nohup.

## Variants (Phase 2, calibration split only)
- drop_example: not applicable to MBPP+ (its only example is the assert that names the function); 16 of 52 HumanEval+
  calibration tasks have two or more examples.
- drop_sentence: applies to 33 of 52 HumanEval+ and 7 of 119 MBPP+ calibration tasks (needs two or more sentences).
- distractor: 8 HumanEval+ calibration tasks have a docstring layout the description finder does not recognise; skipped.
- rename_params: parameter names in ordinary-word prose (e.g. "numbers") are left unchanged so the description keeps its
  meaning; the prompt then names the old parameter in prose while the signature uses the new one.
- Two transform bugs were caught by the EvalPlus selfcheck and fixed before any model saw a variant: tuple-target
  renaming (HumanEval/127) and an MBPP scoring prefix built from padding lines starting with "from" (7/16/43 failures).
- Candidate-code rewrites that go through ast.unparse (reformat, rename_locals, mutators) also drop comments;
  reformat is the control for that.
- rename_locals bug (nested-function parameter, HumanEval/6) caught by the EvalPlus check and fixed.

## Suites and languages
- T20 (other programming languages) deferred: Carson did not approve downloading MultiPL-E or its evaluation image
  (2026-10-23). No programming-language experiment (E9) until that changes.
- HumanEval-XL (commit 1e9301f, MIT in the repo; the Hugging Face card says Apache-2.0) covers 80 of the 164
  HumanEval problems; 28 of them are in the calibration split.

## Stage 1 (2026-10-23/24)
- 3,136 of 4,959 calibration draws (63%) ran on battery because the charger kept disconnecting. Mains periods often
  coincided with charging and ran hotter: 14B 24.9 s/draft on mains vs 16.4 s on battery; 7B 12.5 vs 6.8 s; 1.5B and 3B
  nearly unchanged. 70 cooldown pauses (4.7 h). Thresholds chosen on these seconds may not transfer to a Stage 2 run on mains.

## Phase 4 exploratory experiments (2026-10-25 to 2026-11-01)
- Unjudged labels from network timeouts to the Mac, left unjudged and disclosed: E3 5 tev_nocrit labels; E6 21 tev_hier
  labels (role_tags, test split). Each drops out of its own cells only.
- E3 to E6 and E14b use a 150-task subset of E3 (100 test, 50 calibration; seed 20261026); CIs are several points wide.
- E6: ext/E6/pooled.py was written after the full run because analyze.py did not compute the spec's "pooled" condition;
  it follows SPEC.md's definitions and changes no existing number. Payloads are ten fixed benign canaries, one draw each.
- E4 strip_comments and reformat give identical code for 906 of 1,199 drafts and largely share labels.
- E5 mutants are one-edit bugs on hidden-correct 3B drafts; kept mutants are only those the hidden tests catch.
- E12, E14a and E14b are simulations or re-analyses of stored draws; real retries would be fresh draws.
- E14a/E14b drift monitor: h was tuned on reference drafts whose accept rate differs from the evaluated streams, which
  drives false alarms of 9% to 69%; the monitor as specified is not usable.
- Section 11 pair sensitivity: runs/sensitivity/pairs.py first failed (missing --primary-judge); fixed in pairs.py only,
  with Carson's approval, and rerun. controllers.py and thresholds.json unchanged.
- Not run (deferred to a later session): contamination check on self-authored tasks (10 of a planned 40 exist), judge
  style-bias analysis, E1, E7, E8, E10, E11, E13, E15. T20 (other programming languages) not approved.
- The "visible" gate uses the original benchmark tests (EvalPlus base tests), a subset of the hidden tests. The generator sees only part of them, so it cannot reject a correct draft by construction and stands in for an existing test suite, not just prompt examples.
- H2 for tev is +117 token-compute [-66, +291]: no demonstrated saving, not a demonstrated loss. On seconds, the secondary cost, tev->reroute is 4.4 s/task faster than strong-only [-5.4, -3.4].
- The pre-registration is a git commit in a private repository (e6d9788); no third-party registry deposit is recorded.
