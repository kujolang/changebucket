# ChangeBucket

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
`git ls-files` / `git rev-parse` and never modifies your repository.

## What ChangeBucket is *not*

ChangeBucket measures a change footprint. It is deliberately narrow. It is **not**:

- a code reviewer (it makes no judgements about correctness or quality),
- a diff summarizer like **PatchBrief** (it never explains what the code means),
- and it does not replace **Scout, ShipCheck, Trail, Eval, Spec, Concord, or RunLedger**.

RunLedger records agent *runs*. PatchBrief explains what changed in a diff.
ChangeBucket measures the footprint — counts and categories, not meaning.

## Quick start

ChangeBucket is a small CLI written in the Kujo language. It needs the `kujo`
runtime and `git` on your `PATH`. No network, no API keys, no build step.

```bash
# Point KUJO at your Kujo runtime, then run the launcher:
KUJO=/path/to/kujo/target/release/kujo ./bin/changebucket --help

# Or put the Kujo runtime on PATH and just:
./bin/changebucket --help
```

Expected output starts with:

```text
changebucket 1.0.0 — measure the footprint of a code change

Usage:
```

For convenience, symlink `bin/changebucket` somewhere on your `PATH`.

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

# Enforce a budget (non-zero exit if exceeded)
changebucket check --max-files 20 --max-churn 800
changebucket check --max-files 20 --max-churn 800 \
  --no-dependency-changes --no-lockfile-changes --no-deletes
```

### Commands

| Command | Behavior |
|---|---|
| `changebucket [options]` | Analyze and print a report. Always exits `0`. |
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
section but always exit `0`). They are **enforced** under `check`, which exits
`1` when the budget is exceeded. Put `check` before the budget flags; the
enforcement path is `changebucket check --max-files ...`, not `changebucket
--max-files ... check`.

### Default vs working-tree vs range

- **Default / `--base <ref>`** — *worktree mode.* Compares the working tree
  (including untracked, non-ignored files) against the base ref. If the repo has
  no commits yet, the base is the empty tree, so every tracked file is an addition.
- **`--head <ref>`** — *range mode.* Compares two commits (`base..head`). Working
  tree and untracked files are ignored.

## File categories

Files are bucketed by pragmatic path/extension rules. A file may land in several
buckets (e.g. `package.json` is both **config** and a **dependency manifest**).

| Category | Matches (examples) |
|---|---|
| **source** | source extensions (`.js .ts .tsx .py .rs .go .php .rb .java .c .cpp .h .kujo` etc.); excludes test/docs files |
| **tests** | `test/` `tests/` `__tests__/` `spec/`, `*.test.*`, `*.spec.*`, `test_*`, `*_test.go/py/rs`, `*_spec.rb` |
| **docs** | `*.md` `*.mdx` `*.rst`, `docs/`, `README*` `CHANGELOG*` `LICENSE*` `CONTRIBUTING*` |
| **config** | `package.json` `tsconfig.json` `pyproject.toml` `Cargo.toml` `kujo.toml` `.editorconfig`, `*.config.*`, `vite/rollup/webpack/eslint/tailwind/...` configs, `*.toml/.ini/.cfg/.conf`, `.env*`, `Dockerfile` `Makefile` |
| **dependency_manifests** | `package.json` `pyproject.toml` `Cargo.toml` `composer.json` `go.mod` `Gemfile` `requirements*.txt` `setup.py` `Pipfile` `pom.xml` `build.gradle` |
| **lockfiles** | `package-lock.json` `pnpm-lock.yaml` `yarn.lock` `Cargo.lock` `poetry.lock` `composer.lock` `go.sum` `Gemfile.lock` `Pipfile.lock` `bun.lockb` |
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

## Markdown report

See [`examples/CHANGE_BUCKET.example.md`](examples/CHANGE_BUCKET.example.md) for a
full generated report. Treat that file as output documentation, not as a
hand-authored example style guide; update it only when the markdown report
contract changes. The structure is: title, summary table, budget result (when a
budget was checked), file-category counts, and the largest changes by churn.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Success (the default command always exits `0`, even with budget flags). |
| `1` | A `check` whose budget was exceeded, **or** the target is not a git repository (`error: not a git repository`). |
| `2` | Usage error (unknown command). |

## Tests

```bash
KUJO=/path/to/kujo/target/release/kujo ./tests/run.sh
```

The suite is self-contained and filesystem-isolated: it builds throwaway git
repos under `$TMPDIR`, needs no network or credentials, and touches no global
state. It covers numstat/name-status parsing, every file category, churn and
risk calculation, budget pass/fail, JSON validity, markdown/text rendering,
deleted and binary files, and the non-git error path.

## Non-goals and limitations

- **Not a reviewer or summarizer.** No semantic judgement, no per-hunk prose.
- **No `--diff-file` mode yet.** Analysis requires a git repository. Parsing a
  standalone unified diff is a planned future improvement (see `AGENTS.md`).
- **Rename detection is off** (`--no-renames`). A rename is reported as a delete
  plus an add, which is intentionally conservative for a footprint tool.
- **Untracked binary detection is by extension**, since git's numstat cannot
  report line counts for files it does not yet track.
- **No network, no API keys, no provider dependencies**, and no dependency on
  unstable Kujo ecosystem pieces.
