# PREREG section 11 sensitivity: other local/strong pairs

Exploratory. runs/sensitivity/pairs.py derives a thresholds file per pair from thresholds.json (local tier and that
pair's calibration-data hash replaced; strong14b, delta, k, seed, cost metric, primary judge unchanged) and runs the
unchanged `controllers.py test` on runs/confirmatory.labeled.jsonl (371 test tasks, 2,000 resamples). Two tau modes:
transfer (the frozen 3B taus) and refit (taus from `controllers.py calibrate` on that pair's calibration split, same
rule). First attempt failed (pairs.py did not pass --primary-judge); fixed in pairs.py only and rerun 2026-10-29.
Full reports: runs/sensitivity/<local>.<mode>.md.

| pair, taus | H1 AUROC tev / llama / selfconf | H2 tev->reroute vs strong: acc, token-compute | visible->reroute vs strong | H3 tev reroute - resample |
|---|---|---|---|---|
| 3B, frozen (T26) | all supported | -0.003 [-0.019, +0.013], +117: not supported | supported | +0.063 [+0.037, +0.090]: supported |
| 7B, transfer | 0.779 / 0.681 / 0.645 | +0.008 [-0.006, +0.022], +1148: not supported | +0.035, -1174: supported | +0.017 [-0.008, +0.040]: not supported |
| 7B, refit | same | +0.008 [-0.007, +0.023], +1072: not supported | same | +0.017 [-0.007, +0.039]: not supported |
| 1.5B, transfer | 0.826 / 0.718 / 0.695 | -0.017 [-0.035, +0.001], -132: not non-inferior | +0.018 [-0.001, +0.036], -1912: supported | +0.103 [+0.071, +0.134]: supported |
| 1.5B, refit | same | -0.008 [-0.021, +0.004], +334: not supported | same | +0.105 [+0.069, +0.137]: supported |

- H1 holds for every judge in every pair. H2 fails for every judge in every pair and both tau modes: judge gates are
  non-inferior (except 1.5B with transferred taus, tev and llama) but never cheaper than strong-only. The visible gate
  passes both parts in every pair.
- H3 depends on the gap: with 7B drafts resampling is almost as good as rerouting (no CI excludes 0 for judge gates;
  visible +0.019 [+0.002, +0.038]); with 1.5B drafts rerouting wins by 10 to 15 points for every gate.
- H4 is not supported in any pair; for 1.5B the false-accept rate is if anything lower on hard tasks.
- Refitting taus changes little; the conclusions do not depend on which local model is gated.
