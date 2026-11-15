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
joined in call order, duplicates kept, beside each page's whole value read and the last page's
again, and the source's read applies once to the joined value. A verifier forms every request
again and refuses a page that departs, with the dialect's existing
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
| §11, phase 3 | measures `maxPages`, the number of `pages`, and each page's `result` nesting (section 7) |
| the passages of §§2.1, 5.2, 9, 11, 12, 13 and 14 that section 12 lists | amended (section 12) |

In a document of format `2`, `3`, `2.0.0`, `3.0.0` or `4.0.0`, `paging` is a member §4.1 does not
list, `input-malformed`, and so is an acquisitions member that has `pages`. Phase 3 measures none of
them in such a document (section 7), so past phase 4 its answer is that refusal in phase 5, whatever
their size or nesting.

### 2. Declaring paging

In format `4.1.0` an `operation` source MAY carry `paging`, an object of exactly:

| Member | Form | Meaning |
| --- | --- | --- |
| `next` | a pointer (§1), not `""` | where, in each page's value read, the next reference is read |
| `noNext` | `"absent"`, `"null"` or `"empty-string"` | the one spelling of `next`'s member by which a page names no next reference: the member absent, `null`, or `""` |
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
- `paging` is admitted under exactly two kinds of profile, and under each `fills` may name only
  these members of the request:
  - a profile of shape `mcp`: a member within the tool call's `arguments`. `fills`'s first token is
    `arguments`, and it has at least a second. It never names `tool`, nor `arguments` itself.
  - a profile of shape `http` whose `adapter.name` is exactly `adapter-http`: a member of `query`,
    where `fills` is exactly two tokens, the first `query`; or a member within `body`, where
    `fills`'s first token is `body`, it has at least a second, and `body` is an object. It never
    names `method`, `path`, `query` itself or `body` itself.

  A paged source under any other profile is `profile-mismatch` (§4.1, §5.1), as any request that
  does not fit its profile is: shape `airbyte`; shape `command`; and shape `http` under any other
  adapter, a connection's request `{connection, revision, read, …}` among them. So is a `fills`
  that names any other member under the two profiles above. *Why:* a connection's request is held
  out because its members are known by their form to choose what is read: the connection, its
  revision and its read. Under the two profiles admitted, the tool, the method, the path and the
  endpoint lie outside every member `fills` may name: the profile's `tools`, the template and
  check 3 pin them. So no next reference can choose the next call's tool, method, path, endpoint or
  host. It can choose whatever else the filled member means. The dialect knows no more of what a
  member within a tool's `arguments` or a request's `query` or `body` means than it knows of a
  connection's members: under `mcp` an argument may select the scope or the read as well as
  continue one, and so may a `body` member. The next reference is the source's content, and the
  member it fills carries what the source wrote. The dialect author chooses `fills`, as they choose
  the template, and SHOULD name only a member that the tool or the service defines as an opaque
  continuation of the same read, such as a page token. A `query` member stays one query value only
  because the adapter encodes each value it writes into the URL, so that a reference holding `&` or
  `=` adds no parameter; the reference gateway's `adapter-http` does, and no verifier checks it.
- A `maxPages` that is not an integer (§1), such as `1e3` or `2.0`, or is below 1, is
  `input-malformed`, in phase 5, whatever its magnitude. An integer above the row under the
  document's profile is `input-over-bound`, in §11's phase 3 (section 7).
- A `noNext` of another value is `input-malformed`.

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
paged source, a member that has `response` is `input-malformed`, and so is a member that has
`pages` for a source that is not paged; a member that has both is of neither form, and is
`input-malformed` for every source. More elements than the "Dialect retained responses" row allows is
`input-over-bound`, in phase 3 (section 7).

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
5. The page's value read, `vi`: §6.1's `unwrap` applied to `R`. Then, in this order: `items` MUST
   resolve in `vi` to an array, and then `next`'s parent to an object; otherwise `read-failed`.
   Then the member that `next` names is read. When it is spelled as `noNext` declares (absent,
   `null` or `""`), it names no next reference. When it is a string that is not `""`, that string
   is `ri`, and its bytes are then measured (section 7). Anything else is `read-failed`: a value of
   another type, `null` or an absent member when `noNext` declares another spelling, and `""` when
   `noNext` is not `"empty-string"`. So a page whose `items` is not an array is `read-failed`
   whatever its reference's size, and only a reference is measured.
