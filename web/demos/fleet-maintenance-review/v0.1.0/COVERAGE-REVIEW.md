# Coverage review

All 18 saved tests pass. Source projections are checked independently against each fixture. The suite includes normal outcomes, required missing evidence, incorrect identities/revisions/scopes, explicit refusals, exceptions, unknowns, invalid types and inclusive numeric boundaries.

The structural coverage report retains one advisory **conflict** gap. The two positive rules require the same true prerequisites but complementary ranges of the same metric. The hold rule requires at least one of those prerequisites to be false. They cannot simultaneously resolve to different outcomes for these typed facts. No artificial conflict case was added merely to make a coverage badge green. This is a reasoning review, not an exhaustive proof over all malformed inputs.

Missing evidence can coexist with reason `unknown`: the absent artifact also supplies the exception flag, so the runtime cannot rule out that exception. The expected reasons deliberately preserve both.
