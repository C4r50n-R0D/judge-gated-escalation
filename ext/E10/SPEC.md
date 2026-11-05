# E10: Task perturbations (T17 variants)

Status: DRAFT (2026-10-29). Variants built and verified at T17 for the calibration split; test-split variants of the
E3 subset are built and selfchecked before kickoff (allowed after STOP C). paraphrase needs Carson's spot check of 20
first (Phase 2 leftover); without it, paraphrase is dropped. Needs new generation.

## Question
Do small, meaning-preserving changes to the task text (renamed parameters, an irrelevant paragraph, padding, a dropped
example or sentence, a paraphrase) change pass rates, judge discrimination and the gate comparisons?

## Manipulation
E3's subset (100 test + 50 calibration); variants rename_params, distractor, padding_400, padding_1500, drop_example
(HumanEval+ only), drop_sentence, paraphrase. 3B: 4 draws per task and variant; 14B: 2. Judges tev and llama see
the variant's task text (as a deployment would).

## Outcomes
Hidden pass rate per tier vs the stored clean draws of the same tasks; AUROC; accept rate and accepted-set accuracy
at the frozen tau; visible->reroute vs tev->reroute vs strong-only accuracy and token-compute.

## Predictions
1. padding_1500 lowers the 3B pass rate by at least 3 points; distractor and rename_params change it by at most 2.
2. drop_example lowers the HumanEval+ 3B pass rate more than drop_sentence lowers either suite's.
3. tev's AUROC stays within 0.03 of clean for every variant except padding_1500.
4. visible->reroute is at least as accurate as tev->reroute under every variant.

## Planned size and estimated hours
150 x 7 x (4 + 2) = about 6,300 draws: about 16 h of Mac generation, scoring about 1 h, judging about 4 h.
