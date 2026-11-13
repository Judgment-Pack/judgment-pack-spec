# The annotation vocabulary

## Status

This document is a companion document of the Judgment Pack specification, at draft maturity. It is
normative for one conformance class, the *vocabulary checker* (§6), and for a consumer that applies
it in the statements §4 marks MUST or MUST NOT, and for nothing else. It is published beside the
released Core `0.5.0`, first in release `v0.5.2`, and carries no `specVersion` of its own. Core
`0.5.0`'s §1.1 does not list it, because a release that carries Core `0.5.0` changes no Core text
([VERSIONING.md](../VERSIONING.md)); its standing comes from its design record's acceptance.

Its design record is [RFC 0032](../rfcs/0032-outcome-severity.md), accepted on 2026-11-13 at draft
maturity, which is informative. The maintainer accepted it on a review by a model from the drafting
vendor, with the different-vendor review of the interim review regime waived, as the RFC's
Acceptance section records.

This text is annotation vocabulary version `1.0.0`, status `proposed`. The version is this
document's own: it is not a Core `specVersion`, it is not a release tag, and no pack declares it
(§7). It is proposed because its machine-readable form and its hand-written rows are staged under
[`conformance/annotation-vocabulary/1.0.0/`](https://github.com/Judgment-Pack/judgment-pack-spec/tree/main/conformance/annotation-vocabulary/1.0.0),
and one reader reads it. The rows are not a conformance corpus, no bundle carries them, the site
does not serve them, and no claim may cite them; until a specification version publishes rows for
it, no vocabulary-checker conformance claim is available. The repository's reference checker,
`tools/annotation_vocabulary.py`, is the one reader; no second, independently written reader
exists. What a later version may change is §9's: within version `1`, a later version only adds
levels, so a pack that passes `1.0.0` passes every later `1.y`.

Core `0.5.0` is unchanged by this document. Every pack Core accepts it still accepts, every pack it
refuses it still refuses, and every evaluation gives the result it gave.

## 1. Terms

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT** and **MAY** have their BCP 14
meanings only in capitals.

- **Core** is Judgment Pack Core `0.5.0` ([`spec/judgment-pack-core.md`](judgment-pack-core.md)).
  *Annotations object*, *annotation string* and *evaluation form* are as Core §9.2 and §8.5 define
  them.
- An outcome's **annotations** are the annotations object at
  `/outcomes/<i>/extensions/org.judgmentpack.annotations`, where `<i>` is the outcome's index.
- A **consumer that applies this document** is one that shows, orders, filters or checks outcome
  severity as this document defines it. A consumer that does none of these is not affected by it.
- A **vocabulary checker** is the class of §6.

Core assigns no meaning to any annotation key (Core §9.2), and a project may document its own key
vocabulary ([RFC 0031](../rfcs/0031-annotations-and-value-sets.md) §8). This document is such a
vocabulary, published by the specification, for one key at one position. It states a meaning; it
does not infer one from a spelling, which Core §5 and §9.2 forbid.

## 2. The key `severity`

### 2.1 Position

The key `severity` is defined in an outcome's annotations, and nowhere else.

In the root's, a rule's and a value-set entry's annotations, a key named `severity` has no meaning
this document defines. A vocabulary checker neither checks nor refuses it there, and a consumer
that applies this document gives it no severity meaning there. Only the exact key `severity` is
defined: `severity-level`, `risk` and every other key, at every position, are a project's own.

An outcome is the position because a disposition names an outcome (`outcomeId`, Core §8.3) and never
a rule. A rule only selects an outcome. Several rules may name one outcome, so a severity on rules
could disagree from rule to rule about one outcome, and nothing would settle which one a
disposition shows. Core gives rules no priority (Core §6.5), and a severity on a rule would read as
one.

### 2.2 Values and order

The value of `severity` is one of these four annotation strings:

| Value | Order |
| --- | --- |
| `low` | least severe |
| `medium` | above `low` |
| `high` | above `medium` |
| `critical` | most severe |

The order is total and ascending: `low` < `medium` < `high` < `critical`. It states order only. A
level is not a number, the distance between two adjacent levels has no meaning, and no arithmetic
on levels is defined (§4).

This document gives the levels an order and no other meaning. What makes an outcome `high` is its
author's statement; a project MAY document its own criteria for each level. In an expense approval
pack, for example, the outcome `refer-for-audit` might be `high`; in an access review pack, the
outcome `revoke-access` might be `critical`.

There is no informational level below `low`. An outcome that states no seriousness leaves the key
out (§2.3). A level below `low` can be added by a minor version (§9); one cannot be removed without
a major version.

### 2.3 Absence

An outcome whose annotations do not hold `severity`, or that has no annotations, has **no stated
severity**. Absence is not a level and has no default. A consumer that applies this document MUST
NOT present an outcome with no stated severity as `low`, or as any other level, and MUST NOT rank it
among the levels (§4).

No value spells "none". `none`, `n/a` and every other value outside §2.2 are refused (§6.3).
Absence is the one spelling of "no stated severity", as it is the one spelling of "no annotations"
in Core §9.2.

### 2.4 Matching

A value is a level when it is the same sequence of code points as one of the four values, after
JSON unescaping. Matching is case-sensitive, and there is no trimming, no Unicode normalization, no
case folding and no mapping of look-alike characters. `High`, `HIGH` and `hіgh` (with U+0456
CYRILLIC SMALL LETTER BYELORUSSIAN-UKRAINIAN I) are not levels.

Core already refuses an annotation string that is empty, or that begins or ends with white space
(Core §9.2), so `""` and `"high "` never reach this document (§6.2).

### 2.5 One string, never a list

The value of `severity` MUST be one annotation string. A list is refused, whatever it holds, the
one-element list `["high"]` included. Core admits a plain string and a one-element list as two
spellings of a value (Core §9.2). This key has one spelling, and an outcome has at most one level.

### 2.6 Inertness

There is no new rule. Core §8.5 removes each outcome's annotations from the evaluation form, so an
evaluator never reads `severity`.

**The pack with the key removed.** For a semantically conforming pack, *the same pack with the key
removed* is the pack these steps give, applied to each outcome whose annotations hold `severity`, in
the way Core §8.5 step 3 removes the annotations member:

1. the member `severity` is removed from the outcome's annotations object;
2. if that leaves the annotations object empty, the member `org.judgmentpack.annotations` is
   removed from the outcome's `extensions` object; and
3. if that leaves the `extensions` object empty, the outcome's `extensions` member is removed.

Nothing else changes: every other annotation key, and every other member of the `extensions`
object, is kept. Two other readings are not this one. Removing only the member can leave an empty
annotations object, which Core §9.2 refuses, so the result is not a conforming pack. Removing the
annotations object but keeping an `extensions` object it leaves empty gives a pack whose evaluation
form keeps that empty object (Core §8.5 keeps an `extensions` object already empty in the pack it
reads), so its evaluation form is not the pack's.

Given the same facts document, evidence-availability document and supported-extension set, a pack
gives the result that the same pack with the key removed gives, byte for byte, because the two have
equal evaluation forms. That holds for every value, a value this document refuses included.

A severity orders no rules, breaks no conflict, selects no outcome, changes no handoff, and appears
in no disposition. A vocabulary checker's refusal (§6.3) is not a Core result. The pack stays
semantically conforming, an evaluator evaluates it, and no evaluator reports `pack-not-conformant`
because of it.

## 3. Outcome identifiers

An outcome identifier need not, and SHOULD NOT, repeat its level: write `refer` with
`"severity": "high"`, not `refer-high`. The identifier is the outcome's name in rules, exceptions
and dispositions (Core §5, §8.3). A level in it either repeats the annotation or disagrees with it,
and a change of level would then change the identifier, every reference to it, and every recorded
disposition that names it. A level in an identifier states nothing, because meaning is never
inferred from an identifier's spelling (Core §5).

### 3.1 The identifier advisory

A vocabulary checker SHOULD report the advisory `JPS-VOCABULARY-SEVERITY-IDENTIFIER` at
`/outcomes/<i>/id` when all three hold:

1. the outcome's `severity` is a level (§2.2, §2.4);
2. the identifier's last hyphen-separated segment, or the whole identifier when it has no hyphen,
   is a level; and
3. that segment is not the outcome's level.

A segment is as Core §5's grammar for a local identifier, `^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$`, makes
it: a run of lowercase letters and digits between single hyphens, so the last segment is what
follows the last hyphen. A checker that reports this advisory for any pack claims it, and MUST then
report it exactly when the three conditions hold, at that pointer, and nowhere else. A checker that
never reports it does not claim it, and meets §6 without it.

The advisory changes no result and is never a refusal, and its absence from a checker that does not
claim it states nothing. It does not infer that the outcome has the level its identifier spells
(Core §5): it reports that two things the author wrote disagree, so that the author can look. It is
not reported when the two agree, when the outcome has no stated severity, or when the outcome's
value is refused (the refusal is reported instead). It is not reported for a segment that contains
a level and is not one (`review-highest`, `refer-lowest`), or for a level that is not the last
segment (`high-volume-refer`).

## 4. Consumer views

This section is informative, except for its statements marked MUST or MUST NOT. Each of those stops
a view from misstating what the author wrote, and binds a consumer that applies this document, as
Core §9.2's D1 and D2 bind any consumer that displays or filters annotations. No conformance class
tests this section: the vocabulary checker (§6) reads packs, not views, and no Core class tests
display.

- **A fixed place.** A view of a pack's outcomes can show each outcome's level in one fixed place,
  the same for every outcome, such as a column or the same position beside each label. For an
  outcome with no stated severity, that place MUST show no level: it is left empty, or holds a
  fixed marker such as "no severity stated".
- **Values outside the vocabulary.** A value that is not a level MUST NOT be shown in that place as
  if it were one, and MUST NOT be case-folded or otherwise mapped onto a level. A view can show it as
  written, marked as outside the vocabulary, under Core's display rules (Core §9.2, D2: each
  character outside printable ASCII shown so that its code point can be recovered).
