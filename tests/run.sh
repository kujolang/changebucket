#!/usr/bin/env bash
# Run the ChangeBucket test suite.
#
#   ./tests/run.sh
#   KUJO=/path/to/kujo/target/release/kujo ./tests/run.sh
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KUJO="${KUJO:-kujo}"

cd "$PROJECT_DIR"
TEST_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/changebucket-run.XXXXXX")"
trap 'rm -rf -- "$TEST_ROOT"' EXIT
TMPDIR="$TEST_ROOT" "$KUJO" run "$PROJECT_DIR/tests/changebucket_test.kujo"
