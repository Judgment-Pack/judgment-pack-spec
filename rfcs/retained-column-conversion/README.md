# Retained column conversion draft artifacts

These files support Draft [RFC 0029](../0029-retained-column-conversions.md). They are not
published normative resources or whole-document/preparation verification. No current capability
is established here. The schema validates structure only; readers also enforce exact byte limits,
UTF-8/scalars, duplicate rejection, embedded JSON, cross-member constraints and conversion semantics.

`cases.json` contains handwritten expectations (including the preserved 36 compatibility cases),
not recorded outputs. `examples.json` contains labelled fragments. `reader.py` and `reader.mjs`
separately implement conversion preview and unchanged canon claim admissibility using exact
rational arithmetic. Both have the same author/assisting model; they are not independent authorship
or cross-vendor evidence. `check.py` drives both over the same cases. No network, package install,
model call, acquisition, evaluation or preparation is performed.

Run `python3 -B rfcs/retained-column-conversion/check.py` from the repository root. Python 3 with the repository’s `jsonschema` development dependency and Node 22 or later are required. Set `RFC0029_NODE` to an explicit supported Node binary when
the system `node` is older. The check prints a bounded summary and does not install
anything. Standard input to each reader is one JSON request per line: `{rule,frame}` or a
`{binary64Hex}` shortest-rational probe. Output is a preview plus `claimAdmissible`, or a refusal.
The Draft also exposes `{restore,profile,limits}`: `restore` is the closed four-member generated
carrier and limits contains exactly `originalSnapshotBytes`/`carrierBytes`. Restoration verifies
raw UTF-8 snapshot length/SHA-256 and returns the identical text, not an object serialization.
The complete received carrier bytes are separately counted; nested retained-frame bytes retain
the existing frame bound. The bounded line channel remains 4200000 bytes.

`{admission:{capabilities,required,sizes}}` checks the RFC's closed role-specific shape and exact
trusted expected Spec/schema/corpus pins before any callback. `required` is a complete capability
entry with the caller's limits; every role-applicable size is required. The effective bound is
the lower caller/reporter maximum per member. This is an admission-contract probe, not evidence
that reported sizes came from real production artifacts or that a production role is supported.
`{lineage:{rule,frame,profile?}}` derives the closed inline fragment and refuses issues or noncanon
values as `read-failed`. No failed application receives success lineage.

Run `python3 -B rfcs/retained-column-conversion/check.py --carrier-only` for the focused changed
carrier/capability/lineage fixtures. The default command also runs the preserved conversion corpus;
it is reserved for the stable candidate gate. New cases are handwritten, including original
revision 7 alongside current revision 8, exact numeric/Unicode/raw spellings, missing/null/empty,
complete role-limit boundaries, callback ordering, and intended safeguard-removal controls in
both readers. Examples show full asserted-origin append and distinct published/bound identities;
they are labelled fragments, not producer admission runs. Schema member/alternative removal
controls cover the new closed shapes; duplicate names and byte semantics require the readers.

The conditional document 1/2 MiB, combined 6/12 MiB and standalone producer transport 3 MiB
figures remain proposals. Preparation/record 8/16 MiB accounting, actual producer transport,
original inventory commitments in complete receipts, Runtime/Runner integration, independent
production recomputation, exact-head CI/review and normative adoption remain prerequisites.
