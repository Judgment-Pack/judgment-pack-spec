#!/usr/bin/env bash
# from judgment-pack-devkit v0.2.0 (templates/check.sh)
# scripts/dev/check.sh [--setup] [--only a,b] [--skip a,b] [--all] [--manifest FILE]
# Runs the checks of dev.json in order and prints one summary block; exit status = failures.
# Stops at the first failure unless --all. --setup runs the manifest's setup steps instead.
# A step whose requires_env variable is empty is skipped, and said to be; when CI is set that is a
# failure unless the step is marked optional: true. Standard library python3 only. jpdev sets JPDEV_WRAP to add its caps around each step.
root=${JPDEV_ROOT:-$(cd "$(dirname "$0")" && git rev-parse --show-toplevel)} || exit 2
exec python3 -I - "$root" "$@" <<'PY'
import json, os, re, signal, subprocess, sys, time
root, args = sys.argv[1], sys.argv[2:]
opt = {'only': set(), 'skip': set(), 'all': False, 'setup': False, 'manifest': root + '/dev.json'}
while args:
    a = args.pop(0)
    if a in ('--only', '--skip'): opt[a[2:]] = set(args.pop(0).split(','))
    elif a == '--manifest': opt['manifest'] = args.pop(0)
    elif a in ('--all', '--setup'): opt[a[2:]] = True
    else: sys.exit('check.sh: unknown argument ' + a)
m = json.load(open(opt['manifest'], encoding='utf-8'))
steps = m.get('setup', []) if opt['setup'] else m['checks'] + ([dict(name='parity', **m['parity'])] if 'parity' in m else [])
unknown = (opt['only'] | opt['skip']) - set(s['name'] for s in steps)
if unknown: print('check.sh: no step named ' + ', '.join(sorted(unknown)), file=sys.stderr); sys.exit(2)
wrap, logdir, rows, failed = os.environ.get('JPDEV_WRAP'), os.environ.get('JPDEV_LOGDIR'), [], 0
for c in steps:
    n = c['name']
    if (opt['only'] and n not in opt['only']) or n in opt['skip']: continue
    if failed and not opt['all']: rows.append((n, 'NOT RUN', '', [])); continue
    if c.get('requires_env') and not os.environ.get(c['requires_env']):
        # A skip is a failure under CI (CI is set) unless the step says optional: true.
        if os.environ.get('CI') and not c.get('optional'): failed += 1; rows.append((n, 'FAIL', 'needs %s, which CI must set (or mark the step optional)' % c['requires_env'], []))
        else: rows.append((n, 'SKIP', 'needs ' + c['requires_env'], []))
        continue
    cmd = ['bash', '-c', c['run']]
    if wrap: cmd = [wrap, c.get('toolchain', 'shell'), '--'] + cmd
    tmo = c.get('timeout', 1200)
    t0 = time.time(); print('check: running ' + n, file=sys.stderr, flush=True)
    p = subprocess.Popen(cmd, cwd=os.path.join(root, c.get('cwd', '.')), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, errors='replace', start_new_session=True, env=dict(os.environ, JPDEV_STEP_TIMEOUT=str(tmo)))
    try: out, _ = p.communicate(timeout=None if wrap else tmo)
    except subprocess.TimeoutExpired: os.killpg(p.pid, signal.SIGKILL); out = p.communicate()[0] + '\ncheck: stopped for time\n'
    lines, took = out.splitlines(), '%ds' % (time.time() - t0)
    if logdir: os.makedirs(logdir, exist_ok=True); open('%s/%s.log' % (logdir, n), 'w').write(out)
    hit = [l.strip() for l in lines if c.get('summary') and re.search(c['summary'], l)]
    note = ['    ' + l for l in (hit if len(hit) <= 3 else ['%d lines matched; last: %s' % (len(hit), hit[-1])])]
    if p.returncode == 0: rows.append((n, 'PASS', took, note)); continue
    failed += 1
    rows.append((n, 'FAIL', '%s, exit %d' % (took, p.returncode), note + ['    --'] + ['    ' + l for l in lines[:40]] + (['    ... %d more lines' % (len(lines) - 40)] if len(lines) > 40 else [])))
print('== %s summary (%s) ==' % ('setup' if opt['setup'] else 'check', os.path.basename(opt['manifest'])))
for n, s, head, extra in rows: print('\n'.join(['%-8s %-24s %s' % (s, n, head)] + extra))
print('== %d passed, %d failed, %d skipped, %d not run ==' % tuple(sum(1 for r in rows if r[1] == k) for k in ('PASS', 'FAIL', 'SKIP', 'NOT RUN')))
sys.exit(min(failed, 255))
PY
