# Delegation statement cases

The conformance cases of [RFC 0030](../../rfcs/0030-agent-principals-and-delegated-authority.md)'s
amendment of 2026-11-22 for the delegation statement, steps 1 to 7 and the narrowing check of §3,
and for the scope binding: the build-order steps *ES256* and *The scope binding* of its *Acceptance
plan*; and its cases for the admission reads of §2a, tables 4 and 5. They are staged in no Core
corpus, as the witness and dialect vectors are, are not served by the site, and are normative for nothing while the
RFC is a Draft. Each case states its expected verdict.

| File | Cases | SHA-256 |
| --- | --- | --- |
| [`es256-statements.json`](es256-statements.json) | 55: table 1 (30) and table 2 (25) | `534e256df9babccc5d8bd9c4f17440b3036f5e85829a25e397cd5774a49887d6` |
| [`ed25519-statements.json`](ed25519-statements.json) | 39: the row `ed25519-unchanged` of table 1 | `b1bdfe50cbab49f6408395511c0f9fbee897193f6c58f63328a6d677b99c3bd9` |
| [`scope-binding.json`](scope-binding.json) | 20: table 3, as 9 statement cases, 10 request cases and the row `unbound-unchanged` | `04559c4a04d3f64f059beb47f54790382825b0eb9a5f6c13173762470b54a142` |
| [`scope-binding-es256.json`](scope-binding-es256.json) | 2: table 3's `bound-changed` and `bound-unbound-child` under the P-256 key | `d6c2a44f6d06b772d65526bbb590db3a95bc39998f38e4f05ab93f35afb30d2f` |
| [`admission-reads.json`](admission-reads.json) | 35: table 4 (22) and table 5 (13) | `a620f8e7280652a1c9402c4862ab3ebafa9b8286569a327fdbdd12492f5291e2` |

Each implementation holds each copy to the SHA-256 above, `ed25519-statements.json` included: the
reference gateway checks its `testdata/delegation/statements.json`, of which that file is a copy, by
that digest in a test, as it checks its copies of the others.

`es256-statements.json` was revised once after it was frozen: `link` was set on its two chained
negative cases, `es256-resigned-parent` and `child-parent-id-differs` (both at link `1`), so that
every negative case of more than one link names its link. Nothing else changed: no statement and
no signature. Before the revision its SHA-256 was
`5a687a254c35989951345cea7b7f7b5cdf3a2edc2cc1f02918ed2e3f7d900f8b`.

## How they were made

`es256-statements.json` and `scope-binding.json` were each made once, by a generator independent of
both implementations:
Python 3.8.20 with `cryptography` 44.0.0 for Ed25519 and ECDSA P-256 signing, and plain integer
arithmetic for the Ed25519 edge cases (a signature whose `S` is not below the group order, one that
verifies only under the cofactored equation, and the refused keys). The file is frozen: ES256
signatures are not reproducible, so a second run would make other bytes and other digests (gateway
ADR-0053's corpus rule). The generator is not part of this repository. `scope-binding.json` was
made by the same generator, extended with table 3, under the same keys: its ES256 signatures are
other bytes than any of `es256-statements.json`'s.

`scope-binding-es256.json` was made once, on 2026-11-24, by a second generator, Python 3.8.20 with
`cryptography` 44.0.0, independent of the gateway and sharing no code with `scope-binding.json`'s
generator either; it is not part of this repository. It holds the ES256 counterparts of
`scope-binding.json`'s Ed25519 negative cases `bound-changed` (a child bound to another scope
identifier) and `bound-unbound-child` (an unbound child of a bound link), as `es256-bound-changed`
and `es256-bound-unbound-child`: the same members, host `desk`, pins and scope identifiers, under the
P-256 key of `01` with `alg: "ES256"`, its signatures `r||s` at low S. Both expect `widened` at link
`1`. Before it was frozen, the generator made every Ed25519 signature and parent digest of
`scope-binding.json` again, byte for byte (Ed25519 is deterministic), and verified its ES256 links,
so its `canon`, signing input and digest are the ones that file was made under.
`scope-binding.json` is unchanged.

Canonical bytes follow `canon` as the RFC's *Common forms* states it. Every link's signing input and
digest were checked, before the file was frozen, against the reference gateway's own `canon`.

`ed25519-statements.json` is a byte-for-byte copy of the reference gateway's
`testdata/delegation/statements.json` at commit `12b0f43de0aa4b9e43e3fadca3cb9697e50f1087`: the 39
Ed25519 cases that both implementations pass today, which must pass unchanged.

## The keys

Synthetic keys only; no host holds them.

| Key | Secret | Public key | Key identifier | Pinned |
| --- | --- | --- | --- | --- |
| Ed25519 | the seed `judgment-pack-delegation-host-01` (32 ASCII bytes), the gateway's existing synthetic seed | `00028d283e279178a6ce561e45f1b89f2a6ac45690fbb5ac48313ad61ab04584` | `5c57cc9dc13bda735be87dc1de5db9a4` | yes |
| P-256 | the scalar of 32 bytes of `01`, gateway §1.5's | `026ff03b949241ce1dadd43519e6960e0a85b41a69a05c328103aa2bce1594ca16` | `dbdb99c64b3d511f72c88fb6c054da73` | yes |
| P-256, y odd | the scalar of 32 bytes of `05`, the first such byte whose point starts `03` | `0307810ea974cea5773e63b897f37e3be9a09e7a5fe9b971a44d1065ac2a3a9311` | `dfc9e0f60b06bc6d00c86b3ee4f930a4` | yes |
| P-256, unpinned | the scalar of 32 bytes of `06` | `02b0514c4c13540f2397f54719f3332e7ef38e42ad9dc08b71e660ce16b9e88d09` | `476fdf678a60f12a077450af5936ae39` | no |

