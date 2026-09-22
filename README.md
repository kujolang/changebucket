# ChangeBucket

[![Version](https://img.shields.io/badge/version-1.0.0-black)](https://github.com/kujolang/changebucket)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)
[![built with Kujo](https://img.shields.io/badge/built%20with-Kujo-white.svg)](https://github.com/kujolang/kujo)

ChangeBucket measures the **size, shape, and risk footprint** of a code change.
It is especially useful right after an AI agent modifies a repository, to answer
at a glance:

- How big was the change? (files, additions, deletions, churn)
- What *kinds* of files changed? (source, tests, docs, config, dependencies, lockfiles, generated, CI, scripts)
- Did it touch dependencies or lockfiles?
- Did it delete files? Touch generated or CI files?
- Did it stay within the footprint budget I expected?
- Is this a tiny edit, a medium edit, or a large blast-radius change?

It produces structured metrics and a clear report — a human-readable summary,
JSON, or markdown. It is **read-only**: it only ever runs `git diff` /
`git ls-files` / `git rev-parse` / `git hash-object` (without `-w`).
Analysis never modifies your repository; `--output` writes the requested report.
User-supplied refs are validated before git runs, so bad or unsafe refs fail
explicitly instead of being mistaken for an empty change.

ChangeBucket is a focused footprint tool, not an enterprise-readiness certification
or a universal code-quality score. It works with Git repositories and requires a
local Kujo runtime. The [readiness worklist](docs/audits/next-session-review.md)
records the scope, evidence, and remaining release boundaries.

## What ChangeBucket is *not*

ChangeBucket measures a change footprint. It is deliberately narrow. It is **not**:

- a code reviewer (it makes no judgements about correctness or quality),
- a diff summarizer like **PatchBrief** (it never explains what the code means),
- and it does not replace **Scout, ShipCheck, Trail, Eval, Spec, Concord, or RunLedger**.

RunLedger records agent *runs*. PatchBrief explains what changed in a diff.
ChangeBucket measures the footprint — counts and categories, not meaning.

## Quick start

ChangeBucket is a small CLI written in the Kujo language. It needs the `kujo`
runtime and `git` on your `PATH`. Running analysis needs no network, API keys,
or build step. Installing the runtime or fetching the source does use the network.

The verified runtime is [Kujo v1.4.0](https://github.com/kujolang/kujo/releases/tag/v1.4.0).
The full gate uses its official archives and fixed SHA-256 hashes on Ubuntu 24.04
(x64/ARM64) and macOS 15 (Intel/ARM64). Python 3 is needed for development tests,
not for end users. Other Git versions and OS releases may work but are not in
the hosted support matrix. Git must support `git diff -z` and SHA-256 repos for
the full development gate. The local macOS Intel smoke used Git 2.42.0; all
four hosted runners used Git 2.55.0 in the initial passing matrix run.

For a fresh macOS Intel installation (adjust the archive and hash for your
platform using the [official checksum list](https://github.com/kujolang/kujo/releases/download/v1.4.0/checksums.txt)):

```bash
git clone https://github.com/kujolang/changebucket.git
cd changebucket
mkdir -p .local/kujo
curl -fL -o .local/kujo/runtime.tar.gz \
  https://github.com/kujolang/kujo/releases/download/v1.4.0/kujo-v1.4.0-macos-x64.tar.gz
printf '%s  %s\n' \
  'e0f41e86357d533f6a28a27c310a29deca21decb834f7baa550e894110e06ad5' \
  '.local/kujo/runtime.tar.gz' | shasum -a 256 --check
tar -xzf .local/kujo/runtime.tar.gz -C .local/kujo
KUJO="$PWD/.local/kujo/kujo" ./bin/changebucket --help
```

The `.local/` path is a local installation directory, not part of this repo.
For repeatable CI installation on all four supported targets, see the
[pinned matrix workflow](.github/workflows/full-regression.yml). A clean
source-package layout is exercised by `tests/release_smoke.py`.

```bash
# Run the bundled launcher:
./bin/changebucket --help

# Or invoke the entrypoint directly:
kujo run changebucket.kujo -- --help
```

Expected output starts with:

```text
changebucket 1.0.0 — measure the footprint of a code change

Usage:
```

For convenience, symlink `bin/changebucket` somewhere on your `PATH`.
The launcher resolves its own installation directory but analyzes your current
directory unless you pass `--repo`.

### Repository layout

`changebucket.kujo` is the required thin Kujo entrypoint; `bin/changebucket`
is its portable launcher. Runtime implementation lives in `src/`, tests in
`tests/`, the generated report example in `examples/`, and audit material in
`docs/audits/`. Root-level `kujo.toml`, `VERSION`, `LICENSE`, README, changelog,
contribution guide, and Spec metadata serve packaging, legal, or discovery
purposes. They are not duplicate implementations to move into `src/`.

## Usage

```bash
# Analyze the working tree against HEAD (the default)
changebucket

# Compare the working tree against another ref
changebucket --base main

# Compare a specific commit range (no working tree / untracked files)
changebucket --base main --head HEAD

# Analyze a different repository
changebucket --repo /path/to/repo

# Machine-readable JSON (only JSON is printed)
changebucket --json

# Markdown report to stdout
changebucket --markdown

# Markdown report written to a file
changebucket --output CHANGE_BUCKET.md

# Optional move accounting and top-level directory totals
changebucket --detect-renames --by-directory --json

# Enforce a budget (non-zero exit if exceeded)
changebucket check --max-files 20 --max-churn 800
changebucket check --max-files 20 --max-churn 800 \
  --no-dependency-changes --no-lockfile-changes --no-deletes
```

### Commands

| Command | Behavior |
|---|---|
| `changebucket [options]` | Analyze and print a report. Exits `0` on successful analysis. |
| `changebucket check [budget options]` | Analyze and **enforce** a budget. Exits non-zero if exceeded. |
| `changebucket help` / `changebucket --help` | Show usage. |
| `changebucket version` / `changebucket --version` | Show version. |

### Options

| Option | Meaning |
|---|---|
| `--base <ref>` | Base ref to compare against (default `HEAD`). |
| `--head <ref>` | Head ref. Providing it switches to commit-range mode (`base..head`); no working tree or untracked files are considered. |
| `--repo <path>` | Repository to analyze (default: current directory). |
| `--json` | Emit JSON only. |
| `--markdown` | Emit a markdown report. |
| `--output <file>` | Write a markdown report to `<file>`. |
| `--detect-renames` | Use Git rename detection; report the old and new path as one renamed file. |
| `--by-directory` | Include top-level directory totals in reports. |
| `--max-files <n>` | Budget: maximum changed files. |
| `--max-churn <n>` | Budget: maximum total churn (added + deleted lines). |
| `--max-additions <n>` | Budget: maximum added lines. |
| `--max-deletions <n>` | Budget: maximum deleted lines. |
| `--no-deletes` | Budget: fail if any file is deleted. |
| `--no-dependency-changes` | Budget: fail if a dependency manifest changed. |
| `--no-lockfile-changes` | Budget: fail if a lockfile changed. |
| `--no-config-changes` | Budget: fail if a config file changed. |
| `--no-generated-changes` | Budget: fail if a generated file changed. |

Budget options are **informational** on the default command (they show a Budget
section but do not enforce budget failures). They are **enforced** under
`check`, which exits `1` when the budget is exceeded. Put `check` before the
budget flags; the enforcement path is `changebucket check --max-files ...`, not
`changebucket --max-files ... check`.

Invalid command-line input exits `2`: unknown options, missing option values,
and non-negative integer budget flags that are not numeric. Invalid git refs
exit `1` with an `error:` line. For safety, `--base` and `--head` reject empty
refs, refs that begin with `-`, whitespace, and shell metacharacters before
calling git.
`--json` cannot be combined with `--markdown` or `--output` (usage error, exit
`2`), so a requested report is never silently discarded. `--output` atomically
replaces an existing file only after the full report is ready. It replaces a
symlink at that path rather than following it; a write error leaves the previous
report intact. Keep report paths outside repositories being analyzed when you
do not intend the report itself to count as an untracked change.

### Default vs working-tree vs range

- **Default / `--base <ref>`** — *worktree mode.* Compares the working tree
  (including untracked, non-ignored files) against the base ref. If the repo has
  no commits yet, the base is the empty tree, so every tracked file is an addition.
- **`--head <ref>`** — *range mode.* Compares two commits (`base..head`). Working
  tree and untracked files are ignored.
- **`--detect-renames`** — opt-in Git rename heuristic (`--find-renames`). A
  detected move has `status: "renamed"` and `previous_path`; a pure move has zero
  churn and does not trip `--no-deletes`. Without the flag, the historical
  delete-plus-add behavior remains. Rename similarity depends on Git, not on a
  second ChangeBucket heuristic.

## File categories

Files are bucketed by pragmatic path/extension rules. A file may land in several
buckets (e.g. `package.json` is both **config** and a **dependency manifest**).

| Category | Matches (examples) |
|---|---|
| **source** | source extensions (`.js .ts .tsx .py .rs .go .php .rb .java .c .cpp .h .kujo .zig .hs .fs` etc.); excludes test/docs files |
| **tests** | `test/` `tests/` `__tests__/` `spec/`, `fuzz/corpus/`, `*.test.*`, `*.spec.*`, `test_*`, `*_test.go/py/rs`, `*_spec.rb` |
| **docs** | `*.md` `*.mdx` `*.rst`, `docs/`, `README*` `CHANGELOG*` `LICENSE*` `CONTRIBUTING*` |
| **config** | `package.json` `tsconfig.json` `pyproject.toml` `Cargo.toml` `kujo.toml` `.editorconfig`, `*.config.*`, `vite/rollup/webpack/eslint/tailwind/...` configs, `*.toml/.ini/.cfg/.conf`, `.env*`, `Dockerfile` `Makefile` |
| **dependency_manifests** | `package.json` `pyproject.toml` `Cargo.toml` `composer.json` `go.mod` `Gemfile` `requirements*.txt` `setup.py` `Pipfile` `pom.xml` `build.gradle[.kts]` `deno.json[c]` `pubspec.yaml` `mix.exs` |
| **lockfiles** | `package-lock.json` `pnpm-lock.yaml` `yarn.lock` `Cargo.lock` `poetry.lock` `composer.lock` `go.sum` `Gemfile.lock` `Pipfile.lock` `bun.lock` `bun.lockb` `uv.lock` `deno.lock` `mix.lock` `pubspec.lock` `gradle.lockfile` |
| **generated** | `dist/` `build/` `target/` `node_modules/` `out/` `coverage/` `__pycache__/` `vendor/`, `*.min.js/.min.css`, `*.map`, `*_pb2.py`, `*.pb.go` |
| **ci** | `.github/workflows/`, `.circleci/`, `.gitlab-ci.yml`, `Jenkinsfile`, `.travis.yml`, `azure-pipelines.yml` |
| **scripts** | `scripts/` `bin/`, `*.sh .bash .zsh .ps1` |
| **other** | anything matching none of the above |

The rules live in [`src/classify.kujo`](src/classify.kujo) and are intentionally
simple. This is not a plugin system.

## Risk level (blast radius)

`risk_level` is a simple, documented heuristic over the metrics — **not** a code
quality score. It is called *risk*, or *blast radius*, on purpose.

- **high** — more than 20 files changed, **or** churn over 1000, **or** any file
  deleted, **or** any generated file touched.
- **low** — at most 5 files changed, churn at most 200, no deletes, and no
  dependency / lockfile / CI changes.
- **medium** — everything in between (e.g. a moderate edit that touches a
  dependency manifest and a lockfile).

The heuristic lives in [`src/analyze.kujo`](src/analyze.kujo) (`risk_level`).

## JSON output

`--json` emits exactly one JSON object (no surrounding prose):

```json
{
  "base": "HEAD",
  "head": "working tree",
  "generated_at": "2026-05-29T12:00:00Z",
  "summary": {
    "files_changed": 5,
    "files_added": 1,
    "files_modified": 4,
    "files_deleted": 0,
    "files_renamed": 0,
    "binary_files": 0,
    "lines_added": 12,
    "lines_deleted": 2,
    "total_churn": 14,
    "risk_level": "medium"
  },
  "categories": {
    "source": ["src/math.js"],
    "tests": ["tests/math.test.js"],
    "docs": ["docs/README.md"],
    "config": ["package.json"],
    "dependency_manifests": ["package.json"],
    "lockfiles": ["package-lock.json"],
    "generated": [],
    "ci": [],
    "scripts": [],
    "other": []
  },
  "budget": {
    "checked": true,
    "passed": false,
    "failures": ["Dependency manifest changed: package.json"]
  },
  "files": [
    {
      "path": "src/math.js",
      "status": "modified",
      "additions": 2,
      "deletions": 0,
      "churn": 2,
      "binary": false,
      "categories": ["source"]
    }
  ]
}
```

A file may appear in more than one category list, so category counts can overlap;
`files_changed` is always the unique file count.

The default JSON contract is unchanged (schema v1, with no `schema_version`
field). Either opt-in flag emits `schema_version: 2`. In v2, detected renames
include `files[].previous_path`; `--by-directory` adds `directories`, an object
keyed by `.` for root files or `name/` for each top-level directory. Every row
contains `files_changed`, `lines_added`, `lines_deleted`, and `total_churn`.
Directory totals partition changed files, so their sums equal the overall
summary. The v2 flags work in text and Markdown reports too.

## Markdown report

See [`examples/CHANGE_BUCKET.example.md`](examples/CHANGE_BUCKET.example.md) for a
full generated report. Treat that file as output documentation, not as a
hand-authored example style guide; update it only when the markdown report
contract changes. The structure is: title, summary table, budget result (when a
budget was checked), file-category counts, and the largest changes by churn.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Successful analysis (the default command does not enforce budget failures). |
| `1` | Operational failure, such as a non-git target or invalid git ref, **or** a `check` whose budget was exceeded. |
| `2` | Usage error, such as an unknown command/option, missing option value, or invalid numeric budget. |

## Tests

```bash
./tests/run.sh
```

The suite is self-contained and filesystem-isolated: it builds throwaway git
repos under `$TMPDIR`, needs no network or credentials, and touches no global
state. It covers numstat/name-status parsing, every file category, churn and
risk calculation, budget pass/fail, JSON validity, markdown/text rendering,
deleted and binary files, unusual legal git paths, invalid refs, CLI validation,
and the non-git error path. The earlier hardening baseline had 119 Kujo
assertions; the current count is reported by the gate.

Run the complete development gate (requires Python 3 for the additional
standard-library CLI regressions):

```bash
./tests/verify.sh
```

This checks every Kujo module, runs both suites, and checks the tool-artifact
guard and a clean package-layout smoke test. Each test run owns a unique
temporary workspace. Eval metadata uses
repository-relative paths; run it from the repository root.

For an opt-in, non-gating scale probe, run
`KUJO=/path/to/kujo python3 tests/benchmarks/untracked.py --mib 24 --files 1`.

## Non-goals and limitations

- **Not a reviewer or summarizer.** No semantic judgement, no per-hunk prose.
- **No `--diff-file` mode yet.** Analysis requires a git repository. Parsing a
  standalone unified diff is a planned future improvement (see `AGENTS.md`).
- **Rename detection defaults off** (`--no-renames`) for backwards compatibility.
  `--detect-renames` opts into Git's heuristic and the v2 report contract.
- **Ref syntax is intentionally conservative.** `--base` and `--head` accept
  normal branch/tag/commit-ish values but reject whitespace, leading dashes, and
  shell metacharacters before git runs. This conservative policy is preserved
  even though Git now receives structured arguments.
- **Untracked binary detection** uses known binary extensions and Git's
  first-8,000-byte NUL probe for unknown formats. It does not execute external
  textconv. Symlinks (including dangling links and links with binary extensions)
  count as one added line without reading their targets. A vanished untracked
  file fails explicitly. Text is counted in bounded 64 KiB reads, including
  files larger than Git's separate subprocess-capture bound; non-UTF-8 bytes
  are decoded lossily for line counting. A binary file with no NUL in the probe
  and an unknown extension may still be treated as text.
- **Git execution is bounded:** each subprocess uses the runtime's 30-second
  timeout and a 16 MiB limit per captured stream. Incomplete output fails analysis;
  it is never treated as a partial successful report. Git receives structured
  arguments, so restricted Kujo runs need `process-exec` rather than `shell-exec`.
  External diff/textconv helpers are disabled, paths are root-relative, and
  submodule changes are included regardless of diff display configuration.
- **Working trees are live**, not transactional snapshots. Run against a stable
  worktree or use committed refs when concurrent writers matter. Local Git
  configuration, including clean filters, remains trusted; this is not a sandbox.
- **No network, no API keys, no provider dependencies**, and no dependency on
  unstable Kujo ecosystem pieces.
