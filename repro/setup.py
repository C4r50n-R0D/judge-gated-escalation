#!/usr/bin/env python3
"""Check every file against CHECKSUMS.sha256 and unpack the stored data into runs/. Standard library only."""
import hashlib, lzma, os, shutil, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
bad = 0; n = 0
for line in open("CHECKSUMS.sha256"):
    want, path = line.strip().split(None, 1); path = path.lstrip("*"); n += 1
    if not os.path.exists(path) or hashlib.sha256(open(path, "rb").read()).hexdigest() != want: print("BAD", path); bad += 1
if bad: sys.exit(f"{bad} of {n} files fail their checksum")
print(f"{n} files match CHECKSUMS.sha256")
os.makedirs("runs/eval", exist_ok=True)
for f in sorted(os.listdir("data_store")):
    if f.endswith(".xz"):
        dest = os.path.join("runs/eval" if "_eval_results" in f else "runs", f[:-3])
        with lzma.open(os.path.join("data_store", f)) as i, open(dest, "wb") as o: shutil.copyfileobj(i, o)
print("unpacked into runs/")
