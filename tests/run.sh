#!/usr/bin/env bash
# Run the ChangeBudget test suite.
#
#   ./tests/run.sh
#   KUJO=/path/to/kujo/target/release/kujo ./tests/run.sh
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KUJO="${KUJO:-kujo}"

exec "$KUJO" run "$PROJECT_DIR/tests/changebudget_test.kujo"
