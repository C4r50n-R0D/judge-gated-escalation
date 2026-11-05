# What has been checked

All checks below were run by the study's own author and tools. **No independent party has reproduced this work yet.** Logs
are in `repro/stored/`.

## Clean-room rerun
Fresh Docker container from `Dockerfile.evalplus`, Python 3.11.17 (the study used 3.13.5), `--network none`, using only
this package.

| Check | Result |
|---|---|
| File checksums | all match |
| Unit tests | 0 failures |
| Frozen confirmatory analysis | report identical to `runs/T26_report.md` |
| Thresholds rederived from calibration data | identical to `thresholds.json` for all three judges |
| Independent recomputation, separate code | identical to the stored output |
| Exploratory analyses E2 to E14b, 18 outputs | 9 reports byte-identical; 9 JSON files equal to 1e-9 |
| Post hoc analyses (`pressure.py`, `pressure2.py`) | output byte-identical |

The 9 JSON files differ from the stored ones by at most 1.3e-11, in values up to the thousands. The cause is `sum()` on
floats, which changed in Python 3.12. Rerunning E4 and E5 on Python 3.13.5 gave byte-identical JSON.

The package was rebuilt after this run. Only `repro/exploratory.py`, `repro/run.sh` and `repro/scan_identifiers.py` changed,
and files were added or removed as `CHECKSUMS.sha256` shows; all data, analysis code and reference outputs have the same
sha256 as in the run above. Setup, tests, confirm, independent and all four `pressure` scripts were then rerun on the final
package, with the same results.

## Scoring
`repro/run.sh rescore 500`, run from the package with a fresh scorer cache: 500 of 500 random stored draws matched on both
the visible and the hidden verdict.

## Repeatability of generation and judging
`repro/stored/repeat_check.json`. Same machine, Ollama version, seeds and model digests. Run from this package's code,
at `localhost`.

| Item | Result |
|---|---|
| Draws | 21 of 21 byte-identical (3B 12, 1.5B 6, 14B 3) |
| llama judge | 8 of 8 exact |
| tev judge | 8 of 8 same verdict; largest probability difference 0.007069 |

## Integrity
- `controllers.py`, `PREREG.md`, `thresholds.json` and `split_manifest.json` are byte-identical to the freeze commit
  (`data_store/provenance.json`).
- `split_manifest.json` was recomputed from the benchmarks and matches.
- `repro/scan_identifiers.py` found no network addresses, personal paths, email addresses or keys, in text files or in
  compressed data rows. As a positive control, planted strings in a data row, a stored JSON file, a script and model-written
  code were all caught.

## Not checked
- The whole study has not been regenerated from this package. Repeatability rests on the sample above.
- Generation has not been repeated on other hardware or other Ollama versions. Expect differences there.
- `repeat` has run only on the original generation machine.
- The author's first name appears in the frozen `PREREG.md`, in `DEVIATIONS.md` and in code comments, and `LICENSE` names
  the author. This package is not anonymous, and it cannot be made so without changing frozen files.
- Commit dates are self-reported. There is no third-party registry deposit.
