# E5 result: judge detection of synthetic bugs (T18 mutants)

Exploratory and post-hoc (PREREG v2 section 11). Spec and predictions: commit 8e28559, before any E5 label. Scripts
ext/E5/mutate.py and ext/E5/analyze.py; full tables in ext/E5/out/e5.md and e5.json. Parents: 820 hidden-correct
local3b drafts of E3's subset (100 test + 50 calibration tasks). 1,374 kept mutants (852 test, 522 cal), each failing
the hidden tests under EvalPlus in the `--network none` container; 1 to 27 possibly-equivalent mutants per class and
suite were dropped (ext/E5/out/mutate_check.json). tev and llama: 1,133 new labels each, 0 errors, 0 unparseable.
Task-cluster bootstrap, 1,000 resamples; effect sizes only. Numbers are test split unless noted.

## Main findings
1. **Both judges notice one-token bugs in a correct draft almost every time it matters for ranking.** P(parent scored
   above its mutant): tev 0.961 [0.941, 0.978], llama 0.880 [0.831, 0.920]. tev's mean drop is 0.49 in probability;
   every class drops (smallest wrong_init -0.36, largest early_exit -0.73).
2. **Synthetic bugs are easier than natural ones, not harder.** tev rejects 85.4% of mutants vs 71.7% of natural wrong
   drafts (+13.7 points [+1.8, +26.8]); AUROC correct-vs-mutants 0.874 vs 0.781 for natural wrong drafts. Mutant-based
   judge benchmarks would overstate how well a judge does on a generator's real mistakes.
3. **Class ranking for tev:** early_exit 97.5%, swap_args 89.0%, wrong_init 87.0%, drop_guard 81.8%, off_by_one 80.9%,
   flip_comparison 77.7% (the subtlest edits are hardest). Calibration-split order is similar except off_by_one is last.
4. **llama's high detection rate comes from rejecting nearly everything.** It rejects 95.4% of mutants but also 70% of
   their correct parents; only 25.8% of mutants are "caught" (parent accepted, mutant rejected) vs 63.8% for tev.
5. **Visible tests catch more mutants than tev in five of six classes** (pooled 91.5% vs 85.4%), the exception being
   early_exit (92.0% vs 97.5%). Unplanned descriptive check (ext/E5/either.py, test split): visible tests OR tev catch
   97.7% of mutants; tev catches 52 of the 72 mutants that pass the visible tests.

## Predictions (written before any E5 label) vs outcome
1. tev detects mutants less often than natural wrong drafts: **did not hold**, opposite direction (+13.7 points; CI
   excludes 0 on test, includes 0 on cal: +11.5 [-1.2, +27.7]).
2. early_exit highest for tev; off_by_one and flip_comparison the two lowest: **held**.
3. Pooled P(parent > mutant) >= 0.65 for tev and lower for llama: **held** (0.961, 0.880).
4. Visible tests catch more mutants than tev rejects in every class with >= 20 test mutants: **held in five of six**;
   not for early_exit.
5. tev mean dp negative for every class: **held**.
6. llama pooled detection within 10 points of its natural detection: **held**, narrowly (+9.9 [+1.4, +19.0]; cal +0.9).
Four held in full, one in part, one did not hold.

## Caveats
- Mutants come from correct 3B drafts and are one-edit bugs; they are a convenient, not a representative, bug sample.
  Detection rates depend on which drafts each mutator can touch (drop_guard: 55 test mutants, mostly HumanEval+).
- Kept mutants are those the hidden tests catch, so the comparison with visible tests is among test-detectable bugs.
- The parents were chosen as hidden-correct; their accept rates (tev 0.78, llama 0.30) reflect the frozen taus.
- Mutants with the same code as another draft share one cached label.

## What it means for the study
- tev's signal is genuinely about the code: change one token and its probability collapses. Its weakness in the main
  study is the generator's natural errors, which look plausible, rather than blindness to simple bugs.
- Mutation-based evaluations of LLM judges overstate their usefulness as gates on real drafts.
- On bugs the tests can see, visible tests remain the better single gate; tev adds coverage mainly on bugs the visible
  tests miss (52 of 72 here). On real drafts, though, E12's simulation found vis&tev adds no accuracy over the visible
  gate (+0.000) at about twice its token-compute, so this mutant result does not carry over to the generator's own errors.
