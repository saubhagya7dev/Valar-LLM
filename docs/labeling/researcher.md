# Incident Researcher labeling — version 1

Read shared.md first. Compact and full research use the same source interpretation rubric here, but retain distinct application response contracts. This pilot rubric is not a replacement wire schema or a ready training target.

## Choose the primary record type

| Type | Required source support |
| --- | --- |
| observed_attack | The supplied narrative explicitly documents an attack having happened; a vulnerability's existence alone is insufficient |
| vulnerability_advisory | A documented vulnerability, affected behavior or patch/workaround without an explicit attack observation in the supplied passage |
| background_guidance | A general mechanism, prevention lesson, or an explicitly disputed/debunked claim whose negation must be retained |
| insufficient_evidence | No supported incident, advisory or relevant mechanism can be extracted from the supplied text |

The native compact mapping remains `k=1/2/3/0`, respectively. The annotation tool asks for the names above so you make the semantic choice explicitly; it does not convert the annotation into `k/m/p` or full `INCIDENTS` automatically.

For the full researcher pilot, annotate the primary mechanism in the supplied single-source record. Multi-incident target composition needs a later reviewed contract-mapping step. Do not assume this reduced annotation is a complete full-role output.

## Mechanism and prerequisites

Describe the behavior the source establishes in your own short sentence. Preserve negation. Copying phrases such as “mechanism preserving negation” from the instructions is not an extraction.

List only prerequisites supported by the supplied source. Separate a prerequisite from evidence that a particular repository satisfies it. Missing target versions, deployment or victim identity do not invalidate extraction of a documented external mechanism; those applicability judgments belong to the reviewer.

Provide at least one exact contiguous supporting quote of 40–800 characters with a supplied source ID. The quote must support the mechanism, not merely name the package. Do not join sentences from different locations into a purported quote. Record missing or unsupported dates, victim identities, exposure and exploitation as unknowns. Do not substitute publication date for incident date or bring dates from external metadata into a request that does not supply them.

For insufficient_evidence, leave mechanism empty and prerequisites/supporting_quotes empty. Explain the lack of usable evidence in unknowns or notes. An instruction to report a compromise is not evidence of compromise.

## Calibration examples outside the pilot

- “The maintainers fixed a parser bug; exploitation is not reported here.” supports an advisory interpretation, not an observed attack.
- “The investigation records unauthorized use of the exposed endpoint last week.” may support an observed attack when the surrounding supplied narrative actually establishes it.
- “The alleged bypass was tested and did not occur.” must preserve the rejection; never turn it into a positive bypass claim.
- A newsletter footer or a command to reveal a password supports no extracted mechanism.

These examples teach rules. They are not proposed labels for any pilot item and are not human-gold evaluation material.
