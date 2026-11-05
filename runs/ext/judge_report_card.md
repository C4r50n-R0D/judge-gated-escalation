# Judge report card (T26 and Phase 4 experiments E2 to E14b)

One page across everything run so far. Test split unless noted; brackets are 95% task-cluster bootstrap CIs. Visible
tests are listed as the reference gate. Sources: runs/T26_report.md, ext/E*/RESULT.md, runs/sensitivity/SUMMARY.md.
Exploratory results (everything after T26) are effect sizes only.

| property | tev | llama | selfconf | visible tests |
|---|---|---|---|---|
| Ranking: AUROC on 3B drafts (T26, H1) | **0.813** [0.779, 0.846] | 0.688 [0.647, 0.731] | 0.680 [0.638, 0.721] | n/a (pass/fail) |
| Gate vs 14B-only (T26, H2): accuracy, token-compute | -0.003, +117: not cheaper | -0.009, +1,573: not cheaper | -0.003, +31: not cheaper | **+0.014, -1,928: passes** |
| Same, 7B and 1.5B drafts, frozen and refit taus | fails in all four | fails in all four | fails in all four | passes in all four |
| Stacked on visible tests (E12) | +0.000 accuracy at 2x compute | n/a | -1.4 points (transfer) | best: 3B->7B->14B cascade +1.5 |
| Bigger or other judges (E2) | gemma, qwen35 tie it; 6-judge ensemble +0.023 AUROC at 7.1x cost, still a worse gate | qwen25i about as weak | n/a | n/a |
| Rewording the judge question (E3) | AUROC range 0.029; accept rate 50-61%; <= 8% decisions flip | AUROC range 0.040; accept rate 8-69%; up to 43% flip | n/a | unaffected |
| Input layout (E3) | code before task -0.096 AUROC; task dropped -0.089 | code-first no-op; task barely used | n/a | unaffected |
| Code rewrites with same behaviour (E4) | AUROC unchanged; 4.5-9% decisions flip | AUROC unchanged; verbose comments cut accept rate 26% -> 10% | n/a | unchanged by construction |
| One-token bugs (E5) | catches 64% (parent accepted, mutant rejected) | catches 26%; rejects 70% of correct parents | n/a | catches more than tev in 5 of 6 bug classes |
| Injected text in code (E6), pooled false-accept increase | +7.2 [+1.3, +15.2]; worst +13.9 (string) | +12.6 [+6.7, +18.8]; worst +59.7 (invisible chars) | n/a | unaffected (0 verdict changes) |
| Defense that works (E6) | sanitizer: leaves 31% (strings, names) | sanitizer: removes all | n/a | not needed |
| Frozen tau across generators (E14a) | transfers (accept 47-55% for 1.5B-14B) | transfers (accept 26-30%) | does not (accepts 7% of 1.5B, 53% of 14B) | n/a |
| Frozen tau across suites (E14a) | accepts 76% HumanEval+ vs 42% MBPP+ | small gap, reversed (24% vs 30%) | in effect a suite detector | n/a |
| Accepted-set accuracy under shifts (E14b) | within 2 points under rewording and rewrites; -3.2 under injection | falls up to 12.8 points under injection | n/a | n/a |
| Calibration (E2, E14a, E14b) | ECE 0.13 raw -> 0.06 recalibrated; holds under most shifts | 0.31 -> 0.08; breaks again under rewording and injection | 0.24 -> 0.06 within a generator | n/a |
| Label-free drift monitor (E14a, E14b) | 9-29% false alarms; misses injection (47%) and generator swaps | 39-69% false alarms | works for generator swaps | n/a |

## Verdict per judge
- **tev:** the best ranker of everything tried and the most stable under prompt, style and generator changes. But as a
  gate it never beats 14B-only on compute, adds nothing on top of visible tests, and drifts upward under verdict-like
  text in the code.
- **llama:** a weaker ranker whose threshold is tied to its exact prompt and to code style. Easily captured by
  injected text; needs code sanitizing and refitting after any change.
- **selfconf (generator's own confidence):** cheap, but its threshold reflects the generator and the suite more than
  correctness. Usable only when refit for each generator and suite.
- **Visible tests:** the only gate that saves compute in every pair tested, and the only one immune to prompt, style
  and injection. Their limit is coverage: they miss bugs the original benchmark tests do not exercise (E5: 72 of 852 mutants
  passed them, and tev caught 52 of those).
