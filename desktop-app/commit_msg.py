"""Local heuristic generator for commit messages.

Given a GitStatus from git_ops, produce a short, descriptive commit message
without needing any API key. The result reads like something a human would
write — e.g.:

    Updated 3 files in Subteams/engine
    Added new page Meeting Notes 2026-05-14 in Team
    Updated MAIN Engine and 2 other files in Subteams/engine
"""

from __future__ import annotations

import os
from collections import Counter
from typing import List

from git_ops import GitStatus


def _top_folder(path: str) -> str:
    """Return the topmost meaningful folder for a path, with light grouping.

    Examples:
        docs/Subteams/engine/foo.md      -> Subteams/engine
        docs/Team/meeting notes/x.md     -> Team/meeting notes
        docs/intro.md                    -> docs
        README.MD                        -> (root)
    """
    norm = path.replace("\\", "/")
    parts = norm.split("/")
    # Strip leading "docs/" if present, then take two levels for context
    if parts and parts[0] == "docs":
        parts = parts[1:]
    if not parts:
        return "(root)"
    if len(parts) == 1:
        # Just a top-level file like _toc.yml or intro.md
        return "docs"
    # Take up to two levels for context (e.g. Subteams/engine)
    return "/".join(parts[:2])


def _basename_no_ext(path: str) -> str:
    name = os.path.basename(path.replace("\\", "/"))
    stem, _ = os.path.splitext(name)
    return stem


def _pluralize(n: int, singular: str, plural: str | None = None) -> str:
    plural = plural or singular + "s"
    return f"{n} {singular if n == 1 else plural}"


def generate_commit_message(status: GitStatus) -> str:
    """Generate a one-line commit message that summarizes the changes."""
    if status.is_clean:
        return "No changes"

    added = status.added + status.untracked
    modified = status.modified
    deleted = status.deleted
    renamed = status.renamed

    # Special-case: single file change — name it directly
    total = len(added) + len(modified) + len(deleted) + len(renamed)
    if total == 1:
        if added:
            return f"Add {_basename_no_ext(added[0])}"
        if modified:
            return f"Update {_basename_no_ext(modified[0])}"
        if deleted:
            return f"Delete {_basename_no_ext(deleted[0])}"
        if renamed:
            return f"Rename {_basename_no_ext(renamed[0])}"

    # Group changes by the top-level folder to spot a "main area" of work
    all_paths = added + modified + deleted + renamed
    folder_counts: Counter[str] = Counter(_top_folder(p) for p in all_paths)
    top_folder, top_count = folder_counts.most_common(1)[0]
    everything_in_one_folder = top_count == len(all_paths)

    parts: List[str] = []
    if added:
        parts.append(f"add {_pluralize(len(added), 'file')}")
    if modified:
        parts.append(f"update {_pluralize(len(modified), 'file')}")
    if deleted:
        parts.append(f"delete {_pluralize(len(deleted), 'file')}")
    if renamed:
        parts.append(f"rename {_pluralize(len(renamed), 'file')}")

    if not parts:
        return "Update content"

    # Combine the parts into a sentence: "Add 2 files, update 3 files"
    summary = ", ".join(parts)
    summary = summary[0].upper() + summary[1:]

    if everything_in_one_folder and top_folder != "(root)":
        return f"{summary} in {top_folder}"

    # Multi-folder change: mention top folder if it dominates
    if top_count >= max(2, len(all_paths) // 2):
        return f"{summary} (mostly in {top_folder})"

    return summary


def preview_changes(status: GitStatus, max_lines: int = 12) -> str:
    """Human-readable multi-line preview of what's changed, for the GUI dialog."""
    lines: List[str] = []

    def _section(label: str, paths: List[str]) -> None:
        if not paths:
            return
        lines.append(f"{label} ({len(paths)}):")
        for p in paths[:max_lines]:
            lines.append(f"  {p}")
        if len(paths) > max_lines:
            lines.append(f"  ... and {len(paths) - max_lines} more")

    _section("Added", status.added + status.untracked)
    _section("Modified", status.modified)
    _section("Deleted", status.deleted)
    _section("Renamed", status.renamed)
    if not lines:
        return "(no changes)"
    return "\n".join(lines)
