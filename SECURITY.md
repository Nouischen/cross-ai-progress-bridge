# Security policy

Cross-AI Progress Bridge stores progress in local project files. It has no backend, account system, analytics endpoint, or telemetry. The one network step is performed by Claude Code or Codex to fetch the pinned installer; the installed bridge does not make network requests.

## Safe starting point

For a first test, create a new empty folder under Windows **Documents** or macOS **Documents**, then open that folder as the project. Do not install at a drive/filesystem root, the home folder, the Desktop root, or a directory containing multiple unrelated projects.

Never put passwords, API keys, credentials, patient records, non-de-identified personal data, or other secrets in bridge progress files. Claude Code, Codex, Git, backup software, and file-sync services retain their own data and security policies.

## Installer integrity

The v1.0.0 bootstrap is pinned to:

`https://raw.githubusercontent.com/Nouischen/cross-ai-progress-bridge/v1.0.0/bootstrap/install.py`

Required SHA-256:

`9D5BD5DBDCD2436CD669C419B9731839B1B4E5E080E8C7BCA366915FC63CBA01`

The AI must download this file to the operating-system temporary directory, verify the hash before execution, and stop if it differs. It must not silently use another branch, tag, mirror, or URL. The installer requires Python 3.10 or newer, uses only the standard library, and contains the release payload; it does not fetch dependencies at runtime.

## Filesystem behavior

The installer and runtime are designed to:

- Keep bridge-owned reads and writes under the selected project root.
- Reject a drive/filesystem root, home folder, Desktop root, and bridge-owned symlink, junction, or reparse paths.
- Create `.ai-progress/` and `AI_PROGRESS/` without overwriting an existing bridge-owned directory.
- Add one marked entry block to `CLAUDE.md` and the effective Codex entry, backing up existing entry files before modification.
- Serialize cooperating bridge `save` and `archive` operations for each task with a cross-process OS lock, then use revision checks, backups, temporary-file replacement, and conflict preservation.
- Avoid telemetry and project-content uploads.

Cooperating bridge processes serialize writes to the same task; after the lock is released, a stale second write becomes a revision conflict instead of overwriting the newer task. The lock does not control manual edits, legacy tools, sync clients, or other third-party writers. An interrupted filesystem operation, disk failure, or antivirus interference can still cause partial state. Keep normal project backups and, as the simplest safe practice, allow only one AI at a time to modify a task.

## Existing systems and sidecar consent

Before a first install, detection examines top-level names only. If existing AI/progress-like names are found, the installer prints `INSTALL_NEEDS_CONSENT` and exits without changing the project.

Only after explicit user approval may the same verified installer run with:

`--mode sidecar --accept-existing I_ACCEPT_SIDECAR`

Sidecar mode creates separate bridge data and routes only commands beginning with `接力：`. It does not read, migrate, transform, or overwrite legacy progress records. It does read and preserve the selected Claude/Codex entry file when appending the marked routing block; a backup is created first. This is isolated coexistence, not automatic compatibility mapping.

## Trust boundary and limitations

This project is not a sandbox for Claude Code or Codex. It cannot remove higher-priority instructions already loaded by a tool, restrict permissions granted to the host application, or authenticate the model or conversation. The onboarding test only confirms that two conversations can read the same task files.

Both tools must open the same physical folder. In Git repositories, that means the same checkout/worktree; opening an isolated worktree gives each tool different local state. Cross-computer synchronization is outside this project.

## Reporting a vulnerability

Please use the repository's GitHub Security Advisory flow. Do not include real credentials, patient data, or other sensitive material; reproduce issues with synthetic data only.
