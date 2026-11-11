# Phase 0 feasibility gate

Status: **in progress — offline checks passed; online gate not passed**.

Local evidence: `results/phase0/offline-checks.json` records actual pytest, lint and fixture-check command outputs. Core checks ran on Windows/Python 3.14; Linux/Python 3.12 GPU execution remains a separate unrun gate. The wheel and source distribution were also built successfully. These results establish software scaffolding, not model quality.

| Gate | Current evidence | State |
| --- | --- | --- |
| Inspect application contracts | Read-only source inspection and native schema snapshots | Implemented |
| Versioned task requests, outputs and fixtures | Three roles plus compact researcher submode; synthetic image pages | Implemented |
| Free account eligibility | Owner reports all accounts created; hosting eligibility not yet verified | Accounts created |
| Free training GPU | Owner-supplied result confirms model loading on Tesla T4 | Confirmed for this run |
| Untuned text and image inference | Generation reached; two JSON parsing failures and one reviewer prerequisite failure | Retry failed task checks |
| Tiny online training and masking audit | Runnable three-step QLoRA command | Not run |
| External checkpoint persistence | Notebook download/restore procedure | Not run |
| Fresh-session reload | Separate inference command and manifest checks | Not run |
| Free cloud hosting | New HF account cannot yet meet age criterion | Blocked on eligibility |
| Remote adapter text/image request | Prepared Space packager and remote probe | Not run |
| Laptop-independent operation | Cloud probe procedure | Not run |
| Cold/queue/warm latency, memory, quota | Result formats prepared; no values invented | Unmeasured |

The first online cycle checks mechanics, not quality. A tiny synthetic adapter does not satisfy any role's release-quality gate. No production endpoint or complete application replacement is claimed.

## Next actions

1. Create/verify free accounts using `docs/account-setup.md`.
2. Package the notebook source bundle; upload it and open `notebooks/phase0_colab.ipynb`.
3. Confirm a free GPU in the account, install the locked notebook stack and run base smoke.
4. Train the image fixture, inspect its saved masking audit and persist the adapter externally.
5. Restart the session, restore the adapter and run reload inference.
6. When hosting eligibility exists, package and deploy only to a free ZeroGPU Space. Never upgrade hardware to resolve a failed build.
7. Run the same remote probe from Colab, then verify a request from another client with the laptop off. Preserve real timestamps and outputs.

Record failures as failures and choose a new model/route if necessary. Do not collect a large dataset before this gate passes.

## First setup attempt

The owner reported the notebook's host-Python assertion failing before source upload on 11 November 2026. The traceback proves Colab's notebook interpreter was not 3.12; a later traceback identifies the host as Python 3.13. No training or model download was reached at that point. Setup now provisions its own Python 3.12.12 using pinned uv, leaving the notebook kernel version independent of the GPU dependency lock. The owner subsequently confirmed that setup's CLI fixture check exited successfully.

## First base-model inference attempt

The owner subsequently confirmed successful CLI fixture checks in the managed environment and supplied a result file from the T4 at `2026-11-11T10:52:08.976255+00:00`. Model loading took 179.526044222 seconds. All three requested cases recorded immediate `TypeError` failures; there were no valid predictions. The sanitized original report is preserved in `results/phase0/colab-base-smoke-20261111.json`.

Code inspection found plain-string system messages being passed to the multimodal processor. Transformers 4.57.1 scans every message content as typed blocks, producing a TypeError on these strings. The processor boundary now normalizes string content for both inference and training. See [the pinned upstream implementation](https://github.com/huggingface/transformers/blob/v4.57.1/src/transformers/processing_utils.py#L1501). Regression checks cover all three task paths and assistant training text; a corrected Colab inference run is still pending. New notebook attempts use timestamped filenames and expose synthetic-only debug tracebacks. Failed checks now exit unsuccessfully after saving their diagnostics.

## Processor-fix retry

The owner supplied a second T4 report at `2026-11-11T11:01:26.693720+00:00`, preserved in `results/phase0/colab-base-retry-20261111.json`. The model loaded in 9.494565361 seconds and reached generation for all three cases. Compact research and the image answer failed JSON parsing at the first character; their raw text was not saved by that version, so the cause (for example fencing or prose) remains unknown. Review produced parseable JSON but failed the Supported concern prerequisite invariant. No guardrail has been relaxed and no answer is counted as passing.

The synthetic debug flag now preserves exact unparseable output and parsed candidates rejected by evidence checks, so subsequent failures can be diagnosed without guessing. Normal runs still avoid recording raw failure content. A targeted diagnostic retry is required before choosing formatting changes or proceeding to training.
