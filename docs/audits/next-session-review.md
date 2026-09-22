# ChangeBucket: next-session review and worklist

This is a prioritized backlog, not an enterprise-grade certification. The
previous [hardening receipt](repository-hardening.md) records the earlier
baseline and completed fixes. This pass reviewed the runtime modules, launcher,
tests, docs, package/release metadata, and hosted workflows. The implementation
still measures footprint only; none of the items below should turn it into a
semantic code reviewer.

## Completed in this pass

- `src/diffsrc.kujo`: an untracked file with a binary extension that disappears
  after `git ls-files` now fails explicitly, just like a vanished text file.
- `src/classify.kujo`: recognize several current ecosystem lockfiles,
  manifests, and source extensions. Kujo and CLI regression tests cover these
  contracts; the README and contributor guide describe the actual layout and
  gate. The root entrypoint, metadata, license, and discovery files are still
  needed; no duplicate runtime implementation was found outside `src/`.

## Next work, ordered by impact

1. **P1 — Run the full regression gate in hosted CI.**
   `.github/workflows/kujo-tool-artifacts-guard.yml` only runs the artifact
   guard; the local `tests/verify.sh` runs checker, Kujo assertions, Python CLI
   regressions, and artifact guard. Select an official, pinned Kujo runtime
   release and verify its provenance on both supported CI environments before
   adding a matrix gate. Acceptance: pull requests run the complete gate on
   each supported platform with the same runtime version and no network in tests.
2. **P1 — Measure and bound large untracked-file analysis.**
   `src/diffsrc.kujo:read_added_lines` buffers and splits the whole file; Git
   capture is already capped at 16 MiB per stream. Benchmark representative
   large files and untracked-file counts, investigate supported Kujo streaming
   APIs, and choose a documented size/timeout policy that fails clearly instead
   of exhausting memory. Acceptance: bounded memory or a proven limit, unchanged
   small-file counts, and tests for the chosen boundary.
3. **P1 — Decide binary detection policy.**
   Untracked binary classification is extension-only. Files with unrecognized
   binary extensions can be miscounted as text. Compare a content probe against
   Git's documented behavior and runtime byte APIs without reading symlink
   targets. Acceptance: documented tradeoff, binary fixture without a known
   extension, no external-path reads, and deterministic counts or clear errors.
4. **P2 — Define release support and installation story.**
   The README requires an existing Kujo runtime and a manual launcher symlink;
   there is no pinned support matrix or verified installation procedure.
   Document tested Kujo/Git versions and supported operating systems, then
   provide a reproducible install example. Acceptance: fresh-machine smoke test
   of documented commands and release package layout.
5. **P2 — Evaluate category coverage with real repositories.**
   `src/classify.kujo` intentionally uses fixed, filename-based rules and this
   pass added common formats. Gather false-positive/negative cases from real
   consumer projects before adding configurable rules or more special cases.
   Acceptance: a small fixture corpus, stated precedence, and backwards-
   compatible category keys and JSON shape.
6. **P2 — Evaluate output-write safety and modes.**
   `src/cli.kujo` intentionally overwrites the explicit `--output` path; a
   failed write can leave a partial report, and `--json` takes precedence over
   `--output`/`--markdown`. Decide whether atomic replacement and conflicting-
   option diagnostics justify a compatibility change. Acceptance: documented
   behavior and failure/overwrite tests, without silently dropping output.
7. **P3 — Revisit rename and directory breakdown only with demand.**
   `--no-renames` counts a move as delete+add; there is no per-directory churn.
   Preserve the current JSON contract unless consumers need a new schema.
   Acceptance: consumer example, explicitly versioned semantics, and fixtures
   for unusual Git paths and large moves.

## Release decision

The CLI is usable for its documented scope, but “enterprise-grade” and
“universally useful” are not demonstrated by the existing tests. Hosted full-gate
coverage, scale measurements, binary semantics, and a platform support matrix
remain open. Do not claim those properties in marketing copy until the
corresponding evidence exists.
