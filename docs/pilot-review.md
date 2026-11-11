# Pilot development review

This work is authorized preparation while the Phase 0 hosting gate remains unresolved. There is no large collection, teacher labeling, model call or training run in this workflow.

## What is ready

`data/pilot/v1/manifest.json` describes 24 **unlabeled development items**: eight researcher items (four compact and four full), eight reviewer items and eight Vision items, across eight source families. No training examples or held-out tests are created. A source family's related research/review cases and page/version variants stay in development together.

Three real public sources come from the GitHub Advisory Database at the immutable revision in `sources.lock.json`. Its CC BY 4.0 license snapshot, contributor attribution, original URLs, per-file hashes and transformations are preserved. Synthetic repository fragments and five rendered document pages are original project material declared CC0-1.0. No private repositories or uploads were collected. Input selection, synthetic contexts and upstream reviewer records were prepared by Codex; they are not independently verified supervision.

The first batch targets advisory-versus-attack confusion, copied instructions, unknown deployment/version prerequisites, ignored defenses, source-quote contradictions, image-only values, units, periods, version conflicts and embedded image instructions. Curation tags are excluded from review packets. The batch is small and biased toward known failures, so it supports workflow development, not representative accuracy claims.

## Start a blind review

Read [shared rules](labeling/shared.md), then the relevant [researcher](labeling/researcher.md), [reviewer](labeling/reviewer.md) or [Vision](labeling/vision.md) guide.

```powershell
uv run valar pilot validate
uv run valar pilot review --reviewer reviewer1 --item P001
```

Use a short pseudonym rather than an email address. The command prepares a packet, prints the supplied evidence and asks for your own choices with no default selection. Open any printed PNG paths before answering Vision questions. You may label, skip or request adjudication. Quote text and IDs must be copied from the supplied input, not looked up externally. Stop with Ctrl+C if interrupted; an unfinished draft is not an accepted label.

Accepted records go to ignored `data/private/annotations/pilot-dev-v1/`. Packets/drafts are in ignored `artifacts/pilot-review/`. Nothing is uploaded. The program cannot prove the reviewer is human or independent; its metadata explicitly records self-reported human blind review.

## Edit a draft instead of using terminal prompts

```powershell
uv run valar pilot next --reviewer reviewer1 --item P001
# Open the printed packet.md and annotation.json; fill the rubric using the guide/schema.
uv run valar pilot record artifacts/pilot-review/reviewer1/P001/annotation.json
```

The initial draft has `action: pending` and `rubric: null`. It is deliberately not a proposed answer. For a valid label, use `action: label` and the role rubric. For skip/adjudication, keep rubric null and supply a reason in notes. Research/reviewer rubrics collect human decisions and references, not the full application output contract. Mapping them into training responses is separate work requiring another review; this tool does not create training targets.

The generated review schema is `schemas/pilot-annotation.v1.json`. A researcher rubric contains role, record_type, mechanism, prerequisites, supporting_quotes and unknowns. A reviewer rubric contains role, disposition, prerequisite_assessments, existing_defenses, evidence_ids, incident_ids, missing_information and reason. A Vision rubric contains role, status and claims with citations. No field should be filled from a teacher output during blind review.

If an event already exists for a reviewer/item, submission requires `--supersedes <previous-event-id>`. Earlier records are preserved. Packet generation refuses to overwrite an existing packet, so edit that draft or choose a different `--packets` directory. When resuming an interrupted wizard, use the edit-and-record workflow to preserve the existing draft.

## Progress and disagreements

```powershell
uv run valar pilot report
```

Reports contain counts and IDs rather than private annotation text. Distinct reviewer IDs do not imply independent people. The tool flags differing primary labels for the same item; it does not compute kappa, award gold status or silently adjudicate. Inspect prerequisite and citation differences as well as the primary label. A second actual reviewer should work independently before seeing the first person's responses. Save any reconciliation as an explicit superseding review with a note describing who resolved it.

Neither review completion nor successful structural validation measures model accuracy. No teacher predictions, label-quality score, inter-annotator statistic or unseen-data result is invented.

## Provenance and split rules

Source snapshots and license text are hash-checked offline. Images are checked both by encoded bytes and decoded RGB pixels, then matched to immutable version/page metadata and evidence order. Exact input/content and five-token-shingle near duplicates cannot cross partitions. The validator additionally excludes old smoke requests/images from the new batch. Near-duplicate detection is a heuristic; it does not prove semantic deduplication. Related CVE/advisory identities are grouped deliberately by the curator.

The current manifest allows development only. `splits.json` has empty train/test lists. Do not rebrand these seen development cases as an untouched test. Guideline, item and manifest hashes are bound to every submission. Future real held-out sources and annotation procedures must be established separately before predictions are inspected.

## Remaining gaps

Human labels: none until you submit them. Independent adjudication: not performed. Real observed-attack reports, diverse repositories, real licensed charts/scans, illegibility and multi-page coverage: still needed. Teacher-output terms and quotas: unverified; no teacher harness is activated. Training export and public hosting: unavailable. The online smoke's single image and earlier mistakes do not establish three-role replacement quality.
