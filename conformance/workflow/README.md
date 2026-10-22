# Workflow contract fixture

These hand-written records exercise the version-1 workflow schema and RFC 0020 companion forms.
`left-bundle.json` and `right-bundle.json` each carry both stages' output envelopes, retained Core
dispositions and recorded summaries. `sample.json` is redrawn from its seed; `drift.json` is
recomputed from the two bundles. The `reports/` files are the closed verifier events expected for
the corresponding refusal vectors.

Each summary's `recordsDigest` was fixed independently as SHA-256 of the canonical JSON array of
its stage's dispositions in recorded order. The repository test reconstructs those exact bytes,
recomputes every summary counter and digest, redraws the sample, and reconstructs the complete
drift result. The vectors are deliberately authored inputs, not output captured from an executor.

This fixture establishes no implementation, execution, authentication, verdict or conformance
claim. The full research recording described by companion §11 remains future work.
