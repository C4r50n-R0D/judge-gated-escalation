# E11: Generation factors (temperature, prompt style, output length cap)

Status: DRAFT (2026-10-29). Prompts fixed in ext/E11/prompts.py; commands and spec.json at kickoff (bench.py needs a
prompt-style option; absent = the main-study request, byte for byte, checked as in E3/E6). Needs new generation.

## Question
How much do the main study's generation settings drive its conclusions? Does a different temperature, prompt style or
length cap change the local model's pass rate, its draft diversity, or the benefit of resampling?

## Manipulation
One factor at a time from the main settings (temperature 0.8, direct prompt, num_predict 768), on the 3B and the 14B,
E3's subset (100 test + 50 calibration), 8 draws per task for the 3B and 4 for the 14B (the stored main-run draws are
the reference condition):
- temperature 0.0 and 1.2;
- prompt style reasoning_first (at most five lines of reasoning, then one code block) and few_shot (two worked
  calibration examples of the same suite; a task is never its own example);
- num_predict 256 and 1536.

## Outcomes
Hidden pass rate (pass@1), pass@k from the draws, share of distinct programs per task (diversity), resample benefit
(gate->resample(3) minus gate->reroute accuracy, visible gate and tev), tokens and seconds per draw.

## Predictions
1. Temperature 0.0: 3B pass@1 at least as high as at 0.8; distinct programs per task near 1, so resampling gains nothing.
2. Temperature 1.2 lowers 3B pass@1 by at least 3 points.
3. reasoning_first changes 3B pass@1 by at most 2 points and at least doubles output tokens.
4. few_shot changes pass@1 by at most 2 points for both tiers.
5. num_predict 256 lowers pass@1 by at most 2 points; 1536 is within 1 point of 768.
6. Under no condition does visible->reroute lose its lead over tev->reroute.

## Planned size and estimated hours
3B: 150 x 8 x 6 = 7,200 draws; 14B: 150 x 4 x 6 = 3,600 draws. About 25 h of Mac generation at Stage 2 rates (the
14B dominates; dropping it halves the time). Scoring on the homelab, judging (tev only) about 3 h.
