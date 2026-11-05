# E4 result: judge surface invariance (semantics-preserving rewrites)

Exploratory and post-hoc (PREREG v2 section 11). Spec and predictions: commit 8b14e0e, before any E4 label. Scripts
ext/E4/transform.py and ext/E4/analyze.py; full tables in ext/E4/out/e4.md and e4.json. Drafts: every local3b draft of
E3's subset (100 test + 50 calibration tasks; 1,200 draws). 4,497 rewrites, each re-scored with EvalPlus in the
`--network none` container: 0 verdict changes (after the fix below). tev and llama: 2,902 new labels each, 0 errors,
0 unparseable. Task-cluster bootstrap, 1,000 resamples; effect sizes only. Numbers below are test split unless noted.

Deviation: the first full transform run stopped because rename_locals changed 5 HumanEval/6 verdicts (a local named
like a nested function; the call site was renamed too). Fixed in 8ebd78b with Carson's approval, logged in
DEVIATIONS.md, and the step rerun before any rewritten draft was judged.

Coverage: strip_comments, reformat and verbose_comments apply to almost every draft (800 test pairs); rename_locals to
586 (73%); reorder_helpers to 18 test pairs only (single-function drafts dominate), so its rows are not interpretable.
strip_comments and reformat give identical code for 906 of 1,199 drafts (no docstring), so those two conditions largely
share labels and are not independent evidence.

## Main findings
1. **Ranking survives every rewrite.** AUROC on rewritten minus original code of the same drafts: tev 0.000, +0.001,
   -0.003, -0.005 (strip, reformat, rename, verbose); llama -0.007, -0.006, -0.019, -0.008. Every CI includes 0.
2. **tev's decisions have a surface noise floor of about 5 to 9%.** Rewrites that change nothing the tests can see
   flip 4.5% (reformat) to 9.0% (rename_locals) of tev's frozen-tau decisions; mean |dp| is 0.033 to 0.058. This is the
   same size as E3's paraphrase flips (4 to 8%), so wording and code surface are comparable noise sources for tev.
3. **llama is pushed toward NO by verbose comments and renamed variables, by a lot.** verbose_comments: mean dp
   -0.154 [-0.173, -0.136], accept rate 0.262 -> 0.100, 56% of drafts move by at least 0.1. rename_locals: mean dp
   -0.091, accept rate 0.218 -> 0.087. Because the shift is nearly uniform, AUROC barely moves, but llama's frozen tau
   becomes far stricter: false-accept falls (0.145 -> 0.074) and so does acceptance of correct code.
4. **tev is nearly unbiased in direction.** Mean dp is within +/-0.015 for every transform; the largest acceptance
   change is rename_locals, -4.3 points [-7.6, -0.8].
5. **Calibration split agrees** in sign and size for every finding above (e4.md, cal tables).

## Predictions (written before any E4 label) vs outcome
1. tev mean |dp| <= 0.05 for every transform: **did not hold** for rename_locals (0.058; reorder_helpers 0.052 on 18
   pairs); held for the other three. llama larger than tev for every transform: held for the four interpretable ones.
2. AUROC within 0.02 for strip_comments, reformat, rename_locals for both judges: **held** (largest -0.019).
3. verbose_comments raises mean p for both judges and llama's false-accept by >= 2 points: **did not hold**, in the
   opposite direction (tev -0.015, llama -0.154; llama false-accept -7.1 points).
4. strip_comments lowers tev's mean p: **did not hold** (+0.010 [+0.004, +0.018]).
5. tev flips at most 10% under every transform: **held** (max 9.0%); at most 5% under rename_locals: **did not hold**
   (9.0%).
6. No transform changes any EvalPlus verdict: **did not hold as first run** (the rename_locals scoping bug; 5 drafts);
   held after the fix.
One held in full, three in part, two did not hold.

## Caveats
- Labels are cached and the judges are run once per code, so the within-code re-query noise floor is not measured here;
  some of finding 2 may be sampling noise rather than surface sensitivity.
- The rewrites are mechanical (ast.unparse layout, v1/v2 names, generic comments). Natural refactors may behave
  differently.
- verbose_comments adds the same four generic comments; llama may be reacting to comment volume or to their emptiness.
- 100 test tasks; CIs on rates are several points wide.

## What it means for the study
- AUROC-based conclusions about tev and llama are robust to code surface.
- Any deployed llama-style logprob gate is sensitive to code style: a generator that comments heavily or uses terse
  names would be rejected far more often at the same tau. Thresholds would need refitting per generator style.
- For tev, about 1 in 15 gate decisions is not stable under a meaningless rewrite, which bounds how precise any tev
  gate can be. Visible tests do not have this problem: their verdicts are unchanged by construction.
