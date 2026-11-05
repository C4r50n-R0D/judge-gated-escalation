# E2: Judge zoo and ensembles

Status: SPEC (exploratory by rule, PREREG v2 section 11). Written after T26 was read (2026-10-25); predictions are
made before any E2 label exists.

## Question
Do other local judge models, of different families and sizes, or ensembles and recalibrated versions of the judges,
discriminate correct from wrong 3B drafts better than tev, and does any of them make judge->reroute cheaper than
strong-only (the H2 savings test tev failed)?

## Manipulation
Judges on the same stored 3B drafts (calibration and test splits, all draws):
- existing: tev1:4b (Jev API), llama3.1:8b (logprob YES/NO), selfconf
- new: gemma4:12b (12.4B, nvfp4), qwen3.5:9b (9.7B, Q4_K_M), both with thinking disabled; qwen2.5:7b-instruct (7.6B, Q4_K_M)
  All new judges use the llama judge prompt and the same logprob P(YES) rule (judge.py LogprobYesNo).
- derived (tools/derived_judges.py, fitted on calibration 3B drafts only): Platt and isotonic versions of every
  judge, ens_mean and ens_stack (logistic regression on the six judges logits).
Fixed: the drafts, prompt, temperature 0, Ollama settings (q8_0 KV cache, flash attention).

## Primary outcome
Test-split AUROC on 3B drafts, and the paired AUROC difference against tev (task-cluster bootstrap, 2,000).

## Analysis
tools/judge_eval.py (imports controllers.py unchanged). Secondary: within-task AUROC, Brier, ECE, unparseable rate,
seconds and token-compute per label; recal-mode gate (tau refit on calibration with the pre-registered rule) on the
test split vs strong-only and vs visible->reroute.

## Predictions (directional, written before data)
1. No single new judge beats tev on test AUROC by more than 0.03; gemma4:12b comes closest.
2. qwen2.5:7b-instruct has the lowest AUROC of the new judges (same family as the generator, smallest).
3. ens_stack has the highest test AUROC of all judges, by at most 0.05 over tev.
4. Platt and isotonic leave AUROC within 0.01 of the base judge and cut llama ECE below 0.1.
5. No judge or ensemble makes judge->reroute cheaper than strong-only in token-compute; every new judge costs more
   token-compute per label than tev.
6. No judge->reroute beats visible->reroute on token-compute.

## Planned size and estimated hours
4,336 3B drafts (1,368 calibration + 2,968 test), about 3,400 distinct codes, times 3 new judges. Mac: about 6 to
9 hours of judging (pilot measures it). Homelab: under 1 hour of analysis.

## Comparisons counted in ext/COMPARISONS.md
(listed in spec.json)