## The form of a case

`keys` holds the pins of the issuing host `desk`, each entry in the form an engine configuration
writes it: a string of 64 lowercase hexadecimal characters for an Ed25519 key, and
`{"alg": "ES256", "key": <66 lowercase hexadecimal characters>}` for a P-256 key. Each case holds:

- `name`, as the RFC's tables name it; `table`, `1` or `2`; `kind`, `P`, `N` or `B`;
- `chain`, the array of statements, root first;
- `expect`, the first refusal of steps 1 to 7 (`malformed`, `unsupported-version`, `key-mismatch`,
  `signature-mismatch`, `chain-broken` or `widened`), or `ok`;
- `link`, where the RFC names the link the refusal is at (the index, root `0`);
- `keys`, where the case pins other keys than the file's;
- `pin` and `pinExpect: "refused"`, for a case whose key must be refused when it is pinned: the pin
  is refused, and the chain, verified under the file's keys, gets `expect`;
- `note`, where the case's construction needs a word.

Every negative case of more than one link names its `link`.

The ES256 signatures are `r||s` at low S, except where a case makes another. `es256-der` holds the
signature as a key service may answer it, DER of `(r, n − s)` at 72 bytes, since a DER low-S
signature is at most 71 bytes long.

Only `es256-high-s` exercises the low-S rule: its signature verifies under plain ECDSA, so a
verifier that omits the rule admits it, and only the rule refuses it. `es256-s-half-plus-one` and
the cases of an `r` or `s` of zero or `n` hold signatures that do not verify at all, and are refused
`signature-mismatch` with the rule or without it.

## The scope-binding cases

`scope-binding.json` holds table 3 under the scope identifiers `scope-a` and `scope-b`, which are
synthetic. Its `keys` pin the Ed25519 key and the P-256 key of `01`.

- `statements` are as above: `name`, `kind`, `chain`, `expect`, and `link` on every negative case.
- `unbound` is the row `unbound-unchanged`: it names table 1 of `es256-statements.json`, whose chains
  hold no `scopeId` and keep their verdicts.
- `requests` each hold a valid `chain` and a `request`: `routes`, the routes the case is answered on;
  `scope`, the scope identifier the request names, `null` for none; and `sourceScope`, the scope
  identifier of the source it is for, `null` for none. `hostScopeIds` are the scope identifiers the
  enforcing host's configuration lets the issuing host's delegations be bound to (open question 27).
  `expect` is `admitted`; `scope-id-mismatch`, the request check's refusal; `wrong-scope`, the
  gateway's refusal of a source of another scope identifier; or `withheld`, the result of a call
  the library withholds. `hostRead` and `counted` say whether the issuing host is read and the call
  counted; `at`, where the refusal is made at binding as well as at a call. `appliesTo` names the
  implementations a case applies to: the `library-` cases are the agent library's alone, and
  `request-bound-source-of-other` is the gateway's alone.

`scope-binding-es256.json` holds `statements` alone, in the form above, with the same `keys` and
`scopeIds`; each case's `note` names the Ed25519 case it counterparts.

## The read cases

`admission-reads.json` is hand-written and needs no signer: a read is not signed, and its bodies
are `canon` bytes, which are reproducible. It holds one case per name of tables 4 and 5, a row
naming several cases being several, with `read-v2-binding-step-12` (a step-12 refusal answering a
binding read). It is frozen once both implementations pin it; a change is a new digest. Each case
holds:

- `name`, `table` (`4` or `5`) and `kind`, as the RFC's tables give them;
- `applies`, the side the case is for, `issuing-host`, `sender` or both, each with what that side
  does. A body no conforming sender emits says `"sender": "never emits; refuses on read-malformed"`
  (or the answer it names): a sender passes it by never sending such a body and by refusing under
  that name when it is so answered;
- `senders`, the implementations whose sender part it is, `gateway`, `library` or both; the
  `skills` and skill-load cases are the library's;
- `readVersion`, the sender's configured version, and `hostReads`, the versions the host double
  reads;
- `inputs`: the chain, by the name of a case in `ed25519-statements.json`, whose link digests the
  body's `chain` holds; `host`, `at` and `audience`; the call (`null` for a binding read), the
  standing read's principal, or the load; the approved `version` and the loaded `skills` as the
  sender holds them, unordered where a case orders them; and the host double's `policy` where a
  case needs one;
- `body` and `answer`, the exact bytes as strings, `null` where none is sent or none comes back;
  `skill-load-resume` holds one of each per read, in order;
- `expect`: `verdict`, the RFC's expected verdict; `sender`, what the sender reports; `counted`;
  `reads`, how many reads the sender makes, so that nothing is resent; and for table 5 `loaded`.
