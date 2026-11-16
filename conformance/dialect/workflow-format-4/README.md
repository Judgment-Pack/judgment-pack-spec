# Workflow stages of dialect formats 4.0.0 and 4.1.0

Hand-written vectors for RFC 0020's amendment of 2026-11-15 (issue #326), of `specVersion` `0.6.0`: a workflow stage
whose dialect is of format `4.0.0`, and one whose dialect is of format `4.1.0`. They are not a
conformance corpus, and no claim may cite them.

Each case has a workflow document of one stage, valid against the `0.6.0` schema
`schema/workflow-1.schema.json` and invalid against `0.5.0`'s, `schema/workflow-1-0.5.0.schema.json`,
and a retained release whose `inputMapping` is the stage's dialect. The dialects are the
format vectors' own: [`format-4/case-rule-no-sources/`](../format-4/case-rule-no-sources/) and
[`format-4.1/paged-three-pages-no-next/`](../format-4.1/paged-three-pages-no-next/). The manifest
gives each stage's dialect digest, SHA-256 of the dialect's `canon` bytes, and its release digest,
SHA-256 of the whole release's `canon` bytes (RFC 0020 section 1). Both were computed
with a general-purpose JSON serializer and SHA-256, not by the reader under test.

A third case, `stage-4.0.0-runner-members`, shares the format `4.0.0` stage and dialect. Its release
`stage-4.0.0.runner-release.json` has the four members of the other releases and every other member
judgment-pack-runner's `Release` declares, 21 in all (RFC 0020 section 1 lists them), so its digest
covers members such as `createdAt`, `preview`, `validation` and `sample`. Their values are
hand-written placeholders in the Runner's shapes, not a Runner's bytes, and the encoding turns on
none of them.

Each stage is terminal, since no stage consumes it, so it carries no `selection` (`spec/workflow.md`
§3). A fourth case, `stage-4.0.0-terminal-selection`, is the format `4.0.0` stage with
`selection: {mode: "reviewer"}` added. The schemas cannot see which stages consume which, so the
schema admits it; the workflow reader refuses it `input-malformed`, naming the rule
("selection belongs to producing stages only").

The Python reader's `release_digest_bytes` (`tools/workflow_reader_encoding.py`) gives both release
digests, and the pinned Runner encoding would give others, since it drops the case's `rule` and the
source's `paging`. The workflow reader admits each stage's selector (`admitted` in the manifest), and
the stage's dialect reference, not the release, selects that digest rule.
`tests/test_workflow_format_4.py` holds them to the manifest.
