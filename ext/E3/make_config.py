"""Writes ext/E3/config.json: the E2 config plus the E3 prompt variants of tev and llama (run once from the repo root)."""
import json
c = json.load(open("ext/E2/config.json"))
TEV_Q = ["Is `candidate_code` a correct solution to `task`?",
         "Would `candidate_code` pass a thorough hidden test suite for `task`, including edge cases? It has not been executed.",
         "Read `task` and `candidate_code`. Decide whether the code does exactly what the task asks, for all valid inputs. Do not assume it was tested.",
         "Is `candidate_code` free of bugs and missing edge cases with respect to `task`?",
         "As a strict senior reviewer, would you approve `candidate_code` as a complete and correct implementation of `task`?",
         "Check `candidate_code` against `task` line by line. Is it correct on every input the task allows, including empty, boundary and unusual inputs?"]
LL_Q = ["Is this code a correct solution to the task? Answer YES or NO.",
        "Would this code pass a thorough hidden test suite for the task, including edge cases? It has not been run. Answer YES or NO.",
        "Does this code do exactly what the task asks, for all valid inputs? Do not assume it was tested. Answer YES or NO.",
        "Is this code free of bugs and missing edge cases? Answer YES or NO.",
        "As a strict senior reviewer, would you approve this code as a complete and correct implementation of the task? Answer YES or NO.",
        "Check the code against the task line by line. Is it correct on every input the task allows, including empty, boundary and unusual inputs? Answer YES or NO."]
J = c["judges"]
for i, q in enumerate(TEV_Q, 1): J[f"tev_p{i}"] = dict(J["tev"], question=q)
for i, q in enumerate(LL_Q, 1): J[f"llama_p{i}"] = dict(J["llama"], question=q)
J["tev_nocrit"] = dict(J["tev"], criteria=False); J["llama_crit"] = dict(J["llama"], criteria=True)
for b in ("tev", "llama"):
    J[f"{b}_codeonly"] = dict(J[b], code_only=True); J[f"{b}_codefirst"] = dict(J[b], order="code_first")
json.dump(c, open("ext/E3/config.json", "w"), indent=1)
print(sorted(k for k in J if k.startswith(("tev_", "llama_"))))
