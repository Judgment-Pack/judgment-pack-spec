# Public worked-example downloads

These are informative website materials, outside `examples/` and `conformance/`.
They include companion-tool conventions and do not change or extend JPS Core.

Each directory named in `WORKED_DEMOS` in `web/build.py` has a `manifest.json` that
explicitly lists its public files with reviewed
SHA-256 digests. The site build verifies those bytes, copies only that list, and creates
a deterministic ZIP, per-file `SHA256SUMS`, and a checksum for the ZIP. An extra file
in the source directory is never implicitly published. There is no dependency on a
developer's Desk directory, Runtime, Runner, browser, AI provider or credentials to
build the site.

The printable source for each example is `<example>/one-page.html`. Each committed PDF was
printed from it using Chromium, CSS page size (A4), background graphics enabled, and
no browser headers or footers. The site build serves the committed PDF; it does not
need Chromium. Review its one-page output before updating its manifest digest.

Keep public bundles synthetic and self-contained. Review pack and test results using
the runtime version documented in the bundle. Do not include local IDs, absolute paths,
Desk state, job/run records, credentials, personal meeting notes or customer data.

Published versioned download paths must remain available. For a future version, add a
new directory and retain the old artifact URLs and checksums; do not replace the old
pack or fixtures in place. The walkthrough links the current example separately from
the immutable specification tag and its normative conformance corpus.

## Worked examples

- Deal evidence readiness: v0.2.0, 40 project test cases.
- Data release readiness: v0.1.0, 18 project test cases.
- Fleet maintenance review: v0.1.0, 18 project test cases.
- Location campaign readiness: v0.1.0, 18 project test cases.
- Contractor order readiness: v0.1.0, 18 project test cases.

The bundles contain offline inputs and setup instructions, not exported local Desk
accounts, jobs or run history. Runtime v0.23.1 was used to validate all 112 cases.
