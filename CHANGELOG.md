# Changelog

All notable changes to ChangeBucket are documented here.

## Unreleased

- Reject vanished untracked binary-named files instead of reporting an
  incomplete successful footprint.
- Recognize modern lockfiles/manifests and Zig, Haskell, and F# source files;
  document the repository layout and remaining release-readiness work.
- Fail analysis on Git capture/read failures; use structured Git arguments and
  support unborn SHA-256 repositories without writing objects.
- Correct root `__tests__` classification, empty CLI values, symlink counts,
  and terminal/Markdown escaping for repository-controlled names.
- Limit largest-change selection to the requested rows while retaining ordering.
- Add isolated concurrent-safe tests, CLI failure regressions, and `tests/verify.sh`.

- Added launch-readiness Spec and Eval metadata for the Kujo prelaunch review.

## [1.0.0] - 2026-06-27

- Prepared ChangeBucket for public release with deterministic git footprint analysis, budget enforcement, JSON/Markdown reports, and isolated CLI contract tests.
