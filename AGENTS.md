# ChangeBudget — Agent Orientation Guide

Orientation for the next agent. The README is the user manual; this file is the
map. Don't duplicate the README — read it, then read this.

## Purpose

ChangeBudget is a small, standalone CLI that measures the **footprint** of a code
change (size, file categories, risk/blast-radius) and can **enforce a budget**.
It is read-only over git and is meant to be run right after an AI agent edits a
repo. It is a sibling of RunLedger (`/path/to/runledger`) and
follows the same structure and conventions.

## Canonical examples and search hygiene

- Canonical user-facing examples live in `README.md` and the help text in
  `src/cli.kujo`.
- Canonical output contracts live in `src/render.kujo`, the exact render tests in
  `tests/changebudget_test.kujo`, and the generated markdown sample at
  `examples/CHANGE_BUDGET.example.md`.
- Treat `examples/CHANGE_BUDGET.example.md` as generated output documentation,
  not as a style source for hand-written Kujo.
- Tests are behavior contracts first. Do not shorten fixtures when explicit
  output helps make the contract obvious.
- Start broad searches with `rg --files` and then target noisy patterns with
  `rg -n`. Exclude generated output from readability sweeps unless changing the
  report contract, for example:

```bash
rg -n "pattern" -g '!examples/CHANGE_BUDGET.example.md'
```

## Current status

Complete and working as of 2026-06-12. All 72 tests pass; every source file
passes the checker. v1.0.0.

## First files to read (in order)

1. `README.md` — user-facing behavior, categories, risk, JSON shape.
2. `src/analyze.kujo` — the data model and the analysis pipeline (start here).
3. `src/diffsrc.kujo` — the read-only git layer.
4. `src/classify.kujo` — file → category rules.
5. `src/cli.kujo` — argument parsing, dispatch, exit codes.
6. `tests/changebudget_test.kujo` — what "correct" means.

## Install / test / run

```bash
# The Kujo runtime lives in the (reference-only) runtime repo:
export KUJO=/path/to/kujo/target/release/kujo

# Run:
$KUJO run changebudget.kujo -- --help
./bin/changebudget --help          # if KUJO is exported or the runtime is on PATH

# Test:
./tests/run.sh                     # honors $KUJO

# Lint every module:
for f in changebudget.kujo src/*.kujo tests/*.kujo; do $KUJO check "$f"; done
```

There is **no build step** and **no package install**. `git` must be on `PATH`.

## Repo map

```
changebudget.kujo              entrypoint: from src.cli import main; exit(main(args()))
bin/changebudget               bash launcher (KUJO env override)
kujo.toml                      package metadata
src/util.kujo                  iso_now, commas, pad_right, basename, includes, truthy
src/diffsrc.kujo               READ-ONLY git: is_repo, head_commit, resolve_refs,
                               numstat_text, namestatus_text, untracked_list,
                               is_binary_path, count_added_lines
src/classify.kujo              classify(path) -> [categories]; category_order()
src/analyze.kujo               analyze(repo, base, head) -> model; risk_level(...)
src/budget.kujo                empty_config, has_constraints, evaluate(model, cfg)
src/render.kujo                render_text, render_markdown, top_by_churn
src/cli.kujo                   parse_args, build_config, run, main
tests/changebudget_test.kujo   hand-rolled, filesystem-isolated suite
tests/run.sh                   test runner
examples/CHANGE_BUDGET.example.md   a real generated markdown report
```

## Architecture overview

`cli.main` parses args → `analyze.analyze(repo, base, head)` runs read-only git
(`diffsrc`), parses `--numstat` + `--name-status` (and untracked files in
worktree mode), classifies each path (`classify`), and rolls everything into the
**model** dict. If budget flags are present (always, under `check`),
`budget.evaluate` fills the model's `budget` block. Then `render` (or
`to_json_pretty`) turns the model into output. The model is the single contract
between layers — see the JSON shape in the README.

### The model (data contract)

`{ base, head, generated_at, summary{...}, categories{cat: [paths]}, budget{checked,passed,failures[]}, files[{path,status,additions,deletions,churn,binary,categories[]}] }`

`categories` always contains all ten keys (see `category_order()`), possibly empty.

### Ref resolution (`diffsrc.resolve_refs`)

- `--head` given → **range mode**, `spec = base..head`, no untracked.
- else → **worktree mode**, `spec = base` (default `HEAD`; empty-tree hash if the
  repo has no commits), untracked files included.

## Command reference (for agents)

```bash
changebudget                     # worktree vs HEAD, text report, exit 0
changebudget --base main         # worktree vs main
changebudget --base A --head B   # range A..B
changebudget --json              # JSON only
changebudget --markdown          # markdown to stdout
changebudget --output FILE.md    # markdown to file
changebudget check --max-files N --max-churn N \
  --no-deletes --no-dependency-changes --no-lockfile-changes \
  --no-config-changes --no-generated-changes   # exit 1 if exceeded
```

## Ecosystem boundaries / non-goals

- Measures footprint only. **Not** a reviewer, **not** a diff summarizer
  (that's PatchBrief), and not a replacement for Scout/ShipCheck/Trail/Eval/
  Spec/Concord/RunLedger.
- No network, no API keys, no provider deps, no dependency on unstable Kujo
  ecosystem pieces (Kennel, workflow packs, Eval, Spec, MCP).
- Read-only git only. Never stage/commit/reset/clean/checkout/stash/apply.

## Known gotchas (Kujo runtime — these bit during the build)

- **No nested/complex index assignment.** `info[path]["status"] := x` raises
  `Complex index assignment not yet supported`. Pull the inner dict into a
  local, mutate it single-level, then reassign: `e := info[path]; e["status"] := x; info[path] := e`.
- **`test` is a reserved keyword.** Don't use it as a variable or parameter name
  (it parses as the test-framework keyword). Use `matched_test`, `is_t`, etc.
- **`$KUJO check` rejects >1 `for` loop per function scope.** Use index/`while`
  loops, or one `for` per helper. (The `$KUJO run` path, including tests, does
  not enforce this — but keep modules check-clean anyway.)
- **`write_file` refuses to overwrite** an existing path. Delete first:
  `if file_exists(p) { delete_file(p) }`.
- **The built-in `test "..." {}` framework can't see file-level imports.** The
  test suite is a hand-rolled harness run via the launcher.
- A single-line edit shows as `+1 -1` in numstat (a replacement), not `+1 -0`.
  This surprised the churn assertions — account for it when reasoning about counts.

## Verification checklist

- [ ] `for f in changebudget.kujo src/*.kujo tests/*.kujo; do $KUJO check "$f"; done` all pass
- [ ] `./tests/run.sh` → "72 passed, 0 failed"
- [ ] `$KUJO run changebudget.kujo -- --help` prints help
- [ ] worktree analysis in a temp repo (default, `--json`, `--markdown`)
- [ ] `check --max-files 1` in a multi-file change exits non-zero
- [ ] non-git directory prints `error: not a git repository` and exits 1

## Open questions / future improvements

- `--diff-file <path>`: analyze a standalone unified diff (enables non-git usage).
  Would need a numstat-equivalent parser; deferred.
- Rename detection (currently `--no-renames`): could surface `files_renamed` with
  `-M`, at the cost of brace-path parsing in numstat.
- Configurable category rules / budget profiles (e.g. a `.changebudget.toml`).
  Resist building a plugin system until real usage demands it.
- Per-directory or per-category churn breakdown.

## Session notes

No dated session-notes file is currently checked in. Use this guide, the README,
and git history as the source of truth.
