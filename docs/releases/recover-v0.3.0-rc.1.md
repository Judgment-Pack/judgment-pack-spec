# Recovery of the unchanged 0.3.0 release candidate

The original release run [40192247704](https://github.com/Judgment-Pack/judgment-pack-spec/actions/runs/40192247704)
failed before packaging. Node exited successfully with 271 passes, but the Python test expected TAP
summary lines while Node emitted another reporter's output. The release job had omitted the declared
Node setup used by repository CI. The runner's actual Node version was not recorded; this account
does not infer it from the runner image. Issue [261](https://github.com/Judgment-Pack/judgment-pack-spec/issues/261)
remains open until recovery evidence is recorded. Future ordinary tag releases set up the declared
Node/Python toolchains, and the reader test explicitly selects TAP without weakening its assertions.
That parsed subprocess clears ambient `NODE_OPTIONS`: Node accumulates reporter options rather than
overriding them, so an ambient reporter otherwise conflicts with the explicit argv reporter. Its
existing execution flags remain explicit; unrelated Node subprocess environments are unchanged.

The signed annotated tag `v0.3.0-rc.1`, object `c0ddd58e507ce42891947929acb1ad0330faa038`,
remains at artifact commit `495535f29a517dc6a36075b77238634011e7371e`. Recovery never moves it,
patches that checkout, creates a second candidate, or marks the failed run successful. It introduces
no format, corpus, maturity or release-builder change.

## Reviewed dispatch

After this correction's full checklist, exact-head CI and independent review are accepted, the
coordinator records the immutable **merged main workflow commit** and its checks/review evidence.
Dispatch `recover-core-rc.yml` on `main`, supplying only `expectedWorkflowCommit=<that full SHA>`.
If main has advanced, the actual workflow SHA will differ and recovery refuses; review and record the
new workflow revision before dispatching. A similarly named branch, fork, tag, push event, arbitrary
artifact input, dirty checkout, changed local/remote tag, missing milestone, unknown API response or
existing release (including a draft) refuses. There is no rerun/overwrite or publication command.

The workflow checks out its own revision into `recovery/` and the original artifact commit into
`artifact-source/`. It calls the original milestone and checkout validators with the artifact root,
validates the actual dispatch independently, and uses the original artifact validator and builder.
It checks the original `dev.json` declares Node 22, Python 3.12 and the complete seven-step checklist.
After setup, runtime validation requires Node 22.18 or later within major 22 and Python 3.12 before
tests can skip for unsupported Node. It installs the original requirements including format extras and runs the full original setup and
checklist. `NODE_OPTIONS=--test-reporter=tap` supplies the reporter to the unchanged old Python test;
no file is injected, no test is skipped, and both subprocess status and parsed pass/fail assertions
still run. Failure stops before packaging. Logs record exact patch versions and both source commits.
Only admission, packaging, provenance verification and draft creation receive the GitHub API token;
dependency installation, runtime version checks and tests do not receive that environment variable.

Before packaging and draft creation, remote unavailability, tag drift or a release/draft causes
refusal. The published-only tag lookup cannot prove draft absence: after recovery created draft
`423420021`, that tag route still returned404. The guard now requires the exact repository/id and
explicit authenticated `permissions.push:true` from repository metadata, then walks the release-list
API that exposes drafts to push-capable callers. It rechecks visibility at completion. Missing or
insufficient permission evidence, API errors, malformed/duplicate data, inconsistent/wrong-repository
pagination or exhausted bounds cannot establish absence. It reads at most20 pages of100 releases,
with at most16MiB per API response; a full page without completion evidence requires another page.
Every exact matching tag refuses, regardless of draft/public state or whether it has assets.
See GitHub's [release-list visibility contract](https://docs.github.com/en/rest/releases/releases#list-releases),
[repository metadata](https://docs.github.com/en/rest/repos/repos#get-a-repository) and
[pagination contract](https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api).

Creation remains under the normal release tag's concurrency lock and uses `gh release create`
without replacement flags. The observations are not a transactional repository snapshot or a lock
on outside GitHub clients: a concurrent external change after the final observation remains a race.
No cleanup/delete/overwrite route is provided. Any unexpected creation outcome requires investigation;
never retry against, replace or delete the existing draft/assets. The successful recovery's existing
assets/attestations retain workflow revision `dc8825c41b1f834fce63b798a92ef4a115d5bfb6`;
this guard correction neither rebuilds them nor relabels their provenance.

## Provenance has two source identities

GitHub's attestation certificate identifies the recovery workflow on `refs/heads/main` and its exact
reviewed commit. It does **not** attest that its source-repository commit is the original RC tag.
Both archive attestations and the separately attested `recovery-evidence.json` must cryptographically
verify against that actual main workflow identity. The evidence binds that workflow revision to the
fixed tag object, original artifact commit, actual workflow run/attempt, milestone, original manifest hash, actual toolchains,
validation-log hashes and original archive/checksum hashes. This is a reviewed builder assertion,
not independent proof from a certificate naming the old tag.

The archive verifier separately compares tar and zip inventories and every original-source member
byte with the original committed Git blobs. Only the builder's existing `release-identity.json` is
generated; its source commit must equal the original RC commit. Staged evaluation/witness/dialect
rows, the workflow draft and independently packaged Policy corpus/schema remain excluded. All
historical schema members are compared like every other committed member. The RC distribution map,
notes, draft maturity and original bundle identity/bytes remain unchanged. Recovery evidence and
setup/validation logs are additional assets outside the original bundles/checksums.

For **each** archive and `recovery-evidence.json`, use the supported GitHub CLI and the recorded
workflow SHA, with these exact constraints (also executed before draft creation):

```sh
gh attestation verify "$asset" --hostname github.com \
  --repo Judgment-Pack/judgment-pack-spec \
  --cert-identity 'https://github.com/Judgment-Pack/judgment-pack-spec/.github/workflows/recover-core-rc.yml@refs/heads/main' \
  --cert-oidc-issuer https://token.actions.githubusercontent.com \
  --source-ref refs/heads/main --source-digest "$workflow_commit" \
  --signer-digest "$workflow_commit" --deny-self-hosted-runners \
  --predicate-type https://slsa.dev/provenance/v1 --format json
```

`--cert-identity` enforces the exact certificate SAN, and the digest flags bind both source and
signer revisions; unsupported flags, missing attestations, cryptographic failure or empty/malformed
verification results refuse. No new CLI version cutoff is inferred from flag availability. The
[GitHub CLI manual](https://cli.github.com/manual/gh_attestation_verify) and its
[version 2.96 command contract](https://github.com/cli/cli/blob/v2.96.0/pkg/cmd/attestation/verify/verify.go)
distinguish certificate identity from user-controlled predicate claims. Verification JSON must be
retained with the run evidence. Do not pass the old tag to `--source-ref` or its commit to the source
certificate digest flags; that would claim a different provenance context.

Before public publication, the coordinator downloads the draft assets, repeats checksum and archive
blob/inventory/identity comparisons against the fixed original tag, verifies all three attestations
with the recorded workflow SHA, and compares recovery evidence/log hashes and both source identities.
Also inspect the actual certificate claims, not merely a success label. Any mismatch holds
publication. The workflow creates only a draft prerelease. The approximately one-week adopter period
starts when the RC is actually public, not at the tag, failed run, draft or preparation time.