6. When page `i` names no next reference, the loop ends there, and its **end** is `no-next`. When
   it names one and `i + 1` is `maxPages`, the loop ends there, and its end is `bound`: `ri` is not
   followed, so it is measured for bytes in step 5 and not checked for repeats, since no page is
   read with it. Otherwise an `ri` equal to an earlier page's reference, or to the string `Q0`
   holds at `fills` when it holds a string there, is `read-failed`, because the loop would read a
   page it has read; and the walk takes page `i + 1`. Two references are equal when they are equal
   code point for code point, as §2.2.4 compares a string with a list's: no case folding, no
   Unicode normalization and no trimming, so that a precomposed `é` and `e` followed by U+0301 are
   two references, each followed.

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

**A known limit: a key rotated within a session.** Check 2 holds every page under the profile's
one `publicKey`. A gateway that rotates its key between two pages of one session signs the later
pages under a key the profile does not name, and the first of them is `acquisition-invalid`. The
preparer reads the source again from page 0 in a new session, under a profile of the new key. A
profile names one key, and this amendment adds none.

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
| a next reference of another type or spelled as an end `noNext` does not declare, a repeated one, or a missing `items` array or `next` parent | `read-failed` |
| a page whose `prevSignature` is neither `null` nor a signature in form | `acquisition-invalid` (check 1) |
| a page whose receipt carries `pageItems` | `acquisition-invalid` |

### 5. The end of the loop

The loop has two ends: a page that names no next reference (`no-next`), or the bound (`bound`).
`no-next` takes precedence: a page at the bound that names none ends at `no-next`. Which end it was
is recomputed by the verifier, and it is retained twice: in the joined value, where a rule can read
it (section 6), and in the preparation's outcome (section 8). So a reader of the preparation alone
knows which one ended the loop. A preparer's deadline, a throttled page that was never answered, or
a source failure is not an end. A preparer stopped by one of these has no preparation. Given its
pages, a verifier answers `acquisition-missing` at the page the loop calls for. The Runner fails
the occurrence at its deadline (question 4).

### 6. The joined value and the read

The **joined value** of a paged source is the object
`{"end": X, "items": I, "last": L, "pages": N, "values": V}`:

- `X` is `"no-next"` or `"bound"`;
- `I` is every page's `items` array, concatenated in call order, each element as the page holds it;
- `L` is the last page's value read (section 4, step 5), whole: the same JSON value as `V`'s
  element `N − 1`;
- `N` is the number of pages read;
- `V` is `[v0, ..., vn−1]`, each page's value read (section 4, step 5), whole, in call order.

`N` is at least 1, so `L` is always present and `pages` is never 0. The acquisitions member of a
paged source holds at least one page (section 4: `{"pages": []}` is `input-malformed`); the walk
takes page 0 before any other, and a page 0 not retained is `acquisition-missing`; and the reading
ends at its first finding (§11), so the read over the joined value applies only after a walk that
took page 0, and every page after it that the loop called for, without a finding. A skipped paged source is not walked, and
its claim is §9.2's, with no read, so it forms no joined value.

