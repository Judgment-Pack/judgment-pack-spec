# Explicit migration from prototype 0.0.2

This is the breaking migration to the **Policy draft** `formatVersion: "1.0.0"`,
whose acceptance takes effect only upon required green CI and PR 218 merge.
The default-branch RFC remains Review until then; publication is a separate step. Neither semver arithmetic nor opening a document consents
to migration. The draft reader refuses prototype documents; it never upgrades
or reinterprets them. Prototype 0.0.1 needs its own explicit path to 0.0.2 and is
not silently accepted by this guide.

1. Keep the original 0.0.2 Policy, adoption, fixture and all retained bytes. Record
   their exact digests and the original prototype pin. Migration creates new
   reviewable artifacts; it does not overwrite history.
2. Obtain explicit author/operator intent to migrate, including which exact Policy
   versions, consuming Pack and adoption scope are intended. Explicitly choose
   `workspace-managed` for former `desk-managed` content, or retain
   `externally-managed` intent. Do not infer intent from an imported source's owner,
   publisher, folder, citation, access response or approval history.
3. Preserve the source, narrative, interpretation/review-basis and consumer bytes
   **exactly**, with their existing raw digest, length and declared media types.
   Preserve anchors, local section/source IDs, opaque provider revisions and Pack
   `specVersion`/identity. Do not extract, normalize, reserialize or rewrite those
   files just to satisfy migration. Re-extraction or changed meaning is separate
   authoring and requires a fresh review.
4. Construct a new Policy by removing the complete `prototype` wrapper and adding
   the exact string `formatVersion: "1.0.0"`. Replace `desk-managed` with the
   explicitly selected `workspace-managed`. Preserve the rest of the supported
   content/provenance/sections. Choose the Policy's new immutable identity/version
   explicitly: preserve its stable series ID only with a new artifact version, or
   fork to a new ID. Never reuse an existing immutable `(id, version)` with changed
   bytes. This offline checker cannot detect historical reuse on its own.
5. Serialize and retain those new Policy bytes. Regenerate the raw content digest
   and length and, when requested, the `jps-canon` canonical identity. Update every
   dependent adoption's exact Policy reference (ID, artifact version, bytes and
   optional canonical digest); a stale old hash must refuse. Keep the exact Pack
   bytes/reference; a different Pack is a separate new interpretation.
6. Construct a new adoption with `formatVersion: "1.0.0"` and no prototype wrapper.
   Choose its immutable identity/version explicitly. Preserve or deliberately
   re-review its exact scope and total coverage; do not fill omissions or upgrade
   manual/pending/out-of-scope clauses automatically. Retain new adoption bytes,
   regenerate their identities wherever referenced, and validate the full supplied
   material under the draft checker and vectors.
7. Re-review dependent release/registration/export snapshots that pin changed Policy
   or adoption bytes. Keep historical snapshots and runs on their original pins.
   A new snapshot is an explicit host operation, never a side effect of parsing or
   importing a document. Host authority and current admission remain separate.

No approval, signature, authenticated review assertion, role, permission, lifecycle
state, publication receipt or dispatch grant migrates automatically. Existing
review-basis bytes remain historical explanations only. Even if every narrative
byte and clause ID is unchanged, a host must obtain fresh applicable authorization
for its new candidate and workflow, under its own contract. Informational sources
stay informational; making one governing requires a reviewed new adoption.

The three retained examples intentionally use new Policy/adoption IDs and retain
the old consumer/source/narrative/interpretation files unchanged. Their new hashes
are reproducible examples, not migrated organizational approvals. There is no
migration helper or implicit parser fallback in this slice.

Promotion from the proposed 1.0.0 grammar changes no Policy/adoption artifact
bytes. See [PROMOTION.md](PROMOTION.md) for schema URNs and result-envelope
maturity changes; do not rewrite retained documents to change their maturity.
