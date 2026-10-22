# The checkpoint witness statement

## Status

This document is a companion document of the Judgment Pack specification. It is normative for one
conformance class, the *witness-statement reader* (§11), and for nothing else
([Core §1.1](judgment-pack-core.md#11-normative-artifacts-and-precedence)). It changes nothing in
Judgment Pack Core `0.2.0-draft`, its schema, its four conformance classes, or either of its
corpora.

Its 54 vectors, under
[`conformance/witness/`](https://github.com/Judgment-Pack/judgment-pack-spec/tree/main/conformance/witness),
are **staged** until the next `specVersion` opens: they are in no corpus, no claim may cite them,
the site does not serve them, and no release bundle carries them. When that version opens they move
into a corpus, normative for this class and for nothing else. Until a specification version
publishes them, no witness-statement reader conformance claim is available: §11 holds a reader to
the vectors published with the version its claim names, and no version publishes these.

It specifies version `1` of the witness statement (`witnessVersion` `"1"`, §3). It is published
beside the released Core `0.2.0-draft` and carries no `specVersion` of its own; whether its vectors
take a `suiteVersion` of their own is open in its design record (Unresolved 1). Like Core, it is
at draft maturity.

Its design record is [RFC 0017](../rfcs/0017-checkpoint-witness-statement.md), accepted on
2026-10-12, which is informative. Its text, §§1–11 below, is that RFC's Specification section. It
restates the checkpoint witness statement as the reference gateway released it in `v0.11.0`,
commit `13349cafe33bb7618567e47ce7f6e1a4224231b0`:
[`SPEC.md` §8](https://github.com/Judgment-Pack/judgment-pack-gateway/blob/v0.11.0/SPEC.md#8-the-checkpoint-witness),
its canonical form in §1.1 and its key identifier in §1.2, and
[ADR-0013](https://github.com/Judgment-Pack/judgment-pack-gateway/blob/v0.11.0/docs/adr/0013-checkpoint-witness.md).
"Gateway §n" in this document means a section of that `SPEC.md` at that commit.

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHOULD**, **SHOULD NOT** and **MAY** are to
be interpreted as described by BCP 14 when, and only when, they appear in all capitals.

## 1. Terms and the canonical form

A **trail** is a decision trail: a sequence of records an operator keeps, each one line of bytes.
Its format, how its records chain, and how a checkpoint is printed from it are the reference
runtime's (runtime ADR-0047), not this document's. This document needs three things of a trail: its
identity, 32 lowercase hexadecimal characters; a record's position in it, its **sequence**, counted
from 1; and the SHA-256 of a record line's exact bytes, without its newline.

A **witness** is a party, other than a trail's operator, that signs statements (§3) over the
trail's checkpoints (§2) and serves them. A **reader** reads a set of statements (§7). Hexadecimal
is lowercase throughout. A **digest** is the string `sha256:` followed by 64 hexadecimal characters.
A **key** is the 32-byte encoding of an Ed25519 public key (RFC 8032), and its **key identifier** is
the first 32 hexadecimal characters of the SHA-256 of those 32 bytes.

**The canonical form** of a JSON value — the bytes a signature covers and two statements are
compared by — is defined as follows.

- **Domain.** Objects, arrays, strings, integers, `true`, `false` and `null`. Numbers are integers
  only, within ±(2⁵³−1); a number written with a fraction or an exponent is outside the domain even
  when its value is an integer (`1.0`, `1e2`), and `-0` is inside it, with the canonical form `0`. A
  string is inside the domain only when it is valid UTF-8, so a lone surrogate is outside it. An
  object that gives one member name twice is outside the domain.
- **Output.** Object members are ordered by the Unicode code points of their names; array elements
  keep their order; there is no whitespace; strings are raw UTF-8, with no character outside ASCII
  escaped and `<`, `>`, `&` and `/` not escaped. The escapes are `\"`, `\\`, `\b`, `\f`, `\n`, `\r`
  and `\t`; every other control character below U+0020 is `\u00` followed by two lowercase
  hexadecimal digits; U+007F, U+2028 and U+2029 are written raw.

This is the gateway's canonical form (gateway §1.1). It orders member names by code point where
RFC 8785 orders them by UTF-16 code unit; the two differ only on names outside the Basic
Multilingual Plane, and no name in this document is one. Every value of a statement that has the
form of §3 is a string of ASCII characters none of which is escaped, an integer below 2⁵³, or
`null`, so a statement's canonical form is also its RFC 8785 serialization, and a reader MAY build
it with either.

## 2. The witnessed checkpoint

A **checkpoint** is an object of exactly four members, each given once:

| Member | Form |
| --- | --- |
| `checkpointVersion` | the string `"1"` |
| `trail` | 32 lowercase hexadecimal characters: the trail's identity |
| `sequence` | an integer from 1 to 2⁵³−2: the record's line number in the trail |
| `recordDigest` | a digest: the SHA-256 of the record line's exact bytes, without its newline |

Its canonical form (§1) is the checkpoint line the reference runtime prints, without its newline,
byte for byte: the member names are ASCII and already in code-point order, and the values are
hexadecimal strings, a fixed string and an integer below 2⁵³. The bytes inside a statement's
signing input are therefore the bytes a holder's checkpoint file holds, and their SHA-256 is what a
time stamp of the checkpoint imprints. A witness MUST accept a submitted checkpoint line only in
that form, and MUST NOT re-encode one.

## 3. The statement

A **witness statement** is an object with exactly the members below. Every member is REQUIRED, and
the set is closed: a statement with a member not listed here is malformed, because a new member is
a new `witnessVersion`, and a reader that does not know a version then refuses it rather than
skipping it.

| Member | Form | Meaning |
| --- | --- | --- |
| `witnessVersion` | the string `"1"` | this format |
| `kind` | `"checkpoint"`, `"conflict"` or `"retirement"` | §6 |
| `checkpoint` | the object of §2 | for `"checkpoint"`, the checkpoint witnessed; for `"conflict"`, a checkpoint offered and refused; for `"retirement"`, the trail's latest witnessed checkpoint, repeated |
| `index` | an integer from 0 to 2⁵³−2 | this statement's place in the witness's chain for `checkpoint.trail` |
| `prevSignature` | `null`, or 128 lowercase hexadecimal characters | the `signature` of the statement at `index` − 1 for the same trail; `null` at index 0 (§6) |
| `witnessedAt` | `YYYY-MM-DDThh:mm:ssZ`, a digit where each letter but `T` and `Z` stands: UTC, whole seconds | the witness's clock when it signed |
| `keyId` | a key identifier (§1) | the witness's key |
| `signature` | 128 lowercase hexadecimal characters, the 64 bytes of an Ed25519 signature | §4 |

A statement is read by its JSON value. Whitespace, the order of members and the escapes in a string
are its spelling, not the statement. A member name given twice, a string that is not valid UTF-8,
or a lone surrogate makes it malformed. Each form above is held on the value read: an integer is
spelled in digits alone, with no sign, fraction or exponent — `-0`, `1.0` and `1e0` are not
integers here — and a string is held to its form as its escapes decode. Two statements with the
same canonical bytes are one statement.

`witnessedAt` is held to its form and to nothing else: a reader compares it with no clock and with
no other statement's. A witness MUST NOT state a time earlier than the previous statement's for the
trail — it takes the later of its clock and that time — and that is the witness's rule, which a
reader does not check.

A statement at index 7 and sequence 120, its hexadecimal elided, as a witness serves it:

```
{"checkpoint":{"checkpointVersion":"1","recordDigest":"sha256:…","sequence":120,"trail":"…"},"index":7,"keyId":"…","kind":"checkpoint","prevSignature":"…","signature":"…","witnessVersion":"1","witnessedAt":"2026-10-04T12:00:00Z"}
```

With its hexadecimal in full it is 608 bytes. A witness MUST serve every statement as one line, its
canonical form, ended by a newline (`0x0A`).

## 4. What the signature covers

`signature` is an Ed25519 signature, under the witness's key, over the ASCII bytes
`judgment-pack-gateway/witness/1:` followed by the canonical form of the statement with **its
top-level `signature` member removed and every other member retained**, the nested `checkpoint`
included. Appending anything anywhere therefore invalidates the signature. Built from the values
read, each integer in decimal digits, the signed bytes are exactly:

```
judgment-pack-gateway/witness/1:{"checkpoint":{"checkpointVersion":"1","recordDigest":"<recordDigest>","sequence":<sequence>,"trail":"<trail>"},"index":<index>,"keyId":"<keyId>","kind":"<kind>","prevSignature":<null, or "<prevSignature>">,"witnessVersion":"1","witnessedAt":"<witnessedAt>"}
```

The prefix is neither the gateway receipt's nor its seal's, so none of the three can be replayed as
another. It names the gateway because the gateway defined it; every statement that exists was
signed over it, and this document keeps it unchanged.

`keyId` is the key identifier (§1) of the key that signs. Gateway §8.3 adds a rule on the producer
that this document does not carry: a gateway witness signs under the gateway's own signing seed,
the seed that signs its receipts and seals, so a statement's `keyId` is the gateway's own, and a
party that wants the witness's role apart from its receipts runs a second gateway with a seed of
its own. That rule binds a gateway as a producer, and stays the gateway's. This document leaves the
choice of key to the witness because a reader conformance class should not depend on which key a
producer uses: a reader verifies under the keys it was given (§5), by one equation, and cannot tell
from a statement what else its key signs. A witness that signs with a key of its own therefore
conforms to this document and not to gateway §8.3, and every reader reads its statements alike.

## 5. The key rule and the equation

A reader MUST NOT take a witness key from a statement. It is given the keys it trusts, out of band,
and it MUST hold each to the rule below before it reads anything signed. 32 bytes are a key a reader
may trust exactly when they are the canonical encoding (RFC 8032 §5.1.2) of a point of the curve
whose order does not divide 8. The encoding is read as written, before anything reduces it: `y` is
its low 255 bits, little-endian, and its top bit is the sign of `x`. A key is refused when, taken in
this order:

1. **it is not canonical** (`key-not-canonical`): `y` is p = 2²⁵⁵ − 19 or more, or `x` is 0 (`y`
   is 1 or p − 1) and the sign bit is set. A lenient decoder reads such an encoding as another
   key: `y` = p as `y` = 0, for one;
2. **it is of small order** (`key-small-order`): it is one of the eight points whose order divides
   8, by their canonical encodings — every other encoding of them is refused by 1:

   ```
   0100000000000000000000000000000000000000000000000000000000000000
   ecffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f
   0000000000000000000000000000000000000000000000000000000000000000
   0000000000000000000000000000000000000000000000000000000000000080
   26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc05
   26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc85
   c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac037a
   c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac03fa
   ```

   Under such a key a signature can be made without a private key — for most messages, `R` a point
   of small order and `S` zero verify — and the all-zero key, a plausible placeholder, is one;
3. **it is no point** (`key-not-on-curve`): (`y`² − 1) / (d·`y`² + 1) has no square root modulo p,
   so nothing verifies under it.

A key of mixed order — a point of prime order plus one of small order — is not refused, since its
order does not divide 8, and no key derived from a seed is refused.

A signature is 64 bytes: `R`, the first 32, and `S`, the last 32 read as a little-endian integer.
It verifies under a key's 32 bytes `A` over the signed bytes `M` (§4) exactly when `S` is below
L = 2²⁵² + 27742317777372353535851937790883648493 and the canonical encoding of [`S`]B − [h]A is
`R`, byte for byte, B being the base point and h the SHA-512 of `R` ‖ `A` ‖ `M` read as a
little-endian integer and reduced modulo L. That is RFC 8032's check without the cofactor and with
a canonical scalar. A reader MUST NOT use the cofactored check RFC 8032 §5.1.7 also allows,
[8][`S`]B = [8]`R` + [8][h]A, which accepts more: an `R` with a part of small order, and, under a key
of mixed order, a signature that holds only up to that part. `R` is not otherwise decoded: an
encoding of it that is not canonical never verifies, and one of a point of small order verifies
when the equation holds.

## 6. The chain

A witness keeps one chain of statements per trail, and MUST keep it as follows.

- `index` runs from 0 with no gap, and each statement's `prevSignature` is the `signature` of the
  statement before it, `null` at index 0. The last statement therefore commits to every one before
  it, and a witness that drops, reorders or alters a statement it served breaks the chain for
  anyone who holds a later one.
- The sequences of its `checkpoint` statements strictly increase. Its **latest witnessed
  checkpoint** is its last `checkpoint` statement, and coverage is always stated by that one: a
  `conflict` at sequence 100 after a checkpoint at 200 does not move coverage back to 100.
- A **`conflict`** statement records that a submitter the witness allowed for the trail offered
  another `recordDigest` for a sequence at which the witness holds a `checkpoint` statement. The
  first such offer is the evidence, and there is at most one per sequence. Since a witness holds
  only sequences it signed, a conflict's sequence is at or below the latest `checkpoint`
  statement's before it, and that is what a reader checks of it. That the sequence was held, and
  that no sequence has two conflicts, are the witness's rules, which a reader does not check.
- A **`retirement`** statement is the last of its chain: the witness accepts nothing more for the
  trail, and keeps and serves the chain as before. Its `checkpoint` repeats the latest witnessed
  checkpoint, all four members, so it names the trail and pins where the chain ended; a chain with
  no `checkpoint` statement has nothing to retire.
- The witness's **head** for a trail is the chain's last statement, of any kind.

A witness cannot check that a checkpoint extends the one before it: that needs the records, which
it never sees. A rewrite of a trail from sequence k on is caught by holding the trail to an
**earlier** statement whose sequence is k or above, which the rewritten trail no longer matches —
even when a later checkpoint of the rewritten trail was signed. Whoever presents a chain can leave
that statement out, so a chain is read from its first statement and never late (§7), and the head,
fetched from the witness, says how far the chain reaches. The witness serves the latest statement
it holds as the end of the chain, not in place of it.

## 7. Reading a chain

A reading takes: the identity of the trail being verified; the witness keys the reader trusts, in
an order; the statements supplied, in files of statement lines; and, optionally, a **head** the
reader fetched from the witness, in a file of its own. A file's lines are its bytes up to each
`0x0A`, the piece after the last one included. A line that is empty, or holds only spaces, tabs and
carriage returns, is passed over; every other line is one statement as served (§3), its surrounding
JSON whitespace allowed. A head file holds exactly one statement line.

Before any statement is read the reading is refused — no reading at all, never a reading of part —
by the first of these: more keys than §8 allows (`keys-over-bound`); a key the key rule refuses,
the keys taken in their order, with that key's reason (§5); the files over §8's bound on bytes
(`bytes-over-bound`); and the files over its bound on statements (`statements-over-bound`).
Otherwise:

1. **Each statement.** The statements of every file and the head are one set, whatever files they
   came in and in whatever order. Two with the same canonical bytes are one, and each statement is
   checked once, against, in this order: its form (§3), or **`witness-malformed`** — a head file of
   other than one statement line too; its signature, under the key its `keyId` names among those
   supplied, by §5's equation over §4's bytes, or **`witness-signature-invalid`**, a `keyId` that
   names no key supplied included; and its trail, which MUST be the trail being verified, or
   **`witness-trail-mismatch`**. A statement takes the first of these findings and no other. A
   statement that fails is never passed over, whatever it claims: it fails the reading.
2. **Equivocation.** Two statements that passed step 1, are of one index and differ are
   **`witness-equivocation`**: the witness signed two chains.
3. **The chain.** A set in which steps 1 and 2 found anything is not walked: the findings are those
   steps', and a hole a failed statement leaves is not reported. Otherwise the **chain** is the
   set, less a head whose index is more than one past the highest index of the other statements of
   the set, the highest index of no statement being taken as −1, so that a head alone at index 0 is
   a chain. Taken in index order, it MUST begin at index 0 with `prevSignature` `null` and hold
   every index from there to its highest, each `prevSignature` after the first the `signature` of
   the statement before; each `checkpoint` statement's sequence MUST exceed the latest `checkpoint`
   statement's before it; each `conflict` statement MUST have a `checkpoint` statement before it
   and a sequence at or below the latest one's; and a `retirement` statement MUST have a
   `checkpoint` statement before it, repeat the latest one's checkpoint, all four members, and be
   the chain's last. Otherwise **`witness-chain-broken`**. A set that begins late is never read
   from where it begins, and a set of no statement does not begin at index 0.
4. **The head.** A head left out of the chain in step 3 is **`witness-head-unreached`**: the
   statements supplied do not reach it. A head at an index the chain holds is the chain's statement
   at that index, by its signature, since step 2 found no other; a head one index past every other
   statement was walked in step 3 as the chain's last. The chain may run past the head: statements
   the witness signed after the reader's fetch, supplied from elsewhere, are checked like the rest.

A reading with any finding is credited nothing. A reading with none is **current** when a head was
supplied, as of the reader's fetch of it — a signature does not say when it was fetched — and
**historical** when none was: it ends at the highest statement supplied and says nothing of any
statement after it. It reports what §9 lists.

## 8. Bounds

One reading takes at most **16** keys; statement files and a head file of at most **67108864
bytes** (64 MiB) together; and at most **110000** statements, counted as the lines step 1 of §7
would read — every line of every file, the head file's included, that is not passed over — before
two copies of one statement are one. Over any of them the reading is refused before any statement
is checked (§7), and MUST NOT be truncated. The bytes are bounded first, by the files' sizes,
before any file is read. The statements are then counted as the files are split into lines, the
statements files in their order and the head file last, and the reading is refused at the first
line past the bound, keeping and reading none of the lines after it: a file of many short lines
costs a reader no more than 110000 statements do. Each statement costs one Ed25519 verification,
under the one key its `keyId` names, so the work of a reading is bounded by its statement count.

## 9. Refusals, findings and the report

Refusals and findings are named as the specification names evaluation error classes (Core §8.4):
lowercase words joined by hyphens. The names are the ones the vectors use.

| Name | Kind | When (section) |
| --- | --- | --- |
| `keys-over-bound` | refusal | more than 16 keys (§8) |
| `key-not-canonical` | refusal | a key that is not a canonical encoding (§5, 1) |
| `key-small-order` | refusal | a key of small order (§5, 2) |
| `key-not-on-curve` | refusal | a key that is no point (§5, 3) |
| `bytes-over-bound` | refusal | the files over 67108864 bytes together (§8) |
| `statements-over-bound` | refusal | more than 110000 statement lines (§8) |
| `witness-malformed` | finding | a statement not of §3's form, or a head file of other than one statement line (§7, 1) |
| `witness-signature-invalid` | finding | a signature that does not verify under the key its `keyId` names, or a `keyId` that names no key supplied (§7, 1) |
| `witness-trail-mismatch` | finding | a statement of another trail (§7, 1) |
| `witness-equivocation` | finding | two statements, each verifying, of one index that differ (§7, 2) |
| `witness-chain-broken` | finding | a set that breaks the chain rule (§7, 3) |
| `witness-head-unreached` | finding | a head more than one index past the statements supplied (§7, 4) |

A reader MUST report a refusal by its name, and a reading's findings by their names. Findings are a
set: how many times, and in what order, a reader reports one is not normative. A reading with no
finding MUST report: whether it is current or historical; the head's index, when a head was
supplied; the chain's highest index; the latest witnessed checkpoint's index, sequence and
`witnessedAt`; the sequence of each `conflict` statement, in index order; and whether the chain is
retired. The vectors carry these as JSON (see [`conformance/witness/`](https://github.com/Judgment-Pack/judgment-pack-spec/tree/main/conformance/witness)); that form is the vectors' carrier, not
an output format this document requires.

**The sentences.** A reader that states in words what a reading establishes MUST state no more
than §10 allows, and SHOULD state it in these sentences, with N, T and K filled in. They are the
fixed sentences of gateway ADR-0013 §6, which the reference runtime states verbatim. N is the
highest credited coverage, as ADR-0013 §6 states it: the highest sequence of a `checkpoint`
statement of a reading with no finding (§7) whose checkpoint the copy of the trail matches, with no
failed check of the trail at or before that sequence; T is that statement's `witnessedAt`. Any lower
sequence would make the second sentence below false. The first two sentences apply only when such a
statement exists; when none does, nothing is credited and neither is stated.

- Establishes, for a reader that holds a copy of the trail: "Lines 1 to N are the lines that
  existed when a witness under a key supplied signed its statement for checkpoint N, which it
  states it did at T, if that witness is independent of the trail's operator."
- Does not establish, for the same reader and the same N: "Lines after N are covered by no
  statement of a witness under a key supplied."
- Does not establish, for a current reading whose head is at index K: "That the witness's head for
  this trail is still index K: the head supplied is as current as the reader's fetch of it, and a
  signature does not say when it was fetched."
- Does not establish, for a historical reading whose highest index is K: "That the witness held no
  statement for this trail after index K: no head fetched from the witness was supplied, so the
  chain was read only as far as it was supplied."
- Does not establish, for every reading:
  - "Anything against a witness that is not independent of the operator: one that colludes can sign
    what it is asked, at any time it states, and a second history for another audience; a key
    supplied is trusted because the verifier chose it."
  - "Who submitted any checkpoint: a statement does not name its submitter, and the witness cannot
    tell the trail's operator from a holder of the operator's credential."
  - "When any record was made: the time a witness states is its own clock's, for when it held the
    checkpoint."

This document does not specify the eighth sentence of ADR-0013 §6, which is for a reading
continued from one a reader saved (§7 reads a chain whole). Nor does it specify the runtime's
further findings — `witness-head-behind`, for a head below a saved reading's last statement, and
`countersigned-coverage-missing`, for a requirement on coverage — or the four with which it holds
a statement's checkpoint against a trail copy (`checkpoint-beyond-trail`, `checkpoint-not-chained`,
`checkpoint-trail-mismatch`, `checkpoint-record-mismatch`). They are the runtime's, as are the two
sentences of its own that it adds: one for a reading that credits nothing, one for its conflict
statements.

## 10. What a statement establishes, and what it does not

| | Establishes | Does not establish |
| --- | --- | --- |
| A `checkpoint` statement, verified under a key the verifier trusts | the key's holder was given this checkpoint and signed it as statement `index` of its chain for the trail, and states that it did so at `witnessedAt` | that the checkpoint names a real record; that it extends the one before; that the submitter was the trail's operator; that `witnessedAt` is true; anything against a witness that colludes, or whose key is stolen |
| The same, held against a trail copy | lines 1 to its sequence are the lines that existed when the witness signed, if the witness is independent of the operator | anything after that sequence; that this is the project's only trail; that the records are true, or that every decision was recorded |
| A chain read from index 0, every statement present and linked, up to the signature of a head the reader fetched from the witness | the reader holds every statement of the chain that head commits to, as the witness signed them: none is missing, out of order or altered, and none starts late | that the head is still the witness's head after the fetch; that the witness signed no second chain for the trail, for another audience; that it will serve these tomorrow |
| The same chain read only as far as it was supplied, with no head | the same, up to the highest statement supplied | anything about statements after it: the reading is historical |
| A `conflict` statement | a submitter the witness allowed for the trail offered another record for a sequence the witness held | which of the two is the trail's; who that submitter was, beyond the witness's own registration |
| A `retirement` statement | the witness accepts no more statements for the trail, and the chain ends there | why; whether the trail's operator went on under another trail |

A reading, and a report built on one, MUST NOT be described as establishing anything the
right-hand column names.

Against the trail's operator, a chain read from its first statement and held against a trail copy
establishes that no record up to the latest checkpoint statement's sequence was edited, removed,
inserted or moved since the witness signed the first statement covering it; a copy cut short below
that sequence fails; and a rewrite from any sequence at or below an earlier statement's fails at
that statement. It does not establish:

- anything against a witness that colludes, or whose key is stolen: it can sign any checkpoint at
  any time it states, and a second chain for a trail for another audience. Two statements of one
  trail and one index that differ, both verifying, prove that it signed two chains; a statement
  someone kept that the chain served lacks shows a second chain to whoever holds both. One witness
  gives no protection against collusion;
- who submitted: the witness cannot tell the trail's operator from a holder of the operator's
  credential, and a verifier cannot either. A credential stolen can have a checkpoint signed at a
  sequence no honest checkpoint will exceed, and that statement stays in the chain: the trail is
  then retired, not repaired;
- anything about an operator who stops submitting, about records after the latest checkpoint
  statement, or about a trail rewritten before its first submission;
- that the trail is the project's only one: a verifier must hold the trail identities it expects;
- that the witness keeps what it signed: a witness that loses or withholds its latest statements
  serves an older head that is internally consistent, and for a trail it holds nothing for it
  answers as for one never submitted. A statement of a higher index than the head served shows that
  the served view is not the whole one; it does not show whether the witness forgot or withholds;
- when anything happened: `witnessedAt` is the witness's clock, an upper bound on when it held the
  checkpoint as it states it, under no certificate policy, and it says nothing of when a record was
  made.

What makes a party a witness is who holds its key, not its software. A witness whose key the
trail's operator can use is no witness against that operator, and nothing in a statement can show
independence: the witness cannot know who runs it. A verifier decides which witness keys it trusts,
as it decides which time-stamping roots it trusts.

## 11. The witness-statement reader

An implementation is a *conforming witness-statement reader* when, for every reading it admits, it
gives the refusal, the findings, or the reading §§5–9 define, and when it gives every vector's
expected answer in the witness vectors published with the specification version it names. The
class is independent of Core's four classes: none implies it, and it implies none. It says nothing
about a witness's service, and a conforming witness need not be a conforming reader. A claim of
this class MUST NOT be described as establishing anything §10 says a statement does not establish.
