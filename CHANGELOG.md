# Changelog

All notable changes to ChangeBucket are documented here.

## Unreleased

## [1.1.0] - 2026-09-22

- Add an official Kennel package manifest for the published-release builder.
- Add a pinned, checksum-verified Kujo 1.4.0 four-platform CI regression gate
  and a clean source-package launcher smoke test.
- Stream untracked text in bounded chunks and probe unknown formats for NUL
  bytes; retain symlink handling and fail on files changed during analysis.
- Atomically replace requested Markdown reports and reject conflicting JSON
  output modes rather than silently dropping a report.
- Add opt-in Git rename detection and top-level directory totals under an
  explicit v2 JSON contract while keeping default v1 output unchanged.
- Exercise category rules against paths from real Kujo ecosystem repositories,
  including fuzz-corpus test data, and add a reproducible scale probe.
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

- Add launch-readiness Spec and Eval metadata for the Kujo prelaunch review.

## [1.0.0] - 2026-06-27

- Prepared ChangeBucket for public release with deterministic git footprint analysis, budget enforcement, JSON/Markdown reports, and isolated CLI contract tests.
