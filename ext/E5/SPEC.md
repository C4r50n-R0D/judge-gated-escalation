# E5: Judge detection of synthetic bugs (T18 mutants)

Status: SPEC (exploratory by rule, PREREG v2 section 11). Written after the T26 confirmatory results and after E2, E3,
E4 and E14a were read (2026-10-28), so every comparison is post-hoc; the predictions below are made before any E5 label.

## Question
When a correct draft is broken by one small, known bug, do tev and llama notice? Which bug classes do they miss, and
how does that compare with the natural wrong drafts the generator produces and with the visible tests?

## Manipulation
- Parents: every hidden-correct local3b draft of E3's task subset (100 test + 50 calibration tasks, seed 20261026).
- Mutators (KICKOFF2 T18): off_by_one, flip_comparison, swap_args, wrong_init, drop_guard (an edge-case guard removed),
  early_exit (a loop stops after one iteration). One mutation per parent per class (seeded).
- Every mutant is scored with EvalPlus in the `--network none` container; a mutant is kept only if it now fails the
  hidden tests. Possibly-equivalent mutants (still passing) are dropped and counted per class.
- Natural reference: the hidden-failing local3b drafts of the same subset.
- Judges: tev and llama with their base (frozen) configs; parent and natural labels reused from E2 via the cache.
  selfconf is not applicable (mutants have no generator tokens).
Fixed: frozen taus from thresholds.json, controllers.py unchanged, task-cluster bootstrap 1,000 resamples.

## Primary outcome
Per bug class and judge on the test split: detection rate (mutants rejected at the frozen tau), its difference from the
natural wrong-draft detection rate, and pairwise discrimination P(p_parent > p_mutant).

## Analysis
ext/E5/analyze.py (imports controllers.py). Also: caught rate (parent accepted, mutant rejected), mean dp, AUROC of
correct drafts vs mutants, and the visible tests' catch rate for the same mutants. Both splits; test is primary.

## Predictions (written before any E5 label)
1. Pooled over classes, tev detects mutants less often than natural wrong drafts (detection minus natural < 0): a
   one-token bug in otherwise good code looks more correct than a generator's own failures.
2. For tev, early_exit has the highest detection rate of the six classes; off_by_one and flip_comparison are the two
   lowest.
3. Pooled pairwise discrimination P(p_parent > p_mutant) is at least 0.65 for tev and lower for llama.
4. The visible tests catch a larger share of mutants than tev rejects, for every class with at least 20 test mutants.
5. tev's mean dp (mutant minus parent) is negative for every class.
6. llama's pooled detection rate is within 10 points of its natural wrong-draft detection rate.

## Planned size and estimated hours
About 700 hidden-correct parents; by T18 yields roughly 20 to 50% per class are mutable and fail, so about 1,000 to
1,500 kept mutants. EvalPlus on the homelab: about 1 h. New labels: about 1,200 per judge on the Mac, about 30 min each.
Analysis: minutes. Judging runs only after scoring finishes.

## Comparisons counted in ext/COMPARISONS.md
(listed in spec.json)
