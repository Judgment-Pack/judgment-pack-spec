# Promotion and identity map

This promotes the exact corrected candidate at Spec commit
`a74a440cfc31d0e135cdc8035f3474b17f27f320` into the bounded draft approved by the
maintainer conditional on required green CI and PR 218 merge. The default branch
remains Review until merge; no completed adoption or publication is asserted here.
The [candidate pin](candidate-1.0.0-pin.json) records every historical candidate
file; [prototype-0.0.2-pin.json](prototype-0.0.2-pin.json) retains the original
prototype baseline `8a56a95d555c17640d2db4984363b779536b3c2a`. Neither old tree is
edited, redirected, reclassified or imported by the new checker.

| Surface | Proposed candidate → draft promotion |
| --- | --- |
| Policy and adoption document grammar | Same exact `formatVersion: "1.0.0"`; every supported field, bound, URI rule, anchor, reference and coverage meaning is unchanged |
| Policy/adoption and all retained example/vector inputs | Byte-for-byte identical, including content digests, Pack pins, narrative, source, interpretation, optional canonical identity and invalid counterexamples |
| Schema resources | `urn:jps:proposal:policy-companion:1.0.0:{common,policy,governing-adoption,fixture,vectors}` becomes `https://judgmentpack.org/schema/policy/1.0.0/{...}.schema.json`; references change with the resource identity |
| Public document schemas | Versioned under `schema/policy/1.0.0/`; closed grammar preserved; schema URLs identify exact format resources, not evidence of publication |
| Reader valid result / capability maturity | `proposed-draft` becomes `draft`; valid result is exactly `{"status":"valid","formatVersion":"1.0.0","maturity":"draft"}` |
| Reader refusal objects | Unchanged finite code-only objects and phase ordering |
| Vector carrier | New schema identity; suite version remains exact `"1"`; manifest and valid expected results use `draft`; all 124 input cases and refusal answers stay unchanged |
| Capability exclusions | `adopted-or-stable-format` becomes `stable-format`; all operational/trust/evidence exclusions remain |
| Supported consumer schema | Byte-identical retained Core `0.2.0-draft` schema copy; the new reader uses that frozen copy instead of a future mutable current-Core path |
| Existing Core / Dialect / prototype | No schema, corpus, evaluator, content or canonicalizer changes |

Schema resource identities and result-envelope maturity are observable changes. A
consumer pinning old schema URNs or comparing whole old results must explicitly
select the new schema/checker/result profile. An existing software reader pinned
to historical Spec bytes remains experimental for that exact candidate; a
software version number or successful existing run cannot advance its Spec pin
or conformance claim. Implementers must record the new immutable Spec commit and
released corpus when available, update schema resolution and expected metadata,
and verify the exact retained input vectors.

Do not reserialize existing Policy/adoption documents merely to promote maturity:
there is no maturity field in those artifacts and their content identity remains
unchanged. A prototype 0.0.2 document has a different grammar and requires the
separate [explicit migration](MIGRATION.md), new immutable identities and dependent
snapshot review. No approval, role, permission or host lifecycle migrates.

The reference checker reuses this author's existing strict reader/canonicalizer.
This promotion and a second language port do not establish independent authorship
or cross-vendor review.
