# E3 result: prompt sensitivity of the tev and llama judges

Exploratory and post-hoc (PREREG v2 section 11). Spec and predictions: commit 8bc11db, before any E3 label. Scripts
tools/judge_eval.py and ext/E3/analyze.py; full tables in ext/E3/out/e3.md, ext/E3/out_eval/judges.md and the .json
files beside them. Subset: 100 test + 50 calibration tasks (seed 20261026), all 3B drafts (1,200 draws, 999 distinct
codes). 18 variants x 999 labels on the Mac, 0 unparseable votes, about 7.5 h. Task-cluster bootstrap; effect sizes only.

Data note: 5 tev_nocrit labels (test split) failed with network timeouts to the Mac and were left unjudged. analyze.py
uses only drafts labeled by every variant, so those 5 drafts are dropped from every e3.md comparison; judge_eval.py
(judges.md) uses each judge's own labels. Not rerun.

## Main findings
1. **Rewording the question barely moves ranking quality.** tev AUROC across base + six paraphrases: 0.754 to 0.782
   (range 0.029 [0.013, 0.060]); every paraphrase minus base is within -0.026 [-0.052, +0.001] (p6, the "line by line"
   wording) and +0.003. llama: 0.655 to 0.695 (range 0.040 [0.020, 0.102]).
2. **Prompt choice matters much less than judge choice.** SD of AUROC across prompts minus SD across the six judge models:
   tev -0.040 [-0.073, -0.016], llama -0.036 [-0.069, -0.005]. Model SD 0.049, prompt SD 0.009 (tev) and 0.013 (llama).
3. **tev is sensitive to the order of the state fields, not just to their content.** Putting `candidate_code` before
   `task` in the state costs 0.096 AUROC [-0.161, -0.030]; dropping the task costs 0.089 [-0.162, -0.020]. Both are as
   large as the gap between tev and llama. For llama, code-first is a no-op (-0.003) and code-only costs only -0.027
   [-0.099, +0.040], suggesting llama barely uses the task text in the first place.
4. **Criteria text does nothing to ranking.** tev without criteria +0.006 [-0.007, +0.021]; llama with criteria +0.009
   [-0.019, +0.037]. For llama it fixes calibration (ECE 0.332 -> 0.075) but moves the accept rate from 26% to 75%.
5. **llama's threshold does not survive rewording; tev's mostly does.** At the frozen tau, tev's accept rate spans
   0.50 to 0.61 across paraphrases with at most 8.1% of decisions flipping. llama's accept rate spans 0.08 (p4, a
   wording that does not mention the task) to 0.69 (p1), with up to 43% of decisions flipping (49% with criteria).
   The transfer gates show the cost: llama_p1, llama_p3 and llama_crit lose 4.5 to 7.2 accuracy points vs
   visible->reroute (CIs exclude 0); no tev paraphrase loses more than 2.2.
6. **No variant changes the gate verdict.** Every judge->reroute variant, transfer or recal, costs 1,770 to 4,390 more
   token-compute than visible->reroute (1,611 on this subset) and none is more accurate.

## Predictions (written before any E3 label) vs outcome
1. tev range <= 0.04: **held** (0.029). llama range larger than tev's: **held** (0.040 vs 0.029; CIs overlap).
2. Prompt SD < model SD for both judges: **held** (CIs exclude 0 for both).
3. Code-only lowers AUROC by >= 0.05 for both: **held for tev** (-0.089), **not for llama** (-0.027).
4. Code-first changes AUROC by <= 0.02 for both: **held for llama** (-0.003), **not for tev** (-0.096).
5. Criteria: tev within 0.02 (+0.006), llama within 0.03 (+0.009): **held**.
6. tev accept-rate range >= 10 points: **held** (10.7, from 0.503 to 0.610); >= 10% decision flips for some
   paraphrase: **did not hold** (max 8.1%). The prediction was right in spirit for llama, not for tev.
7. No variant matches visible->reroute on token-compute: **held**.
Four held in full, three held in part.

## Caveats
- 100 test tasks, so AUROC CIs are about +/-0.08. The subset AUROCs (tev 0.781, llama 0.679) sit close to the full test
  split's (0.813, 0.688). Paired differences against base are much tighter than the raw CIs.
- One draw of each wording. Six paraphrases are a small sample of possible prompts; the range is a lower bound.
- Code-first for tev changes only the key order of the JSON `state`; why tev cares is unknown. tev's API may be tuned
  for task-then-artifact order.
- llama_p4 omits the task from the question, so it confounds wording with a weaker version of code-only.

## What it means for the study
- The confirmatory comparisons are not fragile to the exact judge question. tev's lead over llama holds under every
  rewording and is larger than any rewording effect.
- The input layout matters more than the wording for tev: keep task first. This is worth fixing in any deployment.
- For logprob judges like llama, a threshold is tied to its exact prompt. Any prompt change needs a recalibration.
- Nothing here rescues judge gates: visible tests remain the cheaper and at least as accurate gate.
