# Environment of the original study

Nothing here depends on how the two machines were connected. To reproduce a run, use one machine and `localhost`.

## Generation and judging machine
| Item | Value |
|---|---|
| Machine | MacBook Air, Apple M3, 16 GB unified memory, fanless |
| OS | macOS 15.1 (build 24B83) |
| Runtime | Ollama 0.40.8 |
| Ollama settings | `OLLAMA_KEEP_ALIVE=30m`, `OLLAMA_MAX_LOADED_MODELS=1`, `OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_KV_CACHE_TYPE=q8_0` |
| Quantization | Q4_K_M for the generators and llama, mxfp8 for tev1:4b, nvfp4 for gemma4:12b, as served by the digests below |

## Orchestration and scoring machine
| Item | Value |
|---|---|
| Machine | Intel Core i3-7100U, 4 threads, 8 GB of memory |
| OS | Debian 13.5, Linux 6.12 |
| Python | 3.13.5, standard library only for the pipeline and analysis |
| Docker | 29.6.1 |
| Scorer | `evalplus==0.3.1` on `python:3.11-slim`, built from `Dockerfile.evalplus` |
| Scorer limits | `--network none --memory 6g`, `EVALPLUS_MAX_MEMORY_BYTES=8589934592`, `--parallel 1` |

The orchestrator sent requests to Ollama over a private network, so stored seconds include a small network latency. It
did no generation. Accuracy, tokens and token-compute do not depend on this; only seconds do.

## Models
| Role | Model | Digest | Parameters (B) | Draws per task |
|---|---|---|---|---|
| Local, primary | qwen2.5-coder:3b | f72c60cabf62 | 3.1 | 8 |
| Strong | qwen2.5-coder:14b | 9ec8897f747e | 14.8 | 5 |
| Local, secondary | qwen2.5-coder:7b | dae161e27b0e | 7.6 | 8 |
| Local, wide gap | qwen2.5-coder:1.5b | d7372fd82851 | 1.5 | 8 |
| Judge, primary | tev1:4b | 4d24c6f6d61a | 4.2 | once per draft |
| Judge | llama3.1:8b | 46e0c10c039e | 8.0 | once per draft |
| Exploratory judges | gemma4:12b, qwen3.5:9b, qwen2.5:7b-instruct | c7597fc90b86, 6488c96fa5fa, 845dbda0ea48 | 12.4, 9.7, 7.6 | once per draft |

## Generation settings
Temperature 0.8, `num_predict` 768, timeout 300 s, seed 1234 plus the draw number. Judges: llama at temperature 0, seed 1,
one token, top 20 log-probabilities. Tasks ran in blocks of 20 in a fixed random order (`order_seed` 2026) with a
cooldown guard. Everything is in `config.study.json`, where only addresses were changed, to `localhost`.

## Benchmarks
HumanEval+ v0.1.10 and MBPP+ v0.2.0. They are not redistributed: `repro/run.sh fetch` downloads them and checks their
sha256 against `split_manifest.json`.