- **Order.** A view that orders outcomes by severity orders them by §2.2's order, most severe first
  or least severe first, and says which. Outcomes of the same level keep document order. The
  unranked outcomes, those with no stated severity and those whose value is not a level (a value
  the vocabulary checker refuses, `High` and `["high"]` included), come together after the ranked
  outcomes, in document order. A view MUST NOT place an unranked outcome among the ranked ones, or
  at the level its value resembles (§2.3, §2.4).
- **No arithmetic.** A view MUST NOT present a level as a number or a score, and MUST NOT derive a
  severity for a pack, a rule or a disposition from its outcomes' levels, for instance by taking the
  highest.
- **Dispositions.** A disposition of kind `outcome` can be shown with its outcome's level, labelled
  as the outcome's. A disposition of kind `not-applicable` or `unresolved` names no outcome and has
  no severity (Core §8.3). A view MUST NOT give it one, for instance the level of an outcome that a
  conflicting rule names.
- **Filtering.** A view that omits outcomes because of their level is a filtered view, and Core
  §9.2's filtered-view rule (D2) applies to it: it states that it is filtered, by which key and
  values, and how many outcomes it shows of how many the pack holds.
- **The author's statement.** A level is the pack author's statement. A view MUST NOT present it as
  measured, computed, reviewed or approved (Core §3.5; RFC 0031 §6, D1).
