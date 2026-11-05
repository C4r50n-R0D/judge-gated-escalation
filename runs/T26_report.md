# Test-split results (371 tasks; excluded 0; rows {'rows': 10759, 'error_rows': 0, 'unscored_rows': 0, 'tasks_seen': 371}; coverage {'expected': 371, 'usable': 371, 'missing': 0, 'missing_frac': 0.0})

Frozen thresholds: {'tev': 0.8619849230515471, 'llama': 0.4667895416652746, 'selfconf': 0.9602630454757016}. Non-inferiority margin delta = 0.03. Primary judge: tev. Cost metric for the cheapest tau and H2 savings: tok.

## Controllers (mean [95% cluster-bootstrap CI])

| controller | accuracy | USD/task | s/task | token-compute/task (B-param x tokens) | tasks |
|---|---|---|---|---|---|
| local-only | 0.629 [0.589, 0.671] | 0.00000 [0.00000, 0.00000] | 3.2 [3.0, 3.4] | 761 [731, 792] | 371 |
| strong-only | 0.751 [0.710, 0.790] | 0.00000 [0.00000, 0.00000] | 16.8 [15.8, 18.0] | 3749 [3604, 3908] | 371 |
| visible->reroute | 0.765 [0.727, 0.804] | 0.00000 [0.00000, 0.00000] | 8.4 [7.3, 9.5] | 1821 [1635, 2006] | 371 |
| visible->resample(3) | 0.714 [0.673, 0.756] | 0.00000 [0.00000, 0.00000] | 4.9 [4.4, 5.5] | 1125 [1041, 1207] | 371 |
| visible->resample(3)->reroute | 0.778 [0.739, 0.816] | 0.00000 [0.00000, 0.00000] | 8.1 [6.9, 9.5] | 1766 [1531, 2004] | 371 |
| oracle->reroute | 0.802 [0.765, 0.838] | 0.00000 [0.00000, 0.00000] | 10.1 [8.9, 11.2] | 2188 [1993, 2388] | 371 |
| oracle->resample(3) | 0.745 [0.705, 0.784] | 0.00000 [0.00000, 0.00000] | 5.6 [5.1, 6.2] | 1274 [1183, 1365] | 371 |
| oracle->resample(3)->reroute | 0.834 [0.799, 0.869] | 0.00000 [0.00000, 0.00000] | 10.5 [9.1, 12.1] | 2280 [2010, 2556] | 371 |
| judge:tev->reroute | 0.748 [0.707, 0.786] | 0.00000 [0.00000, 0.00000] | 12.4 [11.3, 13.6] | 3866 [3661, 4087] | 371 |
| judge:tev->resample(3) | 0.685 [0.642, 0.727] | 0.00000 [0.00000, 0.00000] | 8.6 [8.0, 9.3] | 3925 [3705, 4166] | 371 |
| judge:tev->resample(3)->reroute | 0.752 [0.711, 0.790] | 0.00000 [0.00000, 0.00000] | 14.2 [12.7, 15.9] | 5148 [4754, 5547] | 371 |
| judge:llama->reroute | 0.742 [0.702, 0.780] | 0.00000 [0.00000, 0.00000] | 18.0 [16.7, 19.5] | 5321 [5017, 5632] | 371 |
| judge:llama->resample(3) | 0.665 [0.622, 0.707] | 0.00000 [0.00000, 0.00000] | 11.9 [11.1, 12.8] | 6078 [5688, 6488] | 371 |
| judge:llama->resample(3)->reroute | 0.737 [0.696, 0.776] | 0.00000 [0.00000, 0.00000] | 23.2 [21.2, 25.4] | 8463 [7859, 9100] | 371 |
| judge:selfconf->reroute | 0.748 [0.707, 0.786] | 0.00000 [0.00000, 0.00000] | 16.6 [15.5, 17.7] | 3779 [3620, 3935] | 371 |
| judge:selfconf->resample(3) | 0.662 [0.619, 0.705] | 0.00000 [0.00000, 0.00000] | 8.0 [7.5, 8.5] | 1926 [1853, 1997] | 371 |
| judge:selfconf->resample(3)->reroute | 0.747 [0.707, 0.784] | 0.00000 [0.00000, 0.00000] | 19.4 [18.1, 20.8] | 4531 [4316, 4732] | 371 |

