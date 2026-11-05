# E14b result: frozen taus, recalibration and the drift monitor under the E3 to E6 shifts

Exploratory and post-hoc (PREREG v2 section 11). Spec and predictions: commit bfcbe65, before any E6 number was seen
and before the script ran. Script ext/E14b/e14b.py; full tables in ext/E14b/out/summary.md and results.json. Stored
labels only (no model calls). Every condition is gated at the BASE judge's frozen tau (tev 0.862, llama 0.467), as a
deployment that did not know about the shift would be. Recalibration maps fitted on 1,368 calibration 3B drafts.
Task-cluster bootstrap, 1,000 resamples; effect sizes only. Numbers are test split unless noted.

Note: differences here are against "subset clean" (all local3b drafts of E3's subset, reps 0 to 7), not paired with
the same drafts as in E6, so E6 numbers differ slightly from ext/E6/RESULT.md (tev pooled false-accept +8.1 here vs
+7.2 there).

## Main findings
1. **tev's frozen tau holds up under every shift except bugs and injection.** Accepted-set accuracy stays within 2
   points of subset clean (0.816) under all six paraphrases and all four rewrites (largest p3, -1.9 [-3.9, -0.2]).
   Acceptance moves (p1 +6.5, codeonly -27.5) but mostly by trading false rejects for false accepts.
2. **Injection is the shift that hurts tev's gate most.** Pooled payloads: false-accept +8.1 points [+0.8, +16.0],
   accepted-set accuracy -3.2 [-7.7, +0.8]; role_tags -5.5 [-11.3, -0.1]. The sanitizer brings it back to +2.9 and
   -2.1, both CIs including 0.
3. **llama's frozen tau does not survive prompt changes or injection.** False-accept rises +32.2 (p1), +29.3 (p3),
   +43.5 (crit); +16.2 pooled injection, +63.3 hidden_chars, +53.6 role_tags. Accepted-set accuracy falls by up to
   12.8 points (hidden_chars, [-23.7, -2.0]).
4. **Recalibration helps tev and not llama.** tev's isotonic ECE stays 0.04 to 0.14 under every non-bug shift. llama's
   rises from 0.065 to about 0.19 to 0.25 under p1, p3, crit, direct, role_tags and hidden_chars. Both maps fail on
   mutants (ECE 0.35 tev, 0.55 llama): an all-wrong stream cannot be calibrated by a map fit on mixed drafts.
5. **The label-free monitor catches big shifts but misses the dangerous ones for tev.** For tev it detects codeonly,
   codefirst, mutants, string, identifier and multilingual payloads in 96 to 99% of streams, but pooled injection in
   only 47% and role_tags in 17%, although role_tags raises false accepts by about 11 points. For llama it detects
   most shifts (pooled injection 93%), but with 39% false alarms on clean streams, so its alarms carry little
   information.
6. **Calibration split agrees in direction** where checked (paraphrases p1 and p3, rename_locals, verbose_comments, pooled injection; 50 tasks, wider CIs).

## Predictions (written before running the script) vs outcome
1. tev accepted-set accuracy within 3 points under every paraphrase and rewrite: **held** (largest 1.9).
2. llama isotonic ECE >= 0.10 for at least three of p1 to p6: **held** (p1 0.201, p3 0.190, p6 0.103). tev isotonic ECE
   <= 0.10 under every paraphrase and rewrite: **did not hold** for p1 (0.113); held for the other nine.
3. Monitor detects llama under verbose_comments in >= 80% of streams: **held** (92%). Detects tev under any single E4
   rewrite in <= 30%: **did not hold** for rename_locals (50%); held for the other three.
4. False alarms on clean streams <= 0.15 for both judges: **held for tev** (0.09), **not for llama** (0.39).
5. Monitor on pooled injection: tev below half, llama above half: **held** (47%, 93%).
Two held in full, three in part.

## Caveats
- The monitor's threshold h was set for 5% false alarms over 1,000 reference drafts from the calibration split; the
  test subset's clean accept rate differs (llama 0.261 vs reference 0.231), which drives llama's 39% false alarms. A monitor fit on the
  stream's own warm-up would behave differently.
- 100 test tasks; acceptance and accuracy CIs are several points wide.
- Each shift is applied to every draft at once. Real shifts are gradual or partial; detection would be slower.
- Mutants are all wrong drafts, so accepted-set accuracy and calibration are degenerate for that condition.

## What it means for the study
- A tev gate keeps its accepted-set accuracy under ordinary prompt and code-style changes. An injected payload is the
  one shift that both lowers that accuracy and evades the accept-rate monitor.
- A llama-style logprob gate needs re-fitting whenever its prompt or the generator's style changes, and a simple
  accept-rate monitor cannot reliably tell it when.
- Visible tests have none of these problems: their verdicts do not depend on prompt, style or injected text.
