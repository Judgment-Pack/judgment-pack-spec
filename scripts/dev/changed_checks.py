#!/usr/bin/env python3
# from judgment-pack-devkit v0.10.0 (lib/changed_checks.py)
"""changed_checks.py --root ROOT --manifest MANIFEST [--base BASE] [--label TEXT]

Selects the check-list steps that the changed paths of a clone can affect, for
`jpdev check --changed [BASE]` and `scripts/dev/check.sh --changed [BASE]`. A repository vendors
this file as scripts/dev/changed_checks.py beside scripts/dev/check.sh. The changed paths are those that differ from the merge base of
BASE and HEAD in HEAD, in the index or in the working tree (deletions, both sides of a rename, and
submodules whatever their ignore setting), plus untracked files that are not ignored. BASE
defaults to the default branch: origin/HEAD, else origin/main, else origin/master. Only what git
reports is seen: an edit hidden by assume-unchanged or skip-worktree, an ignored file and a path
outside the clone are not.

The mapping is the `changed` member of jpdev.json at the root: rules of path globs and the check
names they select. A glob is matched against the whole repository-relative path; `*` and
`?` stay within one path segment and a `**` segment matches any number of segments. The whole
list runs when a changed path matches no rule, when a selection input changed (the mapping file,
the manifest, scripts/dev/check.sh, scripts/dev/changed_checks.py), when nothing changed, or when
there is no mapping. An unmapped untracked path is named as such: a path a workflow creates
inside the clone defeats the selection on every run and belongs outside the clone or in .gitignore.

The first line of the output is the selection, `whole` or `only NAME,NAME`; the lines after it
are the report the runner prints, headed and refused with --label (default `jpdev check
--changed`). Exit 0, or 2 with one line naming the refusal. Standard library only.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

CONFIG = 'jpdev.json'
# Every diff names paths from the top, counts both sides of a rename, runs no external diff, and
# reports a submodule whatever its ignore setting in .gitmodules or the git configuration.
DIFF = ('diff', '--name-only', '-z', '--no-renames', '--no-relative', '--no-ext-diff', '--ignore-submodules=none')
# `generators` is read by lib/generated_docs.py and `duplication` by lib/duplication.py; this reads `changed`.
MEMBERS = {'version', 'generators', 'changed', 'duplication'}
RULE_MEMBERS = {'paths', 'checks'}
UNSUPPORTED = '\\[]{}'
SHOWN = 20
UNMAPPED = 'unmapped path %s: whole list'
UNTRACKED = ('untracked path %s is not mapped; a workflow-created path belongs outside the clone or in '
             '.gitignore: whole list')


class Refused(Exception):
    pass


def glob_regex(glob):
    """Compile a repository-relative path glob: * and ? within a segment, ** as a whole segment."""
    if not isinstance(glob, str) or not glob:
        raise Refused('a glob must be a non-empty string')
    bad = [c for c in UNSUPPORTED if c in glob]
    if bad:
        raise Refused('glob %r: %s is not supported (only *, ? and a ** segment are)' % (glob, ' '.join(bad)))
    if glob.startswith('/'):
        raise Refused('glob %r: must be relative to the repository root' % glob)
    parts = glob.split('/')
    out = []
    for index, part in enumerate(parts):
        last = index == len(parts) - 1
        if part in ('', '.', '..'):
            raise Refused('glob %r: has an empty, . or .. segment' % glob)
        if part == '**':
            out.append('.*' if last else '(?:[^/]+/)*')
            continue
        if '**' in part:
            raise Refused('glob %r: ** must be a whole segment' % glob)
        segment = ''.join('[^/]*' if c == '*' else '[^/]' if c == '?' else re.escape(c) for c in part)
        out.append(segment if last else segment + '/')
    return re.compile(''.join(out), re.DOTALL)


def step_names(manifest):
    """The names check.sh runs, in its order: the checks, then parity when the manifest has one."""
    try:
        with open(manifest, encoding='utf-8') as handle:
            value = json.load(handle)
    except (OSError, ValueError) as error:
        raise Refused('cannot read the manifest %s: %s' % (manifest, error))
    names = [step.get('name') for step in value.get('checks', []) if isinstance(step, dict)]
    if isinstance(value.get('parity'), dict):
        names.append('parity')
    return [name for name in names if isinstance(name, str)]


def load_rules(root, steps, manifest_label, config=CONFIG):
    """Return (rules, None), or (None, why the whole list runs) when there is no mapping."""
    path = root / config
    if not path.is_file():
        return None, 'no %s' % config
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as error:
        raise Refused('%s: not readable JSON: %s' % (config, error))
    if not isinstance(value, dict):
        raise Refused('%s: not a JSON object' % config)
    unknown = sorted(set(value) - MEMBERS)
    if unknown:
        raise Refused('%s: unknown member %s' % (config, ', '.join(repr(k) for k in unknown)))
    if type(value.get('version')) is not int or value['version'] != 1:
        raise Refused('%s: version must be 1' % config)
    if 'changed' not in value:
        return None, 'no change mapping in %s' % config
    rules = value['changed']
    if not isinstance(rules, list) or not rules:
        raise Refused('%s changed: must be a non-empty array of rules' % config)
    compiled = []
    for index, rule in enumerate(rules):
        where = '%s changed[%d]' % (config, index)
        if not isinstance(rule, dict) or set(rule) != RULE_MEMBERS:
            raise Refused('%s: a rule has exactly the members paths and checks' % where)
        for key in ('paths', 'checks'):
            items = rule[key]
            if not isinstance(items, list) or not items or not all(isinstance(i, str) and i for i in items):
                raise Refused('%s.%s: must be a non-empty array of non-empty strings' % (where, key))
            if len(set(items)) != len(items):
                raise Refused('%s.%s: names a value twice' % (where, key))
        globs = []
        for glob in rule['paths']:
            try:
                globs.append((glob, glob_regex(glob)))
            except Refused as error:
                raise Refused('%s.paths: %s' % (where, error))
        for name in rule['checks']:
            if name not in steps:
                raise Refused('%s.checks: no check named %r in %s' % (where, name, manifest_label))
        compiled.append((globs, rule['checks']))
    return compiled, None


def git(root, *args):
    result = subprocess.run(['git', '-C', str(root)] + list(args), stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.returncode, result.stdout


def resolve_base(root, base):
    """Return (label, merge base commit) for BASE, or for the default branch when BASE is None."""
    if base is None:
        status, out = git(root, 'symbolic-ref', '-q', 'refs/remotes/origin/HEAD')
        refs = [out.decode('utf-8', 'replace').strip()] if status == 0 else []
        refs += ['refs/remotes/origin/main', 'refs/remotes/origin/master']
        found = [ref for ref in refs if git(root, 'rev-parse', '--verify', '-q', ref + '^{commit}')[0] == 0]
        if not found:
            raise Refused('no default branch found (origin/HEAD, origin/main or origin/master); name BASE')
        ref = found[0]
        label = ref[len('refs/remotes/'):] if ref.startswith('refs/remotes/') else ref
    else:
        if not base or base.startswith('-'):
            raise Refused('BASE %r is not a revision' % base)
        ref = label = base
    status, out = git(root, 'rev-parse', '--verify', '-q', ref + '^{commit}')
    if status:
        raise Refused('cannot resolve BASE %r to a commit' % label)
    commit = out.decode().strip()
    status, out = git(root, 'merge-base', commit, 'HEAD')
    if status:
        raise Refused('no merge base of %s and HEAD (a shallow clone needs the history)' % label)
    return label, out.decode().strip()


def changed_paths(root, merge_base):
    """Return (the paths HEAD, the index or the working tree changed since the merge base or that are
    untracked, sorted; the untracked ones among them)."""
    raw = set()
    for side, args in (('the working tree', (merge_base,)), ('the index', ('--cached', merge_base)),
                       ('HEAD', (merge_base, 'HEAD'))):
        status, diff = git(root, *(DIFF + args + ('--',)))
        if status:
            raise Refused('git diff of %s against the merge base %s failed' % (side, merge_base[:12]))
        raw |= set(diff.split(b'\0'))
    status, untracked = git(root, 'ls-files', '--others', '--exclude-standard', '--full-name', '-z')
    if status:
        raise Refused('git ls-files of the untracked files failed')
    # Untracked: a path only ls-files --others names, not one a diff names too.
    others = set(untracked.split(b'\0')) - raw
    raw |= others
    return (sorted(p.decode('utf-8', 'replace') for p in raw - {b''}),
            {p.decode('utf-8', 'replace') for p in others - {b''}})


def selection_inputs(root, manifest):
    """The repository paths whose change changes the selection itself."""
    inputs = [CONFIG, 'scripts/dev/check.sh', 'scripts/dev/changed_checks.py']
    # The manifest as named (a symlink retargeted changes the link) and as resolved.
    for path in (os.path.abspath(manifest), os.path.realpath(manifest)):
        for top in (str(root), os.path.realpath(str(root))):
            relative = os.path.relpath(path, top)
            if relative == os.pardir or relative.startswith(os.pardir + os.sep) or os.path.isabs(relative):
                continue
            relative = relative.replace(os.sep, '/')
            if relative not in inputs:
                inputs.append(relative)
    return inputs


def select(root, manifest, base=None, runner='jpdev check --changed'):
    """Return (selected names or None for the whole list, report lines)."""
    status, top = git(root, 'rev-parse', '--show-toplevel')
    if status:
        raise Refused('%s is not inside a git clone' % root)
    root = Path(top.decode('utf-8', 'surrogateescape').strip())
    steps = step_names(manifest)
    rules, no_mapping = load_rules(root, steps, os.path.basename(manifest))
    base_label, merge_base = resolve_base(root, base)
    paths, untracked = changed_paths(root, merge_base)
    short = git(root, 'rev-parse', '--short', merge_base)[1].decode().strip() or merge_base[:12]
    noun = 'path' if len(paths) == 1 else 'paths'
    report = ['== %s: %d changed %s since %s (merge base %s) ==' % (runner, len(paths), noun, base_label, short)]
    why = []
    changed_inputs = [p for p in selection_inputs(root, manifest) if p in paths]
    if changed_inputs:
        why = ['selection input changed: %s: whole list' % p for p in changed_inputs]
    elif no_mapping:
        why = ['%s: whole list' % no_mapping]
    elif not paths:
        why = ['no changed path: whole list']
    reasons = {}
    if not why:
        unmapped = []
        for path in paths:
            hit = False
            for rule, (globs, checks) in enumerate(rules):
                matched = [(rule, index) for index, (_, pattern) in enumerate(globs) if pattern.fullmatch(path)]
                if not matched:
                    continue
                hit = True
                for name in checks:
                    reasons.setdefault(name, set()).update(matched)
            if not hit:
                unmapped.append(path)
        why = [(UNTRACKED if path in untracked else UNMAPPED) % path for path in unmapped[:SHOWN]]
        if len(unmapped) > SHOWN:
            why.append('... %d more unmapped paths' % (len(unmapped) - SHOWN))
        if not why and not reasons:
            why = ['no check selected: whole list']
    if why:
        report.extend(why)
        report.append('== whole list: %d checks ==' % len(steps))
        return None, report
    selected = [name for name in steps if name in reasons]
    width = max(len(name) for name in steps)
    for name in steps:
        if name in reasons:
            globs = []
            for rule, index in sorted(reasons[name]):
                if rules[rule][0][index][0] not in globs:
                    globs.append(rules[rule][0][index][0])
            report.append('selected      %-*s  %s' % (width, name, ', '.join(globs)))
        else:
            report.append('not selected  %-*s  no changed path maps to it' % (width, name))
    report.append('== %d of %d checks selected ==' % (len(selected), len(steps)))
    return selected, report


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--root', required=True)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--base')
    parser.add_argument('--label', default='jpdev check --changed')
    args = parser.parse_args()
    try:
        selected, report = select(args.root, args.manifest, args.base, args.label)
    except Refused as error:
        print('%s: refused: %s' % (args.label, error), file=sys.stderr)
        return 2
    print('whole' if selected is None else 'only ' + ','.join(selected))
    print('\n'.join(report))
    return 0


if __name__ == '__main__':
    sys.exit(main())
