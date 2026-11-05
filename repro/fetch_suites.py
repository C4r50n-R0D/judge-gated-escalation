#!/usr/bin/env python3
"""Download the two pinned benchmark files and check them against split_manifest.json. They are not redistributed here."""
import hashlib, json, os, sys, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); os.chdir(ROOT)
import suites
want = json.load(open("split_manifest.json"))["data_sha256"]; os.makedirs("data", exist_ok=True)
for s, (url, name) in suites.RELEASES.items():
    p = os.path.join("data", name)
    if not os.path.exists(p): urllib.request.urlretrieve(url, p)
    got = hashlib.sha256(open(p, "rb").read()).hexdigest()
    if got != want[s]: raise SystemExit(f"{name}: sha256 {got} does not match the manifest")
    print(name, "ok")
