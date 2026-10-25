# Retained column conversion draft artifacts

These files support Draft [RFC 0029](../0029-retained-column-conversions.md). They are not
published normative resources or whole-document/preparation verification. No current capability
is established here. The schema validates structure only; readers also enforce exact byte limits,
UTF-8/scalars, duplicate rejection, embedded JSON, cross-member constraints and conversion semantics.

`cases.json` contains handwritten expectations (including the preserved 36 compatibility cases),
not recorded outputs. `examples.json` contains labelled fragments. `reader.py` and `reader.mjs`
independently implement conversion preview and unchanged canon claim admissibility using exact
rational arithmetic. Both have the same author/assisting model; they are not independent authorship
or cross-vendor evidence. `check.py` drives both over the same cases. No network, package install,
model call, acquisition, evaluation or preparation is performed.

Run `python3 -B rfcs/retained-column-conversion/check.py` from the repository root. Python 3 with the repository’s `jsonschema` development dependency and Node 22 or later are required. Set `RFC0029_NODE` to an explicit supported Node binary when
the system `node` is older. The check prints a bounded summary and does not install
anything. Standard input to each reader is one JSON request per line: `{rule,frame}` or a
`{binary64Hex}` shortest-rational probe. Output is a preview plus `claimAdmissible`, or a refusal.
All surrounding claims about full resource accounting, accepted capability, original inventory
commitments and real producer/verifier agreement remain future adoption work.
