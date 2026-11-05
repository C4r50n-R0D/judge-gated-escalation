# Test-split results (371 tasks; excluded 0; rows {'rows': 10759, 'error_rows': 0, 'unscored_rows': 0, 'tasks_seen': 371}; coverage {'expected': 371, 'usable': 371, 'missing': 0, 'missing_frac': 0.0})

Frozen thresholds: {'tev': 0.8619849230515471, 'llama': 0.4667895416652746, 'selfconf': 0.9602630454757016}. Non-inferiority margin delta = 0.03. Primary judge: tev. Cost metric for the cheapest tau and H2 savings: tok.

## Controllers (mean [95% cluster-bootstrap CI])

| controller | accuracy | USD/task | s/task | token-compute/task (B-param x tokens) | tasks |
|---|---|---|---|---|---|
| local-only | 0.561 [0.520, 0.603] | 0.00000 [0.00000, 0.00000] | 1.5 [1.4, 1.6] | 338 [324, 352] | 371 |
| strong-only | 0.751 [0.710, 0.790] | 0.00000 [0.00000, 0.00000] | 16.8 [15.8, 18.0] | 3749 [3604, 3908] | 371 |
| visible->reroute | 0.769 [0.730, 0.805] | 0.00000 [0.00000, 0.00000] | 8.8 [7.7, 10.0] | 1836 [1640, 2031] | 371 |
| visible->resample(3) | 0.667 [0.624, 0.712] | 0.00000 [0.00000, 0.00000] | 2.5 [2.3, 2.8] | 566 [526, 608] | 371 |
| visible->resample(3)->reroute | 0.775 [0.736, 0.812] | 0.00000 [0.00000, 0.00000] | 7.2 [6.0, 8.4] | 1497 [1281, 1714] | 371 |
| oracle->reroute | 0.798 [0.760, 0.835] | 0.00000 [0.00000, 0.00000] | 10.0 [8.8, 11.2] | 2103 [1896, 2300] | 371 |
| oracle->resample(3) | 0.689 [0.646, 0.735] | 0.00000 [0.00000, 0.00000] | 2.8 [2.5, 3.0] | 616 [573, 658] | 371 |
| oracle->resample(3)->reroute | 0.822 [0.786, 0.859] | 0.00000 [0.00000, 0.00000] | 8.9 [7.6, 10.2] | 1860 [1623, 2095] | 371 |
| judge:tev->reroute | 0.734 [0.695, 0.771] | 0.00000 [0.00000, 0.00000] | 11.9 [10.8, 13.1] | 3616 [3404, 3826] | 371 |
| judge:tev->resample(3) | 0.631 [0.588, 0.678] | 0.00000 [0.00000, 0.00000] | 5.5 [5.1, 5.8] | 3183 [3007, 3365] | 371 |
| judge:tev->resample(3)->reroute | 0.722 [0.682, 0.761] | 0.00000 [0.00000, 0.00000] | 12.0 [10.7, 13.4] | 4585 [4237, 4957] | 371 |
| judge:llama->reroute | 0.731 [0.691, 0.769] | 0.00000 [0.00000, 0.00000] | 15.9 [14.6, 17.3] | 4721 [4432, 5024] | 371 |
| judge:llama->resample(3) | 0.594 [0.552, 0.640] | 0.00000 [0.00000, 0.00000] | 6.6 [6.1, 7.1] | 4634 [4307, 4969] | 371 |
| judge:llama->resample(3)->reroute | 0.713 [0.672, 0.751] | 0.00000 [0.00000, 0.00000] | 17.8 [16.1, 19.5] | 6970 [6426, 7535] | 371 |
| judge:selfconf->reroute | 0.747 [0.706, 0.786] | 0.00000 [0.00000, 0.00000] | 16.7 [15.6, 17.8] | 3750 [3594, 3905] | 371 |
| judge:selfconf->resample(3) | 0.596 [0.551, 0.642] | 0.00000 [0.00000, 0.00000] | 4.0 [3.8, 4.2] | 933 [895, 970] | 371 |
| judge:selfconf->resample(3)->reroute | 0.739 [0.700, 0.779] | 0.00000 [0.00000, 0.00000] | 17.9 [16.7, 19.1] | 4070 [3868, 4253] | 371 |

