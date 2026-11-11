# Phase 0 feasibility gate

Status: **in progress — online training, external persistence and fresh-session restore verified; cloud-serving gate pending**.

Local evidence: `results/phase0/offline-checks.json` records actual pytest, lint and fixture-check command outputs. Core checks ran on Windows/Python 3.14. Owner-supplied Colab output confirms managed Python setup, T4 generation, a three-step training command, downloaded checkpoint verification and fresh-session image inference using the same adapter manifest. Public cloud serving remains unverified. The wheel and source distribution were also built successfully. These results establish limited mechanics, not general model quality.

| Gate | Current evidence | State |
| --- | --- | --- |
| Inspect application contracts | Read-only source inspection and native schema snapshots | Implemented |
| Versioned task requests, outputs and fixtures | Three roles plus compact researcher submode; synthetic image pages | Implemented |
| Free account eligibility | Owner reports all accounts created; hosting eligibility not yet verified | Accounts created |
| Free training GPU | Owner-supplied result confirms model loading on Tesla T4 | Confirmed for this run |
| Untuned text and image inference | Raw outputs inspected: Vision reads the synthetic image correctly with fenced JSON; researcher and reviewer give incorrect judgments | Mechanics demonstrated; quality failures retained |
| Tiny online training and masking audit | Three steps plus audited saved weights: all 56 intended LoRA-B factors nonzero; warnings retained | Smoke artifact verified |
| External checkpoint persistence | Downloaded ZIP independently hashed and audited; checksum matches the cloud value | Verified |
| Fresh-session reload | Owner followed fresh-session procedure; matching adapter manifest, valid cited image answer | Verified for the smoke fixture |
| Free cloud hosting | HF account-age blocker; Modal overview shows only $1 credit/$1 usage allowance, with net-spend cap and GPU access unverified | Pending hosting/account controls |
| Remote adapter text/image request | Prepared Space packager and remote probe | Not run |
| Laptop-independent operation | Cloud probe procedure | Not run |
| Cold/queue/warm latency, memory, quota | Colab load/generation and training allocation recorded; public serving queue/quota unmeasured | Partial measurements only |

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

## Raw-output inspection and next feasibility step

The targeted diagnostic supplied by the owner is preserved in `results/phase0/colab-raw-diagnostic-20261111.json`:

- Vision: a whole-response JSON fence surrounds a cited answer giving 2025 revenue as 42 USD millions. This agrees with the rendered first-party fixture, on this single synthetic page only.
- Compact researcher: also fenced, but wrongly returns `k=1` for an unexploited advisory and copies instruction phrases into mechanism/prerequisite. Removing the fence does not fix these factual failures.
- Reviewer: wrongly labels exposure supported while acknowledging missing exposure evidence; its claimed existing defense is not established by the supplied observation. The prerequisite guard rejects the answer.

The runtime now permits only a single complete JSON fence as bounded formatting normalization. Smoke records separately retain `strict_json_valid`, `output_normalization` and a hash of the original decoded text. No prose extraction, field repair or factual rewriting is performed. Prior strict-parser failures remain unchanged in their original result files.

Proceed with the three-step synthetic image training smoke to test masking, memory, adapter saving and restoration. The untuned model does not need to pass security-release quality thresholds before testing the training mechanics. This does not authorize larger training runs or application replacement; its security quality failures remain unresolved. The current Colab source already contains the processor fix needed for training, so this step does not require reinstalling or another source upload.

## First online training smoke

The owner reported exit code 0 and a saved `artifacts/smoke-adapter` after three T4 steps. Losses were 1.0783616304397583, 0.7788828611373901 and 0.5237541198730469. The masking audit reports 526 prompt tokens, 564 total tokens and 38 answer tokens, one image, matching prompt prefix and masked image tokens. Peak allocated memory was 3,420,103,680 bytes (about 3.19 GiB). The supplied summary is preserved verbatim in structured form at `results/phase0/colab-training-smoke-20261111.json`.

The run also emitted checkpointing warnings about `use_reentrant` and inputs without gradients. These warnings are retained; no per-parameter gradient audit was collected, so the declining loss must not be presented as independent proof of correct updates to all intended adapter modules. Download the complete adapter and measurements before disconnecting, verify the saved tensors and manifest, then restore into a fresh session and test image inference. None of the three-role quality or cloud-serving release gates is passed by this training smoke.

## Downloaded checkpoint verification

The adapter ZIP saved outside Colab has SHA-256 `7b63cd6a256cec79bbbcb486cdbae1794210f983aadd4880e00412b269daea13`, matching the owner's cloud checksum. Offline inspection of its contents passed CRC, required-file, base/revision/rank, masking, fixture/prompt hash and exact intended tensor-coverage checks. The manifest confirms Python 3.12.12, the pinned dependency versions and the supplied step metrics.

The saved F32 adapter has 1,605,632 parameters in 112 tensors covering all 56 intended q/v projection modules. Every weight is finite; all 56 LoRA-B factors are nonzero. Because the saved config uses `init_lora_weights=true`, PEFT initializes those B factors to zero; their observed nonzero values provide evidence of actual updates despite the checkpointing warnings. This does not reconstruct per-step gradients or prove generalization. See [the pinned PEFT initialization implementation](https://github.com/huggingface/peft/blob/v0.17.1/src/peft/tuners/lora/layer.py#L236).

Reproduce with `python -m valar_llm.eval.checkpoint <adapter.zip> --expected-sha256 <checksum> --output <new-audit.json>`. This narrow auditor supports the smoke's F32 LoRA format, reads the documented safetensors layout without Torch, and does not execute a model. Evidence is saved in `results/phase0/checkpoint-audit-20261111.json` and its companion manifest. The next unpassed gate is fresh-session restoration followed by the image fixture; use the updated notebook's restore section after source upload and setup, skipping baseline and training.

## Fresh-session restore result

The owner supplied the completed fresh-session procedure output at `2026-11-11T11:46:35.591066+00:00`, saved in `results/phase0/colab-fresh-restore-20261111.json`. The upload's ZIP checksum and 112-tensor audit passed again. The inference report's adapter manifest hash is `6f3220efd7730f6f779df11a6e0b9be7fe03659511251bf956ff430b8d3dff48`, exactly matching the independent downloaded-checkpoint audit.

On Tesla T4, base/adapter load took 66.433741213 seconds and the single image generation took 14.839639314 seconds. The restored adapter returned 2025 revenue of 42 USD millions with citation `V1:P1`. This passes the supplied-evidence contract and agrees with the synthetic image. The response still required a single JSON fence to be removed, recorded as `strict_json_valid=false` and `output_normalization=single_json_fence`.

Training, saving, external persistence, checkpoint identity and fresh-session image inference have now been demonstrated for this tiny smoke. The same image was used for training and the untuned base already answered it correctly, so this is not evidence of held-out improvement or teacher parity. The remaining Phase 0 gate is a verified no-spend cloud-serving route and laptop-independent remote calls. Modal investigation is authorized only if the account can enforce $0 net spend; see `docs/modal-no-spend.md`.
