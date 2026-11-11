# Architecture decisions

## ADR 001: Modular package before additional services

Accepted, 11 November 2026. One typed package with pure contracts/integrations, shared model runtime, independent train/eval commands and a cloud smoke entry point. This keeps the feasibility cycle inspectable and avoids a mandatory paid infrastructure dependency. Extraction/search/indexing remain in source applications.

## ADR 002: Preserve native response contracts

Accepted. Snapshot DevSecOps schemas with provenance; implement Vision's grounding invariants. Compact `k/m/p` is separate from full incidents. Do not rename it into an invented universal schema. Export schemas from the same packaged definitions and verify drift.

## ADR 003: Provisional Qwen3-VL-2B-Instruct

Provisional, not benchmark-selected. Model and processor use commit `89644892e4d85e24eaac8bacfd4f463576704203`. Its official card identifies an Apache-2.0 image/text model and Transformers support. Start with this one compact candidate; fit, security reasoning and visual grounding quality are unknown. Use text-tower LoRA projections initially while preserving the base vision encoder. Reconsider after actual memory and host measurements.

## ADR 004: Colab training, ZeroGPU hosting candidate

Provisional. Verify account/runtime access first. The owner reported no existing accounts on 11 November 2026. A newly created Hugging Face account cannot immediately satisfy the documented over-30-day hosting criterion. Record cloud hosting blocked until eligible, a permitted grant exists, or another enforceably zero-spend route is verified. No paid workaround or implicit Modal deployment.

## ADR 005: Small explicit smoke before training framework expansion

Accepted for Phase 0. Three manual QLoRA steps, one example, exact prompt-prefix masking, no sequence truncation, save each step. Avoid implicit chat-template masking assumptions. This is not a full trainer: optimizer resume, dataset batching, distributed training and scheduler selection belong to later phases.

## ADR 006: Python and dependency separation

Accepted. Offline core supports Python 3.12–3.14. Local checks use installed 3.14; free GPU notebook and Space target 3.12. Heavy CUDA dependencies are locked separately for Linux and never installed on the development laptop by default. Core lockfile is `uv.lock`; GPU/serving lockfiles are generated from explicit requirements inputs. GPU runtime compatibility remains unverified until a real run.
