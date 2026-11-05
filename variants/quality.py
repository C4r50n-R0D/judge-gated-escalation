"""Quality checks for semantic variants (paraphrase, translation): KICKOFF2 T17 and T19.

  python3 -m variants.quality equivalence NAME --base-url URL --model MODEL [--threshold 0.5]
      A second local model compares each variant description with the original and answers whether they require
      exactly the same function behaviour. P(YES) comes from first-token log-probabilities (as the llama judge).
      Tasks below the threshold are listed and recorded; the suite's manifest gets the result.
  python3 -m variants.quality backtranslate NAME --base-url URL --model MODEL --embed-url URL [--embed-model nomic-embed-text]
      Translation check: back-translate to English and compare with the original by embedding cosine similarity.
  python3 -m variants.quality spotsheet NAME OUT.md [--n 20] [--seed 1]
      A Markdown sheet of n random pairs (original, variant) for Carson's spot check, with a blank verdict column.
  python3 -m variants.quality record-spotcheck NAME OUT.md
      Reads the filled sheet (OK / NOT OK per row) and records the counts in the manifest.

Only the problem DESCRIPTION is compared; code, examples and tests are identical by construction.
"""
import argparse, json, math, random, re, sys, urllib.request

import variants
from judge import yes_prob

EQ_SYS = "You compare two programming task descriptions. Reply with exactly one word: YES or NO."


def eq_prompt(a, b):
    return (f"Description A:\n{a}\n\nDescription B:\n{b}\n\nDo A and B require exactly the same behaviour from the function, "
            "with no requirement added, removed or changed? Answer YES or NO.")


def ask(base_url, model, a, b, timeout=180):
    body = {"model": model, "system": EQ_SYS, "prompt": eq_prompt(a, b), "stream": False, "logprobs": True, "top_logprobs": 20,
            "options": {"temperature": 0, "seed": 1, "num_predict": 1}}
    req = urllib.request.Request(base_url.rstrip("/") + "/api/generate", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r: return yes_prob(json.loads(r.read()))


def original_of(t):
    return (t.get("variant_notes") or {}).get("original")


def equivalence(name, base_url, model, threshold=0.5, log=print):
    rows = variants.load(name); res = {}; low = []
    for t in rows:
        orig = original_of(t)
        if orig is None: continue
        from variants.transforms import description_span
        s = description_span(t); new = t["raw_prompt"][s[0]:s[1]].strip() if s else t["raw_prompt"]
        p, mass = ask(base_url, model, orig, new)
        res[t["id"]] = {"p_equivalent": p, "mass": mass}
        if p is None or p < threshold: low.append(t["id"])
    out = {"model": model, "threshold": threshold, "n": len(res), "below_threshold": low,
           "mean_p": (sum(v["p_equivalent"] or 0 for v in res.values()) / len(res)) if res else None}
    variants.record_verification(name, "equivalence", out)
    log(json.dumps(out)); return res, out


def embed(base_url, model, text, timeout=120):
    body = {"model": model, "input": text}
    req = urllib.request.Request(base_url.rstrip("/") + "/api/embed", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read())["embeddings"][0]


def cosine(u, v):
    nu = math.sqrt(sum(x * x for x in u)); nv = math.sqrt(sum(x * x for x in v))
    return sum(x * y for x, y in zip(u, v)) / (nu * nv) if nu and nv else 0.0


def backtranslate(name, base_url, model, embed_url, embed_model, threshold=0.85, log=print):
    """Translate each variant description back to English (local model, temperature 0) and compare it with the
    original by embedding cosine similarity (embed_model, e.g. nomic-embed-text on the homelab). Low pairs are listed."""
    from variants.transforms import description_span, ollama_text, TRANS_SYS
    res = {}; low = []
    for t in variants.load(name):
        orig = original_of(t)
        if orig is None: continue
        s = description_span(t); new = t["raw_prompt"][s[0]:s[1]].strip() if s else t["raw_prompt"]
        back = ollama_text(base_url, model, TRANS_SYS.format(lang="English"), new, seed=1)
        sim = cosine(embed(embed_url, embed_model, orig), embed(embed_url, embed_model, back))
        res[t["id"]] = {"similarity": sim, "back": back[:400]}
        if sim < threshold: low.append(t["id"])
    out = {"model": model, "embed_model": embed_model, "threshold": threshold, "n": len(res), "below_threshold": low,
           "mean_similarity": (sum(v["similarity"] for v in res.values()) / len(res)) if res else None}
    variants.record_verification(name, "backtranslation", out); log(json.dumps(out)); return res, out


def spotsheet(name, out, n=20, seed=1):
    rows = [t for t in variants.load(name) if original_of(t)]
    pick = random.Random(seed).sample(rows, min(n, len(rows)))
    from variants.transforms import description_span
    L = [f"# Spot check: {name}", "", "For each row, write OK if the variant asks for exactly the same behaviour as the original, else NOT OK.", "",
         "| # | task | original | variant | verdict |", "|---|---|---|---|---|"]
    for i, t in enumerate(pick, 1):
        s = description_span(t); new = t["raw_prompt"][s[0]:s[1]].strip() if s else ""
        cell = lambda x: x.replace("|", "\\|").replace("\n", " ")
        L.append(f"| {i} | {t['id']} | {cell(original_of(t))} | {cell(new)} |  |")
    open(out, "w").write("\n".join(L) + "\n"); print(f"wrote {len(pick)} rows -> {out}")


def record_spotcheck(name, path):
    v = [l.rsplit("|", 2)[-2].strip().upper() for l in open(path) if re.match(r"^\| \d+ \|", l)]
    out = {"rows": len(v), "ok": sum(x == "OK" for x in v), "not_ok": sum(x == "NOT OK" for x in v), "blank": sum(x == "" for x in v)}
    variants.record_verification(name, "spotcheck", out); print(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(prog="python3 -m variants.quality"); ap.add_argument("cmd", choices=["equivalence", "backtranslate", "spotsheet", "record-spotcheck"])
    ap.add_argument("name"); ap.add_argument("out", nargs="?"); ap.add_argument("--base-url"); ap.add_argument("--model")
    ap.add_argument("--embed-url"); ap.add_argument("--embed-model", default="nomic-embed-text")
    ap.add_argument("--threshold", type=float, default=0.5); ap.add_argument("--n", type=int, default=20); ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    if a.cmd == "equivalence": equivalence(a.name, a.base_url, a.model, a.threshold)
    elif a.cmd == "backtranslate": backtranslate(a.name, a.base_url, a.model, a.embed_url, a.embed_model, a.threshold if a.threshold != 0.5 else 0.85)
    elif a.cmd == "spotsheet": spotsheet(a.name, a.out, a.n, a.seed)
    else: record_spotcheck(a.name, a.out)
