# Phase 0 feasibility gate

Status: **in progress — offline checks passed; online gate not passed**.

Local evidence: `results/phase0/offline-checks.json` records actual pytest, lint and fixture-check command outputs. Core checks ran on Windows/Python 3.14; Linux/Python 3.12 GPU execution remains a separate unrun gate. The wheel and source distribution were also built successfully. These results establish software scaffolding, not model quality.

| Gate | Current evidence | State |
| --- | --- | --- |
| Inspect application contracts | Read-only source inspection and native schema snapshots | Implemented |
| Versioned task requests, outputs and fixtures | Three roles plus compact researcher submode; synthetic image pages | Implemented |
| Free account eligibility | Owner reported no configured accounts | Pending setup |
| Free training GPU | Colab/Kaggle accelerator not checked in account | Pending |
| Untuned text and image inference | Runnable smoke command, no GPU measurements | Not run |
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
