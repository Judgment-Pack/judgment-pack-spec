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

A row names a pack and three expectations:

- `expectedCore`: Core `0.5.0`'s document result, with an empty supported-extension set, and the
  primary diagnostic in the document corpus's codes, or `null`. Core admits every value the
  vocabulary refuses, which is why the vocabulary exists: Core cannot refuse such a value under
  `0.5.0`.
- `expectedResult`: the vocabulary checker's result. `pass` and `refused` are for a pack Core
  admits; `not-checked` is for a pack Core refuses, which takes no vocabulary finding (§6.2).
- `expectedFindings` and `expectedAdvisories`: code and JSON Pointer pairs, compared as sets.

## The pair

The pair names three packs, a baseline with no annotations, the same pack with a level on every
outcome, and the same pack with a refused value on every outcome, and five facts documents. The
three packs have equal evaluation forms (Core §8.5), and for each facts document each gives the
hand-written disposition. The vocabulary checker passes the second and refuses the third, and Core
evaluates all three alike (§2.6).

## Checks

`tests/test_annotation_vocabulary.py` runs each row through the document corpus's harness and
through the checker, the pair through the repository's second Core evaluator
(`tools/core_050_eval.py`), and the fragment through a general JSON Schema validator, and holds
the three readings to the hand-written expectations. `python tools/annotation_vocabulary.py rows`
runs the checker alone.
