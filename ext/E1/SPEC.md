# E1: Model ladder, families and quantization

Status: DRAFT (2026-10-29). Needs model pulls: Carson approves each pull after a disk check (Mac: 27 GB free on
2026-10-29). Needs new generation.

## Question
Do the main results depend on the Qwen2.5-Coder family and on 4-bit quantization? Does a non-Qwen generator, or a
less quantized 3B, change pass rates, judge discrimination and the value of the gates?

## Manipulation
E3's subset (100 test + 50 calibration), 4 draws per task, main settings. Proposed pulls (about 17 GB in total):
- qwen2.5-coder:3b at q8_0 (about 3.3 GB) and fp16 (about 6.2 GB), against the stored q4_K_M 3B draws;
- two non-Qwen coder models of similar size: deepseek-coder:6.7b-instruct (about 3.8 GB) and
  codellama:7b-instruct (about 3.8 GB).
The 1.5B, 3B, 7B and 14B Qwen draws already exist. Judges tev and llama on every new draft.

## Outcomes
Hidden pass rate; tev and llama AUROC and frozen-tau behaviour per generator; gate->reroute vs strong-only for each
new generator as the local tier (exploratory transfer of the frozen taus).

## Predictions
1. q8_0 and fp16 3B change the pass rate by at most 3 points from q4_K_M.
2. Both non-Qwen 7B models pass fewer tasks than qwen2.5-coder:7b.
3. tev's AUROC on non-Qwen drafts is within 0.05 of its AUROC on Qwen 7B drafts.
4. visible->reroute beats tev->reroute on token-compute for every local tier.

## Planned size and estimated hours
4 new generators x 150 tasks x 4 draws = 2,400 draws: about 8 h of Mac generation (fp16 is slow), scoring about
1 h, judging about 2 h.
