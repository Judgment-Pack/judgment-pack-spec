# RFC 0033: A paged operation source

- Status: Draft
- Type: Standards track, draft maturity. An amendment of the dialect companion,
  [`spec/dialect.md`](../spec/dialect.md), whose design record is [RFC 0018](0018-dialect.md): a
  named format `4.1.0`, proposed, of format `4.0.0`'s family.
- Created: 2026-11-15
- Issue: [#328](https://github.com/Judgment-Pack/judgment-pack-spec/issues/328), milestone `v0.6.0`
- Related: judgment-pack-runner #247 and its proposal, judgment-pack-runner #287, whose design
  record is the Runner's `docs/design/paging.md`; RFC 0018's amendment of 2026-11-12, format
  `4.0.0`, proposed

> This Draft is normative for nothing. [`spec/dialect.md`](../spec/dialect.md) is unchanged by it:
> the Specification below gives the text proposed for the companion, which lands only after
> acceptance, staged vectors, and the agreement of the reference Runner and a second reader on them.
> No schema, vector, reader or preparer changes with this Draft, and Core `0.5.0` is untouched.

## Summary

An `operation` source may declare `paging`: where in a page the next reference is read, which
request member it fills, where a page's records are, and a bound on pages. Its pages are one gateway
session's calls 0 to n−1, each with its own signed receipt, and each request after the first is the
first with that member set to the reference the page before named. The loop ends at a page that
names no next reference, or at the bound, and the preparation records which. The pages' records are
joined in call order, duplicates kept, and the source's read applies once to the joined value. A
verifier forms every request again and refuses a page that departs, with the dialect's existing
findings. `pageItems` stays refused. The form is a new named format, `4.1.0`; no document of an
earlier format changes its answer.

## Problem

A source that answers in pages cannot be read by a preparation today. Examples are a change query
that returns a reference to the next page, and a time window read page by page. The dialect
prepares one acquisition per source name (§4, §5.2). §5.2's check 1 refuses a receipt that attests
a page (`pageItems`), and refers to the reference Runner's deferred scope. So a job that runs
unattended, and has to read every page of its window or every change since its last run and decide
once over what it read, has no form. Its operator needs that decision to stay verifiable offline,
as a preparation over one acquisition is: each page held by its receipt, and each request shown to
follow from the case and the page before it.

## Evidence

- **The dialect.** §5.2 admits one `{"response"}` per source, and check 1 refuses `pageItems`
  "whatever the source's shape". §4.1 says `adapter-airbyte` answers every read with a page, so no
  acquisition of that shape is read. The sessions rule admits several sources in one session at
  differing call indexes, or each alone at call index 0. It has no form for several acquisitions of
  one source. §9.1 orders `cites` by `callIndex`, except with a `research` source, where it is in
  the order of `sources`.
- **The gateway** (its `SPEC.md`). A receipt's `callIndex` is 0-based and contiguous within a
  session, and its `prevSignature` names the previous receipt's signature, `null` at call 0 (§1.2).
  A seal records a session's `finalCount` (§3), and a session identifier is a flat token chosen by
  the caller (§3a). An adapter page, an envelope with `page: true`, is one result that is an array
  of items, which the gateway digests one by one into `pageItems` (§1.2a, §6). The gateway keeps no
  cursor: each `/acquire` is one request and one receipt. A page answered `429` or `503` is not
  receipted and takes no call index.
- **The reference Runner** (its `docs/design/paging.md`, sections 2 to 4). A run's input is held to
  2 MiB and one acquisition to 1 MiB, and the Runtime takes one facts document. The Runner names a
  session of its own for each unattended acquisition, and seals it after. The design compared three
  answers: a paged source in the dialect (A), one run per page (B), and one page per run (C). A is
  the only one in which a run reads every page of its window and is decided once, and the only one
  that keeps every page verifiable offline by `verify-run`. The maintainer chose A. The design asks
  the dialect for the rule (its 4.1), and for one receipt and one citation per page, in order
  (its 4.3).
- **Services in general** page in a few forms: a token in the answer that the caller sends back as
  one request member; a link to the next page; an offset; and a flag that more remains, beside the
  last record's identifier. A time window is usually read by a token within fixed bounds. This RFC
  serves the token form and the window read by a token. The others are unresolved questions 6 and 7.

## Specification

"§n" is a section of `spec/dialect.md`, and "section n" one of this Specification; "gateway §n" is
the gateway's `SPEC.md`. "MUST" and the other key words are as `spec/dialect.md` reads them.

### 1. Format 4.1.0

Format `4.1.0` is format `4.0.0`'s family, and every rule of §2.1 and §2.2 holds in it. It adds the
forms below and nothing else:

| Where | In format `4.1.0` |
| --- | --- |
| an `operation` source (§4.1) | MAY carry `paging` (section 2 below) |
| the acquisitions (§5.2) | a paged source's member is `{"pages": [...]}` (section 4) |
| §11, phase 4 | names `"4.1.0"` beside `"4.0.0"` (section 11) |
| the preparation (§9) | `formatVersion` `"4.1.0"`; a paged source's outcome, lineage and citations (section 8) |

In a document of format `2`, `3`, `2.0.0`, `3.0.0` or `4.0.0`, `paging` is a member §4.1 does not
list, `input-malformed`, and so is an acquisitions member of the form `{"pages"}`.

### 2. Declaring paging

In format `4.1.0` an `operation` source MAY carry `paging`, an object of exactly:

| Member | Form | Meaning |
| --- | --- | --- |
| `next` | a pointer (§1), not `""` | where, in each page's value read, the next reference is read |
| `fills` | a pointer, not `""` | the member of the request that the next reference fills |
| `items` | a pointer | where, in each page's value read, the page's records are: an array |
| `maxPages` | an integer of at least 1, and at most Core §4.1's "Dialect retained responses" (64 under `base`) | the most pages the loop reads |

A source that carries `paging` is a **paged source**, and a **page** is one of its acquisitions:
one call, one result and one receipt. A page here is not §5.1's constrained page, a web page read
by URL.

- `paging` is never on a source that has `calculation` (§7): `input-malformed`. No other kind takes
  it. An unbound operation (§4.4) may carry it, and binding leaves it as written.
- `fills`'s parent, the pointer without its last token, MUST resolve, in the source's `arguments` as
  the dialect writes them, to an object that is not a template form and lies within no template
  form. Its last token names a member of that object, which the object may or may not hold.
  Otherwise the dialect is `input-malformed`. (The parent is literal, so every page's request has
  it.)
- Under a profile of shape `mcp`, `fills` names a member within the call's `arguments`: its first
  token is `arguments`, and it has a second. Under a profile whose adapter is `adapter-http`, it
  names a member of `query`, or a member within an object `body`. Otherwise the source is
  `profile-mismatch` (§4.1, §5.1), as any request that does not fit its profile is.
- A `maxPages` that is not an integer, or is below 1, is `input-malformed`. One above the row under
  the document's profile is `input-over-bound`, in §11's phase 3.

The read digest (§6) stays the digest of `read`. `paging` is committed by the dialect digest, as a
request's template is.

### 3. The requests

The first page's request, `Q0`, is the source's request (§4.1). For `i` from 1, `Qi` is `Q0` with
the member that `fills` names set to `ri−1`, the next reference that page `i−1` named. The member is
replaced where `Q0` holds it and added where it does not, and nothing else in `Q0` changes. A next
reference is carried as the JSON string it is: it is never parsed, split, or rendered into another
member. Since `Q0` is in the `canon` domain and a string is, so is every `Qi`.

A change query names in `fills` the member its first page takes from a case parameter, and later
pages replace it. A time window whose start and end are case parameters names a member that `Q0`
lacks, and the second page adds it.

### 4. The pages and their checks

A paged source's member of the acquisitions is `{"pages": [P0, P1, ...]}`, exactly, of at least one
element. Each `Pi` is `{"result": R, "receipt": E, "salts": S}`, exactly, the form that §5.2's
`response` has, and is the gateway's acquire answer for call `i`, as the preparer kept it. For a
paged source, a `{"response"}` member is `input-malformed`, and so is `{"pages"}` for a source that
is not paged. More elements than the "Dialect retained responses" row allows is
`input-over-bound`, in phase 3.

A skipped paged source that has a member is `acquisition-unexpected` (§5.2), as any skipped source
is, and is not walked. Otherwise a verifier walks the pages from `i = 0`, finishing each page
before it takes the next. Each page gives its findings in this order:

1. When the acquisitions hold no `Pi`: `acquisition-missing`.
2. §5.2's checks 1 to 5 on `Pi`, under the source's profile, with check 4 opened over `Qi`:
   `acquisition-invalid`. Check 1's refusal of `pageItems` holds for every page. Since the rule in
   step 4 reads `prevSignature`, check 1 holds it to its form, `null` or a signature (gateway
   §1.2a).
3. §5.2's times, for each page against `verifiedAt` under the source's `maxAge`:
   `acquisition-stale`.
4. The page's session: `Ei.sessionId` is `E0.sessionId`; `Ei.callIndex` is `i`; `Ei.prevSignature`
   is `null` for `i = 0`, and `Ei−1.signature` otherwise. For `i = 0` also, no receipt of an earlier
   source names `E0.sessionId`. Otherwise: `acquisition-sessions`.
5. The page's value read, `vi`: §6.1's `unwrap` applied to `R`. Then `items` MUST resolve in `vi` to
   an array, and `next`'s parent to an object; otherwise `read-failed`. The member that `next`
   names, when it is absent, `null` or `""`, names no next reference. When it is any other string,
   that string is `ri`. When it is of another type, the result is `read-failed`. An `ri` equal to
   an earlier page's reference, or to the string `Q0` holds at `fills`, is `read-failed`, because
   the loop would read a page it has read.
6. When page `i` names no next reference, the loop ends there, and its **end** is `no-next`. When
   it names one and `i + 1` is `maxPages`, the loop ends there, and its end is `bound`. Otherwise
   the walk takes page `i + 1`.

After the walk, an element of `pages` after the last page the walk took is `acquisition-unexpected`.
Then the source's read is applied to the joined value (section 6), giving `read-failed` as §6 gives
it.

**The sessions across sources.** §5.2's two forms hold, as written, over the receipts of the
sources that are not paged. A paged source's session is its own: a receipt of another source that
names it is `acquisition-sessions`, at the first such receipt in the order of `sources`. Step 4
holds the same in the other direction. The pages are calls `0` to `n−1` of that session, chained by
`prevSignature`. *Why:* only a session of its own lets the call indexes and the chain show that no
call came between two pages. The gateway already holds `callIndex` contiguous and the chain in
order (gateway §1.2), so a sequence that passes here is one the gateway's own verifier walks.

**Each departure and its finding.** No new finding or refusal is needed:

| Departure | Answer |
| --- | --- |
| a page's request is not the one formed from the case and the page before | `acquisition-invalid` (check 4) |
| pages retained in another order than their calls | `acquisition-invalid` at the first misplaced page, whose receipt commits another request |
| a gap in call indexes, or call indexes that are out of order while the requests are in order | `acquisition-sessions` |
| a page from another session, or a broken `prevSignature` chain | `acquisition-sessions` |
| a paged source's session that is shared with another source | `acquisition-sessions` |
| a page retained after one that named no next reference | `acquisition-unexpected` |
| more pages than `maxPages` | `acquisition-unexpected`; over the row, `input-over-bound` |
| a page the loop calls for that is not retained | `acquisition-missing` |
| a next reference of another type, a repeated one, or a missing `items` array or `next` parent | `read-failed` |
| a page whose receipt carries `pageItems` | `acquisition-invalid` |

### 5. The end of the loop

The loop has two ends: a page that names no next reference (`no-next`), or the bound (`bound`).
`no-next` takes precedence: a page at the bound that names none ends at `no-next`. Which end it was
is recomputed by the verifier, and it is retained twice: in the joined value, where a rule can read
it (section 6), and in the preparation's outcome (section 8). So a reader of the preparation alone
knows which one ended the loop. A preparer's deadline, a throttled page that was never answered, or
a source failure is not an end. A preparer stopped by one of these has no preparation. Given its
pages, a verifier answers `acquisition-missing` at the page the loop calls for.

### 6. The joined value and the read

The **joined value** of a paged source is the object `{"end": E, "items": I, "pages": N}`:

- `E` is `"no-next"` or `"bound"`;
- `I` is every page's `items` array, concatenated in call order, each element as the page holds it;
- `N` is the number of pages read.

The source's `copy` or `rule` (§6.2, §6.3) applies once, to the joined value, as the value read,
and `unwrap` is not applied again. The claim, its class (the profile's, §5.1), its targets and its
lineage are one source's, as for any `operation`.

**Duplicates are kept.** An element that appears on two pages appears twice in `I`, and nothing is
removed or merged. *Why:* the dialect has no record identity. Equality of two JSON values is not
identity: two equal elements may be two records, and one record changed between two pages is two
unequal elements. Removing one would make `I` something other than the pages' bytes in call order,
which is what §13 lets a verifier establish. A source that moves under its reader shows up as
repeats or gaps that no rule of the dialect can tell from data. A rule that needs distinct records
can test for them, and the pack decides what a repeat means.

*Why one read over the joined value, rather than one per page:* a claim's `acquisitionStatus`,
`reason` and `basis` have no join, and a rule applied to one page cannot see another page's records.
A job reads its window to decide once over all of it, and the pages are where the source cuts its
answer, not where the pack does.

### 7. Bounds

- `maxPages`, and the number of pages retained for one paged source, are at most Core §4.1's
  "Dialect retained responses": 64 under `base` and 128 under `extended`. They are measured in
  phase 3. A page is a retained response, the same row a `research` source's responses take.
- A next reference is at most Core §4.1's "Dialect text value bytes" (8192 UTF-8 bytes under
  `base`). It is measured when read, during recomputation, as an unwrapped string's bytes are, and
  refused `input-over-bound` with nothing else reported.
- The joined value's nesting is at most §12's value nesting (32 levels under `base`). It is
  measured when the value is formed, before the read applies, as §6.4's combined value is, and
  refused `input-over-bound` otherwise.
- The dialect, the case and the acquisitions, every page included, stay within §12's combined
  bound, 2097152 bytes under `base`. The dialect has no byte bound per acquisition, and this adds
  none per page. The joined value adds no byte bound of its own, since each element is a value read
  from a retained page.
- The Runner's limits are a preparer's own: 1 MiB per acquisition, which holds for each page, and
  2 MiB per run input, which equals the combined bound under `base`. With full pages a paged read
  holds one or two pages; holding more is unresolved question 9. The bundled verifiers support
  `base` alone (§2).

### 8. The preparation

A preparation of a dialect of format `4.1.0` has `formatVersion` `"4.1.0"`, and is §2.2.6's form
with these additions:

- **The outcome** of an acquired paged source carries `arguments`, `Q0`, as every acquired source
  carries its request, and `paging`: `{"end": E, "pages": N, "references": [r0, ..., rN−2]}`, the
  loop's end, the number of pages, and the next references the loop followed, in call order, `N−1`
  of them. Since `Q0` and `references` give every request, a reader of the preparation alone can
  tell what each page was asked with. A skipped paged source has neither `arguments` nor `paging`
  (§9.2), and no other outcome carries `paging`.
- **Lineage.** Each entry of an acquired paged source carries `receipts`, its pages' citations
  (§5.2) in call order, and no `receipt`: one citation per page, as the Runner's design asks.
- **`cites`.** In a preparation with a paged source, `cites` is in the order of `sources`, as it is
  with a `research` source (§9.1). Each paged source adds its pages' citations in call order, a
  `research` source adds its list, and every other acquired source adds its one citation.
- **`unsignedParameters`** (§11). A paged source's acquisition commits a parameter that `Q0`
  commits (§4.1). A parameter carried only at `fills` is committed by the first page's receipt, and
  by none after it.
- **`unsignedFreshness`** keeps one entry per acquired source, `checks` `["acquisition"]`, judged
  for every page.
- `verification` is unchanged: the pages are verified acquisitions, and a session's sealing is not
  established (section 9).

### 9. What a paged acquisition establishes

Proposed for §13, beside "An acquisition of class `record`":

- **A paged acquisition, verified.** Establishes: for each page, what an acquisition establishes;
  that the pages are calls 0 to n−1 of one session that no other source used, chained in that
  order; that each request after the first is the first with one member set to the reference the
  page before named; and that the loop ended where its pages say, at a page that named no next
  reference or at the declared bound.

  Does not establish: that the session is sealed, or that no call was made in it after the last
  page (the seal is not read here, unresolved question 1); that the caller did not discard a whole
  session and begin again; that the source did not change between pages, so that records moved,
  repeated or were skipped; that the joined records are distinct, or complete for any window when
  the loop ended at `bound`; that a reference means what the source says it means.

### 10. `pageItems`

§5.2's check 1 stays as written, for every page of a paged source as for any acquisition. A receipt
that carries `pageItems` attests an adapter's page: the adapter paged within one call, by a
continuation it holds, such as `adapter-airbyte`'s stream state. The receipt commits neither where
that paging goes next nor whether the page is the last, so no verifier can form the next request
from it, or tell a whole read from part of one. Its item digests serve a consumer that re-digests
one item it uses (gateway §5a), not a preparation over the whole. A paged source's page is the
whole result of a request the caller formed, which a verifier forms again. `airbyte` stays defined
and not claimable (unresolved question 10).

### 11. Readers that do not read the format

A reader written to the text before this amendment defines no format `4.1.0`. It takes §11's phases
0 to 3 as for any document, and refuses a document of the format that passes them in phase 5, as an
unknown selector (§2.1): `input-malformed`. A reader written to this text that does not read the
format takes phases 0 to 3 as it takes them for format `4.0.0`, and refuses the document
`version-unread` in phase 4, before any form; phase 4 names `"4.1.0"` beside `"4.0.0"`. Neither
reads more of the document, and neither changes its answer to a document of an earlier format. So a
reader that does not read paging never reads one page of a paged source as a whole read.

### 12. Out of scope

- A cursor kept between runs, per job and source. That is the Runner's (its design, 4.1 and 4.2):
  it fills a case parameter, which `Q0` carries, so the case retained in the run says where the
  first page began.
- A cursor or high-water mark kept by the gateway. Paging stays the caller's.
- Throttling and retries inside the loop. These follow the Runner's retry policy. A page answered
  `429` or `503` takes no call index, so asking it again in the same session leaves no gap.
- Evaluating records one by one. The joined value is read once.
- Paging over a durable connection, and every kind other than `operation`.

## Alternatives

- **No change.** A job reads one page per source and cannot read a window.
- **One run per page, or one page per run** (the Runner's B and C). These need no amendment. B
  decides each page apart, so a decision depends on where the source cuts its pages. C cannot
  advance a window of more than one page. C is A's subset for change references alone, and the
  Runner may build it first.
- **A claim per page joined, duplicates removed, pages anywhere in a shared session, or
  `pageItems` read.** Rejected in sections 6, 6, 4 and 10.
- **Format `5.0.0`.** `4.1.0` is proposed instead, because every document of `4.0.0` keeps its
  answer and the format only adds. Under §2.1 a selector is exact, so the number carries no reader
  rule (unresolved question 2).
- **Paging over `3.0.0`'s family** (a `3.1.0`). The Runner could adopt it without first reading
  `4.0.0`, but there would be two selectors for one feature (unresolved question 3).

## Compatibility

- **Reader.** Every reader refuses a document of format `4.1.0` it does not read, by section 11.
  None of them reads part of one.
- **Writer.** A document with no paged source has no reason to take format `4.1.0`, and a writer
  SHOULD keep `4.0.0` for it. Writers discover the selectors a reader takes before they emit one
  (RFC 0021).
- **Semantic.** No answer, digest, preparation or vector of format `2`, `3`, `2.0.0`, `3.0.0` or
  `4.0.0` changes. The forty-seven staged vectors and format `4.0.0`'s rows stay as they are.
- **Migration.** A `4.0.0` document becomes a `4.1.0` one only by an explicit new artifact (RFC
  0021), under another digest.
- **Outside the companion.** As with format `4.0.0` (RFC 0018, the amendment of 2026-11-12, open
  question 2), no workflow schema names `4.1.0`, and the dialect-recording preparation schema
  requires an integer `version`. So neither admits the format until those documents change.

## Security and privacy

- **Resources.** The loop ends by `maxPages`, at most 64 under `base`. A cycle of references is
  refused at the first repeat, rather than read again until the bound. Every page counts against
  the combined byte bound, and the references and the joined value are bounded (section 7).
- **What a source can steer.** A next reference fills one declared member and nothing else. It
  cannot change a tool, a method or a path (section 2), nor the endpoint, which the profile pins
  and check 3 holds. It is never followed as a URL or spliced into a template.
- **Choosing among answers.** The call indexes and the chain show that no call came between two
  pages. They do not show a call after the last page, or a whole session begun and dropped
  (section 9).
- **A partial read.** A loop that ends at `bound` read part of the source. Its preparation says so,
  and a rule can test `/end` and claim `unknown`. A pack decided on a partial read without such a
  test is the dialect author's choice, and §13 says what was not established.
- **A wrong `next` pointer.** A member name misspelled in `next` reads as absent, so the loop ends
  after one page with end `no-next`. The rule that the parent must resolve catches a wrong parent,
  but not a wrong last token. The preparation shows `pages` 1, and an author's vectors should show
  the rest (unresolved question 8).
- **Disclosure.** A reference can carry a query's state, such as a filter or a scope identifier. It
  is already in the committed requests and the retained results. The preparation now carries it in
  `references`, as it carries every request in `arguments`.

## Conformance

The vectors are hand-written and staged in a directory of their own beside format `4.0.0`'s, in no
corpus and in no claim, as RFC 0018's are. Their receipts are signed under RFC 8032 section 7.1
TEST 1's published seed, as format `4.0.0`'s are. The reference Runner's recordings join them when
judgment-pack-runner #247 lands. Refusals are reader tests until the staging README defines a
refusal row. Each name takes the prefix `paged-`.

| Case | Kind | Expected |
| --- | --- | --- |
| `three-pages-no-next`: shape `mcp`, three pages, the third naming none | positive | reading; `paging` `no-next`, 3; three `cites` and `receipts` in call order |
| `one-page`: the first page names none | positive | reading; 1 page |
| `ends-at-bound`: `maxPages` 2, the second page names a reference | positive | reading; `bound` |
| `bound-rule-unknown`: a rule claims `unknown` when `/end` is `bound` | positive | reading; status `unknown` |
| `fills-added`: a window, `Q0` without the member | positive | reading |
| `fills-replaced`: `Q0`'s member from a case parameter | positive | reading; the parameter committed by page 0 |
| `end-null`, `end-empty-string` | positive | reading; `no-next` |
| `empty-middle-page`: `items` `[]` with a reference | positive | reading |
| `duplicates-kept`: one element on two pages | positive | reading; it appears twice in `items` |
| `http-query`: `adapter-http`, `fills` `/query/pageToken` | positive | reading |
| `beside-unpaged`: a paged and an unpaged source, sessions apart | positive | reading; `cites` in the order of `sources` |
| `max-pages-at-row`: 64 of 64 | boundary | reading |
| `max-pages-over-row`: `maxPages` 65 | boundary | refusal `input-over-bound` |
| `pages-over-row`: 65 pages retained | boundary | refusal `input-over-bound` |
| `reference-at-bytes`, `reference-over-bytes`: 8192 and 8193 bytes, two-byte characters | boundary | reading; refusal `input-over-bound` |
| `joined-nesting-over` | boundary | refusal `input-over-bound` |
| `request-not-formed`: page 1 asked with another reference | negative | `acquisition-invalid` |
| `pages-swapped` | adversarial | `acquisition-invalid` |
| `page-items-receipt`: page 1's receipt carries `pageItems` | negative | `acquisition-invalid` |
| `stale-last-page` | negative | `acquisition-stale` |
| `call-index-gap`: calls 0 and 2, page 1 asked twice and the second kept | adversarial | `acquisition-sessions` |
| `call-index-reordered`: calls 1 and 0, requests in loop order | adversarial | `acquisition-sessions` |
| `page-from-another-session` | adversarial | `acquisition-sessions` |
| `chain-broken`: page 1's `prevSignature` is not page 0's signature | adversarial | `acquisition-sessions` |
| `session-shared`: an unpaged source's receipt in the paged session | negative | `acquisition-sessions` |
| `page-missing`: page 0 names a reference below the bound, no page 1 | negative | `acquisition-missing` |
| `page-after-end` | adversarial | `acquisition-unexpected` |
| `page-beyond-bound`: `maxPages` 2, three retained | adversarial | `acquisition-unexpected` |
| `reference-repeated`, `reference-number`, `next-parent-absent`, `items-not-array` | negative | `read-failed` |
| `end-changed`, `reference-dropped`: the preparation's `paging` rewritten | adversarial | `preparation-differs` |
| `paging-in-4.0.0`, `paging-with-calculation`, `fills-in-template-form`, `pages-empty`, `max-pages-zero`, `response-form-for-paged` | negative | refusal `input-malformed` |
| `fills-tool`: shape `mcp`, `fills` `/tool` | negative | `profile-mismatch` |
| `format-4.1.0-unread`: a reader of this text that does not read the format; and the preserved `v0.3.0` reader | negative | refusal `version-unread`; refusal `input-malformed` |

## Implementation

- **The reference Runner**, judgment-pack-runner #247 (its design, section 4). It prepares a paged
  source over a gateway connection that is not durable, in a session of its own, sealed after the
  last page, and its `verify-run` verifies the run. It reads no format `4.0.0` today, so it reads
  that format first (unresolved question 3).
- **A second reader**: an offline preparation verifier written from this text alone, in another
  language than the first, as RFC 0018's second reader was. It verifies the staged vectors before
  the text is incorporated. The repository's reader that reads format `4.0.0` is the natural first
  reader of the hand-written vectors.

## Unresolved questions

1. **The seal.** Recommended: decide before Review whether to retain the session's seal record
   beside the pages and check `finalCount` equal to `n` under the profile's key. That would
   establish that no call followed the last page. It costs one acquisitions member and a new
   `verification` sentence, and the Runner already seals the session and receives the record.
   Without it, sealing stays the preparer's duty and outside what is established.
2. **The number.** Recommended: `4.1.0`. Alternatively `5.0.0`, following the step from `3.0.0`
   to `4.0.0`, where a format that only added forms took a new major.
3. **Riding on `4.0.0`.** Format `4.0.0` is proposed, and the Runner reads it nowhere. Recommended:
   keep `4.1.0`, and let #247 take up `4.0.0` first. Otherwise define the same addition over
   `3.0.0`.
4. **The deadline.** The Runner's design lists the occurrence's deadline as an end of the loop. Here
   it is not one (section 5). Recommended: the Runner fails the occurrence at its deadline.
5. **An expired reference.** The Runner re-reads from the cursor's first value. Recommended: it does
   so in a new session, with the case's parameter holding that first value, since the expired
   answer already took a call of the old session and `Q0` is formed from the case. The verifier
   sees only the new session; a dropped one is not shown.
6. **References that are not strings**, such as an integer offset. They are `read-failed` today.
   Recommended: leave them out until a source needs them.
7. **Other paging forms**: a link to the next page, which the profile's fixed endpoint cannot
   follow, and a has-more flag beside the last record's identifier. Neither is expressible.
   Recommended: a later amendment, with a source that needs it.
8. **The end's spellings.** Absent, `null` and `""`. Open: whether an `items` array missing from an
   empty last page should read as `[]` (`read-failed` today), and whether a repeated reference
   should end the loop instead of failing.
9. **More than two full pages.** This needs the Runner's retained pages moved out of the run's
   record (its 4.5), and a bound for a paged source apart from the combined bound.
10. **`adapter-airbyte`.** Its every answer carries `pageItems`. Open: whether a paged source should
    ever read such pages.
11. **The review.** Under RFC 0009 the pull request that moves this Draft to Review carries a
    recorded adversarial review and its dispositions. None has run.
