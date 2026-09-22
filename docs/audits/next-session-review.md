# ChangeBucket: next-session review and worklist

This was a prioritized backlog, not an enterprise-grade certification. The
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

## Worklist and completion evidence (2026-09-22)

1. **P1 — Run the full regression gate in hosted CI. Complete.**
   `.github/workflows/full-regression.yml` pins the official Kujo v1.4.0
   release archives and their published SHA-256 digests for Ubuntu 24.04 and
   macOS 15, x64 and ARM64. The four jobs in [hosted run 35726954862](https://github.com/kujolang/changebucket/actions/runs/35726954862)
   passed module checks, 132 Kujo assertions, 18 CLI regressions, clean-package
   smoke, and the artifact guard. All four reported Git 2.55.0. The tests are
   offline after the earlier, checksum-verified runtime download. The previous
   artifact-only workflow is retained as an independent guard. A subsequent
   large-move regression brings the CLI suite to 19 methods.
2. **P1 — Measure and bound large untracked-file analysis. Complete.**
   `read_added_lines` uses released Kujo `io_read_at` and `decode_text_lossy`
   to count 64 KiB chunks, so analysis no longer buffers the entire file or its
   split-line array. The per-chunk decoded output is capped at 192 KiB; a
   concurrent truncation/size change fails explicitly. A reusable non-gating
   `tests/benchmarks/untracked.py` measures one run per configuration. On this
   host: 2 MiB/one file 0.600s before, 0.429s after; 1 MiB/eight files 1.023s
   before, 0.843s after; 24 MiB/one file 1.824s after. These are exploratory
   wall timings, not throughput guarantees. A regression counts an 18 MiB file
   and a newline crossing the 64 KiB boundary. The 16 MiB Git capture limit is
   separate and unchanged. The final JSON report is necessarily proportional
   to the number of changed files.
3. **P1 — Decide binary detection policy. Complete.**
   A released byte-range read checks the first 8,000 bytes for NUL, matching
   [Git's source heuristic](https://kernel.googlesource.com/pub/scm/git/git/+/b42b995d22bb2cf57be5cccb58e682117d5726a5/xdiff-interface.c).
   The extension list remains a conservative fallback. Tests cover an unknown
   binary extension, non-UTF-8 text, and an external-target symlink counted as
   a link without reading its target. No claim is made that this defeats a
   malicious concurrent filesystem writer.
4. **P2 — Define release support and installation story. Complete for source
   distribution.** README pins Kujo v1.4.0 and the four-platform hosted matrix,
   gives a checksum-verified install example, and records local Git 2.42.0 and
   hosted Git 2.55.0. A fresh temporary HTTPS clone at commit `7c18649` fetched
   and verified the official macOS x64 archive, then passed help and JSON
   analysis. `tests/release_smoke.py` also copies only the necessary package
   files into a clean directory and exercises the launcher on all four CI
   runners. The existing GitHub v1.0.0 release has no downloadable ChangeBucket
   asset; publishing a new release is separate from this source-distribution
   verification and was not performed.
5. **P2 — Evaluate category coverage with real repositories. Complete.**
   `tests/fixtures/category_cases.json` captures seven paths verified present
   in `ai-chat`, `ssg`, `ai-sdk`, and `kujo`. The corpus caught one false negative:
   `fuzz/corpus/` was source rather than test data. Rules now treat it as tests;
   other paths match the expected overlapping categories. Category order and
   JSON keys remain unchanged; fixed rules are still preferable to an unproven
   plugin/configuration system.
6. **P2 — Evaluate output-write safety and modes. Complete.**
   `--output` uses Kujo's stable same-directory `write_file_atomic`, replacing
   an existing report only after a complete write. It replaces rather than
   follows an output-path symlink. `--json` plus `--markdown` or `--output` now
   fails with exit 2 instead of silently discarding the requested report.
   Regression tests cover overwrite, symlink target preservation, conflicting
   modes, and nonexistent parent failures.
7. **P3 — Revisit rename and directory breakdown. Complete.**
   User-requested generality supplies the demand. `--detect-renames` uses Git's
   similarity heuristic and shows both paths; `--by-directory` partitions
   changed files into top-level directory totals. Default output remains v1;
   either opt-in emits `schema_version: 2`. A CLI fixture moves a file to a name
   containing both tab and newline and verifies old/new paths, one renamed file,
   zero pure-move churn, directory totals, and `--no-deletes` behavior. A second
   fixture moves a 2 MiB file without churn. No
   per-category churn or automatic rename detection was added.

## Release decision

Every numbered item above has a source-backed implementation or explicit
scope decision and verification evidence. This supports a production-shaped
Git footprint CLI on the four tested host targets, not a universal enterprise
certification. A published ChangeBucket release artifact and transactional
snapshots of concurrently edited worktrees remain outside the completed scope.
