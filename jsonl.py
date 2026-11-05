"""Shared JSONL reader. A run killed mid-write can leave a truncated last line; skip it with a warning instead
of crashing every downstream script. A malformed line anywhere else is a real error and raises."""
import json, sys

def read_jsonl(path):
    with open(path) as f:
        lines = f.read().split("\n")
    while lines and not lines[-1].strip(): lines.pop()
    out = []
    for i, l in enumerate(lines):
        if not l.strip(): continue
        try: out.append(json.loads(l))
        except json.JSONDecodeError:
            if i == len(lines) - 1:
                print(f"warning: {path}: ignoring truncated last line (interrupted write?)", file=sys.stderr); continue
            raise
    return out

def open_append(path):
    """Open for appending after repairing a truncated last line (a killed writer can leave one). Without this, the
    next append would glue a valid record onto the fragment and every later read would fail."""
    import os
    if os.path.exists(path) and os.path.getsize(path) > 0:
        with open(path, "rb+") as f:
            data = f.read()
            if not data.endswith(b"\n"):
                cut = data.rfind(b"\n") + 1          # 0 if no newline at all: the whole file is one fragment
                f.seek(cut); f.truncate()
                print(f"warning: {path}: removed a truncated last line before appending", file=sys.stderr)
    return open(path, "a")

def resolve(cfg, key, default):
    """Paths in config are relative to the config file's directory, never to the current working directory."""
    import os
    p = cfg.get(key, default)
    return p if os.path.isabs(p) else os.path.join(cfg.get("_config_dir", "."), p)
