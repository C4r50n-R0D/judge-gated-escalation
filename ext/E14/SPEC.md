# E14a: Calibration and drift of the frozen taus (shifts already in the stored data)

Status: SPEC (exploratory by rule, PREREG v2 section 11). Written 2026-10-26 after T26, E12 and the interim E2 numbers
were read. E14 is split: E14a (this file) uses only shifts present in runs/confirmatory.labeled.jsonl; E14b repeats the
same measurements for the E3 to E6 shifts (prompt variants, surface rewrites, mutants, injections) once those exist.

## Question
How do the frozen thresholds.json taus behave when the drafts they gate are not the calibration-split 3B drafts they were
set on, does Platt or isotonic recalibration (fitted on the calibration 3B drafts) fix the calibration error and keep
fixing it under shift, and can a label-free monitor detect a shift?

## Manipulation (no model calls)
Conditions, each gated with the frozen tau of tev, llama and selfconf (controllers.gate, unchanged):
- reference: calibration split, 3B drafts; split shift: test split, 3B drafts;
- generator shift: test split, 1.5B, 7B and 14B drafts (same tasks as test 3B, so paired);
- suite: test 3B drafts on MBPP+ and on HumanEval+; time: test 3B drafts by quintile of generation time
  (each quintile is also a different set of tasks, so time and task are confounded).
Drift monitor: two-sided Bernoulli CUSUM (k 0.05) on (A) the accept indicator and (B) "accepted and fails the visible
tests"; reference rate and threshold from the reference condition only (5% false alarms over 1,000 drafts); evaluated
on 1,000-draft streams of test 3B drafts, and of 300 test 3B drafts followed by 700 of another generator.

## Outcomes
At the frozen tau: acceptance rate, accepted-set accuracy, false-accept rate, false-reject rate. AUROC, ECE (10 bins)
and Brier of raw, Platt and isotonic scores. Monitor: false-alarm rate, detection rate within 700 drafts, median delay.

## Analysis
Script ext/E14/e14.py (imports controllers.py and judgestats.py unchanged). Task-cluster bootstrap, 2,000 resamples;
paired over tasks for generator conditions. Effect sizes and CIs only.

## Already seen before writing this (so not predicted)
Test 3B AUROC and raw ECE for tev, llama, selfconf (T26, E2 interim); calibration-split AUROC and raw ECE by generator
(Gate 1 v2 report). Not yet seen: anything at the frozen tau by generator, suite or time on test; recalibrated ECE on
test; the monitor.

## Predictions (written before running the script)
1. Recalibration fitted on calibration 3B lowers test-3B ECE below 0.10 for llama and selfconf; for tev the
   recalibrated ECE is within 0.05 of raw.
2. tev at its frozen tau: on 1.5B drafts the acceptance rate is at least 10 points below test 3B and accepted-set accuracy
   is 0 to 8 points lower; on 7B drafts the acceptance rate is at least 3 points higher and accepted-set accuracy within
   3 points; on 14B drafts the acceptance rate is higher than on 7B.
3. Recalibration does not transfer across generators: isotonic ECE on test 1.5B drafts is higher than on test 3B,
   for each of the three judges.
4. tev's false-accept rate on 7B and on 14B drafts is higher than on 3B drafts (wrong code from stronger models
   looks more plausible).
5. For tev, the HumanEval+ minus MBPP+ and the Q5 minus Q1 differences in accepted-set accuracy both have CIs that
   include 0.
6. Monitor A with tev: false-alarm rate on test-3B-only streams at most 0.15; detects a switch to 1.5B in at least 80%
   of streams with median delay at most 150 drafts; detects a switch to 7B less often or more slowly than to 1.5B.

## Planned size and estimated hours
About 16,000 stored drafts; homelab CPU only, under 1 hour. Mac: 0.

## Comparisons counted in ext/COMPARISONS.md
(listed in spec.json)
