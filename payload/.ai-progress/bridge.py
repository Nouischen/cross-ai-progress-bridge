#!/usr/bin/env python3
"""Dependency-free Markdown progress bridge for Claude Code and Codex.

The canonical records are Markdown files in AI_PROGRESS/tasks/. The project
root is derived only from this installed script's .ai-progress directory.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import tempfile
import time
import unicodedata
import uuid
from pathlib import Path
from typing import Any, BinaryIO


APP = "AI_PROGRESS"
TASK_STATUSES = {"active", "blocked", "completed"}
ALL_STATUSES = {*TASK_STATUSES, "archived"}
BODY_FIELDS = (
    "goal",
    "progress",
    "next_steps",
    "blockers",
    "decisions",
    "verification",
    "related_files",
    "rerun",
)
LINE_BOUNDARY_RE = re.compile(r"\r\n|[\n\r\v\f\x1c-\x1e\x85\u2028\u2029]")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


class BridgeError(Exception):
    pass


def one_line(value: object) -> str:
    return " ".join(str(value).splitlines()).strip() or "unknown error"

def normalize_line_boundaries(value: str) -> str:
    """Map every Python splitlines boundary accepted by our format to LF."""
    return LINE_BOUNDARY_RE.sub("\n", value)


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def fail(message: str) -> None:
    raise BridgeError(one_line(message))


def lexists(path: Path) -> bool:
    return os.path.lexists(os.fspath(path))


def is_link_or_reparse(path: Path) -> bool:
    try:
        if path.is_symlink():
            return True
        info = path.stat(follow_symlinks=False)
    except FileNotFoundError:
        return False
    except OSError as exc:
        fail(f"cannot inspect bridge path: {exc}")
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(getattr(info, "st_file_attributes", 0) & reparse)


def project_root() -> Path:
    """Anchor the project only to this installed script, never cwd or an argument."""
    lexical_script = Path(os.path.abspath(os.fspath(Path(__file__))))
    if not lexists(lexical_script):
        fail("bridge script is missing")
    if is_link_or_reparse(lexical_script):
        fail("bridge script may not be a symlink or reparse point")
    if lexical_script.parent.name != ".ai-progress":
        fail("bridge script must be installed directly inside .ai-progress")

    lexical_bridge_dir = lexical_script.parent
    lexical_root = lexical_bridge_dir.parent
    if is_link_or_reparse(lexical_bridge_dir) or is_link_or_reparse(lexical_root):
        fail("bridge directory and project root may not be a symlink or reparse point")

    try:
        resolved_script = Path(__file__).resolve(strict=True)
        root = resolved_script.parent.parent
        resolved_lexical_root = lexical_root.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        fail(f"cannot resolve bridge project root: {exc}")
    if resolved_script.parent.name != ".ai-progress":
        fail("bridge script must resolve directly inside .ai-progress")
    if resolved_lexical_root != root:
        fail("bridge path crosses a symlink or reparse point")
    if not root.is_dir() or is_link_or_reparse(root):
        fail("project root must be a regular directory")
    return root


def safe_child(root: Path, *parts: str, must_exist: bool = False) -> Path:
    """Return a non-linked child and reject linked parents or path escapes."""
    path = root
    for part in parts:
        if not part or part in {".", ".."} or "/" in part or "\\" in part:
            fail("unsafe path component")
        path = path / part
        if lexists(path):
            if is_link_or_reparse(path):
                fail("bridge-owned path may not be a symlink or reparse point")
            try:
                path.resolve(strict=True).relative_to(root)
            except (OSError, RuntimeError, ValueError):
                fail("bridge-owned path escapes project root")
    if must_exist and not lexists(path):
        fail("required bridge path is missing")
    return path


def ensure_dir(root: Path, *parts: str) -> Path:
    path = safe_child(root, *parts)
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        fail(f"cannot create bridge directory: {exc}")
    if not path.is_dir() or is_link_or_reparse(path):
        fail("bridge-owned directory is unsafe")
    return path


def atomic_write(root: Path, destination: Path, text: str) -> None:
    """Write UTF-8 with a same-directory temp file and atomic replacement."""
    try:
        destination.relative_to(root)
    except ValueError:
        fail("write escapes project root")
    parent = destination.parent
    if not parent.is_dir() or is_link_or_reparse(parent):
        fail("bridge-owned destination directory is unsafe")
    if lexists(destination) and is_link_or_reparse(destination):
        fail("bridge-owned path may not be a symlink or reparse point")
    temp_name = ""
    try:
        fd, temp_name = tempfile.mkstemp(prefix=".bridge-", suffix=".tmp", dir=parent)
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, destination)
    except (OSError, UnicodeError) as exc:
        fail(f"cannot write {destination.name}: {exc}")
    finally:
        if temp_name and os.path.exists(temp_name):
            try:
                os.unlink(temp_name)
            except OSError:
                pass


def exclusive_write(root: Path, destination: Path, text: str) -> None:
    """Publish a new UTF-8 file without overwriting any existing path."""
    try:
        destination.relative_to(root)
    except ValueError:
        fail("write escapes project root")
    parent = destination.parent
    if not parent.is_dir() or is_link_or_reparse(parent):
        fail("bridge-owned destination directory is unsafe")
    if lexists(destination):
        fail("archive target already exists")
    try:
        encoded = text.encode("utf-8")
    except UnicodeError as exc:
        fail(f"cannot encode {destination.name}: {exc}")

    created = False
    try:
        with destination.open("xb", buffering=0) as handle:
            created = True
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        if is_link_or_reparse(destination) or not destination.is_file():
            fail("new archive target is unsafe")
        if destination.read_bytes() != encoded:
            fail("archive target read-back verification failed")
    except BridgeError:
        if created and lexists(destination) and not is_link_or_reparse(destination):
            try:
                destination.unlink()
            except OSError:
                pass
        raise
    except (OSError, UnicodeError) as exc:
        if created and lexists(destination) and not is_link_or_reparse(destination):
            try:
                destination.unlink()
            except OSError:
                pass
        fail(f"cannot create archive target: {exc}")


def atomic_json(root: Path, destination: Path, value: Any) -> None:
    try:
        rendered = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    except (TypeError, ValueError, UnicodeError) as exc:
        fail(f"cannot encode JSON: {exc}")
    atomic_write(root, destination, rendered)


def paths(root: Path) -> dict[str, Path]:
    bridge_dir = safe_child(root, ".ai-progress", must_exist=True)
    if not bridge_dir.is_dir():
        fail(".ai-progress must be a directory")
    progress = ensure_dir(root, APP)
    return {
        "progress": progress,
        "config": safe_child(root, APP, "config.json"),
        "tasks": ensure_dir(root, APP, "tasks"),
        "archive": ensure_dir(root, APP, "archive"),
        "drafts": ensure_dir(root, APP, "drafts"),
        "conflicts": ensure_dir(root, APP, "conflicts"),
        "backups": ensure_dir(root, APP, "backups"),
        "locks": ensure_dir(root, APP, "locks"),
    }


def default_config() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "bridge_version": "1.0.0",
        "installation_id": uuid.uuid4().hex,
        "mode": "fresh",
        "trigger_prefix": "",
        "claude_entry": "CLAUDE.md",
        "codex_entry": "AGENTS.md",
        "created_at": now(),
    }


def config(root: Path, create: bool = True) -> dict[str, Any]:
    path = paths(root)["config"]
    if not lexists(path):
        if not create:
            fail("AI_PROGRESS/config.json is missing; run status once to initialize")
        value = default_config()
        atomic_json(root, path, value)
        return value
    if is_link_or_reparse(path) or not path.is_file():
        fail("AI_PROGRESS/config.json is not a regular file")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        fail(f"invalid config.json: {exc}")
    if not isinstance(value, dict) or not isinstance(value.get("installation_id"), str):
        fail("invalid config.json schema")
    return value


def slug(title: str) -> str:
    """Create a stable, readable ASCII id without collapsing Unicode-only titles.

    The digest is deliberately part of every generated id: punctuation, non-ASCII
    titles, and otherwise-similar readable bases must not accidentally select the
    same task. Explicit ids remain available for callers that need a chosen id.
    """
    normalized = unicodedata.normalize("NFKC", title).strip()
    readable = re.sub(r"[^A-Za-z0-9_-]+", "-", normalized).strip("-_").lower()
    readable = readable or "task"
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]
    return f"{readable[:64]}-{digest}"


def validate_task_id(task_id: str) -> None:
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,79}", task_id):
        fail("invalid task id")


def task_path(root: Path, task_id: str, archived: bool = False) -> Path:
    validate_task_id(task_id)
    return safe_child(root, APP, "archive" if archived else "tasks", task_id + ".md")


def parse_markdown(path: Path) -> dict[str, Any]:
    if is_link_or_reparse(path) or not path.is_file():
        fail(f"task is not a regular file: {path.name}")
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        fail(f"task cannot be read: {path.name}: {exc}")
    header_match = re.match(r"^---\n(.*?)\n---\n", text, flags=re.S)
    if not header_match:
        fail(f"invalid task front matter: {path.name}")
    fields: dict[str, Any] = {}
    for line in header_match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    task_id = str(fields.get("id", ""))
    status = fields.get("status")
    if (
        not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,79}", task_id)
        or task_id != path.stem
        or status not in ALL_STATUSES
        or not fields.get("title")
    ):
        fail(f"invalid task metadata: {path.name}")
    if path.parent.name == "tasks" and status not in TASK_STATUSES:
        fail(f"task status does not match tasks directory: {path.name}")
    if path.parent.name == "archive" and status != "archived":
        fail(f"task status does not match archive directory: {path.name}")
    try:
        revision = int(fields.get("revision", ""))
    except (TypeError, ValueError):
        fail(f"invalid task revision: {path.name}")
    if revision < 1 or str(revision) != str(fields.get("revision")):
        fail(f"invalid task revision: {path.name}")
    fields["revision"] = revision
    body = text[header_match.end():]
    headings = (
        ("Goal", "goal"),
        ("Progress", "progress"),
        ("Next steps", "next_steps"),
        ("Blockers", "blockers"),
        ("Decisions", "decisions"),
        ("Verification", "verification"),
        ("Related files", "related_files"),
        ("Rerun", "rerun"),
    )
    for heading, name in headings:
        match = re.search(
            rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)",
            body,
            flags=re.M | re.S,
        )
        fields[name] = match.group(1).strip() if match else ""
    fields["path"] = path
    return fields


def render_task(data: dict[str, Any]) -> str:
    def clean(name: str) -> str:
        value = data.get(name, "")
        return value.strip() if isinstance(value, str) else ""

    return "\n".join(
        [
            "---",
            f"id: {data['id']}",
            f"title: {clean('title')}",
            f"status: {data['status']}",
            f"revision: {data['revision']}",
            f"created_at: {data['created_at']}",
            f"updated_at: {data['updated_at']}",
            "---",
            "",
            f"# {clean('title')}",
            "",
            "## Goal",
            clean("goal"),
            "",
            "## Progress",
            clean("progress"),
            "",
            "## Next steps",
            clean("next_steps"),
            "",
            "## Blockers",
            clean("blockers"),
            "",
            "## Decisions",
            clean("decisions"),
            "",
            "## Verification",
            clean("verification"),
            "",
            "## Related files",
            clean("related_files"),
            "",
            "## Rerun",
            clean("rerun"),
            "",
        ]
    )


def read_draft(root: Path, filename: str) -> tuple[dict[str, Any], Path]:
    name = Path(filename).name
    if name != filename or not name.endswith(".json"):
        fail("draft must be a JSON filename inside AI_PROGRESS/drafts")
    draft_path = safe_child(root, APP, "drafts", name, must_exist=True)
    if not draft_path.is_file() or is_link_or_reparse(draft_path):
        fail("draft must be a regular JSON file")
    try:
        value = json.loads(draft_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        fail(f"invalid draft JSON: {exc}")
    required = {"title", "status", *BODY_FIELDS}
    if (
        not isinstance(value, dict)
        or not required.issubset(value)
    ):
        fail(
            "draft schema requires title, status, goal, progress, next_steps, "
            "blockers, decisions, verification, related_files, rerun"
        )
    title = value.get("title")
    if value.get("status") not in TASK_STATUSES:
        fail("draft status must be active, blocked, or completed; use archive command")
    if (
        not isinstance(title, str)
        or not title.strip()
        or LINE_BOUNDARY_RE.search(title)
    ):
        fail("draft title must be a non-empty single line")
    for key in BODY_FIELDS:
        field = value.get(key)
        if not isinstance(field, str):
            fail(f"draft field {key} must be a string")
        normalized = normalize_line_boundaries(field)
        value[key] = normalized
        if re.search(r"(?m)^## ", normalized):
            fail(f"draft field {key} may not contain a line beginning with ## ")
    if "id" in value and not isinstance(value["id"], str):
        fail("draft id must be a string")
    return value, draft_path


def backup(root: Path, source: Path, task_id: str) -> Path:
    backup_dir = ensure_dir(root, APP, "backups")
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    destination = safe_child(root, APP, "backups", f"{task_id}-{stamp}.md")
    try:
        shutil.copy2(source, destination)
    except OSError as exc:
        fail(f"cannot back up task: {exc}")
    return destination


class TaskLock:
    """Cross-process exclusive lock; the harmless lock file remains permanently."""

    def __init__(self, root: Path, task_id: str):
        validate_task_id(task_id)
        ensure_dir(root, APP, "locks")
        self.path = safe_child(root, APP, "locks", task_id + ".lock")
        self.handle: BinaryIO | None = None

    def __enter__(self) -> "TaskLock":
        if lexists(self.path) and is_link_or_reparse(self.path):
            fail("task lock path may not be a symlink or reparse point")
        try:
            handle = self.path.open("a+b", buffering=0)
            if is_link_or_reparse(self.path):
                handle.close()
                fail("task lock path may not be a symlink or reparse point")
            path_stat = self.path.stat(follow_symlinks=False)
            file_stat = os.fstat(handle.fileno())
            if (path_stat.st_dev, path_stat.st_ino) != (file_stat.st_dev, file_stat.st_ino):
                handle.close()
                fail("task lock file changed while opening")
            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b"\0")
                handle.flush()
                os.fsync(handle.fileno())
            handle.seek(0)
            if os.name == "nt":
                import msvcrt

                while True:
                    try:
                        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                        break
                    except OSError:
                        time.sleep(0.05)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            self.handle = handle
            return self
        except BridgeError:
            raise
        except (OSError, ImportError) as exc:
            fail(f"cannot acquire task lock: {exc}")

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        handle = self.handle
        if handle is None:
            return
        try:
            handle.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()
            self.handle = None


def save(root: Path, draft_name: str) -> dict[str, Any]:
    draft, _ = read_draft(root, draft_name)
    task_id = str(draft.get("id") or slug(draft["title"]))
    validate_task_id(task_id)
    with TaskLock(root, task_id):
        destination = task_path(root, task_id)
        existing = parse_markdown(destination) if lexists(destination) else None
        archived_destination = task_path(root, task_id, archived=True)
        if lexists(archived_destination):
            fail("task id is already archived and cannot be reused")
        expected = draft.get("expected_revision")
        if existing and expected is None:
            fail("update requires expected_revision")
        if existing and (
            not isinstance(expected, int)
            or isinstance(expected, bool)
            or expected != int(existing["revision"])
        ):
            conflict = safe_child(
                root,
                APP,
                "conflicts",
                f"{task_id}-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}.json",
            )
            atomic_json(
                root,
                conflict,
                {
                    "reason": "revision_conflict",
                    "expected_revision": expected,
                    "actual_revision": existing["revision"],
                    "draft": draft,
                },
            )
            return {
                "result": "conflict",
                "conflict": str(conflict.relative_to(root)),
                "actual_revision": int(existing["revision"]),
            }
        created = existing["created_at"] if existing else now()
        revision = int(existing["revision"]) + 1 if existing else 1
        data = dict(
            draft,
            id=task_id,
            revision=revision,
            created_at=created,
            updated_at=now(),
        )
        if existing:
            backup(root, destination, task_id)
        atomic_write(root, destination, render_task(data))
        return {
            "result": "saved",
            "id": task_id,
            "revision": revision,
            "path": str(destination.relative_to(root)),
        }


def all_tasks(root: Path, archived: bool = False) -> list[dict[str, Any]]:
    folder = paths(root)["archive" if archived else "tasks"]
    try:
        files = sorted(folder.glob("*.md"))
    except OSError as exc:
        fail(f"cannot list tasks: {exc}")
    if any(is_link_or_reparse(path) for path in files):
        fail("bridge-owned path may not be a symlink or reparse point")
    records = [parse_markdown(path) for path in files]
    return sorted(records, key=lambda item: item.get("updated_at", ""), reverse=True)


def list_tasks(root: Path, open_only: bool) -> list[dict[str, Any]]:
    result = all_tasks(root)
    return [
        item
        for item in result
        if not open_only or item["status"] in {"active", "blocked"}
    ]


def cmd_status(root: Path, _: argparse.Namespace) -> dict[str, Any]:
    cfg = config(root)
    tasks = list_tasks(root, True)
    return {
        "installation_id": cfg["installation_id"],
        "mode": cfg.get("mode", "fresh"),
        "open": [
            {"id": item["id"], "title": item["title"], "status": item["status"]}
            for item in tasks
        ],
    }


def cmd_list(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    tasks = list_tasks(root, args.open)
    return {
        "tasks": [
            {
                "id": item["id"],
                "title": item["title"],
                "status": item["status"],
                "revision": item["revision"],
                "updated_at": item["updated_at"],
                "next_steps": item["next_steps"],
            }
            for item in tasks
        ]
    }


def cmd_show(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    candidate = task_path(root, args.task)
    if not lexists(candidate):
        candidate = task_path(root, args.task, archived=True)
    if not lexists(candidate):
        fail("task not found")
    data = parse_markdown(candidate)
    data.pop("path", None)
    return data


def cmd_archive(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    with TaskLock(root, args.task):
        source = task_path(root, args.task)
        target = task_path(root, args.task, archived=True)
        if not lexists(source):
            fail("active task not found")
        if lexists(target):
            fail("archive target already exists")
        record = parse_markdown(source)
        if args.expected_revision != record["revision"]:
            fail(
                f"archive revision conflict: expected {args.expected_revision}, "
                f"actual {record['revision']}"
            )
        backup(root, source, args.task)
        updated = dict(
            record,
            status="archived",
            revision=int(record["revision"]) + 1,
            updated_at=now(),
        )
        updated.pop("path", None)
        archived_text = render_task(updated)
        exclusive_write(root, target, archived_text)
        try:
            source.unlink()
        except OSError as exc:
            cleanup_error: OSError | None = None
            try:
                target.unlink()
            except OSError as cleanup_exc:
                cleanup_error = cleanup_exc
            if cleanup_error is not None:
                fail(
                    f"cannot remove active task and archive rollback failed: "
                    f"{exc}; {cleanup_error}"
                )
            fail(f"cannot remove active task; archive publication rolled back: {exc}")
        return {
            "result": "archived",
            "id": args.task,
            "revision": updated["revision"],
            "path": str(target.relative_to(root)),
        }


def parser() -> argparse.ArgumentParser:
    command_parser = argparse.ArgumentParser(description=__doc__)
    sub = command_parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    list_parser = sub.add_parser("list")
    list_parser.add_argument("--open", action="store_true")
    show_parser = sub.add_parser("show")
    show_parser.add_argument("task")
    save_parser = sub.add_parser("save")
    save_parser.add_argument("--draft", required=True)
    archive_parser = sub.add_parser("archive")
    archive_parser.add_argument("task")
    archive_parser.add_argument("--expected-revision", required=True, type=int)
    return command_parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = parser().parse_args(argv)
        root = project_root()
        commands = {
            "status": cmd_status,
            "list": cmd_list,
            "show": cmd_show,
            "save": lambda project, options: save(project, options.draft),
            "archive": cmd_archive,
        }
        result = commands[args.command](root, args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except BridgeError as exc:
        print(f"bridge error: {one_line(exc)}", file=sys.stderr)
        return 2
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"bridge error: {one_line(exc)}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"bridge error: unexpected {type(exc).__name__}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