The source's `copy` or `rule` (§6.2, §6.3) applies once, to the joined value, as the value read,
and `unwrap` is not applied again. The claim, its class (the profile's, §5.1), its targets and its
lineage are one source's, as for any `operation`.

**A page's own members are kept.** A page's value read may carry more than its records and its
next reference: a flag that the read is incomplete, a count, a warning. `V` keeps each page's,
so a rule can test any page's flag, at `/values/i` followed by the flag's pointer within the
page, as a rule over an unpaged read tests it at the flag's pointer. The last page's flag is tested
at `/last` followed by the same pointer, `/last/incomplete`, whatever the page count: one clause,
not one per count up to `maxPages`. *Why:* a joined value of `items` alone would let a last page
`{"items": [...], "incomplete": true}` that names no next reference read as a whole read, ending
`no-next`, where an unpaged read of the same answer could test `/incomplete`. And without `last`,
the last page sits at `/values/` followed by an index that a pointer names as a fixed number, so a
rule would need a clause for each count. `L` adds nothing that `V` does not hold: a verifier forms
it again from `V` (section 9), and a reader that sets it to another page's value read reads the
rule over another value, which the vector `last-is-the-last-page` shows (Conformance).

**Duplicates are kept.** An element that appears on two pages appears twice in `I`, and nothing is
removed or merged. *Why:* the dialect has no record identity. Equality of two JSON values is not
identity: two equal elements may be two records, and one record changed between two pages is two
unequal elements. Removing one would make `I` something other than the pages' bytes in call order,
which is what §13 lets a verifier establish. A source that moves under its reader shows up as
repeats or gaps that no rule of the dialect can tell from data. Neither rule version `1` nor `2.0.0`
has an operator that iterates over records or counts them, so no rule tests for distinct records:
only the pack can, and the pack decides what a repeat means.

*Why one read over the joined value, rather than one per page:* a claim's `acquisitionStatus`,
`reason` and `basis` have no join, and a rule applied to one page cannot see another page's records.
A job reads its window to decide once over all of it, and the pages are where the source cuts its
answer, not where the pack does.

### 7. Bounds

- `maxPages`, and the number of pages retained for one paged source, are at most Core §4.1's
  "Dialect retained responses": 64 under `base` and 128 under `extended`. A page is a retained
  response, the same row a `research` source's responses take.
- Each page's `result` is held to §12's nesting of a value a read applies to, 32 levels under
  `base`, as every acquisition's result is: a page is an acquisition (section 4), and §11's phase 3
  measures "the nesting of each acquisition's result".
- These are measured in phase 3, wherever measurable before any form, and only in a document whose
  `formatVersion` is `"4.1.0"`: `maxPages` when it is an integer (§1); and, in every acquisitions
  member that has `pages`, before phase 5 decides whether its source is paged, the number of
  elements of `pages` when it is an array, and the nesting of the `result` of each element that is
  an object with a `result` member. Otherwise phase 3 measures none of them, and phase 5 decides:
  in a document of an earlier format `paging` and a member that has `pages` are `input-malformed`
  (section 1), and so is a `maxPages` that is not an integer, such as `1e3` (section 2). So a page
  whose `result` nests 33 levels is refused `input-over-bound` in phase 3, before any page's
  receipt is checked, whatever its value read would be after `unwrap`, and every reader refuses it
  there alike.
- A next reference is at most Core §4.1's "Dialect text value bytes" (8192 UTF-8 bytes under
  `base`). It is measured when read, during recomputation, as an unwrapped string's bytes are, and
  refused `input-over-bound` with nothing else reported.
- The joined value's nesting, `values` included, is at most §12's value nesting (32 levels under
  `base`). Each page's value read sits two levels below the joined value's root, in `values`, so a
  page whose value read is nested at more than 30 levels is refused here, although its result is
  within the bound. Each element of `items` is a part of its page's value read, and sits two
  levels below the root too; `last` sits one level below it, and holds a value that `values` holds
  one level deeper; so `values` decides. It is measured when the value is formed, before the read
  applies, as §6.4's combined value is, and refused `input-over-bound` otherwise.
- The dialect, the case and the acquisitions, every page included, stay within §12's combined
  bound, 2097152 bytes under `base`. The dialect has no byte bound per acquisition, and this adds
  none per page. The joined value adds no byte bound of its own: `values` holds each page's value
  read, a part of a retained result, once, `items` holds each record a second time, and `last`
  holds the last page's value read a second time, so the joined value is about twice the pages'
  values read plus the last page's once more, and is bounded by the retained pages.
- The preparation keeps §12's 8388608 bytes, and its `references` are a part of it that page
  content sizes. In §9.5's form a reference grows by up to six times: `<`, `>` and `&` are written
  `<`, `>` and `&`, and a control character other than the five with a short escape
  as `\u00` and two digits. Up to 2 MiB of references can lie within the combined bound, so a
  preparation whose references are mostly such characters can exceed 8 MiB. It fails closed: a
  preparer cannot write it, and a verifier refuses it `input-over-bound` in phase 1. But the
  source's pages, not the dialect, decide whether a read stays within it, and this amendment adds no
  bound on the references' total.
- The Runner's limits are a preparer's own: 1 MiB per acquisition, which holds for each page, and
  2 MiB per run input, which equals the combined bound under `base`. With full pages a paged read
  holds one or two pages; holding more is unresolved question 9. The bundled verifiers support
  `base` alone (§2).

### 8. The preparation

A preparation of a dialect of format `4.1.0` has `formatVersion` `"4.1.0"`, and is §2.2.6's form
with these additions:

- **The outcome** of an acquired paged source carries `arguments`, `Q0`, as every acquired source
  carries its request, and `paging`: `{"end": X, "pages": N, "references": [r0, ..., rN−2]}`, the
  loop's end, the number of pages, and the next references the loop followed, in call order, `N−1`
  of them. Since `Q0` and `references` give every request, a reader of the preparation alone can
  tell what each page was asked with. A skipped paged source has neither `arguments` nor `paging`
  (§9.2), and no other outcome carries `paging`.
- **Lineage.** Each entry of an acquired paged source carries `receipts`, its pages' citations
  (§5.2) in call order, and no `receipt`: one citation per page, as the Runner's design asks.
