# E8: Natural-language prompt languages (HumanEval-XL, T19)

Status: DRAFT (2026-10-29). Data pinned at T19 (HumanEval-XL commit 1e9301f, MIT; 23 languages pass the EvalPlus
selfcheck on calibration tasks). Test-split variants are built and selfchecked before kickoff. Own translations and
judge-prompt translations wait for the T19 back-translation check, so this draft uses only the published set and the
English judge prompt. Needs new generation.

## Question
When the problem is written in another language (code, signature and tests unchanged), how much do pass rates, judge
discrimination and the gates change, and does the 3B suffer more than the 14B?

## Manipulation
HumanEval-XL tasks that map onto HumanEval+ (84 of 164, both splits). Languages: English (control: the XL English
text, not HumanEval+'s), Spanish, German, Russian, Chinese, Arabic, Persian, Tagalog (Latin and non-Latin scripts,
high and lower resource). 3B: 4 draws per task and language; 14B: 2. Judges tev and llama with the English judge
prompt, seeing the translated task.

## Outcomes
Hidden pass rate per tier and language vs XL English; AUROC; frozen-tau accept rate and accepted-set accuracy; gate
comparisons as in E10.

## Predictions
1. Every non-English language lowers the 3B pass rate; Tagalog and Persian lower it most, Spanish and German least.
2. The 14B's drop is smaller than the 3B's for every language.
3. tev's AUROC falls by at least 0.03 on Chinese, Arabic and Persian tasks.
4. visible->reroute remains at least as accurate as tev->reroute in every language.

## Planned size and estimated hours
8 languages x 84 tasks x (4 + 2) = about 4,000 draws: about 10 h of Mac generation, scoring about 1 h, judging about 3 h.
