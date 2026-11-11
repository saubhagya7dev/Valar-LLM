# Application boundary inspection

Inspected read-only on 11 November 2026. Neither source application was edited.

## DevSecOps

Repository: `D:/Code/Projects/DevSecOps`.

- `devsecops/contracts.py`: `COMPACT_INCIDENT`, `INCIDENTS`, `REVIEW` are snapshotted without field renaming. Provenance is packaged with the snapshots.
- `devsecops/incident_research.py`: `run_research` owns discovery and extraction orchestration. A low researcher allowance selects a single source/passage of at most 450 characters. `expand_compact` maps 0 to no record, 1 to observed attack, 2 to advisory, 3 to background; Python supplies quotes, IDs, unknown dates and limitations.
- `devsecops/agents.py`: `research_incidents` delegates retrieval; `review_security` receives bounded views and uses `REVIEW`. Reviewer must consider counterevidence, observed versus inferred facts, unknown prerequisites, and at most one follow-up.
- `devsecops/context.py:reviewer_views`: reduces observations to sixteen, incidents to four, and shortens fields. The Phase 0 reviewer builder accepts these views, not the full repository.
- `devsecops/providers.py:ModelClient.call`: provider-specific structured requests, untrusted-evidence boundary, budgets and bounded retries. Current researcher selection uses schema identity (`schema is contracts.COMPACT_INCIDENT`), so a future provider adapter must preserve explicit mode dispatch rather than rely on a copied dictionary having the same identity.

No adapter has been installed into the live application. Search plans and follow-up response contracts are not training targets in Phase 0. Normal research window/technique metadata is not in the minimal smoke envelope; add explicit versioned fields after parity fixtures rather than silently discarding it in a live integration.

## Vision Native RAG

Repository: `D:/Code/Projects/Vision_Native RAG pipeline`.

- `src/vision_rag/core/generator.py`: legacy abstract `generate(query, images) -> str` alone is insufficient for the live grounded path.
- `src/vision_rag/models/gemini_generator.py:generate_grounded`: takes query, evidence metadata and ordered PIL page images, returns a dictionary, supports optional streaming/cancellation, and exposes usage.
- `src/vision_rag/generate/grounding.py:GroundedSynthesizer.query`: validates storage document/version/page identity, resolves images, calls `generate_grounded` or its streaming counterpart, validates references, and requires requested documents to be represented in cited sources.
- `src/vision_rag/generate/grounding.py:validate_answer`: requires claims for supported/conflicting, no claims for insufficient, valid supplied citations, and two distinct citations for conflict.
- `src/vision_rag/api/routes.py`: constructs the generator and the grounded synthesizer in the active query path. This is not only a base-URL substitution.

Phase 0 preserves metadata fields `id`, `document`, `version_id`, `page`, `text`, plus image order. The application retains `document_id` and `build_id` in its source map and continues source/version checks before and after generation. The smoke bound is two pages; it may reject ordinary larger application requests until later measured capacity work. Streaming, cancellation, `last_usage`, `close`, legacy `generate` and requested-document end-to-end behavior still need a full generator implementation and application parity tests. Comparison generation is excluded.
