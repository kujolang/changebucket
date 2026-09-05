#!/usr/bin/env bash
# Full local regression gate. Python is a test-only dependency.
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KUJO="${KUJO:-kujo}"
export KUJO
cd "$PROJECT_DIR"
for module in changebucket.kujo src/*.kujo tests/*.kujo tests/benchmarks/*.kujo; do
  "$KUJO" check "$module"
done
./tests/run.sh
python3 tests/hardening_test.py
bash .github/scripts/check-kujo-tool-artifacts.sh