- **`cites`.** In a preparation of a dialect that declares a paged source, acquired or skipped,
  `cites` is in the order of `sources`, as it is with a `research` source (§9.1). Each acquired
  paged source adds its pages' citations in call order, a `research` source adds its list, every
  other acquired source adds its one citation, and a skipped source adds none. The order is keyed
  on the dialect, not on what was acquired, so that a skipped paged source changes it as an
  acquired one does: with the paged source skipped and two unpaged sources sharing a session at
  call indexes 1 and 0, in the order of `sources`, `cites` holds the call at index 1 first. §9.1's
  rule for a `research` source reads "in a preparation with one", which leaves the same question
  open for a skipped `research` source; this amendment does not settle it (unresolved question 13).
- **`unsignedParameters`** (§11). A paged source's acquisition commits a parameter that `Q0`
  commits (§4.1). A parameter carried only at `fills` is committed by the first page's receipt, and
  by none after it. A starting cursor that the case carries from an earlier run is committed so,
  and is not in `unsignedParameters`; that it continues the earlier run is not established
  (section 9).
- **`unsignedFreshness`** keeps one entry per acquired source, `checks` `["acquisition"]`, judged
  for every page.
- `verification` is unchanged: the pages are verified acquisitions, and a session's sealing is not
  established (section 9).

### 9. What a paged acquisition establishes

Proposed for §13, beside "An acquisition of class `record`":

- **A paged acquisition, verified.** Establishes: for each page, what an acquisition establishes;
  that the pages are calls 0 to n−1 of one session that no other source of this preparation
  names, chained in that order; that each request after the first is the first with one member set to the reference the
  page before named; and that the loop ended where its pages say, at a page that named no next
  reference or at the declared bound. The joined value's members are formed from those pages
  alone: `last` is derived from `values`, its last element, and a verifier forms it again as it
  forms `end`, `items` and `pages`, so it establishes nothing beyond the pages.

  Does not establish: that the session is sealed, or that no call was made in it after the last
  page (the seal is not read here, question 1); that the caller did not discard a whole
  session and begin again; that the source did not change between pages, so that records moved,
  repeated or were skipped; that the joined records are distinct, or complete for any window when
  the loop ended at `bound`; that a reference means what the source says it means; that no other
  preparation, of this run or another, read the same session; that `Q0`'s reference or window
  continues from an earlier run: the starting cursor is the case's, which `Q0` commits, so it is
  absent from `unsignedParameters` and yet only the operator says it is where the last run
  stopped, and a gap of changes skipped between two runs is not shown.

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

### 12. Sentences of the companion this amends

These passages of `spec/dialect.md` say what is true of every format, acquisition or preparation
today, and are amended as follows when the format lands. Sections 1 to 11 land beside §2.2, as the
paged source's rule that the amended passages name.

- **§2.1, the `formatVersion` row.** Its form becomes "exactly `"2.0.0"` or `"3.0.0"`, or
  `"4.0.0"` or `"4.1.0"`, proposed (§2.2, and the paged source's rule)", and its meaning adds:
  "`"4.1.0"` selects `"4.0.0"`'s with the paged source's additions".
- **§5.2, the opening.** "of the form `{"response": {"result": R, "receipt": E, "salts": S}}`,
  exactly, except for `research` as below" becomes "…, exactly, except for `research` as below and,
  in format `4.1.0`, a paged source, whose member is `{"pages": [...]}` as the paged source's rule
  gives it".
- **§5.2, the sessions.** After "The form is read from the receipts and from nothing else.", add:
  "In format `4.1.0` the two forms hold over the receipts of the sources that are not paged; a
  paged source's session is its own, as the paged source's rule gives it."
- **§5.2, the last paragraph.** The sentence "The receipt's `caller`, its `statement`, its chain
  (`prevSignature`) and its `witness` are the gateway's verifier's to read (gateway §1.4, §4), and
  are not read here." becomes: "The receipt's `caller`, its `statement` and its `witness` are the
  gateway's verifier's to read (gateway §1.4, §4), and are not read here. Its chain
  (`prevSignature`) is read for a paged source's pages alone: check 1 holds it to its form, `null`
  or a signature, and the paged session rule holds page 0's to `null` and each later page's to the
  `signature` of the page before. For every other acquisition it is not read here."
- **§9.1, the `version` row.** "A preparation of a dialect of format `4.0.0` has `formatVersion`,
  `"4.0.0"`, in its place (§2.2.6)" becomes "A preparation of a dialect of format `4.0.0` or
  `4.1.0` has `formatVersion`, `"4.0.0"` or `"4.1.0"`, in its place (§2.2.6, and the paged source's
  rule)".
- **§9.1, the `cites` paragraph.** At its end, add: "In format `4.1.0`, in a preparation of a
  dialect that declares a paged source, acquired or skipped, `cites` is in the order of `sources`:
  each acquired paged source adds its pages' citations in call order, a `research` source its list
  as above, and every other acquired source its one citation."
- **§9.2, the outcome's members.** Add: "`paging`: in format `4.1.0`, for an acquired paged source,
  the loop's end, the number of pages and the next references followed (the paged source's rule);
  absent otherwise."
