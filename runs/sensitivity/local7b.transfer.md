# Test-split results (371 tasks; excluded 0; rows {'rows': 10759, 'error_rows': 0, 'unscored_rows': 0, 'tasks_seen': 371}; coverage {'expected': 371, 'usable': 371, 'missing': 0, 'missing_frac': 0.0})

Frozen thresholds: {'tev': 0.8619849230515471, 'llama': 0.4667895416652746, 'selfconf': 0.9602630454757016}. Non-inferiority margin delta = 0.03. Primary judge: tev. Cost metric for the cheapest tau and H2 savings: tok.

## Controllers (mean [95% cluster-bootstrap CI])

| controller | accuracy | USD/task | s/task | token-compute/task (B-param x tokens) | tasks |
|---|---|---|---|---|---|
| local-only | 0.714 [0.673, 0.753] | 0.00000 [0.00000, 0.00000] | 8.2 [7.7, 8.7] | 1806 [1737, 1876] | 371 |
| strong-only | 0.751 [0.710, 0.790] | 0.00000 [0.00000, 0.00000] | 16.8 [15.8, 18.0] | 3749 [3604, 3908] | 371 |
| visible->reroute | 0.786 [0.750, 0.822] | 0.00000 [0.00000, 0.00000] | 12.1 [11.0, 13.2] | 2575 [2384, 2769] | 371 |
| visible->resample(3) | 0.767 [0.728, 0.806] | 0.00000 [0.00000, 0.00000] | 11.1 [10.1, 12.1] | 2412 [2240, 2591] | 371 |
| visible->resample(3)->reroute | 0.800 [0.763, 0.836] | 0.00000 [0.00000, 0.00000] | 13.4 [11.8, 15.1] | 2876 [2580, 3189] | 371 |
| oracle->reroute | 0.820 [0.784, 0.855] | 0.00000 [0.00000, 0.00000] | 13.8 [12.6, 15.0] | 2945 [2734, 3155] | 371 |
| oracle->resample(3) | 0.805 [0.766, 0.843] | 0.00000 [0.00000, 0.00000] | 12.9 [11.7, 14.1] | 2748 [2555, 2943] | 371 |
| oracle->resample(3)->reroute | 0.853 [0.819, 0.887] | 0.00000 [0.00000, 0.00000] | 16.6 [14.7, 18.6] | 3522 [3177, 3881] | 371 |
| judge:tev->reroute | 0.759 [0.720, 0.798] | 0.00000 [0.00000, 0.00000] | 17.6 [16.4, 18.8] | 4896 [4677, 5133] | 371 |
| judge:tev->resample(3) | 0.743 [0.703, 0.783] | 0.00000 [0.00000, 0.00000] | 17.7 [16.5, 18.9] | 5800 [5483, 6133] | 371 |
| judge:tev->resample(3)->reroute | 0.761 [0.721, 0.800] | 0.00000 [0.00000, 0.00000] | 23.5 [21.4, 25.7] | 7061 [6578, 7571] | 371 |
| judge:llama->reroute | 0.753 [0.713, 0.791] | 0.00000 [0.00000, 0.00000] | 23.2 [21.6, 24.9] | 6379 [6056, 6723] | 371 |
| judge:llama->resample(3) | 0.740 [0.701, 0.781] | 0.00000 [0.00000, 0.00000] | 23.8 [22.0, 25.6] | 8589 [8076, 9126] | 371 |
| judge:llama->resample(3)->reroute | 0.758 [0.719, 0.797] | 0.00000 [0.00000, 0.00000] | 35.8 [32.9, 38.8] | 11136 [10420, 11892] | 371 |
| judge:selfconf->reroute | 0.746 [0.706, 0.783] | 0.00000 [0.00000, 0.00000] | 19.2 [18.1, 20.3] | 4372 [4213, 4536] | 371 |
| judge:selfconf->resample(3) | 0.729 [0.689, 0.770] | 0.00000 [0.00000, 0.00000] | 18.3 [17.3, 19.4] | 4124 [3979, 4273] | 371 |
| judge:selfconf->resample(3)->reroute | 0.742 [0.702, 0.780] | 0.00000 [0.00000, 0.00000] | 27.1 [25.6, 28.7] | 6221 [5943, 6503] | 371 |

