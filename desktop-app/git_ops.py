"""Git operations for the BlueHorizon Desktop app.

All operations shell out to the `git` CLI via subprocess so we don't need
GitPython or any other heavy dependency. The repo root is passed in by
the caller (the GUI) and stored on a GitOps instance.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from typing import List, Tuple


# On Windows, subprocess.Popen pops a console window for each call. We hide it
# by setting STARTUPINFO. On other OSes this is a no-op.
if os.name == "nt":
    _STARTUPINFO = subprocess.STARTUPINFO()
    _STARTUPINFO.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    _CREATIONFLAGS = subprocess.CREATE_NO_WINDOW
else:
    _STARTUPINFO = None
    _CREATIONFLAGS = 0


@dataclass
class GitStatus:
    """Summary of `git status --porcelain` output."""

    modified: List[str]
    added: List[str]
    deleted: List[str]
    renamed: List[str]
    untracked: List[str]

    @property
    def is_clean(self) -> bool:
        return not (
            self.modified or self.added or self.deleted or self.renamed or self.untracked
        )

    @property
    def total_changes(self) -> int:
        return (
            len(self.modified)
            + len(self.added)
            + len(self.deleted)
            + len(self.renamed)
            + len(self.untracked)
        )

    def all_changed_paths(self) -> List[str]:
        return self.modified + self.added + self.deleted + self.renamed + self.untracked


class GitError(Exception):
    """Raised when a git command fails."""


class GitOps:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    # ------------------------------------------------------------------ utils
    def _run(self, *args: str, timeout: int = 60) -> Tuple[int, str, str]:
        """Run a git command and return (returncode, stdout, stderr)."""
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=timeout,
                startupinfo=_STARTUPINFO,
                creationflags=_CREATIONFLAGS,
            )
            return result.returncode, result.stdout, result.stderr
        except FileNotFoundError as e:
            raise GitError(
                "Git is not installed or not on PATH. "
                "Install Git from https://git-scm.com/ and restart the app."
            ) from e
        except subprocess.TimeoutExpired as e:
            raise GitError(f"git {' '.join(args)} timed out after {timeout}s") from e

    def _run_checked(self, *args: str, timeout: int = 60) -> str:
        rc, out, err = self._run(*args, timeout=timeout)
        if rc != 0:
            raise GitError(
                f"git {' '.join(args)} failed (exit {rc}):\n{err.strip() or out.strip()}"
            )
        return out

    # -------------------------------------------------------------- public API
    def is_repo(self) -> bool:
        if not os.path.isdir(self.repo_path):
            return False
        rc, _, _ = self._run("rev-parse", "--is-inside-work-tree")
        return rc == 0

    def current_branch(self) -> str:
        return self._run_checked("rev-parse", "--abbrev-ref", "HEAD").strip()

    def status(self) -> GitStatus:
        out = self._run_checked("status", "--porcelain=v1")
        modified, added, deleted, renamed, untracked = [], [], [], [], []
        for line in out.splitlines():
            if len(line) < 3:
                continue
            xy, path = line[:2], line[3:]
            # untracked
            if xy == "??":
                untracked.append(path)
                continue
            x, y = xy[0], xy[1]
            # consider both index and worktree status; rename takes priority
            if "R" in xy:
                renamed.append(path)
            elif "D" in xy:
                deleted.append(path)
            elif "A" in xy:
                added.append(path)
            elif "M" in xy or "T" in xy:
                modified.append(path)
            elif y != " " and y != "":
                # fallback: any worktree change counts as modified
                modified.append(path)
        return GitStatus(modified, added, deleted, renamed, untracked)

    def fetch(self) -> str:
        # Fetch only the `origin` remote. We deliberately avoid `--all` so that
        # a broken or removed `upstream` remote (a leftover from a previous fork
        # relationship, for instance) doesn't take down the whole sync loop.
        return self._run_checked("fetch", "origin", "--prune")

    def behind_ahead(self) -> Tuple[int, int]:
        """Return (behind, ahead) commits vs upstream. (0, 0) if no upstream."""
        rc, out, _ = self._run(
            "rev-list", "--left-right", "--count", "@{u}...HEAD"
        )
        if rc != 0:
            return (0, 0)
        parts = out.strip().split()
        if len(parts) != 2:
            return (0, 0)
        try:
            behind = int(parts[0])
            ahead = int(parts[1])
            return behind, ahead
        except ValueError:
            return (0, 0)

    def pull(self) -> str:
        """Pull from origin. Uses --rebase --autostash so local edits aren't lost
        in the rare event the user is mid-edit during the auto-pull tick."""
        return self._run_checked("pull", "--rebase", "--autostash", timeout=120)

    def add_all(self) -> None:
        self._run_checked("add", "-A")

    def commit(self, message: str) -> str:
        # --allow-empty-message would let blank slip through; we always require text
        if not message.strip():
            message = "Update content"
        return self._run_checked("commit", "-m", message)

    def push(self) -> str:
        return self._run_checked("push", timeout=120)

    def remote_url(self) -> str:
        rc, out, _ = self._run("remote", "get-url", "origin")
        if rc != 0:
            return ""
        return out.strip()

    def last_commit_summary(self) -> str:
        rc, out, _ = self._run("log", "-1", "--pretty=format:%h %s (%cr)")
        if rc != 0:
            return ""
        return out.strip()
