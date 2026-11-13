# Annotation vocabulary rows (staged, proposed)

Hand-written rows for the proposed annotation vocabulary `1.0.0`
([`spec/annotation-vocabulary.md`](../../spec/annotation-vocabulary.md), proposed by
[RFC 0032](../../rfcs/0032-outcome-severity.md), a Draft). They are not a conformance corpus: no
bundle carries them, the site does not serve them, and no claim may cite them. They are not
recordings. Every expectation was written by hand from the companion text and Core `0.5.0`, and the
reference checker, [`tools/annotation_vocabulary.py`](../../tools/annotation_vocabulary.py), is held
to them, never the other way round. It is the one reader; no second, independently written reader
exists.

Core `0.5.0`'s corpora are unchanged. Nothing here is named by `conformance/manifest.json` or
`conformance/evaluation/manifest.json`, and nothing here is a schema file.

## The files

Each version of the vocabulary has its own directory. [`1.0.0/`](1.0.0/) holds:

- [`vocabulary.json`](1.0.0/vocabulary.json), the machine-readable form: the key, its position,
  the levels in ascending order, the two codes, and a JSON Schema fragment for an outcome's
  annotations object that refuses what the companion's §6.3 refuses, given a pack Core has
  admitted. The fragment has no `$id`, and the companion text governs where the two differ.
- [`manifest.json`](1.0.0/manifest.json), the rows and the pair.
- `packs/`, the input packs, one per row, and three for the pair.

## A row

A row names a pack and its expectations:

- `expectedCore`: Core `0.5.0`'s document result, with an empty supported-extension set (for a
  pack that declares `extended`, a reader's that supports it), and the primary diagnostic in the
  document corpus's codes, or `null`. Core admits every value the vocabulary refuses, which is
  why the vocabulary exists: Core cannot refuse such a value under `0.5.0`.
- `expectedResult`: the vocabulary checker's result. `pass` and `refused` are for a pack the
  vocabulary is applied to. `not-checked` is the vocabulary not applied (§6.2), for one of three
  reasons, and takes no vocabulary finding.
- `expectedReason`: why the vocabulary was not applied, or `null` when it was applied:
  `spec-version` for a pack whose `specVersion` is another selector, such as `0.3.0` or `0.6.0`;
  `core-refused` for a pack Core `0.5.0` refuses, whose report also names the Core layer that
  refused it; `profile-unsupported` for a ceiling profile (Core §4.1) the checker does not support.
  No row expects `profile-unsupported` (below).
- `expectedFindings` and `expectedAdvisories`: code and JSON Pointer pairs, compared as sets.
  `expectedAdvisories` binds only a checker that claims the identifier advisory, a SHOULD
  (§3.1): such a checker reports it exactly where the rows say and nowhere else. A checker that
  does not claim it compares results, reasons and findings alone.

A row whose pack declares the `extended` profile records the result of a checker that supports
`extended`, as Core's document corpus does ([`conformance/README.md`](../README.md)). A checker
that supports only `base` reports the vocabulary not applied, with the reason
`profile-unsupported`, and the row as not run under an unsupported profile, not failed. The
reference checker supports only `base`.

## The pair

The pair names three packs, a baseline with no annotations, the baseline with a level on every
outcome (and another key on one outcome), and the baseline with a refused value on every outcome,
and five facts documents. The three packs have equal evaluation forms (Core §8.5), and for each
facts document each gives the hand-written disposition. The vocabulary checker passes the second
and refuses the third, and Core evaluates all three alike (§2.6). The baseline is not the second
with the key removed, because of that other key. "The same pack with the key removed" is §2.6's
definition, which follows Core §8.5 step 3: remove the member; if the annotations object is then
empty, remove it; if that leaves the outcome's `extensions` object empty, remove that too. The
tests apply that removal to every admitted row's pack.

## Checks

`tests/test_annotation_vocabulary.py` runs each row through the document corpus's harness and
through the checker, the pair through the repository's second Core evaluator
(`tools/core_050_eval.py`), and the fragment through a general JSON Schema validator, and holds
the three readings to the hand-written expectations. `python tools/annotation_vocabulary.py rows`
runs the checker alone, and lists the `extended` row as not run.
