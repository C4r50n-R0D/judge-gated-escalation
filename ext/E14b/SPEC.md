# E14b: Frozen taus, recalibration and the drift monitor under the E3 to E6 shifts

Status: SPEC (exploratory by rule, PREREG v2 section 11). Written 2026-10-29 after E3, E4 and E5 results were read and
before any E6 label was seen. Second half of E14 (E14a: shifts already in the confirmatory data).

## Question
When the judge's prompt, the code's surface, the kind of bug, or injected text shifts, what happens at the frozen tau
to acceptance, accepted-set accuracy and false accepts; do the Platt and isotonic maps fitted on calibration 3B drafts
still calibrate; and does E14a's label-free accept-rate monitor notice the shift?

## Manipulation (no model calls)
Conditions, all on the E3 subset's local3b drafts and gated with the BASE judge's frozen tau (a deployment would not
know the shift happened): subset clean (reference for paired differences); E3 prompt variants p1 to p6, codeonly,
codefirst, nocrit (tev) / crit (llama); E4 strip_comments, reformat, rename_locals, verbose_comments; E5 mutants
pooled (all wrong); E6 each payload, payloads pooled, and each defense (clean and injected drafts together).
Recalibration maps: fitted on runs/confirmatory.labeled.jsonl calibration 3B drafts (as E14a). Monitor: E14a's
two-sided Bernoulli CUSUM on the accept indicator (k 0.05, h for 5% false alarms over 1,000 reference drafts);
streams of 300 subset-clean test drafts then 700 shifted ones, 400 streams.

## Outcomes
Per condition, judge and split: acceptance rate, accepted-set accuracy, false-accept and false-reject rates at the
frozen tau, ECE raw / Platt / isotonic; paired differences against subset clean. Monitor: detection rate within 700
drafts, median delay, early alarms; false-alarm rate on subset-clean streams.

## Analysis
ext/E14b/e14b.py. Task-cluster bootstrap, 1,000 resamples. Effect sizes and CIs only. Test split primary.

## Already seen before writing this (so not predicted)
E3 accept rates and decision flips per prompt variant; E4 mean dp, flips and accept rates per rewrite; E5 detection
rates. Not yet seen: accepted-set accuracy, ECE (raw or recalibrated) and the monitor under any of these shifts; all E6
numbers.

## Predictions (written before running the script)
1. tev's accepted-set accuracy at its frozen tau stays within 3 points of subset clean under every E3 paraphrase
   (p1 to p6) and every E4 rewrite.
2. The isotonic map does not survive llama's prompt changes: llama's isotonic ECE is at least 0.10 for at least three
   of p1 to p6. For tev, isotonic ECE stays at most 0.10 under every E3 paraphrase and every E4 rewrite.
3. The monitor detects llama under verbose_comments in at least 80% of streams within 700 drafts, and detects tev
   under any single E4 rewrite in at most 30% of streams.
4. The monitor's false-alarm rate on subset-clean streams is at most 0.15 for both judges.
5. E6: the monitor on tev detects the pooled injection condition in fewer than half of the streams; for llama it
   detects it in more than half.

## Planned size and estimated hours
Stored labels only; homelab CPU, about 1 hour (stdlib bootstrap). Runs after E6 completes; the pilot (200 resamples)
can run before, with empty E6 conditions.

## Comparisons counted in ext/COMPARISONS.md
(listed in spec.json)
