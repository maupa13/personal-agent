#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
sha256sum -c SHA256SUMS.txt
generated=$(find . \( -name __pycache__ -o -name '*.pyc' \) -print 2>/dev/null || true)
if [ -n "$generated" ]; then echo '[INFO] Ignoring local generated Python cache artifacts; they are not part of the signed payload.'; fi
echo '[PASS] Personal Agent Rus signed package integrity verified'