## H1 judge discrimination (AUROC vs hidden-test correctness of local drafts)

- tev: AUROC 0.813 [0.779, 0.846]; correct 1870, wrong 1098; supported: True; within-task AUROC 0.801 [0.752, 0.848] over 150 tasks; unjudged drafts (counted as rejections) 0
- llama: AUROC 0.688 [0.647, 0.731]; correct 1870, wrong 1098; supported: True; within-task AUROC 0.666 [0.612, 0.716] over 150 tasks; unjudged drafts (counted as rejections) 0
- selfconf: AUROC 0.680 [0.638, 0.721]; correct 1870, wrong 1098; supported: True; within-task AUROC 0.637 [0.590, 0.687] over 150 tasks; unjudged drafts (counted as rejections) 0

## H2 gate->reroute vs strong-only (paired differences)

- judge:tev: accuracy -0.003 [-0.019, +0.013], USD +0.00000 [+0.00000, +0.00000], seconds -4.4, token-compute +117; non-inferior True, cheaper False, supported False
- judge:llama: accuracy -0.009 [-0.021, +0.002], USD +0.00000 [+0.00000, +0.00000], seconds +1.2, token-compute +1573; non-inferior True, cheaper False, supported False
- judge:selfconf: accuracy -0.003 [-0.010, +0.003], USD +0.00000 [+0.00000, +0.00000], seconds -0.3, token-compute +31; non-inferior True, cheaper False, supported False
- visible: accuracy +0.014 [-0.006, +0.034], USD +0.00000 [+0.00000, +0.00000], seconds -8.4, token-compute -1928; non-inferior True, cheaper True, supported True
- oracle: accuracy +0.051 [+0.038, +0.067], USD +0.00000 [+0.00000, +0.00000], seconds -6.8, token-compute -1561; non-inferior True, cheaper True, supported True
- sensitivity (two-stage bootstrap, primary judge, accuracy diff): [-0.022, +0.014]

## S1 what the primary judge adds: gate->reroute vs local-only (read H2 together with this)

- accuracy +0.118 [+0.091, +0.146], token-compute +3104 [+2914, +3303], seconds +9.2 [+8.2, +10.2]

## S2 judges vs the generator's own confidence (selfconf)

- tev: AUROC difference 0.133 [0.092, 0.171]; judge:tev->reroute minus selfconf->reroute: accuracy -0.000 [-0.014, +0.014], token-compute +86
- llama: AUROC difference 0.008 [-0.052, 0.064]; judge:llama->reroute minus selfconf->reroute: accuracy -0.006 [-0.018, +0.006], token-compute +1542

## H3 after rejection: reroute vs resample

- judge:tev: reroute - resample +0.063 [+0.037, +0.090] (reroute better: True); hybrid - reroute +0.005 [-0.003, +0.012] (no gain > delta: True)
- judge:llama: reroute - resample +0.077 [+0.047, +0.108] (reroute better: True); hybrid - reroute -0.005 [-0.013, +0.003] (no gain > delta: True)
- judge:selfconf: reroute - resample +0.086 [+0.053, +0.118] (reroute better: True); hybrid - reroute -0.001 [-0.006, +0.005] (no gain > delta: True)
- visible: reroute - resample +0.051 [+0.028, +0.075] (reroute better: True); hybrid - reroute +0.013 [+0.004, +0.022] (no gain > delta: True)

## H4 stopping debt by difficulty (false-accept rate among wrong drafts)

- tev: hard 0.243 vs not-hard 0.219; diff 0.025 [-0.073, 0.125]; 260 wrong accepts, strong model right on those tasks 0.381; hard tasks 106
- llama: hard 0.162 vs not-hard 0.104; diff 0.058 [-0.017, 0.129]; 161 wrong accepts, strong model right on those tasks 0.409; hard tasks 106
- selfconf: hard 0.060 vs not-hard 0.057; diff 0.003 [-0.055, 0.056]; 65 wrong accepts, strong model right on those tasks 0.412; hard tasks 106

H5 (latency) is the s/task column above. Visible-test execution time is charged as 0 s and 0 token-compute.
