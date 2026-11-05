# Test-split results (371 tasks; excluded 0; rows {'rows': 10759, 'error_rows': 0, 'unscored_rows': 0, 'tasks_seen': 371}; coverage {'expected': 371, 'usable': 371, 'missing': 0, 'missing_frac': 0.0})

Frozen thresholds: {'tev': 0.9212951287233725, 'llama': 0.6837422139643745, 'selfconf': 0.9642530018765577}. Non-inferiority margin delta = 0.03. Primary judge: tev. Cost metric for the cheapest tau and H2 savings: tok.

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
| judge:tev->reroute | 0.743 [0.701, 0.781] | 0.00000 [0.00000, 0.00000] | 14.0 [12.8, 15.2] | 4083 [3869, 4303] | 371 |
| judge:tev->resample(3) | 0.638 [0.595, 0.684] | 0.00000 [0.00000, 0.00000] | 6.2 [5.9, 6.6] | 3619 [3437, 3806] | 371 |
| judge:tev->resample(3)->reroute | 0.736 [0.695, 0.775] | 0.00000 [0.00000, 0.00000] | 15.1 [13.7, 16.6] | 5551 [5187, 5926] | 371 |
| judge:llama->reroute | 0.748 [0.708, 0.787] | 0.00000 [0.00000, 0.00000] | 18.5 [17.2, 19.8] | 5347 [5085, 5618] | 371 |
| judge:llama->resample(3) | 0.597 [0.553, 0.642] | 0.00000 [0.00000, 0.00000] | 7.6 [7.1, 8.0] | 5329 [5029, 5646] | 371 |
| judge:llama->resample(3)->reroute | 0.749 [0.708, 0.788] | 0.00000 [0.00000, 0.00000] | 22.5 [20.9, 24.2] | 8557 [8067, 9071] | 371 |
| judge:selfconf->reroute | 0.748 [0.708, 0.788] | 0.00000 [0.00000, 0.00000] | 17.0 [15.9, 18.1] | 3802 [3641, 3955] | 371 |
| judge:selfconf->resample(3) | 0.596 [0.551, 0.642] | 0.00000 [0.00000, 0.00000] | 4.1 [3.8, 4.3] | 945 [907, 982] | 371 |
| judge:selfconf->resample(3)->reroute | 0.744 [0.704, 0.783] | 0.00000 [0.00000, 0.00000] | 18.4 [17.2, 19.7] | 4167 [3970, 4351] | 371 |

## H1 judge discrimination (AUROC vs hidden-test correctness of local drafts)

- tev: AUROC 0.826 [0.794, 0.856]; correct 1661, wrong 1307; supported: True; within-task AUROC 0.825 [0.782, 0.869] over 175 tasks; unjudged drafts (counted as rejections) 0
- llama: AUROC 0.718 [0.680, 0.756]; correct 1661, wrong 1307; supported: True; within-task AUROC 0.668 [0.619, 0.715] over 175 tasks; unjudged drafts (counted as rejections) 0
- selfconf: AUROC 0.695 [0.662, 0.728]; correct 1661, wrong 1307; supported: True; within-task AUROC 0.659 [0.616, 0.702] over 175 tasks; unjudged drafts (counted as rejections) 0

## H2 gate->reroute vs strong-only (paired differences)

- judge:tev: accuracy -0.008 [-0.021, +0.004], USD +0.00000 [+0.00000, +0.00000], seconds -2.9, token-compute +334; non-inferior True, cheaper False, supported False
- judge:llama: accuracy -0.003 [-0.009, +0.003], USD +0.00000 [+0.00000, +0.00000], seconds +1.6, token-compute +1599; non-inferior True, cheaper False, supported False
- judge:selfconf: accuracy -0.003 [-0.007, +0.001], USD +0.00000 [+0.00000, +0.00000], seconds +0.1, token-compute +54; non-inferior True, cheaper False, supported False
- visible: accuracy +0.018 [-0.001, +0.036], USD +0.00000 [+0.00000, +0.00000], seconds -8.0, token-compute -1912; non-inferior True, cheaper True, supported True
- oracle: accuracy +0.047 [+0.034, +0.063], USD +0.00000 [+0.00000, +0.00000], seconds -6.8, token-compute -1645; non-inferior True, cheaper True, supported True

## S1 what the primary judge adds: gate->reroute vs local-only (read H2 together with this)

- accuracy +0.182 [+0.148, +0.215], token-compute +3745 [+3538, +3959], seconds +12.5 [+11.4, +13.7]

## S2 judges vs the generator's own confidence (selfconf)

- tev: AUROC difference 0.131 [0.095, 0.167]; judge:tev->reroute minus selfconf->reroute: accuracy -0.006 [-0.018, +0.006], token-compute +281
- llama: AUROC difference 0.023 [-0.025, 0.070]; judge:llama->reroute minus selfconf->reroute: accuracy +0.000 [-0.007, +0.007], token-compute +1545

## H3 after rejection: reroute vs resample

- judge:tev: reroute - resample +0.105 [+0.069, +0.137] (reroute better: True); hybrid - reroute -0.007 [-0.015, +0.002] (no gain > delta: True)
- judge:llama: reroute - resample +0.152 [+0.114, +0.188] (reroute better: True); hybrid - reroute +0.000 [-0.005, +0.006] (no gain > delta: True)
- judge:selfconf: reroute - resample +0.152 [+0.112, +0.192] (reroute better: True); hybrid - reroute -0.004 [-0.010, +0.001] (no gain > delta: True)
- visible: reroute - resample +0.102 [+0.075, +0.131] (reroute better: True); hybrid - reroute +0.006 [-0.001, +0.014] (no gain > delta: True)

## H4 stopping debt by difficulty (false-accept rate among wrong drafts)

- tev: hard 0.109 vs not-hard 0.118; diff -0.009 [-0.079, 0.056]; 145 wrong accepts, strong model right on those tasks 0.531; hard tasks 130
- llama: hard 0.044 vs not-hard 0.034; diff 0.009 [-0.028, 0.047]; 54 wrong accepts, strong model right on those tasks 0.381; hard tasks 130
- selfconf: hard 0.019 vs not-hard 0.028; diff -0.009 [-0.040, 0.021]; 28 wrong accepts, strong model right on those tasks 0.543; hard tasks 130

H5 (latency) is the s/task column above. Visible-test execution time is charged as 0 s and 0 token-compute.
