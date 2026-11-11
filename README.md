# Valar LLM

Evidence-grounded model adaptation for **DevSecOps Incident Researcher**, **DevSecOps Security Reviewer**, and **Vision grounded answers**.

**Status: Phase 0 training/save/restore smoke verified on free Colab; public cloud serving remains pending.** The saved adapter passed an independent tensor audit and fresh-session image inference. This is one synthetic training example, not evidence of general model quality. The project targets zero out-of-pocket cost, free online training and cloud inference independent of the owner's laptop.

Start with [the Phase 0 checklist](docs/phase-0.md), [architecture](docs/architecture.md), [account setup](docs/account-setup.md) and the [build plan](Valar%20LLM%20Build%20Plan.md).

## Pilot review preparation

The owner authorized small offline data/evaluation preparation while free hosting is blocked. The [pilot review guide](docs/pilot-review.md) covers 24 **unlabeled development items**, licensed source snapshots and original synthetic pages. No human-gold labels, teacher calls or pilot training have been created.

Read [the shared labeling rules](docs/labeling/shared.md), then start in a terminal from the project folder:

```powershell
uv run valar pilot validate
uv run valar pilot review --reviewer reviewer1 --item P001
uv run valar pilot report
```

The interactive reviewer supplies all decisions. Packets contain evidence and no model predictions; annotations stay in ignored private storage. A pending or invalid form does not count as a label. This preparation does not complete Phase 0 or establish three-role model quality.

## Local development

Python 3.12–3.14 and uv. Local tools validate contracts and prepare cloud artifacts; they do not train or serve the model publicly.

```powershell
uv sync --locked --python 3.14
uv run valar check
uv run python -m pytest
uv run ruff check .
uv run valar status
```

Use `--python 3.12` in an online Linux environment. If uv is unavailable, create a virtual environment and install the package plus pytest and ruff; use `python -m valar_llm.cli check` for the CLI.

## First online experiment

```powershell
uv run python scripts/prepare_bundle.py notebook
```

Upload `notebooks/phase0_colab.ipynb` to a free Colab GPU runtime, then upload the generated source zip when prompted. The notebook installs its separate Linux GPU lockfile, runs three base-inference attempts, trains three synthetic image steps, and downloads the adapter. Restart, restore and run the reload cell. See the account guide for exact steps.

The provisional base is `Qwen/Qwen3-VL-2B-Instruct` at an immutable revision. This is a compatibility hypothesis, not a claim that a 2B model meets security-review quality. No large dataset or teacher-labeling run should begin before the train/restore/cloud gate passes.

## Cloud smoke preparation

```powershell
uv run python scripts/prepare_bundle.py space
```

Review the generated `artifacts/space` directory before deployment. Hosting requires an eligible free ZeroGPU account, Gradio configuration and private caller credentials. New HF accounts have a documented age requirement; no deployment is assumed. No paid overflow or automatic teacher fallback exists.

[Modal investigation](docs/modal-no-spend.md) found a refundable upfront verification charge in the owner's account flow, so that route is excluded under the strict zero-cash-outlay requirement. No Modal resources have been activated. Cloud serving awaits eligible fee-free ZeroGPU access or an approved allocation; Phase 0 is not complete.

## Repository map

| Path | Responsibility |
| --- | --- |
| `src/valar_llm/contracts` | Strict input envelopes, packaged native output schemas, evidence invariants |
| `src/valar_llm/integrations` | Pure DevSecOps/Vision request builders |
| `src/valar_llm/runtime` | Shared prompts, pinned processor/model loading and generation |
| `src/valar_llm/train` | Bounded online QLoRA smoke and masking audit |
| `src/valar_llm/eval` | Offline fixtures and measured inference smoke |
| `src/valar_llm/gateway` | Authentication and atomic daily request reservations |
| `src/valar_llm/serve` | Disabled-by-default ZeroGPU smoke endpoint |
| `configs`, `schemas`, `requirements` | Experiment settings, exported contracts, locked GPU dependencies |
| `notebooks`, `scripts`, `tools` | Thin cloud entry point, packaging/probe, maintenance generators |
| `tests/fixtures` | First-party synthetic text/image smoke examples, never human gold |
| `docs` | Architecture, upstream contracts, decisions, resources and gate status |
| `artifacts`, `results/runs` | Ignored generated adapters, bundles and runtime measurements |

Canonical schemas live inside the package; refresh exports with `uv run valar schemas`. The snapshot maintenance command is `uv run python tools/snapshot_contracts.py D:/Code/Projects/DevSecOps`; review upstream changes before accepting generated diffs. Neither source application is modified by this repository.

## Validation boundaries

Offline tests cover task contracts, quotes, references, abstention, prerequisite consistency, image ordering, admission and schema drift. They do not measure model correctness. Synthetic fixtures carry no independent human-gold claim.

The smoke service has one caller credential, one concurrent GPU request, bounded queue/input/output/image sizes and a small global daily request cap. Its SQLite storage can be ephemeral. Durable user-level quotas, application integrations, private-document retention, full cloud application hosting and production readiness remain later gates.

## Reproducibility and privacy

Core dependencies are in `uv.lock`. Online GPU and serving dependencies are in `requirements/*.lock`, resolved for Linux/Python 3.12; runtime compatibility still requires the real smoke run. Model and processor revisions are pinned in `configs/phase0.json`. Measurements come only from saved runtime output, never manually filled tables.

Keep tokens in notebook/Space secret stores. `.env`, private/raw data, generated artifacts and experiment runs are ignored. Only synthetic fixtures are currently authorized for the smoke workflow. The selected model's license is recorded separately; this repository does not grant redistribution rights to future third-party data.
