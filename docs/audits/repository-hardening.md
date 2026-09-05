# ChangeBucket repository hardening receipt

## Repository

- Repository: `kujolang/changebucket`; branch: `main`.
- Starting SHA: `6fcaf41e7ca6c317ebb3b3408b4d185e76fb1640` (clean worktree).
- Ending implementation SHA: `21a67978b18e280e4233f28ab6394d80b03662d6`.
  This report and its evidence are a subsequent documentation-only commit;
  `git log -1 --format=%H -- docs/audits/repository-hardening.md` identifies that
  receipt commit without an impossible self-referential commit hash.
- Purpose: read-only Git footprint measurement and optional budget enforcement.
- Runtime dependencies: Kujo 1.0.0, Git, Bash launcher; no package dependencies,
  network services, credentials, providers, or build step. Python 3 is required
  only by the new development regression gate.
- Integrations: CLI consumers and the documented JSON model; launch Spec/Eval
  metadata. Compatibility exports were retained because other tools may import
  the modules. No sibling repository was modified.

## Baseline

Read every source module, the complete Kujo test suite, README, AGENTS,
CONTRIBUTING, changelog/version/package metadata, launcher, Spec/Eval artifacts,
example report, ignore rules, and the sole hosted workflow and its guard script.
Broad inventory excluded `.git`; generated report content was inspected as an
output contract, not used as a source-code style guide.

- `kujo --version`: 1.0.0.
- `./tests/run.sh`: **112 passed, 0 failed**.
- `for f in changebucket.kujo src/*.kujo tests/*.kujo; do kujo check "$f"; done`:
  all nine modules passed.
- No pre-existing failures in the existing gate.
- Renderer benchmark: **60.11 s wall**, **49.51 s user**, **2.71 s system**.
  The same newly supplied fixture was run before changing the renderer.
- The new 12-method CLI regression suite was also run in a temporary `git archive`
  of the starting SHA, with `cwd` explicitly set to the archived repository:
  **13 assertion/subtest failures**. These are regression demonstrations, not
  thirteen independent vulnerabilities. See [baseline evidence](evidence/baseline-regressions.txt).

## Findings

| ID | Priority | Area | Finding | Evidence | Action | Status |
| -- | -------- | ---- | ------- | -------- | ------ | ------ |
| CB-01 | P1 | Failure semantics | Secondary diff/ls-files failures became empty data; root lookup could silently fall back | Injected Git exits in CLI regression suite; old scalar helpers returned empty strings/lists | Checked analysis results and explicit operational errors; retain legacy scalar exports | Fixed |
| CB-02 | P1 | Process boundary | Shell execution rejected legal CR/newline repository paths; capture truncation was unchecked | CR-root regression and oversized fake numstat output | Structured argv; reject incomplete captures; explicit 16 MiB per-stream bound | Fixed |
| CB-03 | P1 | Runtime | Renderer fully selection-sorted all files to show only 5 or 10 | 2,000-file benchmark; original nested full-array loop | Stop after requested selections, preserving historical tie order | Fixed |
| CB-04 | P1 | Git semantics | Missing `--` made refs ambiguous with paths; SHA-1 empty-tree constant failed SHA-256 unborn repos | HEAD-named path and both object-format fixtures | Terminate revisions with `--`; compute empty-tree hash without writing objects | Fixed |
| CB-05 | P1 | File integrity | Dangling links counted zero, binary-named links counted binary, failed reads could undercount budgets | Symlink and vanished-file fixtures | Count links as one line; return checked read/probe failures | Fixed |
| CB-06 | P1 | Presentation | ESC/BEL filenames reached terminals; Markdown budget failures could contain active markup | Hostile Unicode/control filename and generated-file budget fixtures | Encode controls for human output and Markdown syntax in budget messages; JSON paths remain exact | Fixed |
| CB-07 | P2 | Contracts | Empty separate option values bypassed validation; root `__tests__` was source | CLI empty-value and classification regression tests | Validate empty tokens and correct root category match; normalize numeric zero prefixes before parsing | Fixed |
| CB-08 | P2 | Test state | Fixed shared temp directory could be deleted by another run; shell paths were unquoted | Old setup unconditionally removed `changebucket_selftest`; two concurrent runs under quoted TMPDIR now pass | Unique workspaces, quoted fixture arguments, launcher cleanup trap, local signing/hooks settings | Fixed |
| CB-09 | P2 | Efficiency | Up-front validation repeated an entire name-status diff | Wrapper counts: 7 total Git calls/3 diffs before, 6/2 after | Consume the checked name-status result directly | Fixed |
| CB-10 | P2 | Developer experience | No single full gate; Eval metadata embedded one workstation path | Metadata and workflow inspection | Add `tests/verify.sh`; make Eval paths repository-relative; refresh docs | Fixed |

