# E12: Controllers beyond the baseline (simulation part)

Status: SPEC (exploratory by rule, PREREG v2 section 11). Written after the T26 confirmatory results were read
(2026-10-25), so every comparison here is post-hoc; the predictions below are made before running this script.

## Question
Can combining the cheap gates the main study measured (visible tests, tev, llama, selfconf), resampling more, or
adding a middle tier beat the best T26 controller, visible->reroute (test: 0.765 accuracy, 1,821 token-compute,
8.4 s per task), on accuracy, token-compute or seconds?

## Manipulation
All simulated from stored draws (runs/confirmatory.labeled.jsonl); no new generation or judge calls.
- Combined gates: vis&tev, vis&llama, vis&selfconf (the judge is called only when the visible tests pass);
  tev&sc and tev|sc (both judges' accept decisions combined).
- k: visible and tev resample(k)->reroute, k = 1 to 5.
- Cascade: 3B -> 7B -> 14B with the visible, tev, and vis&tev gates at each step.
- Accuracy-vs-cost curves: 21 taus per judge (calibration quantiles) on the test split.
- Every gate in two modes: transfer (frozen taus) and recal (tau refit on the calibration split with the
  pre-registered rule and cost metric). For tev&sc and tev|sc the recal score is the min / max of percentile ranks.
Fixed: local 3B, strong 14B, mc 200, seed 20261009, 2,000 task-cluster bootstrap resamples, controllers.py unchanged.

## Primary outcome
Paired accuracy difference and token-compute difference of each controller vs visible->reroute on the test split.

## Analysis
Script: ext/E12/sim.py (imports controllers.py; no changes to it). Task-cluster bootstrap CIs; effect sizes only.
Both splits are reported; the calibration split shows how much of a gap is selection on that split (recal mode).

## Predictions (directional, written before running this script)
1. vis&tev->reroute (transfer) is at least as accurate as visible->reroute (difference within +/-1 point or above),
   costs more token-compute than visible->reroute, and less than strong-only.
2. vis&selfconf->reroute adds 0 to 2 points over visible->reroute at under 10% extra token-compute.
3. tev&sc is more accurate and more expensive than tev|sc; neither beats visible->reroute on token-compute.
4. Resampling: visible->resample(k)->reroute accuracy rises from k = 1 to 3 and is flat (within 1 point) from 3 to 5;
   tev->resample(k)->reroute never costs less token-compute than tev->reroute.
5. The 3B->7B->14B cascade with the visible gate is within 2 points of visible->reroute in accuracy; direction of
   the token-compute difference: no prediction.
6. Recal and transfer taus give accuracies within 1 point of each other on the test split for every gate.

## Planned size and estimated hours
371 test + 171 calibration tasks; about 50 simulated controllers; homelab CPU only, about 1 to 2 hours. Mac: 0.

## Comparisons counted in ext/COMPARISONS.md
(listed in spec.json)