- **Comparison.** A comparison of two versions of a pack is expected to report a change of an
  outcome's level as a change, including a level added or removed. An annotation change is a change
  of the pack's content (Core §5, §11).
- **Two meanings of "severity".** An advisory diagnostic's severity, as the document corpus records
  it for each check mode ([`conformance/README.md`](../conformance/README.md), Layers), is not an
  outcome's level. Showing the two in one place invites reading one as the other.

## 5. What this document does not define

- **No suggested action.** It defines no action, remedy, response time, owner or notification for a
  level, and no key for one. What a level asks of a person is a project's own, and a project MAY
  document its own key for it (RFC 0031 §8). An action vocabulary is not this document's: it
  differs from project to project, and a specification-defined action would read as an
  authorization, which an outcome is not (Core §6.4).
- **No other measure.** It defines no likelihood, impact, confidence or priority, and no mapping
  from another scale onto the levels.
- **No other position.** It defines no severity for a rule, the root, a value-set entry, a
  disposition or a pack (§2.1, §4).

## 6. The vocabulary checker

### 6.1 The class

A **vocabulary checker** checks a pack against this document and reports a result, its findings
and its advisories. Every report MUST state the vocabulary version the checker applied, `1.0.0`
for this text.

### 6.2 Core `0.5.0` first

The vocabulary applies only to `specVersion` `0.5.0`. A pack declaring another selector is reported
not applied, for that reason. A pack declares another selector when its `specVersion` is a string
other than `0.5.0`, such as `0.3.0` or `0.6.0`. The selector is read after only the parsing needed
to find it and before Core's structural layer, as a reader dispatches on the complete selector
(Core §11); a pack whose `specVersion` is missing or is not a string is Core's refusal.

A vocabulary checker MUST then establish that the pack is a semantically conforming Core `0.5.0`
document (Core §3.3). When Core refuses the pack, the checker reports that the vocabulary was not
applied, with the Core layer that refused it, and reports no finding of this document. So an empty
value, a value that begins or ends with white space, an empty list, and a value that is neither a
string nor a list are Core's refusals, never this document's: in the repository's document corpus
they are `JPS-STRUCTURE-MIN-LENGTH`, `JPS-STRUCTURE-NOT`, `JPS-STRUCTURE-COLLECTION-ARITY` and
`JPS-STRUCTURE-TYPE`, at the structural layer. A checker that cannot establish conformance for a
ceiling profile (Core §4.1) it does not support also reports the vocabulary not applied, for that
reason.

Whenever the vocabulary is not applied, the report MUST say which of the three is the reason:
another selector, Core's refusal (with the layer), or an unsupported ceiling profile. A report of
"not applied" is never a pass and never a refusal of this document.

The check does not depend on the checker's supported extensions. It reads only annotation values,
whose shape Core's schema fixes whatever extension a pack requires (Core §9.2), so a required
extension the checker does not support is not a reason to skip it.

### 6.3 What a checker MUST refuse