## Changes implemented

- **Git analysis** — `src/diffsrc.kujo` and `src/analyze.kujo` now check root,
  revision, diff, enumeration, and file-read boundaries. Git receives arrays,
  not interpolated shell text. Timeouts and either truncated stream fail before
  model construction. Git display options cannot enable external diff/textconv,
  make paths relative, or suppress submodule changes. The redundant validation
  diff is removed. Legacy scalar helper signatures and return shapes remain;
  analysis uses the new checked helpers instead of their historical fallbacks.
- **CLI and classification** — `src/cli.kujo` rejects empty separate values as
  usage errors, normalizes leading zeroes for numeric parsing, and escapes
  untrusted diagnostic/output paths. `src/classify.kujo` recognizes root
  `__tests__`. These fix documented behavior rather than add flags or categories.
- **Rendering** — `src/render.kujo` performs only the required selection-sort
  passes. Prefix order, including displaced equal-churn entries, remains the
  same as the original algorithm. `src/util.kujo` uses JSON string escaping for
  C0 controls plus explicit DEL escaping. Markdown budget prose encodes markup.
  Existing exact ordinary text/Markdown assertions remain unchanged.
- **Verification** — `tests/changebucket_test.kujo` adds category and selection
  contracts and owns a unique workspace; `tests/run.sh` cleans its private parent
  on exit. `tests/hardening_test.py` provides 12 standard-library CLI tests with
  disposable repositories, failure-injecting Git wrappers, object-format tests,
  hostile paths, and a real capture-limit boundary test. `tests/verify.sh` is the
  local regression gate. No timing threshold was added to avoid a flaky ratchet.
- **Documentation** — README, AGENTS, changelog, and Eval metadata describe the
  verified commands, corrected semantics, test dependencies, and limits. The
  ordinary generated example is unchanged because its output contract did not
  change.

## Performance and efficiency

| Measurement | Before | After | Interpretation |
| -- | --: | --: | -- |
| Top 10 of 2,000 files, three iterations, wall time | 60.11 s | 8.51 s | Same fixture and installed runtime; one sample per revision |
| Same workload, user CPU | 49.51 s | 6.74 s | Local measurement, not a production throughput claim |
| Same workload, system CPU | 2.71 s | 1.62 s | Includes process startup and runtime overhead |
| Normal worktree Git calls | 7 | 6 | Deterministic wrapper trace regression |
| Normal worktree diff calls | 3 | 2 | Removed redundant validation scan |
| Runtime package dependencies | 0 | 0 | Python is test-only; no pip packages |
| Text/Markdown largest-file rows | 5 / 10 | 5 / 10 | Output remains compact and compatible |

[Machine-readable measurements](evidence/performance.json). Selection comparisons
change from O(F²) to O(F × min(F, N)); the existing O(F) input copy remains. No
memory/RSS improvement is claimed. Untracked text still buffers the file and
splits lines; changing that without a verified streaming primitive or measured
workload would be speculative. There is no build/binary-size measurement because
this is an interpreted tool with no build. There are no prompts/provider schemas
or model calls to optimize, and no token-saving claim is made. Full JSON file
lists and budget failures remain available rather than being silently shortened.

## Security and state

Reviewed arguments, refs, shell/process dispatch, Git configuration, filenames,
untracked symlinks/read failures, report output writes, terminal/Markdown/JSON
serialization, temporary cleanup, runtime capabilities, and the pinned checkout
used by the hosted artifact guard. There are no network, authentication, archive
extraction, persistence-service, queue, lock, or retry surfaces in this CLI.

Structured process execution removes shell interpretation of repository paths.
Conservative ref validation remains for compatibility. No Git operation writes
objects, stages files, changes refs, or updates the worktree. `--output` still
intentionally writes/overwrites the explicitly requested report path. Runtime
capture bounds are checked instead of passing incomplete data to parsers.

This is not a filesystem sandbox or atomic snapshot mechanism. Worktrees may
change between Git reads; local Git configuration/clean filters are trusted.
Symlink inspection is not a claim of protection against an adversarial concurrent
filesystem writer. Use stable worktrees or committed ranges for reproducibility.
The report timestamp intentionally varies. No new background state, caches,
retries, or network dependencies were introduced.

