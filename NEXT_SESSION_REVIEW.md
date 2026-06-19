# ChangeBucket Next Session Review

Date: 2026-06-19

This document captures the follow-up list from the enterprise-readiness review.
ChangeBucket is useful and production-shaped for its current footprint-measurement
scope, but "enterprise grade" should stay tied to verified behavior, clear
contracts, and deliberately small expansion.

## Completed in this pass

- Hardened `--base` and `--head` handling so unsafe ref strings are rejected
  before git runs.
- Added explicit git diff validation so missing or invalid refs produce an
  `error:` result instead of an empty-change report.
- Tightened CLI parsing for unknown options, missing option values, and invalid
  numeric budget flags.
- Updated README and maintainer guidance to document the stricter input and
  exit-code behavior.
- Expanded the test suite from 72 to 81 assertions.
- Removed the stale generated test-output snapshot from the tracked tree.

## High-value next improvements

1. Add a focused `--diff-file <path>` mode.
   This is the biggest universality unlock because it lets ChangeBucket analyze
   patch files from code review systems, email, CI artifacts, and non-git
   workflows. Keep it narrow: parse file paths and numstat-equivalent additions
   and deletions; do not turn it into a semantic diff summarizer.

2. Add optional machine-stable compact JSON.
   `--json` currently emits pretty JSON for humans. A `--json-compact` option
   would be better for CI logs and shell pipelines while preserving the existing
   pretty output contract.

3. Add per-category churn totals.
   Category file counts are useful, but enterprise users will also ask whether
   churn concentrated in tests, generated files, config, or source. Keep overlap
   explicit because one file can be in multiple categories.

4. Improve report escaping.
   Markdown rendering wraps paths in backticks. Add escaping for backticks and
   table delimiters in file paths so unusual repository filenames cannot break
   report tables.

5. Add CI usage examples.
   Add copy-paste snippets for GitHub Actions and generic shell CI that enforce
   `changebucket check` budgets. This helps make ChangeBucket feel immediately
   adoptable without adding dependencies.

## Robustness and security ideas

- Consider replacing shell command construction with a process API that accepts
  an argv list if Kujo exposes one. The current implementation quotes paths and
  validates refs, but argv execution would be cleaner.
- Add tests for repository paths that contain spaces or single quotes.
- Add tests for filenames containing backticks, pipes, brackets, and non-ASCII
  characters once markdown escaping is improved.
- Validate `--output` parent-directory behavior and document whether missing
  directories should fail or be created.
- Keep explicit invalid-ref tests around; this was the most important failure
  mode found during this review.

## Product-presentation ideas

- Add a short "Why Kujo?" section to the README that points out what this tool
  demonstrates: a readable CLI, git integration, JSON/markdown rendering,
  deterministic tests, and no dependency install step.
- Add a tiny annotated example showing text, JSON, and markdown outputs for the
  same change.
- Keep the first screen of the README practical. The funnel into Kujo should
  come from credibility and clarity, not marketing weight.

## Things to keep resisting

- Do not make ChangeBucket a code reviewer.
- Do not add provider/API dependencies.
- Do not build configurable category plugins until real users need custom
  classification.
- Do not silently broaden git behavior in ways that mutate repositories.
- Do not shorten exact output tests when they make the report contract clearer.

## Suggested first task next session

Start with markdown escaping because it is small, security-adjacent, and easy to
verify with exact render tests. Then decide whether `--diff-file` is ready to
promote from future idea to implemented feature.
