# E14a result: calibration and drift of the frozen taus (stored-data shifts)

Exploratory and post-hoc (PREREG v2 section 11). Spec and predictions: commit 29509b3, before the run. Script
ext/E14/e14.py; full tables in ext/E14/out/summary.md and results.json. No model calls; 3.5 min on the homelab.
2,000 task-cluster bootstrap resamples; generator comparisons paired over the same test tasks. Effect sizes only.

## Main findings
1. **tev's frozen tau transfers across generators.** On test drafts its acceptance rate stays within 5 points of the
   3B's (1.5B 0.474, 3B 0.523, 7B 0.521, 14B 0.545), and its false-accept rate stays at 0.21 to 0.25. Accepted-set accuracy
   follows the generator's own pass rate: 0.808 (1.5B), 0.832 (3B), 0.867 (7B, +3.4 [+0.9, +6.0] vs 3B), 0.885 (14B).
2. **selfconf's tau does not transfer.** Bigger generators are more confident: at the same frozen tau selfconf accepts 7%
   of 1.5B drafts, 15% of 3B drafts and 53% of 14B drafts (14B minus 3B +38 points [+35, +42]); its false-accept rate on
   14B drafts is 0.35 vs 0.06 on 3B drafts.
3. **The largest shift is the benchmark suite, not the generator or the split.** On test 3B drafts, tev accepts 76% of
   HumanEval+ drafts vs 42% of MBPP+ (+34 points [+26, +42]); its accepted-set accuracy is 9 points higher on HumanEval+
   [+1, +17]. selfconf accepts 47% of HumanEval+ drafts and 0.8% of MBPP+ drafts: at its frozen tau it is in effect a
   suite detector. This bears on how the T26 selfconf controller made its decisions.
4. **Recalibration fitted on calibration 3B drafts fixes calibration on test 3B drafts.** Test 3B ECE: tev 0.129 raw ->
   0.058 Platt / 0.059 isotonic; llama 0.307 -> 0.080 / 0.081; selfconf 0.244 -> 0.066 / 0.063. AUROC is unchanged by
   construction (monotone maps). The fits carry over to 7B and 14B drafts (ECE 0.02 to 0.06 for tev and llama) but less
   well to 1.5B drafts (llama 0.151, selfconf 0.122, tev 0.073).
5. **No clear drift over the run.** Q5 minus Q1 in accepted-set accuracy: tev +0.049 [-0.072, +0.171]; CIs include 0 for
   every judge and metric. Quintiles are also different task sets, so this cannot separate time from task mix.
6. **The label-free CUSUM monitor, as specced, is not usable for tev or llama.** On streams of test 3B drafts only, the
   accept-rate monitor false-alarms in 29% (tev) and 69% (llama) of 1,000-draft streams, against the 5% it was tuned for
   on calibration drafts: it reacts to the cal-to-test task-mix change. It catches a switch to 1.5B drafts (tev 88%,
   median delay 249 drafts) but rarely a switch to 7B or 14B (tev 24% and 7%), because tev's acceptance rate barely
   moves (finding 1). For selfconf the accept-rate monitor works (4% false alarms; 97 to 99% detection), because selfconf
   is itself generator-sensitive. The "accepted but fails the visible tests" signal almost never false-alarms but detects
   only selfconf's switch to 14B (86%).

## Predictions (written before the run) vs outcome
1. Recalibration brings llama and selfconf test ECE below 0.10: **held** (0.08, 0.06). tev's recalibrated ECE within
   0.05 of raw: **did not hold** (0.129 -> 0.058; recalibration helped tev more than predicted).
2. tev on 1.5B: acceptance at least 10 points lower: **did not hold** (-4.9); accepted-set accuracy 0 to 8 lower: held
   (-2.4, CI includes 0). On 7B: acceptance at least 3 points higher: **did not hold** (-0.2); accepted-set accuracy
   within 3 points: **did not hold** (+3.4). 14B acceptance above 7B: held (point estimate only).
3. Isotonic ECE higher on 1.5B than on 3B for all three judges: **held** (tev only by +0.014, CI includes 0).
4. tev false-accept higher on 7B and 14B than on 3B: direction held, size about 0 (+0.006, +0.015; CIs include 0).
5. tev accepted-set accuracy, HumanEval+ minus MBPP+ CI includes 0: **did not hold** (+0.092 [+0.011, +0.172]);
   Q5 minus Q1 CI includes 0: held.
6. tev monitor: false alarms at most 0.15: **did not hold** (0.29); 1.5B detected at least 80%: held (88%), with median
   delay at most 150: **did not hold** (249); 7B detected less often than 1.5B: held.
Two predictions held in full, four held in part or not at all.

## Caveats
- Calibration-split ECE after recalibration is in-sample (isotonic is 0.000 there by construction). The test-split
  numbers are the out-of-sample ones.
- ECE is biased upward in small resamples, so bootstrap CIs for ECE differences are skewed. Read them as rough.
- Monitor streams are drawn with replacement from each condition's pool and ignore task order.
- Time quintiles are confounded with task identity.

## What it means for the study
- For tev, the frozen threshold is robust to swapping the generator. Gating 7B or 14B drafts with it costs nothing in
  accepted-set accuracy. Its weak spot is the task distribution: it is much more permissive on HumanEval+ than on MBPP+.
- selfconf thresholds have to be refit per generator and per suite. Its T26 accept decisions mostly reflect which suite
  a task came from.
- Recalibration is cheap and works within a generator. It does not change any gate decision, because gates threshold
  on ranks.
- A drift monitor on acceptance rate flags harmless task-mix changes and misses generator swaps for the most robust
  judge. A useful monitor needs a few labelled checks, which E14b can test.