## H1 judge discrimination (AUROC vs hidden-test correctness of local drafts)

- tev: AUROC 0.826 [0.794, 0.856]; correct 1661, wrong 1307; supported: True; within-task AUROC 0.825 [0.782, 0.869] over 175 tasks; unjudged drafts (counted as rejections) 0
- llama: AUROC 0.718 [0.680, 0.756]; correct 1661, wrong 1307; supported: True; within-task AUROC 0.668 [0.619, 0.715] over 175 tasks; unjudged drafts (counted as rejections) 0
- selfconf: AUROC 0.695 [0.662, 0.728]; correct 1661, wrong 1307; supported: True; within-task AUROC 0.659 [0.616, 0.702] over 175 tasks; unjudged drafts (counted as rejections) 0

## H2 gate->reroute vs strong-only (paired differences)

- judge:tev: accuracy -0.017 [-0.035, +0.001], USD +0.00000 [+0.00000, +0.00000], seconds -4.9, token-compute -132; non-inferior False, cheaper False, supported False
- judge:llama: accuracy -0.020 [-0.034, -0.008], USD +0.00000 [+0.00000, +0.00000], seconds -0.9, token-compute +972; non-inferior False, cheaper False, supported False
- judge:selfconf: accuracy -0.004 [-0.009, +0.000], USD +0.00000 [+0.00000, +0.00000], seconds -0.1, token-compute +2; non-inferior True, cheaper False, supported False
- visible: accuracy +0.018 [-0.001, +0.036], USD +0.00000 [+0.00000, +0.00000], seconds -8.0, token-compute -1912; non-inferior True, cheaper True, supported True
- oracle: accuracy +0.047 [+0.034, +0.063], USD +0.00000 [+0.00000, +0.00000], seconds -6.8, token-compute -1645; non-inferior True, cheaper True, supported True

## S1 what the primary judge adds: gate->reroute vs local-only (read H2 together with this)

- accuracy +0.173 [+0.142, +0.205], token-compute +3278 [+3072, +3481], seconds +10.5 [+9.4, +11.5]

## S2 judges vs the generator's own confidence (selfconf)

- tev: AUROC difference 0.131 [0.095, 0.167]; judge:tev->reroute minus selfconf->reroute: accuracy -0.013 [-0.029, +0.004], token-compute -134
- llama: AUROC difference 0.023 [-0.025, 0.070]; judge:llama->reroute minus selfconf->reroute: accuracy -0.016 [-0.030, -0.004], token-compute +970

## H3 after rejection: reroute vs resample

- judge:tev: reroute - resample +0.103 [+0.071, +0.134] (reroute better: True); hybrid - reroute -0.012 [-0.022, -0.002] (no gain > delta: True)
- judge:llama: reroute - resample +0.136 [+0.100, +0.169] (reroute better: True); hybrid - reroute -0.018 [-0.027, -0.008] (no gain > delta: True)
- judge:selfconf: reroute - resample +0.151 [+0.112, +0.191] (reroute better: True); hybrid - reroute -0.007 [-0.014, -0.001] (no gain > delta: True)
- visible: reroute - resample +0.102 [+0.075, +0.131] (reroute better: True); hybrid - reroute +0.006 [-0.001, +0.014] (no gain > delta: True)

## H4 stopping debt by difficulty (false-accept rate among wrong drafts)

- tev: hard 0.194 vs not-hard 0.245; diff -0.051 [-0.139, 0.035]; 270 wrong accepts, strong model right on those tasks 0.496; hard tasks 130
- llama: hard 0.159 vs not-hard 0.171; diff -0.011 [-0.085, 0.064]; 212 wrong accepts, strong model right on those tasks 0.482; hard tasks 130
- selfconf: hard 0.025 vs not-hard 0.037; diff -0.012 [-0.047, 0.021]; 37 wrong accepts, strong model right on those tasks 0.573; hard tasks 130

H5 (latency) is the s/task column above. Visible-test execution time is charged as 0 s and 0 token-compute.
