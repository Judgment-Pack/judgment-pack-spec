#!/usr/bin/env bash
# No machine-local path in tracked text: a /home/<name> or /tmp/<name> path of someone's machine.
# Not counted: the files below, where a /tmp path is a test input (a path a bundle must refuse) or
# a scratch file of the deploy workflow. A new file is checked.
set -e
if git grep -nE '(^|[^A-Za-z0-9_])/(home|tmp)/[A-Za-z0-9_.-]+' -- . ':!*.png' ':!*.jpg' \
  ':!.github/workflows/deploy.yml' \
  ':!tests/test_demo_bundle.py' \
  ':!tests/test_domain_demos.py'; then
  echo 'a machine-local path is in tracked text'; exit 1
fi
