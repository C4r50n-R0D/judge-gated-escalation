# Gate 1 v2 report: Stage 1 calibration split

Date: 2026-10-24. Data: `runs/stage1.labeled.jsonl`: all 171 calibration tasks, four generator tiers, three judges.
No test-split row has been generated. Code at commit 30fd107 and later (collection code unchanged since cbf7646 + d227133 + 7c21c28). Spend: $0.

**Proposed Gate 1 v2 decisions:** primary judge **tev**; delta **0.03**; local model stays **qwen2.5-coder:3b**; no draw changes; cost metric **token-compute** (STOP A).
Stage 2 (test split, 371 tasks) is estimated at **about 40 hours** of wall time. One item to confirm before the freeze (section 7): token-compute makes H2's savings test strict.

## 1. Collection and throughput

4,959 of 4,959 planned draws: 0 errors, 0 unscored, 0 missing, 0 excluded tasks; no network-outage retries were needed after the
restart. Wall time 08:11 to 02:20 UTC (18.1 h): generation 14.6 h (of which cooldown pauses 4.7 h, 70 pauses), EvalPlus
scoring 19 min, judging 3 h 16 min.

| Tier | Draws | s/draft (net of model load) mean / median | Tokens out | Decode tok/s |
| --- | --- | --- | --- | --- |
| qwen2.5-coder:1.5b | 1,368 | 1.60 / 1.17 | 78 | 60.1 |
| qwen2.5-coder:3b | 1,368 | 3.60 / 2.63 | 99 | 32.4 |
| qwen2.5-coder:7b | 1,368 | 8.42 / 5.73 | 89 | 13.2 |
| qwen2.5-coder:14b | 855 | 18.09 / 13.29 | 109 | 6.8 |

Judges: tev 1.60 s/label (median 1.43), llama 1.39 s/label (median 1.13), selfconf 0 (no call).

**Stage 2 estimate (371 test tasks, 2.17 x Stage 1):** generation about 32 h including cooldowns, scoring about 45 min, judging
about 7 h: **about 40 hours**, less if the Mac stays on mains with better cooling (fewer pauses). The old 26-hour figure no longer applies.

## 2. Pass rates and tier gaps (descriptive; no rule attached)

Per-task hidden pass rates, task-cluster bootstrap (2,000 resamples):

| Local tier | Local pass rate | 14B pass rate | Gap (14B minus local) |
| --- | --- | --- | --- |
| 1.5B | 0.562 [0.506, 0.621] | 0.794 [0.743, 0.847] | +0.232 [+0.170, +0.296] |
| **3B (primary)** | **0.702 [0.651, 0.756]** | 0.794 [0.743, 0.847] | **+0.092 [+0.046, +0.138]** |
| 7B | 0.763 [0.711, 0.811] | 0.794 [0.743, 0.847] | +0.031 [-0.008, +0.072] |

