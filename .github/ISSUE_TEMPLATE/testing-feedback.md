---
name: Testing feedback
about: Report schema, authoring, reference-model, or testing-guide feedback using synthetic data
title: "[Testing] "
labels: ""
assignees: ""
---

<!--
Thank you for testing the JPS research preview.

Do not include customer, employee, personal, confidential, regulated, credential, or production
data. Remove access tokens, internal URLs, organization names, and real policy text. Use a minimal
synthetic reproduction. Anything submitted here may become public.

This template is for structural-validation and authoring feedback. Core 0.1.0-draft has no
evaluator conformance class, so please do not describe an inferred outcome as an evaluator result.
-->

## What did you test?

<!-- Baseline validation, intentional structural failure, local-reference review, or synthetic authoring exercise. -->


## Tool and settings

- Repository commit or release:
- Validator name and version:
- JSON Schema dialect selected:
- Format assertion enabled (`uri`, `date`, and `date-time`): yes / no / unknown
- Operating system (optional):

## Minimal synthetic example

<!--
Paste the smallest safe example or link to a proposed fixture. Do not include real records,
policies, or source locators.
-->

```json

```

## Observed result

<!-- Include accept/reject, diagnostics, instance location, and schema location when available. -->


## Expected result or clearer behavior

<!-- Explain what you expected and why. It is okay to report uncertainty about the intended behavior. -->


## Feedback area

- [ ] JSON Schema acceptance or rejection
- [ ] Carrier behavior outside JSON Schema (for example, duplicate object member names)
- [ ] Authoring experience or missing concept
- [ ] Local IDs or references
- [ ] Documentation clarity
- [ ] Boundary between structure, semantics, authority, and evaluation

## Safety and scope checklist

- [ ] The reproduction is synthetic and low risk.
- [ ] I removed sensitive data, credentials, internal URLs, organization names, and real policy text.
- [ ] I am not treating schema acceptance as proof of truth, authority, safety, or operational fitness.
- [ ] I am not claiming evaluator conformance under `0.1.0-draft`.
