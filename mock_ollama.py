"""Fake Ollama (incl. log-probabilities and Tev1's /v1/systemone) for testing the pipeline
without hardware or spend.
python mock_ollama.py PORT QUALITY(0..1)
Generation: success probability = QUALITY (per task, shifted by difficulty); 10% of successes on difficulty>=3 tasks are
a cheat that calls SystemExit(0) (the harness must score these as failures). Failures are a stub that fails both
visible and hidden tests, so the mock never makes visible and hidden results disagree.
Judges (YES/NO prompts and /v1/systemone): noisy, better than chance, computed from hidden-test truth.
Mock results say NOTHING about real models; they only exercise the code paths."""
import json, sys, random, math
from http.server import BaseHTTPRequestHandler, HTTPServer
import suites
from bench import run_tests
port, q = int(sys.argv[1]), float(sys.argv[2])
rnd = random.Random(port)
TASKS = suites.load("own")
def find(text): return next((t for t in TASKS if t["prompt"] in text or t["judge_task"] in text), None)
def gen(prompt):
    task = find(prompt)
    if task is None: return "```python\ndef add(a,b): return a+b\n```"
    p = q - 0.08 * ((task.get("difficulty") or 2) - 2)
    u = rnd.random()
    if u < p:
        if (task.get("difficulty") or 0) >= 3 and rnd.random() < 0.10:
            return f"```python\ndef {task['entry']}(*a, **k):\n    raise SystemExit(0)\n```"
        return f"```python\n{task['reference']}\n```"
    return f"```python\ndef {task['entry']}(*a, **k):\n    return None\n```"
def judge_p(text, code):
    task = find(text); ok = task is not None and run_tests(code, task["hidden"])[0]
    return min(0.99, max(0.01, (0.75 if ok else 0.35) + rnd.uniform(-0.3, 0.3)))
def code_in(prompt):
    import re
    m = re.findall(r"```python\n(.*?)```", prompt, re.S); return m[-1] if m else ""
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _send(self, o):
        b = json.dumps(o).encode(); self.send_response(200); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self): self._send({"models": [{"name": "mock:7b", "size": 4_000_000_000}]})
    def do_POST(self):
        n = int(self.headers["Content-Length"]); body = json.loads(self.rfile.read(n))
        if self.path.endswith("/v1/systemone"):
            st = body["state"]; local = self.path.endswith("/v1/systemone")   # Tev1 on Ollama reports no cost
            return self._send({"id": "x", "model": body["model"] + ("" if local else "-20260901"), "provider": "mock",
                               "answers": {"is_correct": {"type": "noul", "noul": judge_p(st["task"], st["candidate_code"])}},
                               "usage": {"input_tokens": 300, "output_tokens": 0} if local else {"input_tokens": 300, "output_tokens": 0, "cost": 0.00004}})
        prompt = body["prompt"]
        system = body.get("system", "")
        lp = None
        if "strict code reviewer" in system:
            p = judge_p(prompt, code_in(prompt))
            txt = "YES" if rnd.random() < p else "NO"
            if body.get("logprobs"):   # first-token alternatives, with some mass on a markdown token as real models do
                p = min(0.98, max(0.02, p)); top = [("YES", 0.9 * p), ("NO", 0.9 * (1 - p)), ("**", 0.1)]
                lp = [{"token": top[0][0] if p >= .5 else top[1][0], "logprob": math.log(max(top[0][1], top[1][1])),
                       "top_logprobs": [{"token": t, "logprob": math.log(v)} for t, v in top]}]
        else:
            txt = gen(prompt)
            if body.get("logprobs"):   # correct code a little more confident than wrong code
                ok = "return None" not in txt and "SystemExit" not in txt
                lp = [{"token": "x", "logprob": -abs(rnd.gauss(0.15 if ok else 0.4, 0.1))} for _ in range(5)]
        out = {"response": txt, "eval_count": 100, "eval_duration": int(100 / 20 * 1e9), "prompt_eval_count": 60,
               "prompt_eval_duration": int(60 / 500 * 1e9), "load_duration": 0}
        if lp is not None: out["logprobs"] = lp
        self._send(out)
HTTPServer(("127.0.0.1", port), H).serve_forever()
