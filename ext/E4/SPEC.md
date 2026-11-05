# E4: Judge surface invariance (semantics-preserving rewrites)

Status: SPEC (exploratory by rule, PREREG v2 section 11). Written after the T26 confirmatory results and after E2, E3
and E14a were read (2026-10-27), so every comparison is post-hoc; the predictions below are made before any E4 label.

## Question
Do tev and llama give the same probability to the same program when only its surface changes (comments, layout,
local names, helper order)? A judge that ranks drafts on surface features rather than behavior should move here.

## Manipulation
- Drafts: every local3b draft of E3's task subset (100 test + 50 calibration tasks, seed 20261026; 1,200 draws).
- Transforms (KICKOFF2 T18, verified at T18 with 0 verdict changes on calibration rows): strip_comments (comments and
  docstrings removed), reformat (ast.unparse layout; drops comments, keeps docstrings), rename_locals (local variables
  to v1, v2, ...), verbose_comments (a generic explanatory comment above every code line in functions), reorder_helpers
  (last top-level function moved up; applies to about 1% of drafts, reported as such).
- Every rewritten draft is re-scored with EvalPlus in the `--network none` container; any visible or hidden verdict
  change stops the run (ext/E4/transform.py exits non-zero) and is reported as a transform bug.
- Judges: tev and llama with their base (frozen, confirmatory) configs; labels on original code reused from E2 via the
  cache. selfconf is not applicable (it scores the generator's own tokens, which a rewrite does not have).
Fixed: frozen taus from thresholds.json, controllers.py unchanged, task-cluster bootstrap 1,000 resamples.

## Primary outcome
Per transform and judge on the test split: mean dp and mean |dp| (rewritten minus original probability, same draft),
decision flips at the frozen tau, and AUROC on rewritten minus AUROC on original code of the same drafts.

## Analysis
ext/E4/analyze.py (imports controllers.py). Both splits reported; test is primary. Effect sizes and CIs only.

## Predictions (written before any E4 label)
1. tev mean |dp| is at most 0.05 for every transform; llama's mean |dp| is larger than tev's for every transform.
2. AUROC changes by at most 0.02 (point estimate) for strip_comments, reformat and rename_locals, for both judges.
3. verbose_comments raises mean p for both judges (mean dp > 0), and raises llama's false-accept rate at its frozen tau
   by at least 2 points.
4. strip_comments lowers tev's mean p (mean dp < 0).
5. tev flips at most 10% of frozen-tau decisions under every transform; under rename_locals at most 5%.
6. No transform changes any EvalPlus verdict.

## Planned size and estimated hours
About 3,600 rewritten drafts (rename_locals and reorder_helpers apply to fewer). EvalPlus re-scoring on the homelab:
about 1 h. New labels: about 3,000 distinct codes per judge (identical codes share a cached label), about 1.3 h per
judge on the Mac, so about 3 h of Mac time. Analysis: minutes. Judging runs only after re-scoring finishes.

## Comparisons counted in ext/COMPARISONS.md
(listed in spec.json)