For each outcome whose annotations hold the key `severity`, a vocabulary checker MUST refuse the
pack when the value:

- is a string that is not a level (§2.2, §2.4), such as `hihg`, `High`, `none` or `informational`;
  or
- is a list, whatever it holds (§2.5).

The finding is `JPS-VOCABULARY-SEVERITY-VALUE` at
`/outcomes/<i>/extensions/org.judgmentpack.annotations/severity`. A checker reports one finding for
each refused outcome, every refused outcome and not only the first. Findings compare as a set of
code and JSON Pointer pairs, as in Core's document corpus.

A vocabulary checker MUST NOT refuse a pack for:

- an outcome with no stated severity, or a pack with no `severity` key anywhere;
- a key named `severity` at any position other than an outcome's annotations; or
- any other key, at any position.

A vocabulary checker MUST NOT change, repair, trim, normalize or case-fold a value, and MUST NOT
present a refused value as meaning a level.

### 6.4 What a refusal is

A refusal is the vocabulary checker's result, not Core's. A checker MUST NOT report it as a Core
document-conformance result or as an evaluation error. The pack remains semantically conforming,
and Core evaluator conformance still requires that it be evaluated (Core §3.4). A project MAY make
passing this check a condition of its own process, such as publishing a pack.

Codes are provisional test metadata, as the [conformance README](../conformance/README.md) says of
every code.

## 7. Which version a pack was written to

A pack does not declare a vocabulary version. The checker states the version it applied (§6.1),
and a project that requires the check names the checker and the version in its own tooling or
process.

- A declaration in the pack would need a place. A second well-known key would be a second key
  (§8), and an annotation that changes what a checker does is no longer only a label. A vendor
  extension is not portable. A Core member needs a new selector.
- Within a major version, versions only add levels (§9). A pack that passes version `1.x` passes
  every later `1.y`, so a later checker never refuses what an earlier one passed. A refusal names
  the checker's version, from which an author can see whether a level the checker does not yet
  know is the cause.
- A pack's bytes are part of every digest that covers it (Core §5). A declaration added to existing
  packs would change their content and no evaluation.

## 8. One key, not a registry

This document defines one key. It is not a registry, and it does not open one. A second key needs
its own RFC, which shows all of these:

1. projects that do not share authors need the same meaning;
2. the values are few, closed, and can be matched exactly;
3. consumers display, order or filter by the key in the same way;
4. the key has no effect on evaluation, as §2.6 states for `severity`; and
5. the meaning is not a project's own business, such as an action, an owner or a process, and is
   not already a Core member.

Each new key would be a new major version of this document (§9), because a pack that already uses
that key with another value would then be refused. If keys accumulate past a handful, the question
of a registry that RFC 0031 set aside is reopened, in its own record.

## 9. Versioning of this document

This document has its own version, `MAJOR.MINOR.PATCH`, starting at `1.0.0`.

- **Patch.** Explanation only. No result, finding or advisory changes.
- **Minor.** Adds levels, each with its stated place in the order, and keeps every existing level
  and their order; or changes an advisory. Every pack an earlier version of the same major version
  passes, it passes.
- **Major.** Anything that refuses a pack an earlier version passed, or that changes the order or
  meaning of a level: removing, renaming or reordering a level, defining another position, or
  defining another key.

While Core's schema does not list the levels, a minor version adds a level without a Core release.
Once a Core selector's schema lists them (RFC 0032, D18), that selector freezes the list it adopted:
a level that a later minor version adds reaches Core only through a new selector, and each such
selector records which version `1.x` of this document it froze.

Version `1.0.0` is `proposed` for the reasons its Status gives: its rows are staged, and one
reader reads it.

## 10. Machine-readable form

[`vocabulary.json`](https://github.com/Judgment-Pack/judgment-pack-spec/blob/main/conformance/annotation-vocabulary/1.0.0/vocabulary.json)
holds the version, the key, its position, the levels in ascending order, the two codes, and a JSON
Schema fragment for an outcome's annotations that refuses what §6.3 refuses, given a pack Core has
already admitted. Where the file and this text differ, this text governs. The fragment has no
`$id`: it is not one of the repository's catalogued schema families, and no Core schema names it.

## 11. Security and privacy

- A level is the author's statement, and is as untrusted as every other pack string (Core §10). A
  pack whose levels are wrong evaluates exactly as one whose levels are right (§2.6); what changes
  is what a reader looks at first. A view that orders by level says so (§4), and a comparison of
  two versions reports a change of level (§4).
- Exact matching (§2.4) refuses look-alike and wrong-case values, rather than showing one as a level
  it resembles.
- A view that hides the lower levels is a filtered view, and a review made from it covers only what
  it showed (Core §9.2, D2).
- The key adds no resource cost beyond Core's annotation ceilings (Core §4.1): one string per
  outcome, matched against four values.
