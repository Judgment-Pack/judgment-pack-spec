# RFC 0032: Outcome severity, one well-known annotation key

- Status: Draft
- Type: Standards track, draft maturity. A proposed companion document beside Core, the annotation
  vocabulary, with its own version, `1.0.0`. Not a Core amendment.
- Created: 2026-11-13
- Target: specification release `v0.5.2`, a patch release that carries Core `specVersion` `0.5.0`
  unchanged ([VERSIONING.md](../VERSIONING.md)). The companion is normative for nothing until this
  RFC is accepted.
- Issue: [#320](https://github.com/Judgment-Pack/judgment-pack-spec/issues/320)
- Proposed text: [`spec/annotation-vocabulary.md`](../spec/annotation-vocabulary.md)
- Staged rows: [`conformance/annotation-vocabulary/`](../conformance/annotation-vocabulary/README.md)
- Related: [RFC 0031](0031-annotations-and-value-sets.md) (accepted, Core `0.5.0`),
  [RFC 0016](0016-outcome-values.md) (Draft), [#306](https://github.com/Judgment-Pack/judgment-pack-spec/issues/306)
  (annotation positions)

> This record is a Draft, and it and the companion it proposes are normative for nothing. See
> [RFC 0000](0000-rfc-process.md) for the process and its bar.
>
> **Review standing.** [RFC 0009](0009-interim-review-regime.md) requires a recorded adversarial
> review by a model from a different vendor, with a written maintainer disposition for each
> finding, on the pull request that creates this RFC. That review has not happened, and this record
> does not claim it. No review by a model from the drafting vendor has happened either. The
> decisions below are numbered so that a review can disposition each one.

## Summary

Define one well-known annotation key, `severity`, on an outcome, with a closed, ordered vocabulary
of four levels: `low`, `medium`, `high` and `critical`. The key lives in a new companion document,
the annotation vocabulary, which has its own version, starting at `1.0.0`, and status `proposed`.
A vocabulary checker refuses any other value, and any list, with one stated code. Absence means no
stated severity, never a default. Core `0.5.0` is untouched: its schema, text and corpora keep
their bytes, `spec validate` accepts what it accepts today, and Core §8.5's evaluation form already
removes outcome annotations, so the key is inert with no new rule. The values and their order are
written so that a later selector can adopt them, in Core's schema or as a typed outcome member,
without a second vocabulary. This is one key, not a registry.

## Problem

Packs used for risk and review decisions want each outcome to state how serious it is: in an
access review, `revoke-access` is more serious than `keep-access`; in an expense approval,
`refer-for-audit` is more serious than `approve`. Core `0.5.0` has no member for that. An
annotation on the outcome can carry it, but Core gives no key a meaning (Core §9.2), and RFC 0031
§8 leaves vocabularies to projects: "Core defines no keys. A project MAY document its own key
vocabulary." Three things follow:

1. Every project picks its own key and values (`severity`, `risk`, `level`; `sev1`, `P2`, `High`),
   so no tool can show, order or filter by seriousness in the same way for two projects.
2. Authors fold the level into the outcome identifier as well (`refer-high`), and the identifier and
   the annotation can then disagree. A change of level then changes the identifier, every reference
   to it, and every recorded disposition that names it.
3. A wrong value, such as `hihg`, `High` or a one-element list `["high"]`, is a valid annotation
   under Core `0.5.0`, and nothing finds it.

## Evidence

- **The request.** [#320](https://github.com/Judgment-Pack/judgment-pack-spec/issues/320) states the
  three costs above for one key, and links two reference-runtime issues that need a shared meaning:
  [runtime #405](https://github.com/Judgment-Pack/judgment-pack-runtime/issues/405) (a check of the
  key, and a view that shows each outcome's level) and
  [runtime #402](https://github.com/Judgment-Pack/judgment-pack-runtime/issues/402) (a comparison of
  two versions that reports annotation changes).
- **The level is already folded into identifiers.** The repository's own advisory fixtures name
  outcomes `medium` and `high` (`conformance/advisory/rules-overlap-exact.json` and its siblings).
  Nothing in them says whether that is a level or a name, and Core §5 forbids reading it as either.
- **Severity is reached for as a precedence.** The data-request intake worked example has to say
  that two conflicting rules are never tie-broken "by severity"
  ([`docs/use-cases/data-request-intake.md`](https://github.com/Judgment-Pack/judgment-pack-spec/blob/main/docs/use-cases/data-request-intake.md)). A
  specification-defined severity has to say the same, and §2.6 of the companion does.
- **No pack in the repository uses a severity key.** Annotations were released on 2026-11-12, with
  Core `0.5.0`. The collision cost of giving `severity` a meaning is lowest now (see Compatibility).

### Why this is the case RFC 0031 set aside, for one key

RFC 0031 rejected "a registry of keys" "for now", because "a registry is governance work that no
evidence yet asks for" (RFC 0031, Alternatives). What it set aside was a general mechanism for
specification-defined keys. This record asks for no mechanism. It asks for one key whose three
costs are each a cost of *not* sharing a meaning: display and ordering that differ from project to
project, an identifier that duplicates and contradicts the annotation, and a typo that no one can
refuse because no one has said what is right. A project vocabulary (RFC 0031 §8) removes none of
them for a second project or a general tool. Nothing in #320 or elsewhere asks for a second key, so
this record does not open a registry, and it says what a second key would need (D17).

## Specification

The proposed normative text is [`spec/annotation-vocabulary.md`](../spec/annotation-vocabulary.md),
annotation vocabulary `1.0.0`. In brief:

- the key `severity` is defined in an outcome's annotations object, and nowhere else (§2.1);
- its value is one string, one of `low`, `medium`, `high` and `critical`, in that ascending order
  (§2.2), matched by code point (§2.4); every list is refused (§2.5);
- absence is no stated severity, never a default, and `none` is not a value (§2.3);
- the key is inert, by Core §8.5 (§2.6);
- an outcome identifier should not repeat the level, and a recommended advisory reports one that
  ends in a level the annotation contradicts (§3);
- consumer views show a level in a fixed place, order by the vocabulary, and never compute with
  levels (§4);
- no suggested action is defined (§5);
- a vocabulary checker admits the pack under Core first, then refuses each outcome whose value is
  not a level, with `JPS-VOCABULARY-SEVERITY-VALUE` (§6);
- no pack declares the version it was written to; the checker states the version it applied (§7);
- one key, not a registry, and the bar for a second (§8); the document's own versioning (§9); and
  its machine-readable form (§10).

### Decisions

Each decision is numbered for disposition. **Maintainer's decision** marks one that this record
cannot settle on the maintainer's behalf. Each such decision lists its options, the recommended one
first.

**D1. A new RFC, not an amendment of RFC 0031.** *Maintainer's decision.*

- (a) **A new RFC, 0032** (recommended).
- (b) An amendment to RFC 0031.

*Why:* RFC 0031 is accepted, and its content is now Core `0.5.0`'s frozen text. An amendment is
how this repository changes what a record itself proposed: the amendment of RFC 0018 that proposes
dialect format `4.0.0` changes the companion RFC 0018 created. Nothing here amends
Core or RFC 0031's design: Core §9.2 and RFC 0031 §8 already let a vocabulary define a key, and
this one is a new document with its own version, as each companion so far has had its own record
(RFCs 0017, 0018, 0020, 0023, 0029). RFC 0031's "Rejected for now" anticipates a later record; this
is one, for one key. RFC 0031 is not edited.

**D2. Option 1 of #320 now; options 2 and 3 later.** *Maintainer's decision* (the issue proposes
it, and this record recommends it).

*Why:* A Core `0.5.0` pack whose outcome carries `"severity": "sev1"` is valid today. Option 2
(Core's schema enforces the values) and option 3 (a typed outcome member) would each refuse or
reinterpret it, so each needs a new selector. Option 1 needs none, and it can be released in a
patch release because it changes no normative artifact of `0.5.0` (VERSIONING.md).

**D3. The key is spelled `severity`, unprefixed.** *Maintainer's decision.*

- (a) **`severity`** (recommended).
- (b) A prefixed key, such as `jp-severity`.

*Why:* every local identifier is already admissible as a project key under `0.5.0`, so a prefix
reserves nothing; the companion's meaning is applied only by a consumer that applies the companion.
A prefix would make the key look like a namespace, which invites a second and third prefixed key
(D17). The collision risk is low: annotations shipped a day before this record. A project whose
`severity` means something else keeps a Core-conforming pack and renames its key when it applies
the vocabulary (Compatibility).

**D4. Outcomes only.** *Maintainer's decision.*

- (a) **Outcomes only** (recommended).
- (b) Outcomes and rules.

*Why:* a disposition names an outcome, never a rule (Core §8.3). Several rules may name one outcome,
so severities on rules could disagree about one outcome, with nothing to settle which one is shown;
and Core gives rules no priority (Core §6.5), which a rule-level severity would look like. At the
root, on a rule and on a value-set entry, the key has no defined meaning, and a checker neither
checks nor refuses it there (companion §2.1). A later position is a major version (D15), and
[#306](https://github.com/Judgment-Pack/judgment-pack-spec/issues/306) tracks positions in general.

**D5. Four levels, ascending, and no informational level.** *Maintainer's decision.*

- (a) **`low` < `medium` < `high` < `critical`** (recommended).
- (b) The same four with `informational` below `low`.
- (c) The same four with `none` below `low`.

*Why:* four levels is the common ordinal scale, and each is a plain English word with no number to
compute with. (b) is not needed for `1.0.0`: an outcome that states no seriousness leaves the key
out. Starting narrow is cheap to widen: adding a level below `low` is a minor version, while
removing one is a major version (D15). `informational` is the first candidate for `1.1.0` if
packs ask for it. (c) is refused, because absence is already the one spelling of "none" (D6).

**D6. Absence is no stated severity, never a default.**

*Why:* Core §9.2 makes absence the one spelling of "no annotations". A default level would make
every pack written before this record state something its author never wrote. So a consumer never
shows absence as `low`, and `none` is not a value (companion §2.3).

**D7. Every list is refused, the one-element list included.** *Maintainer's decision.*

- (a) **Refuse every list** (recommended).
- (b) Accept a one-element list as a second spelling of the string.

*Why:* Core admits `"high"` and `["high"]` as two spellings (Core §9.2). An outcome has at most one
level, and one spelling makes matching, display and comparison exact. (b) would make every reader
handle two forms for no gain.

**D8. Exact matching: case-sensitive, no trimming, by code point.**

*Why:* this is Core §9.2's string equality. Folding case or mapping look-alikes would let `High` or
`hіgh` be shown as `high`, a display of something the author did not write. Core already
refuses a value with white space at either end.

**D9. Core first: the vocabulary applies only to a pack Core admits.** *Maintainer's decision.*

- (a) **Core first** (recommended): a pack Core refuses is reported `not-checked`, with Core's
  refusal, and takes no vocabulary finding. An empty string is therefore Core's
  `JPS-STRUCTURE-MIN-LENGTH`, not the vocabulary's code, and so are `"high "`
  (`JPS-STRUCTURE-NOT`), a number (`JPS-STRUCTURE-TYPE`) and `[]`
  (`JPS-STRUCTURE-COLLECTION-ARITY`).
- (b) The vocabulary also reports its own code for those values.

*Why:* Core's layering (Core §3.3; conformance/README.md, "Validation proceeds in layer order")
stops a document at the first layer it fails. A second code for one refusal would make the codes
disagree between tools that do and do not run the vocabulary. This departs from #320's reading
that an empty string is refused "with the code": it is refused, but with Core's code. A required
extension the checker does not support does not stop the check, because annotations are never
requirable (Core §9.2).

**D10. Codes.** *Maintainer's decision* (spelling).

- (a) **`JPS-VOCABULARY-SEVERITY-VALUE`** for every refusal, at
  `/outcomes/<i>/extensions/org.judgmentpack.annotations/severity`, one per refused outcome; and
  **`JPS-VOCABULARY-SEVERITY-IDENTIFIER`** for the advisory, at `/outcomes/<i>/id` (recommended).
- (b) One code per kind of refusal (unknown, case, list).

*Why:* the repository's codes are `JPS-<LAYER>-<NAME>`; `VOCABULARY` names the layer above Core's
`CARRIER`, `STRUCTURE` and `SEMANTIC`. One refusal code matches Core's practice of naming a code
for the rule that fails, not for each way of failing it (RFC 0031, Codes). Findings compare as a
set of code and pointer pairs, as in Core's corpus. The codes are provisional test metadata, as
every code is.

**D11. Identifiers should not repeat the level, with a recommended advisory.** *Maintainer's
decision.*

- (a) **SHOULD NOT repeat, and a recommended (SHOULD) advisory** when the identifier's last
  hyphen-separated segment, or the whole identifier, is a level other than the outcome's (recommended).
- (b) SHOULD NOT repeat, with no advisory.
- (c) An advisory also for an identifier that ends in a level and has no annotation.

*Why:* the advisory reports a disagreement between two things the author wrote, so that the author
can look; it infers no level from the identifier (Core §5), changes no result and never refuses. It
is silent when the two agree, when there is no annotation, when the value is refused, for a segment
that merely contains a level (`review-highest`) and for a level that is not the last segment
(`high-volume-refer`). (c) would read a level from an identifier alone, which Core §5 forbids.

**D12. A suggested action is deliberately not defined.**

*Why:* what a level asks of a person (a remedy, a response time, an owner) is a project's own and
differs from project to project. A specification-defined action would read as an authorization,
which an outcome is not (Core §6.4). The companion also defines no likelihood, impact, confidence,
priority or mapping from another scale (companion §5).

**D13. Consumer views.** *Maintainer's decision* (strength).

- (a) **Normative for a consumer that applies the companion** (recommended): a fixed place, SHOULD;
  no level shown for an outcome without one, MUST; a value outside the vocabulary never shown or
  ranked as a level, MUST; ordering by the vocabulary with unranked outcomes together after the
  ranked ones; no arithmetic and no derived pack, rule or disposition severity, MUST; filtering is
  Core's filtered view (D2 of Core §9.2); a level is the author's statement, MUST; a comparison
  reports a change of level, SHOULD.
- (b) All informative.

*Why:* the issue's acceptance asks that a view list each outcome's level in a fixed place and show
none for a pack without one. The MUSTs are each a way a view could misstate the pack; the SHOULDs
are presentation. A disposition that names no outcome has no severity, which stops a view from
giving an `unresolved` conflict the higher of its two outcomes' levels.

**D14. No in-pack declaration of the vocabulary version.** *Maintainer's decision.*

- (a) **No declaration; the checker states the version it applied**, and a project pins its checker
  in its own tooling (recommended).
- (b) A second well-known annotation key on the root, such as `annotation-vocabulary`.
- (c) A vendor extension naming the version.

*Why:* (b) is a second key (D17), and an annotation that changes what a checker does is no longer
only a label. (c) is not portable. A Core member needs a selector. Within a major version, versions
only add levels (D15), so a pack that passes `1.x` passes every later `1.y`, and a refusal names
the checker's version. A declaration added to existing packs would change their bytes, and so
every digest that covers them (Core §5), for no change in evaluation.

**D15. The companion's own versioning, from `1.0.0`.**

*Why:* as for the dialect format, the document's version is its own, not a `specVersion` and not a
tag. Patch: explanation only. Minor: adds levels with their place in the order, keeping every
existing level and the order, or changes an advisory. Major: anything that refuses a pack an
earlier version passed, or changes the order or meaning of a level, including a new position or a
new key (companion §9).

**D16. Inertness needs no new rule.**

*Why:* Core §8.5 removes each outcome's annotations from the evaluation form, so a pack evaluates as
the same pack with the key removed, byte for byte, whatever the value. A vocabulary refusal is not
a Core result: the pack stays semantically conforming and is evaluated, and nothing reports
`pack-not-conformant` for it (companion §2.6, §6.4).

**D17. One key, not a registry; the bar for a second key.**

*Why:* RFC 0031's question of a registry stays closed. A second key needs its own RFC showing all
of: the same meaning needed by projects that do not share authors; a few closed values that can be
matched exactly; a meaning that consumers display, order or filter alike; no effect on evaluation;
and that it is neither a project's own business (an action, owner or process) nor already a Core
member. Each new key is a major version of the companion. If keys accumulate past a handful, the
registry question is reopened in its own record (companion §8).

**D18. The path to a later selector, with one vocabulary.** *Maintainer's decision*, for the next
selector, not now.

- (a) **Option 2: Core's schema adopts the values** (recommended): the outcome annotations object
  gains `"properties": {"severity": {"type": "string", "enum": [...]}}`, the fragment in
  `vocabulary.json`, verbatim. No new member, no change to the evaluation form, and every pack the
  vocabulary passes stays conforming. The vocabulary checker's refusal becomes Core's
  structural refusal, mapped by RFC 0031's code rule (`enum` would take a new structural code), and
  the companion then states that Core enforces the key.
- (b) Option 3: a typed optional outcome member, such as `severity`, with the same four values and
  order. It must say what the evaluation form does with the member (remove it, as §8.5 removes
  annotations, or state that it is inert because no step reads it), that the disposition does not
  carry it, and how it relates to the annotation: refuse the annotation beside the member, or
  require the two to be equal. It sits beside RFC 0016's outcome values, which are not inert.

*Why (a):* it keeps one spelling in one place, and the companion's values, order and absence rule
carry over unchanged. Under either option the values come from this vocabulary's `1.x` and no
second vocabulary is defined; a pack that passes the vocabulary today is the pack that stays
conforming under the next selector, which makes the vocabulary a preview of that migration.

**D19. Publication in `v0.5.2`: proposed and staged.** *Maintainer's decision.*

- (a) **Staged** (recommended): while this RFC is a Draft the companion is `export-ignore`, as
  `spec/workflow.md` is for RFC 0020, has no site page, and is read at the tag; the rows are staged
  under `conformance/annotation-vocabulary/`, in no corpus, bundle or claim. The patch release
  carries Core unchanged.
- (b) The maintainer accepts this RFC before `v0.5.2`; acceptance removes the `export-ignore` line,
  and the companion gets a page and ships in the bundle. The rows stay staged either way.

*Why:* RFC 0009's review has not happened, and one reader exists. (a) lets the release go out with
the proposal visible and no claim made. The proposed dialect format `4.0.0` did ship in the
`v0.5.1` bundle undecided, but as §2.2 of a companion already accepted; a new companion whose RFC is
a Draft follows RFC 0020's rule instead.

**D20. The machine-readable form is a plain `vocabulary.json`, not a schema file.**

*Why:* a `*.schema.json` under `conformance/` would be a schema family for the record-shape catalog
(`catalog/README.md`), and one with an `$id` under `0.5.0` would join Core `0.5.0`'s normative set,
which a patch release may not change (`tools/build_release.py`, `normative_paths`). A plain file
with an embedded fragment and no `$id` is neither, and is exactly what D18 (a) would copy.

**D21. The vocabulary-checker class.**

*Why:* the class is what a tool claims when it applies the companion: Core admission first (D9),
the refusals of §6.3 for every outcome, the version it applied in every report (D14), no repair of a
value, and a refusal never reported as a Core result (D16).

## Alternatives

- **No change.** Projects keep their own keys (RFC 0031 §8). Rejected: none of the three costs in
  Problem goes away for a second project or a general tool.
- **Option 2 or 3 now.** Rejected for now: each needs a new selector (D2). Kept as the path (D18).
- **A vendor extension, such as `com.example.severity`.** Rejected: not portable, and a vendor
  extension on an outcome is kept in the evaluation form (Core §8.5 removes only annotations), so
  inertness would need its own argument.
- **A profile.** Rejected: profiles select document ceilings (Core §4.1), not meanings.
- **A registry of keys.** Rejected again (D17).
- **Product-only behaviour.** The reference runtime alone could define the key. Rejected: a second
  tool would then pick other values, which is the first cost in Problem.
- **A numeric score.** Rejected: numbers invite arithmetic and averages that the levels do not
  support (companion §4).

## Compatibility

Nothing in Core moves, so each dimension VERSIONING.md names has the same answer as for `v0.5.1`:

- **Reader compatibility:** unchanged. A `0.5.0` reader reads what it read.
- **Writer compatibility:** unchanged. Writers emit `specVersion` `0.5.0`; a writer that applies the
  vocabulary writes one of the four levels or leaves the key out.
- **Semantic compatibility:** unchanged for evaluation. The vocabulary adds a meaning only for a
  consumer that applies it.
- **Migration compatibility:** no document transformation applies.

A project whose packs already use an outcome key named `severity` with other values, or as a list,
keeps Core-conforming packs; only a vocabulary checker refuses them. It maps its values onto the
levels, or renames its own key (for instance to `risk-level`). Under D18 (a), the packs the
vocabulary refuses today are the packs the next selector would refuse.

## Security and privacy

- **Confusion.** A level is the author's statement, not a measurement or a review (Core §3.5). A
  pack with wrong levels evaluates exactly as one with right levels; what changes is what a reader
  looks at first. Views say how they order (companion §4), and a comparison of two versions reports
  a change of level, so that a lowered level is visible.
- **Look-alikes and case.** Exact matching refuses `High` and `hіgh` rather than showing either
  as a level it resembles (D8).
- **Hidden outcomes.** A view that hides the lower levels is a filtered view under Core §9.2, D2,
  and a review made from it covers only what it showed.
- **Disclosure.** Nothing new: levels are pack content, and no level is placed in a disposition.
- **Resources.** One string per outcome, compared with four values, within Core's annotation
  ceilings (Core §4.1).

## Conformance

The rows are hand-written and staged under
[`conformance/annotation-vocabulary/1.0.0/`](../conformance/annotation-vocabulary/README.md), with the
machine-readable form `vocabulary.json`. They are in no corpus, and no claim may cite them. Each
row records Core `0.5.0`'s result, the vocabulary checker's result, and its findings and
advisories.

| Row | Pack | Core `0.5.0` | Vocabulary |
| --- | --- | --- | --- |
| `pass-each-level` | the four levels on four outcomes | valid | pass |
| `pass-no-severity` | no annotations | valid | pass |
| `pass-some-outcomes` | a level beside another key; annotations without the key | valid | pass |
| `refuse-unknown-value` | `hihg` | valid | refused |
| `refuse-wrong-case` | `High` and `CRITICAL` on two outcomes | valid | refused, two findings |
| `refuse-none` | `none` | valid | refused |
| `refuse-informational` | `informational` | valid | refused |
| `refuse-look-alike` | `hіgh` | valid | refused |
| `refuse-list-one` | `["high"]` | valid | refused |
| `refuse-list-two` | `["low", "high"]` | valid | refused |
| `core-empty-string` | `""` | `JPS-STRUCTURE-MIN-LENGTH` | not checked |
| `core-trailing-space` | `"high "` | `JPS-STRUCTURE-NOT` | not checked |
| `core-number` | `3` | `JPS-STRUCTURE-TYPE` | not checked |
| `core-empty-list` | `[]` | `JPS-STRUCTURE-COLLECTION-ARITY` | not checked |
| `not-checked-rule` | `sev1` on a rule | valid | pass |
| `not-checked-root` | `sev1` on the root | valid | pass |
| `not-checked-entry` | `sev1` on a value-set entry | valid | pass |
| `not-checked-other-keys` | `severity-level` and `risk` on an outcome | valid | pass |
| `refuse-with-unsupported-extension` | `hihg`, and a required extension the checker lacks | unsupported | refused |
| `advisory-identifier-disagrees` | `refer-high` at `low` | valid | pass, advisory |
| `advisory-identifier-whole` | `critical` at `low` | valid | pass, advisory |
| `no-advisory-identifier-agrees` | `refer-high` at `high` | valid | pass |
| `no-advisory-identifier-contains` | `review-highest` at `low` | valid | pass |
| `no-advisory-identifier-not-last` | `high-volume-refer` at `low` | valid | pass |
| `no-advisory-identifier-no-severity` | `refer-high`, no annotation | valid | pass |
| `no-advisory-identifier-refused-value` | `refer-high` at `hihg` | valid | refused, no advisory |
| `inert-baseline`, `inert-levels`, `inert-refused` | the pair's packs | valid | pass, pass, refused |

The pair `inert-severity` holds the three `inert-` packs to equal evaluation forms and to the same
hand-written disposition for each of five facts documents: an outcome twice, a conflict, an
unknown, and not applicable. `tests/test_annotation_vocabulary.py` also removes the key from every
admitted row's pack and holds the evaluation form unchanged, and applies the `vocabulary.json`
fragment with a general JSON Schema validator, which must refuse exactly the outcomes the checker
refuses. Core `0.5.0`'s schema and corpora do not change, and the builder's patch-release check
holds them to `releases/v0.5.0.normative.json`.

## Implementation

- **The repository's reference checker**, [`tools/annotation_vocabulary.py`](https://github.com/Judgment-Pack/judgment-pack-spec/blob/main/tools/annotation_vocabulary.py),
  written from the companion, admits the pack with `tools/core_050_eval.py` and applies §§3 and 6.
  It is one reader, by the drafting vendor.
- **The schema fragment** in `vocabulary.json`, applied by a general JSON Schema validator, is a
  second reading of the refusal alone (not of Core admission or the advisory). It is not an
  independent implementation.
- **The reference runtime**, [runtime #405](https://github.com/Judgment-Pack/judgment-pack-runtime/issues/405),
  plans the check and a view; it would be a second reader. Nothing has been built there.

RFC 0000 asks for two plausible independent implementations before a stable feature is accepted.
One exists; the second is planned.

## Unresolved questions

1. **An informational level** below `low` (D5 b): wait for packs that ask for it, or add it in `1.0.0`.
2. **A second independent reader** before acceptance, or acceptance at draft maturity on one reader
   (D19).
3. **Positions** (D4; [#306](https://github.com/Judgment-Pack/judgment-pack-spec/issues/306)): whether
   a later version should define the key anywhere else.
4. **An identifier with a level and no annotation** (D11 c): whether a checker should say anything.
5. **The next selector's path** (D18): option 2 or option 3, decided when that selector opens.
6. **The rows' future**: whether they join a corpus, with a `suiteVersion`, when Core `0.6.0` opens,
   or stay the companion's own.
7. **Review**: the RFC 0009 review this record does not have.
