# Security policy

Cross-AI Progress Bridge is a set of local Markdown instructions. It has no backend, account system, analytics endpoint, or telemetry.

## What the installer is allowed to do

- Read the fixed, versioned `INSTALL.md` from this repository.
- Inspect file and directory names in the currently opened project.
- Create bridge-owned Markdown files only after the safety checks in `INSTALL.md` pass.
- Add a marked, removable entry block to the effective `CLAUDE.md` and Codex `AGENTS.md` entry.
- Back up any existing file before a permitted modification.

## What it must not do

- Read secrets, credentials, patient records, or private notes as part of discovery.
- Follow symlinks, junctions, reparse points, or unexpected hard links.
- Overwrite an existing progress system without explicit consent.
- Upload project content or send telemetry.
- Claim cross-tool verification succeeded without a fresh-session PASS from both Claude Code and Codex.

## Safe use

Start in a new, empty, non-Git folder. Do not test in a folder containing medical records, personally identifiable information, passwords, API keys, or credentials. Use one AI at a time; simultaneous edits to the same task are unsupported.

The installer is fail-closed. If the environment cannot reliably inspect paths, hard-link counts, or atomic file operations, it should stop rather than weaken the checks.

## Integrity

The public v1.0.0 bootstrap prompt pins `INSTALL.md` to this exact URL:

`https://raw.githubusercontent.com/Nouischen/cross-ai-progress-bridge/v1.0.0/INSTALL.md`

Its required SHA-256 is:

`62B052F6791BDA02C6749B3FD8FEDF320C3A4EE969EC8D32C432E438032C4FA2`

Do not proceed if the downloaded file has a different hash.

## Reporting a vulnerability

Please open a GitHub Security Advisory for the repository. Do not include real credentials, patient data, or other sensitive material in the report; use synthetic examples only.