## Compatibility

- Public CLI commands, flags, exit-code meanings, JSON keys, category keys,
  budget schema, file formats, configuration files, and `KUJO` override remain.
- Corrected edge cases can change results: root `__tests__` classification,
  symlink churn, previously ambiguous refs, and failures previously mistaken for
  successful or partial analysis. Missing values now consistently exit 2.
- Ordinary text and Markdown exact fixtures pass. Human-facing control/markup
  escaping intentionally changes unsafe names; JSON `files[].path` stays exact.
- New checked module helpers are additive; existing exported scalar helpers are
  retained. Restricted runtime callers now need `process-exec` instead of the
  production shell-exec capability. Full captures are limited to 16 MiB per
  stream with the runtime's existing 30-second timeout; exceeding these fails
  explicitly. The old default capture limit was 1 MiB and was not checked.
- Runtime dependencies remain unchanged. Full development verification adds
  Python 3 and Git with SHA-256 repository support. Eval commands now require
  the documented repository-root working directory rather than a hardcoded host.
- External consumers need no schema migration; they may observe the corrected
  classifications, counts, escaped human messages, and operational failures.

## Coverage of the requested audit phases

| Phases | Disposition |
| -- | -- |
| 0–1: repository and baseline | Complete source/config/test inventory and baseline above |
| 2–4: complexity, runtime, resources | Removed redundant diff work and full sort; checked capture bounds; retained compatible exports and unmeasured file buffering |
| 5–6: agent context and output | Existing README/AGENTS split retained; concise gate added; no provider context; full evidence remains available |
| 7–9: errors, security, state | Checked failures, argv boundary, control escaping, symlink semantics, unique test workspaces; live worktree limitation documented |
| 10–11: contracts and dependencies | Exact output/schema tests preserved; empty values/category bug fixed; zero package dependencies; no speculative runtime upgrade |
| 12–13: tests and ratchets | 119 Kujo assertions, 12 CLI tests, static checks, deterministic process-count gate; existing hosted artifact guard retained |
| 14–16: docs, agent experience, dead weight | Portable Eval metadata, corrected runtime boundaries and counts; legacy exports preserved because absence of external callers cannot be proved |
| 17–18: implementation and verification | Changes committed, complete relevant local gate passed, receipt and evidence preserved |

Hosted CI still runs the artifact guard. The full gate is locally executable;
this pass does not invent an unverified hosted Kujo installation/release pin or
claim hosted tests ran. No new dependency scanner is useful for an empty package
manifest; no advisory-based claim about the externally installed runtime is made.

## Cross-repository follow-ups

None required. Related runtime documentation was inspected read-only to confirm
`spawn_process` result flags and capture bounds. No sibling changes or ecosystem
migration are required for the normal CLI/JSON contract.

## Remaining work

- **P0 / P1 / P2 / P3:** no admitted unresolved implementation findings.
- **Needs more evidence:** streaming untracked text and hosted runtime provisioning
  would need representative workload/toolchain evidence before adding machinery.
- **Not worth changing in this pass:** category plugins, standalone diff parsing,
  rename detection, speculative deletion of exported helpers, cosmetic rewrites,
  and reduction of complete JSON/budget evidence. Existing limitations remain
  documented rather than being presented as solved.

## Verification receipt

Exact main commands executed:

```bash
kujo --version
./tests/run.sh
for f in changebucket.kujo src/*.kujo tests/*.kujo; do kujo check "$f"; done
/usr/bin/time -p kujo run tests/benchmarks/top_churn.kujo
python3 tests/hardening_test.py
./tests/verify.sh
bash -n bin/changebucket tests/run.sh tests/verify.sh .github/scripts/check-kujo-tool-artifacts.sh
kujo run changebucket.kujo -- --help
./bin/changebucket --help
./bin/changebucket version
changebucket --help
changebucket version
git diff --check
```

All final commands passed. The complete gate checks ten Kujo files and reports
**119 passed, 0 failed**, **12 CLI tests OK**, and artifact-guard success.
[Verification output](evidence/verification.txt). Default/JSON/Markdown/report
writing, range/worktree analysis, budget enforcement, invalid numeric/ref input,
and non-Git analysis are covered by the suites. The two concurrent `tests/run.sh`
processes both passed all 119 assertions under a TMPDIR containing spaces and a
single quote; the parent directory was empty afterward. The benchmark ran before
and after the selection change; it is deliberately outside the mandatory gate.
