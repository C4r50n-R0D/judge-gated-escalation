# E3: Judge prompt sensitivity

Status: SPEC (exploratory by rule, PREREG v2 section 11). Written 2026-10-26 after T26, E12, E2 and E14a were read.
Predictions below are made before any E3 label exists.

## Question
How much does a judge's quality depend on how it is asked? Is AUROC more variable across wordings of the same
question than across judge models (E2), and does the frozen tau still mean the same thing when the wording changes?

## Manipulation
Two judges, the ones with frozen taus that use a prompt: tev (Tev1 decision API: instructions + criteria + state) and
llama (YES/NO prompt, first-token log-probabilities). Nine variants each, set through optional judge settings added to
judge.py (absent settings give the main-study request byte for byte; verified against the old judge.py, and cache
hashes for tev, llama and selfconf are unchanged):
- six paraphrases of the question (ext/E3/make_config.py lists them; same polarity: "correct" is YES / true);
- criteria toggled: tev without its true/false criteria; llama with the same criteria added to its prompt;
- code only: the task text is omitted;
- code first: the code comes before the task.
Drafts: every stored 3B draft of 100 random test tasks and 50 random calibration tasks (seed 20261026; ext/E3/subset.py),
about 1,200 drafts and about 1,070 distinct codes per variant. The calibration tasks are used only to refit taus.
Comparison judges (no new calls): tev, llama, selfconf, gemma, qwen35, qwen25i labels from E2 on the same drafts.

## Outcomes
Test subset: AUROC and paired AUROC difference vs the base judge; ECE; mean |p - p_base| on the same draft; share of
accept decisions that flip at the frozen base tau; at that tau, acceptance rate, accepted-set accuracy, false-accept
rate, and judge->reroute accuracy and token-compute (transfer mode). Recal mode: tau refit on the 50 calibration tasks
(tools/judge_eval.py, the pre-registered rule). Spread: SD and range of AUROC over base + six paraphrases, against the
SD and range over six judge models, with the paired difference.

## Analysis
tools/judge_eval.py and ext/E3/analyze.py (import controllers.py and judgestats.py unchanged). Task-cluster bootstrap,
2,000 resamples for judge_eval and 1,000 for analyze.py. Effect sizes and CIs only.

## Predictions (written before any E3 label)
1. Across base + six paraphrases, tev's AUROC range is at most 0.04; llama's range is larger than tev's.
2. The SD of AUROC across the seven tev prompts is smaller than the SD across the six judge models; the same holds for
   llama's prompts.
3. Code only lowers AUROC by at least 0.05 for both judges.
4. Code first changes AUROC by at most 0.02 for both judges.
5. Criteria: tev without criteria is within 0.02 AUROC of base; llama with criteria changes AUROC by at most 0.03.
6. The frozen tau does not travel across wordings even where AUROC does: for tev, acceptance rate at the frozen tau
   ranges over at least 10 points across the paraphrases, and at least 10% of accept decisions flip for at least one
   paraphrase.
7. No variant, in either mode, makes judge->reroute match visible->reroute on token-compute.

## Planned size and estimated hours
18 variants x about 1,070 judge calls = about 19,300 calls on the Mac at about 1.5 s: about 8 hours. Pilot: 10 + 10
tasks, 2 draws each, about 20 minutes. Homelab analysis under 1 hour.

## Comparisons counted in ext/COMPARISONS.md
(listed in spec.json)