## H1 judge discrimination (AUROC vs hidden-test correctness of local drafts)

- tev: AUROC 0.779 [0.738, 0.819]; correct 2121, wrong 847; supported: True; within-task AUROC 0.699 [0.632, 0.762] over 121 tasks; unjudged drafts (counted as rejections) 0
- llama: AUROC 0.681 [0.634, 0.728]; correct 2121, wrong 847; supported: True; within-task AUROC 0.662 [0.602, 0.716] over 121 tasks; unjudged drafts (counted as rejections) 0
- selfconf: AUROC 0.645 [0.597, 0.690]; correct 2121, wrong 847; supported: True; within-task AUROC 0.605 [0.544, 0.666] over 121 tasks; unjudged drafts (counted as rejections) 0

## H2 gate->reroute vs strong-only (paired differences)

- judge:tev: accuracy +0.008 [-0.006, +0.022], USD +0.00000 [+0.00000, +0.00000], seconds +0.7, token-compute +1148; non-inferior True, cheaper False, supported False
- judge:llama: accuracy +0.002 [-0.007, +0.011], USD +0.00000 [+0.00000, +0.00000], seconds +6.3, token-compute +2630; non-inferior True, cheaper False, supported False
- judge:selfconf: accuracy -0.005 [-0.016, +0.006], USD +0.00000 [+0.00000, +0.00000], seconds +2.4, token-compute +624; non-inferior True, cheaper False, supported False
- visible: accuracy +0.035 [+0.015, +0.057], USD +0.00000 [+0.00000, +0.00000], seconds -4.7, token-compute -1174; non-inferior True, cheaper True, supported True
- oracle: accuracy +0.069 [+0.052, +0.088], USD +0.00000 [+0.00000, +0.00000], seconds -3.0, token-compute -804; non-inferior True, cheaper True, supported True

## S1 what the primary judge adds: gate->reroute vs local-only (read H2 together with this)

- accuracy +0.045 [+0.021, +0.070], token-compute +3090 [+2908, +3295], seconds +9.4 [+8.4, +10.4]

## S2 judges vs the generator's own confidence (selfconf)

- tev: AUROC difference 0.134 [0.086, 0.183]; judge:tev->reroute minus selfconf->reroute: accuracy +0.013 [+0.002, +0.025], token-compute +524
- llama: AUROC difference 0.036 [-0.029, 0.097]; judge:llama->reroute minus selfconf->reroute: accuracy +0.007 [-0.007, +0.020], token-compute +2007

## H3 after rejection: reroute vs resample

- judge:tev: reroute - resample +0.017 [-0.008, +0.040] (reroute better: False); hybrid - reroute +0.001 [-0.005, +0.009] (no gain > delta: True)
- judge:llama: reroute - resample +0.012 [-0.015, +0.039] (reroute better: False); hybrid - reroute +0.005 [-0.000, +0.011] (no gain > delta: True)
- judge:selfconf: reroute - resample +0.017 [-0.011, +0.042] (reroute better: False); hybrid - reroute -0.004 [-0.011, +0.004] (no gain > delta: True)
- visible: reroute - resample +0.019 [+0.002, +0.038] (reroute better: True); hybrid - reroute +0.014 [+0.007, +0.021] (no gain > delta: True)

## H4 stopping debt by difficulty (false-accept rate among wrong drafts)

- tev: hard 0.269 vs not-hard 0.172; diff 0.098 [-0.005, 0.205]; 206 wrong accepts, strong model right on those tasks 0.274; hard tasks 82
- llama: hard 0.155 vs not-hard 0.084; diff 0.071 [-0.008, 0.152]; 115 wrong accepts, strong model right on those tasks 0.277; hard tasks 82
- selfconf: hard 0.163 vs not-hard 0.093; diff 0.070 [-0.011, 0.151]; 122 wrong accepts, strong model right on those tasks 0.456; hard tasks 82

H5 (latency) is the s/task column above. Visible-test execution time is charged as 0 s and 0 token-compute.
