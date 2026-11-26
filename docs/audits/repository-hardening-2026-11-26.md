# ChangeBucket hardening, 2026-11-26

Reviewed the public CLI, tracked and untracked file ingestion, classification,
budgets, report rendering, source launcher, Kennel metadata, and release
workflow at baseline `030eea63c60449f82c9ba2680227485d318fdb6d`.

- Tracked status and line counts now come from one read-only Git diff. A
  fixture that removes a modified file between Git calls previously reported
  it as modified with deletion-only churn. The report now consistently uses
  the single tracked result. The default worktree path makes five Git calls
  instead of six, with one diff instead of two.
- A missing final NUL or malformed status or numstat record now fails analysis.
  The previous parser accepted a successful but unterminated numstat response
  and reported churn for a path missing from the status result.
- The untracked binary probe now checks that each path is a regular file before
  opening it. Symlinks still count as one line without a target read. Linked
  paths and file sizes can still change later in a live worktree.
- The previously exported format-specific Git helpers and both report schemas
  remain compatible. The tracked formats now share the documented 16 MiB
  process capture limit. The untracked listing remains a separate operation,
  so a live worktree still does not support a transactional report.

The SHA-verified public Kujo 1.4.0 macOS x64 archive and Git 2.42.0 passed
`tests/verify.sh`: all module checks, 132 Kujo assertions, 21 Python CLI
regressions, clean source package launcher smoke, and the artifact guard. Both
new subprocess-output regressions fail on the baseline. The existing tests
cover empty repositories, range analysis, read-only execution, size-limited
captures, large streamed untracked files, binary data, and renames with tabs
and newlines in paths. No public release was published in this pass.