- **§9.3, the `receipt` and `receipts` rows.** `receipt` is also absent for an acquired paged
  source. `receipts` adds: "in format `4.1.0`, for an acquired paged source, its pages' citations in
  call order, the list it adds to `cites`".
- **§11, phase 3.** After "the nesting of each acquisition's result", add: "each page of a paged
  source being an acquisition; and, in format `4.1.0`, `maxPages` and the number of pages retained
  for one paged source (the paged source's rule)".
- **§11, phase 4.** "or whose `formatVersion` is `"4.0.0"`, a format the verifier does not read
  (§2.2.7)" becomes "or whose `formatVersion` is `"4.0.0"` or `"4.1.0"`, a format the verifier does
  not read (§2.2.7, and the paged source's rule)".
- **§11, the bounds measured later.** The paragraph that begins "Some bounds are measured later"
  adds a paged source's next reference, whose bytes are measured when step 5 reads it, and its
  joined value, whose nesting is measured when it is formed, before the read applies; over either
  the reading is refused, `input-over-bound`, with nothing reported but the refusal.
- **§11, finding 3.** After "`calculation-invalid` (§7) and `read-failed` (§6), in that order.",
  add: "For a paged source, after its `parameter-invalid`: when it is skipped and has a member,
  `acquisition-unexpected`, and nothing more for it. Otherwise its pages, from page 0, completing
  one page before the next, each in this order: `acquisition-missing` when the page is not
  retained; `acquisition-invalid`; `acquisition-stale`; `acquisition-sessions`; then `read-failed`
  for the page's own read: its `items` array, `next`'s parent, the next reference's spelling, and a
  repeated reference. After the last page the walk takes, `acquisition-unexpected` for a page
  retained after it. Then `read-failed` for the source's read over the joined value. So, unlike an
  unpaged source's, a paged source's findings interleave page by page: page 0's `read-failed`
  precedes page 1's `acquisition-invalid`, and a page's `read-failed` precedes the
  `acquisition-unexpected` of a page retained after the end. A receipt of a later source that names
  a paged source's session is `acquisition-sessions` at that later source, in its place among its
  own findings."
- **§12, the bound list.** Add an item: "in format `4.1.0`, the paged source's: `maxPages`, and the
  pages retained for one paged source, at most 64; a next reference at most 8192 UTF-8 bytes; and
  a joined value nested at most 32 levels. Each page's result is a result, held to the 32 levels
  above."
- **§13, the list.** Section 9's entry, after "An acquisition of class `record`".
- **§14, its last paragraph.** "No claim names format `4.0.0` (§2.2): its vectors are hand-written
  and staged" becomes "No claim names format `4.0.0` (§2.2) or `4.1.0`: their vectors are
  hand-written and staged".

### 13. Out of scope

- A cursor kept between runs, per job and source. That is the Runner's (its design, 4.1 and 4.2):
  it fills a case parameter, which `Q0` carries, so the case retained in the run says where the
  first page began. That it is where the earlier run stopped is the operator's say (section 9).
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
  rule (question 2, resolved).
- **Paging over `3.0.0`'s family** (a `3.1.0`). The Runner could adopt it without first reading
  `4.0.0`, but there would be two selectors for one feature (question 3, resolved).

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
  and check 3 holds. Paging is admitted only under a tool call's `arguments` and an `adapter-http`
  request's `query` and `body` (section 2), so no reference fills a member of a connection's
  request. Within those, the reference is the source's content, and the filled member means what
  the tool or the service says: an argument that selects a scope or a read takes what the source
  wrote. So a dialect author names in `fills` only an opaque continuation member (section 2). A
  `query` member stays one value by the adapter's encoding of query values, which no verifier
  checks. A reference is never followed as a URL or spliced into a template.
- **Choosing among answers.** The call indexes and the chain show that no call came between two
  pages. They do not show a call after the last page, or a whole session begun and dropped
  (section 9).
- **A partial read.** A loop that ends at `bound` read part of the source. Its preparation says so,
  and a rule can test `/end` and claim `unknown`. A page that says of itself that the read is
  incomplete keeps saying so in `/values`, and the last page in `/last` too, which one clause tests
  whatever the page count (section 6). A pack decided on a partial read without such a test is the
  dialect author's choice, and §13 says what was not established.
- **A wrong `next` pointer.** A member name misspelled in `next` reads as absent. Under `noNext`
  `"null"` or `"empty-string"`, that is `read-failed` at page 0, so the misspelling does not pass
  as a short read. Under `noNext` `"absent"` it ends the loop after one page with end `no-next`,
  as a source that answers in one page does. The rule that the parent must resolve catches a wrong
  parent, but not a wrong last token. The preparation shows `pages` 1, and an author's vectors
  should show the rest (question 8).
- **Disclosure.** A reference can carry a query's state, such as a filter or a scope identifier. It
  is already in the committed requests and the retained results. The preparation now carries it in
  `references`, as it carries every request in `arguments`. A reference can also be a signed or
  bearer-like token, which a holder may present to the source to read on until it expires. A
  preparation may travel further than the raw results, to a record's reader or an auditor who is
  not given the pages, so a preparer and an operator treat `references` as they treat the results:
  a source whose references grant access is one whose preparations are held as its results are.

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
| `max-pages-one`: `maxPages` 1, page 0 names a reference | positive | reading; `bound`, 1 page, `references` `[]` |
| `reference-repeated-at-bound`: `maxPages` 2, page 1 names page 0's reference again | positive | reading; `bound` (not followed, so not a repeat) |
| `bound-rule-unknown`: a rule claims `unknown` when `/end` is `bound` | positive | reading; status `unknown` |
| `fills-added`: a window, `Q0` without the member | positive | reading |
| `fills-replaced`: `Q0`'s member from a case parameter | positive | reading; the parameter committed by page 0 |
| `end-absent`, `end-null`, `end-empty-string`: the last page's `next` member absent, `null` and `""`, each under the `noNext` that declares it | positive | reading; `no-next` |
| `empty-middle-page`: `items` `[]` with a reference | positive | reading |
| `duplicates-kept`: one element on two pages | positive | reading; it appears twice in `items` |
| `references-equivalent-not-equal`: three pages, page 0 naming a precomposed `é` and page 1 `e` followed by U+0301 | positive | reading; three pages, both references followed |
| `last-page-incomplete`: three pages, the third `{"items": [...], "incomplete": true}` naming none; a rule claims `unknown` when `/last/incomplete` is `true` | positive | reading; `no-next`; status `unknown` |
| `last-is-the-last-page`: three pages, the first `{"items": [...], "incomplete": true}` with a reference and the third `"incomplete": false` naming none; the same rule | positive | reading; `no-next`; status not `unknown` (a reader that sets `last` to the first page claims `unknown`) |
| `page-flag-at-values`: three pages, the second `"incomplete": true`; a rule claims `unknown` when `/values/1/incomplete` is `true` | positive | reading; status `unknown` |
| `http-query`: `adapter-http`, `fills` `/query/pageToken` | positive | reading |
| `http-body`: `adapter-http`, `body` an object, `fills` `/body/cursor` | positive | reading |
| `unbound-paged`: an unbound operation (§4.4) carrying `paging`, bound by a binding document | positive | reading; `paging` as written |
| `beside-unpaged`: a paged and an unpaged source, sessions apart | positive | reading; `cites` in the order of `sources` |
| `two-paged-sessions-apart`: two paged sources, each in a session of its own | positive | reading; `cites` in the order of `sources`, each source's pages in call order |
| `cites-order-paged-skipped`: a skipped paged source, and two unpaged sources sharing one session at call indexes 1 and 0, in the order of `sources` | positive | reading; `cites` in the order of `sources`, call index 1 first |
| `max-pages-at-row`: 64 of 64 | boundary | reading |
| `max-pages-over-row`: `maxPages` 65 | boundary | refusal `input-over-bound` |
| `pages-over-row`: 65 pages retained | boundary | refusal `input-over-bound` |
| `reference-at-bytes`: 4096 two-byte characters, 8192 bytes | boundary | reading |
| `reference-over-bytes`: 4096 two-byte characters and one one-byte character, 8193 bytes | boundary | refusal `input-over-bound` |
| `reference-over-bytes-at-bound`: `maxPages` 2, page 1 naming an 8193-byte reference that is not followed | boundary | refusal `input-over-bound` |
| `items-before-reference-bytes`: one page, `items` not an array, naming an 8193-byte reference | negative | `read-failed`, not `input-over-bound` |
| `joined-nesting-at-bound`: a page's value read at 30 levels, the joined value at 32 | boundary | reading |
| `joined-nesting-over`: a page's value read at 31 levels, the joined value at 33 | boundary | refusal `input-over-bound` |
| `page-result-nesting-at-bound`: page 1's `result` at 32 levels, unwrapped to a shallow value | boundary | reading |
| `page-result-nesting-over`: page 0's receipt failing check 2, and page 1's `result` at 33 levels, unwrapped to a shallow string | boundary | refusal `input-over-bound` in phase 3, not `acquisition-invalid` |
| `request-not-formed`: page 1 asked with another reference | negative | `acquisition-invalid` |
| `pages-swapped` | adversarial | `acquisition-invalid` |
| `page-items-receipt`: page 1's receipt carries `pageItems` | negative | `acquisition-invalid` |
| `prev-signature-malformed`: page 1's `prevSignature` neither `null` nor a signature in form | negative | `acquisition-invalid` |
| `stale-last-page` | negative | `acquisition-stale` |
| `stale-middle-page`: three pages, page 1's times outside `maxAge` | negative | `acquisition-stale` |
| `call-index-gap`: calls 0 and 2, page 1 asked twice and the second kept | adversarial | `acquisition-sessions` |
| `call-index-reordered`: calls 1 and 0, requests in loop order | adversarial | `acquisition-sessions` |
| `page-from-another-session` | adversarial | `acquisition-sessions` |
| `chain-broken`: page 1's `prevSignature` is not page 0's signature | adversarial | `acquisition-sessions` |
| `session-shared`: a later unpaged source's receipt in the paged session | negative | `acquisition-sessions` |
| `session-of-earlier-source`: page 0 in the session of an earlier unpaged source | negative | `acquisition-sessions` |
| `two-paged-one-session`: the second paged source's page 0 in the first's session | adversarial | `acquisition-sessions` |
| `page-missing`: page 0 names a reference below the bound, no page 1 | negative | `acquisition-missing` |
| `page-after-end` | adversarial | `acquisition-unexpected` |
| `page-beyond-bound`: `maxPages` 2, three retained | adversarial | `acquisition-unexpected` |
| `skipped-paged-with-member`: a skipped paged source with a member that has `pages` | negative | `acquisition-unexpected` |
| `reference-repeated`, `reference-number`, `next-parent-absent`, `items-not-array` | negative | `read-failed` |
| `reference-equals-q0`: page 0 names the string `Q0` holds at `fills` | adversarial | `read-failed` |
| `end-spelling-undeclared`: `noNext` `"null"`, the last page's `next` member `""` | negative | `read-failed` |
| `end-absent-member-null`: `noNext` `"absent"`, the last page's `next` member `null` | negative | `read-failed` |
| `next-misspelled`: `noNext` `"null"`, `next`'s last token misspelled, so every page's member is absent | negative | `read-failed` |
| `read-failed-before-invalid`: page 0's `items` not an array, and page 1's receipt not verifying | negative | `read-failed` (page 0's finding precedes page 1's) |
| `end-changed`, `reference-dropped`: the preparation's `paging` rewritten | adversarial | `preparation-differs` |
| `cites-by-call-index-paged-skipped`: `cites-order-paged-skipped`'s preparation with `cites` ordered by call index | adversarial | `preparation-differs` |
| `paging-in-4.0.0`, `paging-with-calculation`, `fills-in-template-form`, `fills-parent-unresolved`, `pages-empty`, `max-pages-zero`, `response-form-for-paged`, `pages-form-for-unpaged`, `pages-and-response`, `no-next-unknown` | negative | refusal `input-malformed` |
| `max-pages-not-integer`: `maxPages` `1e3` | negative | refusal `input-malformed` |
| `pages-over-row-in-4.0.0`: 65 pages retained in a document of format `4.0.0` | negative | refusal `input-malformed`, not `input-over-bound` |
| `fills-tool`: shape `mcp`, `fills` `/tool` | negative | `profile-mismatch` |
| `fills-path`, `fills-method`: `adapter-http`, `fills` `/path` and `/method` | negative | `profile-mismatch` |
| `fills-connection`: shape `http` under a connection's profile, `fills` `/connection` | negative | `profile-mismatch` |
| `fills-arguments-itself`, `fills-query-itself`, `fills-body-itself`: `fills` `/arguments` under shape `mcp`, and `/query` and `/body` under `adapter-http` | negative | `profile-mismatch` |
| `fills-query-three-tokens`: `adapter-http`, `fills` `/query/filter/cursor`, `Q0`'s `query` holding `filter` as an object so that the parent resolves | negative | `profile-mismatch` |
| `format-4.1.0-unread`: a reader of this text that does not read the format; and the preserved `v0.3.0` reader | negative | refusal `version-unread`; refusal `input-malformed` |

## Implementation

- **The reference Runner**, judgment-pack-runner #247 (its design, section 4). It prepares a paged
  source over a gateway connection that is not durable, in a session of its own, sealed after the
  last page, and its `verify-run` verifies the run. It reads no format `4.0.0` today, so it reads
  that format first (question 3, resolved).
- **A second reader**: an offline preparation verifier written from this text alone, in another
  language than the first, as RFC 0018's second reader was. It verifies the staged vectors before
  the text is incorporated. The repository's reader that reads format `4.0.0` is the natural first
  reader of the hand-written vectors.

## Unresolved questions

1. **The seal.** Resolved: not required. Retaining the session's seal record beside the pages and
   checking `finalCount` equal to `n` would show that no call followed the last page. But dropping
   the last pages already gives `acquisition-missing`, since the last page retained then names a
   next reference below the bound, which the loop calls for; and a seal does nothing about a
   caller who discards a whole session and begins again, which stays outside what is established
   (section 9). Sealing stays the preparer's duty. Decided before Review, because adding a seal
   later would change the acquisitions' form.
2. **The number.** Resolved: `4.1.0`, stated as format `4.0.0` as published at the same
   specification version, plus this amendment. `5.0.0`, following the step from `3.0.0` to
   `4.0.0`, where a format that only added forms took a new major, is not taken.
3. **Riding on `4.0.0`.** Resolved: build on `4.0.0`, which is proposed and which the Runner reads
   nowhere today. The reference Runner reads `4.0.0` first, and judgment-pack-runner #247 depends
   on that. The same addition over `3.0.0` is not defined.
4. **The deadline.** Resolved: not an end of the loop (section 5), though the Runner's design lists
   the occurrence's deadline as one. The Runner fails the occurrence at its deadline, because a
   deadline end would let the preparer choose where the read stops.
5. **An expired reference.** The Runner re-reads from the cursor's first value. Recommended: it does
   so in a new session, with the case's parameter holding that first value, since the expired
   answer already took a call of the old session and `Q0` is formed from the case. The verifier
   sees only the new session; a dropped one is not shown.
6. **References that are not strings**, such as an integer offset. They are `read-failed` today.
   Recommended: leave them out until a source needs them.
7. **Other paging forms**: a link to the next page, which the profile's fixed endpoint cannot
   follow, and a has-more flag beside the last record's identifier. Neither is expressible.
   Recommended: a later amendment, with a source that needs it.
8. **The end's spelling.** Narrowed: a source declares one, `noNext` (section 2), absent, `null`
   or `""`, and every other spelling is `read-failed` (section 4, step 5). A misspelled last token
   in `next` still ends the loop after one page under `"absent"` (Security). An API that drops
   `next`'s parent, and not only its member, on its last page gets `read-failed` under this rule,
   since the parent must resolve; it would need `"absent"` together with a parent read as
   optional, which this text does not offer. Open: whether to offer that; whether an `items`
   array missing from an empty last page should read as `[]` (`read-failed` today); and whether a
   repeated reference should end the loop instead of failing.
9. **More than two full pages.** This needs the Runner's retained pages moved out of the run's
   record (its 4.5), and a bound for a paged source apart from the combined bound.
10. **`adapter-airbyte`.** Its every answer carries `pageItems`. Open: whether a paged source should
    ever read such pages.
11. **The review.** Under RFC 0009 the pull request that moves this Draft to Review carries a
    recorded adversarial review and its dispositions. None has run.
12. **The last page's members.** Resolved: the joined value carries `last`, the last page's value
    read whole, the same JSON value as `values`'s last element (section 6). A rule tests the last
    page's flag at `/last` followed by the flag's pointer, with one clause whatever the page count,
    where it needed one clause per count before. `last` adds nothing beyond `values`, so it changes
    nothing a verifier establishes (section 9). `pages` is never 0, so `last` is always present.
    Decided before Review, because adding a member later would change what a rule reads.
13. **A skipped `research` source and `cites`.** §9.1 orders `cites` by `sources` "in a preparation
    with" a `research` source, and does not say whether a skipped one counts; no vector decides it.
    This amendment keys its own rule on the dialect (section 8), and leaves §9.1's rule as written
    in every format, since settling it changes the text of formats this amendment does not touch.
    Open: whether a later amendment keys the `research` rule on the dialect too.
