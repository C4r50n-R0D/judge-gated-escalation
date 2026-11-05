# E2 result: judge zoo and ensembles

Exploratory and post-hoc (PREREG v2 section 11). Spec and predictions committed before data (0915a3c, c829cf5).
Labels: gemma4:12b (gemma), qwen3.5:9b (qwen35), qwen2.5:7b-instruct (qwen25i) on every stored 3B draft, both splits,
run on the Mac 2026-10-25 18:19 to 2026-10-26 02:55 UTC (3,862 judge calls each; identical drafts share a cached label).
0 unparseable labels; 1 test draft unjudged by qwen35. Derived judges (Platt, isotonic, ens_mean, ens_stack) are fitted on
calibration 3B drafts only (ext/E2/fits.json). Analysis: tools/judge_eval.py; tables in ext/E2/out/judges.md.
2,000 task-cluster bootstrap resamples. Effect sizes only.

## Test split, 3B drafts (371 tasks)

| judge | AUROC | AUROC minus tev | within-task AUROC | ECE | token-compute per label |
|---|---|---|---|---|---|
| tev (4B, primary) | 0.813 [0.779, 0.846] | | 0.801 | 0.129 | 1,397 |
| gemma (12B) | 0.822 [0.788, 0.854] | +0.009 [-0.018, +0.036] | 0.836 | 0.303 | 2,989 |
| qwen35 (9B) | 0.807 [0.772, 0.841] | -0.006 [-0.027, +0.013] | 0.821 | 0.103 | 2,228 |
| qwen25i (7B) | 0.689 [0.647, 0.731] | -0.124 [-0.157, -0.090] | 0.750 | 0.265 | 1,626 |
| llama (8B) | 0.688 | -0.124 | 0.666 | 0.307 | 1,713 |
| selfconf | 0.680 | -0.133 | 0.637 | 0.244 | 0 |
| ens_mean (6 judges) | 0.822 [0.785, 0.855] | +0.009 [-0.009, +0.027] | 0.854 | 0.060 | 9,952 |
| ens_stack (6 judges) | **0.836 [0.803, 0.869]** | **+0.023 [+0.006, +0.040]** | 0.842 | 0.055 | 9,952 |

## Findings
1. **Bigger judges rank no better than tev.** gemma (3x tev's size) and qwen35 (2x) tie tev on AUROC; both CIs include
   0. They are slightly better at ordering drafts of the same task (within-task AUROC 0.836 and 0.821 vs 0.801).
2. **The judge family matters more than size.** qwen25i, a general instruct model from the generator's own family, is as
   weak as llama (0.689). Of the 8B-class judges only qwen35 matches tev.
3. **The stacked ensemble is the only judge that beats tev with a CI above 0**: +0.023 AUROC. It needs all six judges,
   7.1x tev's token-compute per label.
4. **Calibration is a separate problem from ranking, and cheap to fix.** gemma ranks best but is the worst calibrated
   (ECE 0.303: its P(YES) is tiny even for correct code, and its refit tau was 0.00003). Platt or isotonic maps
   (calibration-split fits) cut every judge's test ECE to 0.06 to 0.09 and move AUROC by at most 0.008.
5. **As gates, every new judge and ensemble is worse than tev, and every one is worse than the visible tests.** Test
   accuracy and token-compute per task of judge->reroute (recal tau): tev 0.748 / 3,866; gemma 0.742 / 5,029; qwen35
   0.739 / 4,355; qwen25i 0.728 / 4,727; ens_stack 0.742 / 12,073. visible->reroute: 0.765 / 1,821. strong-only: 0.751 /
   3,749. A better ranking does not buy accuracy, because each label costs more than the drafts it saves.
6. **The calibration-split ranking of judges did not hold on test.** qwen35 led on calibration (+0.040 over tev) and
   tied on test (-0.006); gemma did the reverse (-0.015 -> +0.009). Judge choice on 171 tasks is noisy at this size.

## Predictions (written before data) vs outcome
1. No new single judge beats tev by more than 0.03; gemma closest: **held** (+0.009, -0.006, -0.124).
2. qwen25i lowest of the new judges: **held** (0.689).
3. ens_stack highest of all, by at most 0.05 over tev: **held** (+0.023).
4. Platt and isotonic keep AUROC within 0.01 and bring llama ECE below 0.1: **held** (largest change -0.008; llama 0.080).
5. No judge->reroute cheaper than strong-only; every new judge costs more per label than tev: **held** (tev_platt and
   selfconf are +117 and +31 with CIs including 0; none is below).
6. No judge->reroute beats visible->reroute on token-compute: **held**.
All six held.

## Caveats
- Only 3B drafts were judged by the new judges (the primary local model); generator shift for them is not measured.
- Ensemble cost charges every base judge on every draft. A cascade that calls the big judges only on uncertain drafts
  might be cheaper; it was not tested.
- Calibration-split ECE for isotonic is in-sample (0.000 by construction).