The 3B-to-14B gap is about 9 points, well above the 20-task pilot's 5 and close to the published-score estimate of 9.3. The 7B
(Chen's pair) is within about 3 points of the 14B, and its CI includes 0.

## 3. Judges

AUROC against hidden correctness of each tier's drafts, task-cluster bootstrap CI; within-task AUROC compares correct and wrong
drafts of the same task.

| Drafts by | Judge | AUROC | Within-task AUROC | Brier | ECE |
| --- | --- | --- | --- | --- | --- |
| 3B | **tev** | **0.793 [0.739, 0.843]** | 0.725 [0.654, 0.795] (74 tasks) | 0.162 | 0.084 |
| 3B | llama | 0.673 [0.619, 0.725] | 0.557 [0.489, 0.625] | 0.355 | 0.392 |
| 3B | selfconf | 0.674 [0.613, 0.732] | 0.642 [0.578, 0.701] | 0.227 | 0.176 |
| 1.5B | tev | 0.822 [0.778, 0.863] | 0.835 [0.775, 0.887] (96 tasks) | 0.200 | 0.162 |
| 1.5B | llama | 0.727 [0.675, 0.778] | 0.721 [0.658, 0.776] | 0.275 | 0.244 |
| 1.5B | selfconf | 0.678 [0.625, 0.726] | 0.684 [0.628, 0.737] | 0.325 | 0.310 |
| 7B | tev | 0.731 [0.663, 0.798] | 0.695 [0.616, 0.777] (65 tasks) | 0.165 | 0.077 |
| 7B | llama | 0.666 [0.603, 0.728] | 0.573 [0.491, 0.656] | 0.393 | 0.456 |
| 7B | selfconf | 0.608 [0.539, 0.676] | 0.631 [0.560, 0.700] | 0.199 | 0.151 |

- **Proposed primary judge: tev**, by the unchanged rule (higher AUROC of tev and llama on the primary model's calibration drafts: 0.793 vs 0.673).
- 0 unjudged drafts and 0 unparseable labels for every judge.
- The 20-task pilot had selfconf ahead of tev; on 171 tasks tev is clearly ahead and selfconf ties llama.
- llama is badly calibrated (ECE 0.39 on the 3B), as in the pilot; its ranking is still above chance.

## 4. Power rule (printed exactly)

```
calibration pilot tasks 171 (excluded 0); judge:tev tau=0.8619849230515471 (pre-registered rule); per-task diff sd 0.169
note: the mean difference is not shown, to keep the margin decision independent of effect size
sd=0.169 n=371: SE 0.0088 -> delta 0.03 (test H2 with this delta); power if true diff 0: 0.93, if -delta/2: 0.40
```

n_test = 371 from `split_manifest.json`. **Proposed delta: 0.03.** (llama for comparison: sd 0.108, delta 0.03.)

## 5. Tau curves and proposed thresholds (`runs/thresholds.proposed.json`, not `thresholds.json`)

Every distinct calibration probability is a candidate. Cost metric = **token-compute** (Carson's STOP A decision); the
chosen taus are identical under seconds.

| Judge | Candidates | Feasible | Proposed tau | Token-compute per task at that tau | Seconds per task at that tau |
| --- | --- | --- | --- | --- | --- |
| tev (primary) | 1,232 | 655 | 0.862 | 3,676 | 12.8 |
| llama | 1,232 | 277 | 0.467 | 5,546 | 20.3 |
| selfconf | 1,274 | 173 | 0.960 | 3,835 | 17.4 |
| strong-only (reference) | | | | 3,872 | 18.3 |

Per call, in billion-parameter tokens: 3B draft 780, 14B draft 3,872, tev label 1,313, llama label 1,624. A judge label costs
more compute than a 3B draft, because token-compute counts prompt tokens at full weight (correct for FLOPs), while on the
Mac prompt tokens run about 10 times faster than generated ones. So **on the calibration split the primary gate saves about
5% of compute but about 30% of time** relative to strong-only. Under token-compute, H2's savings test is strict.

Full curves (accuracy, cost, bootstrap lower bound, feasibility per candidate) are in `runs/thresholds.proposed.json`
under `details`. Calibration data hash `bd4b216fa113…` (171/171 tasks covered). Power rule under token-compute: same tau, sd
0.169, delta 0.03.

## 6. Ceiling and floor

The primary model (3B) passes hidden tests on 70.2% of its calibration drafts: inside the 15-90% band. No model change.

## 7. Decisions taken at STOP A (2026-10-24) and one to confirm
1. **Cost metric: token-compute** (option b), seconds reported as H5 with a power-source sensitivity analysis. To confirm
   before the freeze, given section 5: token-compute makes H2's savings test strict (about 5% calibration savings vs about
   30% in seconds). Alternatives: keep it (recommended if "compute" is the claim), weight prompt tokens less, or return to seconds.
2. **S1 and S2: approved and implemented** (commit bd0f7d6); `controllers.py test` computes and reports both.
3. **Stage 2 conditions:** the Mac stays on mains (charger seated) for the whole stage; power source is logged per draw.

## 8. Limitations added at this stage
- 63% of Stage 1 draws ran on battery; charging periods ran hotter. See `runs/limitations.md`.
- The thresholds use wall seconds measured under mixed power states; if Stage 2 runs on mains, its seconds will not be
  directly comparable to the calibration seconds the taus were chosen on.
