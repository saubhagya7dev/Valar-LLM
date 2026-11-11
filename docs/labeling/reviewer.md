# Security Reviewer labeling — version 1

Read shared.md first. Review the quoted external source before trusting the accepted record's title, mechanism or category. Its summary may be wrong. Read repository observation quotes before accepting their claims.

## Assess every material prerequisite

Write one assessment per prerequisite needed for the proposed mechanism to apply. Cite supplied incident IDs and repository observation IDs and give a short reason.

| State | Meaning |
| --- | --- |
| supported | Direct observed repository evidence establishes the prerequisite within the supplied coverage |
| contradicted | Supplied counterevidence establishes that the prerequisite does not hold, or a material source claim is refuted |
| unknown | The evidence does not establish either side; inferred architecture, version ranges and missing deployment context remain uncertain |

An `inferred` observation alone cannot support a prerequisite. A package name alone does not establish the vulnerable version or behavior. A declaration such as `library>=2` is not a resolved version. A mitigation listed by an advisory is not automatically a defense implemented by the repository.

For a source claim that is itself debunked, reject the match and explain from the source quote. Do not manufacture an otherwise unknown vulnerability simply because version details are missing.

## Overall disposition

| Disposition | Conditions |
| --- | --- |
| supported_concern | Supported external mechanism, all material prerequisites supported by observed evidence, nonempty citations, and no missing material information |
| needs_verification | Supported external mechanism with one or more unknown prerequisites or required missing facts |
| background_lesson | A useful supported general lesson without evidence establishing a repository concern; shared stack alone belongs here |
| reject_match | A material prerequisite is contradicted or the external mechanism is not substantiated by its own quote |
| insufficient_context | The available inputs do not support even a reliable applicability classification; explain the precise gap |

A supported concern is not confirmed exploitability, a complete audit or permission to probe a live system. Do not recommend live network tests as though authorization exists. Favor reviewing the supplied/configured artifacts and state any additional access that would be required separately.

Write observed existing defenses, missing information and a concise reason. Every reference must be supplied. A label that simultaneously calls exposure supported and says exposure is unknown is inconsistent. The tool can catch some state/reference contradictions; it cannot determine that you enumerated every prerequisite or interpreted a quote correctly.

## Calibration examples outside the pilot

- A vulnerable-version declaration with no deployment information leaves deployment prerequisites unknown.
- A source requires attacker-controlled template source; a quoted static template literal is relevant counterevidence, not proof that the unsafe path exists elsewhere.
- A workaround in an advisory does not become an existing repository defense until repository evidence shows it.
- A guessed public architecture is not observed public exposure.

Do not use these examples as an answer key. Evaluate each supplied request and its coverage independently.
