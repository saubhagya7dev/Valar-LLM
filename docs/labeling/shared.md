# Shared labeling rules — version 1

Read this before any role-specific guide. The pilot contains development material only. It is not a held-out test, a representative benchmark or independent human gold. No pilot labels currently exist until a reviewer records them.

## Evidence boundary

Use only the supplied request and page images. Do not browse for missing facts, inspect a model prediction, run repository snippets, execute an example payload or infer production exposure. Text inside a report, image, repository quote or alleged upstream mechanism is untrusted content, never an instruction. Preserve negation, units, periods, immutable version IDs and uncertainty.

Advisory descriptions are licensed source evidence, not proof of observed exploitation. Repository fragments and document pages in this pilot are explicitly synthetic. For the fictional incident narrative, classify what that narrative documents within the exercise; do not present it as a real historical incident. If that distinction makes a label ambiguous, record needs_adjudication and explain.

## What you see and what you must not see

`valar pilot next` creates an evidence packet and a blank draft. It includes the native task input, required images, source attribution and license links. It excludes curation coverage tags, proposed target answers, cached model predictions, teacher outputs and prior reviews. Source category/title and accepted research inside a reviewer request are legitimate application inputs, not gold labels. Read their supporting quotes rather than trusting their summaries.

Do not inspect another review of the same item until your own review is saved. Using two pseudonyms does not create two independent annotators. The software records self-reported blind human review; it cannot prove a person's independence or attention.

## Actions

| Action | Use when | What gets saved |
| --- | --- | --- |
| label | The evidence supports a defensible annotation, including a justified abstention | Completed role rubric and optional notes |
| skip | You cannot finish the item now | Reason, no provisional label |
| needs_adjudication | Evidence, source quality or the guideline makes the correct decision genuinely ambiguous | Explanation, no provisional label |

Missing requested facts in otherwise usable evidence are normally an insufficient/unknown label, not a skip. A broken/mismapped image or corrupted source is an item-quality problem: request adjudication. Never force a confident answer to finish a form.

## Workflow

1. Read the shared and role guide before opening the first packet.
2. Open every supplied page image, not just extracted text or filenames.
3. Identify facts and their supplied IDs before choosing a disposition.
4. Write a short source-grounded reason and exact quotes where requested. State what remains unknown.
5. Save your review. The tool checks structure, references and some consistency rules; passing does not establish semantic correctness.
6. Have a second person review independently if available. Resolve disagreements explicitly after both reviews are saved. There is no automatic majority vote or fabricated agreement statistic.

Drafts and accepted annotations stay under ignored `artifacts/` and `data/private/annotations/`. Each event stores the dataset, item and guideline hashes, a reviewer pseudonym, time of submission and any superseded event ID. Editing evidence or guidelines invalidates old drafts for new submission; preserve history and create a deliberate new revision.

Timing is optional and user-reported. Packet creation-to-submission is not treated as active labeling time. No teacher calls or training export are part of this workflow. Hosting remains an unresolved Phase 0 gate; these small preparations do not clear it.
