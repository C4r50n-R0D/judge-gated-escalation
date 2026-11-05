# E12: Controllers beyond the baseline (simulation part): result

Status: reported 2026-10-25. Exploratory and post-hoc (designed after T26 was read); effect sizes with CIs only.

## What was run
`python3 tools/exprun.py run E12` -> `nice python3 ext/E12/sim.py runs/confirmatory.labeled.jsonl ext/E12/out`
(script commit 8c6ab4f; controllers.py unchanged and imported). Homelab CPU, 59 min, no Mac time. Pilot: 20 tasks
per split, 0 failures. Full tables: ext/E12/out/summary.md; everything: ext/E12/out/results.json.
mc 200, seed 20261009, 2,000 task-cluster bootstrap resamples; 371 test and 171 calibration tasks.

## Results (test split; paired differences vs visible->reroute = 0.765 accuracy, 1,821 token-compute, 8.4 s)

| controller | accuracy | token-compute | s/task | accuracy minus visible->reroute | token-compute minus visible->reroute |
|---|---|---|---|---|---|
| strong-only | 0.751 | 3,749 | 16.8 | -0.014 [-0.034, +0.006] | +1,928 |
| **cascade 3B->7B->14B, visible gate** | **0.780** | **1,809** | **8.3** | **+0.015 [+0.006, +0.024]** | **-12 [-89, +70]** |
| visible->resample(2)->reroute | 0.774 | 1,725 | 7.9 | +0.009 [+0.003, +0.015] | -96 [-144, -47] |
| visible->resample(3)->reroute | 0.778 | 1,766 | 8.1 | +0.013 [+0.004, +0.022] | -55 [-133, +30] |
| visible->resample(5)->reroute | 0.784 | 1,905 | 8.8 | +0.019 [+0.007, +0.032] | +84 [-50, +232] |
| vis&tev->reroute (transfer) | 0.766 | 3,634 | 12.7 | +0.000 [-0.011, +0.013] | +1,814 |
| vis&tev->reroute (recal, tau 0.016) | 0.765 | 2,835 | 9.5 | +0.000 [+0.000, +0.000] | +1,014 |
| vis&selfconf->reroute (transfer) | 0.751 | 3,841 | 16.9 | -0.014 [-0.032, +0.005] | +2,020 |
| vis&selfconf->reroute (recal, tau 0.616) | 0.765 | 1,821 | 8.4 | +0.000 (rejects nothing) | +0 |
| tev->reroute (frozen, = T26) | 0.748 | 3,866 | 12.4 | -0.018 [-0.031, -0.004] | +2,045 |
| tev->resample(3)->reroute | 0.752 | 5,148 | 14.2 | -0.013 [-0.027, +0.002] | +3,327 |
| tev AND sc ->reroute (transfer) | 0.750 | 5,265 | 18.4 | -0.015 [-0.033, +0.005] | +3,444 |
| tev OR sc ->reroute (transfer) | 0.745 | 3,778 | 12.1 | -0.020 [-0.034, -0.006] | +1,957 |
| cascade, vis&tev gate | 0.772 | 4,591 | 15.5 | +0.006 [-0.006, +0.019] | +2,770 |
| cascade, tev gate | 0.750 | 4,939 | 15.2 | -0.015 [-0.029, -0.000] | +3,118 |

Accuracy-vs-cost curves (21 taus each, test split): the best tev->reroute at any tau reaches 0.755 (at 4,794
token-compute); no tau of tev, llama or selfconf reaches visible->reroute accuracy. vis&tev peaks at 0.767 (3,473).
The calibration split shows the same ordering (cascade 0.851, visible->reroute 0.834, strong-only 0.794).

Findings:
1. **Executing the visible tests is the gate; a judge adds cost and no accuracy on top of it.** Refit on the
   calibration split with the pre-registered rule, every judge stacked on the visible gate is pushed to accept
   (almost) everything that passed: the cheapest feasible judge is no judge.
2. **Rejecting a draft that passed its visible tests lowers accuracy**: a fresh 14B draft is right less often than
   a 3B draft that already passed (vis&selfconf transfer: -1.4 points).
3. **Best controller found: a 3B->7B->14B cascade with the visible gate**, +1.5 points over visible->reroute at the
   same token-compute and time, and +2.9 points over strong-only at 48% of its compute and half its seconds.
   Retrying the 3B once before escalating (resample(2)) is a cheaper +0.9 points.
4. Resampling behind a judge never pays: every tev->resample(k) costs more and gains at most 0.5 points.

## Predictions vs outcome
1. vis&tev at least as accurate as visible, dearer than visible, cheaper than strong-only: **held** (+0.000; 3,634 vs 1,821 vs 3,749).
2. vis&selfconf adds 0-2 points at under 10% extra compute: **did not hold** (transfer -1.4 points at +111%; recal identical to visible).
3. tev AND sc more accurate and dearer than tev OR sc; neither beats visible on compute: **held in transfer**; cost order reversed in recal; second part held.
4. visible resample rises from k=1 to 3, flat within 1 point from 3 to 5; tev resample never cheaper than tev reroute: **held** (+0.6 points from 3 to 5).
5. Visible-gate cascade within 2 points of visible->reroute: **held** (+1.5, and more accurate).
6. Recal and transfer within 1 point for every gate: **mostly held**; fails for vis&selfconf (1.4 points). For tev,
   llama and selfconf alone, recal reproduces the frozen taus exactly (same rule, same calibration data).

## Verification and caveats
- Simulation from stored draws: cascade and resample controllers reuse each task's 8 3B, 8 7B and 5 14B draws,
  sampled with replacement within a task; real retries would be fresh draws.
- Visible-test execution is charged 0 s and 0 token-compute, as in the main study; this favours every visible gate.
- Seconds come from mixed power states (DEVIATIONS.md); token-compute is unaffected.
- All comparisons are post-hoc, chosen after T26 showed visible->reroute was strongest.
