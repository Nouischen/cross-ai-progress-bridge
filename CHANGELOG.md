# Changelog

## 1.0.0 — 2026-07-19

- Added a short, no-manual-download bootstrap prompt for Claude Code and Codex.
- Replaced the long AI-interpreted setup protocol with a SHA-pinned, deterministic Python 3.10+ standard-library installer.
- Added a dependency-free local CLI backed by Markdown tasks in `AI_PROGRESS/tasks/`.
- Added natural-language routing for recording, resuming, and listing unfinished work.
- Added consent-gated sidecar mode with the `接力：` prefix for isolated coexistence with existing systems; legacy progress is not read, migrated, transformed, or overwritten.
- Added per-task cross-process OS locks, revision guards, backups, conflict preservation, path containment checks, and link/reparse rejection for bridge-owned paths.
- Added reproducible installer generation, unit tests, release validation, and a mobile-friendly guided landing page.
- No account, backend, database, Obsidian dependency, telemetry, or installed-runtime network access.
