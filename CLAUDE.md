# Working in this repository

This file is read by Codex as `AGENTS.md` and by Claude as `CLAUDE.md`; the two are the same text.
Edit `AGENTS.md` and run `scripts/sync-agent-docs.sh` to regenerate `CLAUDE.md`.

## Before you open a pull request

- Run `scripts/dev/check.sh` (or `jpdev check` where the kit is installed) once. It runs the
  checks listed in `dev.json` in order and prints one summary block.
- Paste that summary block in the pull request body, under a "Checks" heading.
- If a check fails: read its first lines in the block, fix the cause, re-run that one check with
  `--only NAME`, then run the whole list once more. Do not loop on the whole list.
- Start no CI watch. Push, report once, and stop; CI owns everything deterministic.

## Rules

- Write test vectors and fixtures by hand. Never record them "from a run" of the code under test.
- Keep machine-local paths and personal names out of tracked files, commit messages and pull
  request bodies. Refer to people by role or handle where a name is needed.
- Sign off every commit (`git commit -s`). Never force-push; never rewrite published history.
- End a process you started by its process id. Never use a pattern kill (`pkill`, `killall`).
- One pull request per issue or batch. State what changed and why in plain, factual wording.
- A change to a public surface (a schema, a contract, a command's output) says so in the pull
  request and changes its vectors and documentation in the same pull request.
- If a safeguard stops you (a permission prompt, a refused command, a failed gate), stop and say
  so in your report. Do not work around it.

## Reports

Your final report is short: the pull request and its head commit, what changed, the check
summary block, and anything you stopped on or chose not to do.

## This repository

- The checks are `dev.json`, run by `scripts/dev/check.sh`; the `repository-conformance` job in
  CI runs the same list, and branch protection requires that job name. `repository-tests` is
  declared with the `node` toolchain because the suite starts Node (the dialect verifier and the
  site checks).
- Install `requirements-dev.txt` (`scripts/dev/check.sh --setup`) before the tests, even if the
  suite appears to run without it: without the `format-nongpl` extras of `jsonschema` the `format`
  keyword is silently ignored and the suite checks less than it says it does.
- This is a specification repository and a research preview. A pull request that changes normative
  behavior updates prose, schema, examples and conformance cases together and includes a negative
  or adversarial case; material changes go through an RFC (`rfcs/0000-rfc-process.md`). Do not
  claim that conformance proves truth, authorization or safety.
- Do not put customer, personal, credential or production data in an example, a fixture or an issue.
