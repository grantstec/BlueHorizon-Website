"""BlueHorizon Desktop — a one-window app for editing the Jupyter Book site
without touching Git or the GitHub Actions UI.

Buttons:
  - Publish Changes       commit + push everything with an auto-generated message
  - New Page              create a new top-level page under a chosen section
  - New Sub Page          create a new page nested under an existing page
  - Fix Structure         dedup _toc.yml captions, fix folder casing
  - Settings              choose repo path, toggle auto-pull, set interval

A background thread polls the remote every N seconds and rebases any new
commits into the working copy so the user's Obsidian vault stays live.
"""

from __future__ import annotations

import os
import queue
import sys
import threading
import time
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Optional

from commit_msg import generate_commit_message, preview_changes
from config import Settings
from git_ops import GitError, GitOps
from page_ops import (
    create_new_page,
    create_new_subpage,
    fix_toc_structure,
    list_chapters_in_part,
    list_parts,
    parse_toc,
)


APP_TITLE = "BlueHorizon Desktop"
APP_VERSION = "1.0.0"


# ---------------------------------------------------------------------------
# Thread-safe logging into the GUI
# ---------------------------------------------------------------------------

class _LogQueue:
    """The background thread can't touch Tk widgets directly, so it pushes
    log lines onto a queue that the GUI drains on a Tk after() tick."""

    def __init__(self) -> None:
        self._q: "queue.Queue[tuple[str, str]]" = queue.Queue()

    def info(self, msg: str) -> None:
        self._q.put(("info", msg))

    def error(self, msg: str) -> None:
        self._q.put(("error", msg))

    def drain(self):
        while True:
            try:
                yield self._q.get_nowait()
            except queue.Empty:
                return


# ---------------------------------------------------------------------------
# Background auto-pull
# ---------------------------------------------------------------------------

class AutoPuller(threading.Thread):
    def __init__(self, app: "App") -> None:
        super().__init__(daemon=True, name="auto-puller")
        self.app = app
        self._stop = threading.Event()

    def stop(self) -> None:
        self._stop.set()

    def run(self) -> None:
        # Initial pull-on-startup
        time.sleep(2)
        while not self._stop.is_set():
            if self.app.settings.auto_pull_enabled and self.app.git is not None:
                try:
                    status = self.app.git.status()
                    if not status.is_clean:
                        # Skip auto-pull if user has uncommitted edits — pulling
                        # with --autostash would interrupt their typing in Obsidian
                        self.app.log.info(
                            "[auto-pull] skipped — you have local changes"
                        )
                    else:
                        self.app.git.fetch()
                        behind, _ahead = self.app.git.behind_ahead()
                        if behind > 0:
                            self.app.git.pull()
                            self.app.log.info(
                                f"[auto-pull] pulled {behind} new commit(s) from GitHub"
                            )
                        else:
                            # quiet success — only mention it on first tick
                            pass
                except GitError as e:
                    self.app.log.error(f"[auto-pull] {e}")
                except Exception as e:  # defensive — never let the thread die
                    self.app.log.error(f"[auto-pull] unexpected: {e}")
            # Sleep in small slices so stop() responds quickly
            for _ in range(max(1, self.app.settings.auto_pull_seconds)):
                if self._stop.is_set():
                    return
                time.sleep(1)


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------

class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(f"{APP_TITLE} — v{APP_VERSION}")
        self.root.geometry("720x540")
        self.root.minsize(620, 480)

        self.settings = Settings.load()
        self.git: Optional[GitOps] = None
        self.log = _LogQueue()
        self.auto_puller = AutoPuller(self)

        self._build_ui()
        self._bind_repo()
        self._tick_log_drain()
        self.auto_puller.start()
        self._tick_status_refresh()

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("vista" if os.name == "nt" else "clam")
        except tk.TclError:
            pass

        # Top status panel
        top = ttk.Frame(self.root, padding=(12, 10))
        top.pack(side="top", fill="x")

        self.repo_label = ttk.Label(top, text="(no repo selected)", font=("Segoe UI", 10, "bold"))
        self.repo_label.pack(side="left")
        ttk.Button(top, text="Change folder…", command=self._choose_repo).pack(side="right")

        self.branch_label = ttk.Label(top, text="branch: —")
        self.branch_label.pack(side="left", padx=(16, 0))

        # Main action buttons — big and obvious
        actions = ttk.Frame(self.root, padding=(12, 4))
        actions.pack(side="top", fill="x")

        self.publish_btn = ttk.Button(
            actions,
            text="📤  Publish Changes",
            command=self._publish_changes,
        )
        self.publish_btn.grid(row=0, column=0, sticky="ew", padx=4, pady=4, ipady=6)

        ttk.Button(actions, text="📝  New Page", command=self._new_page).grid(
            row=0, column=1, sticky="ew", padx=4, pady=4, ipady=6
        )
        ttk.Button(actions, text="↪  New Sub Page", command=self._new_subpage).grid(
            row=0, column=2, sticky="ew", padx=4, pady=4, ipady=6
        )
        ttk.Button(actions, text="🧹  Fix Structure", command=self._fix_structure).grid(
            row=1, column=0, sticky="ew", padx=4, pady=4, ipady=4
        )
        ttk.Button(actions, text="↻  Pull now", command=self._manual_pull).grid(
            row=1, column=1, sticky="ew", padx=4, pady=4, ipady=4
        )
        ttk.Button(actions, text="⚙  Settings…", command=self._open_settings).grid(
            row=1, column=2, sticky="ew", padx=4, pady=4, ipady=4
        )
        for c in range(3):
            actions.columnconfigure(c, weight=1)

        # Status summary
        status_frame = ttk.LabelFrame(self.root, text="Status", padding=(12, 8))
        status_frame.pack(side="top", fill="x", padx=12, pady=(8, 4))
        self.status_label = ttk.Label(status_frame, text="—")
        self.status_label.pack(anchor="w")
        self.last_commit_label = ttk.Label(status_frame, text="", foreground="#666")
        self.last_commit_label.pack(anchor="w")

        # Activity log
        log_frame = ttk.LabelFrame(self.root, text="Activity", padding=(8, 6))
        log_frame.pack(side="top", fill="both", expand=True, padx=12, pady=(4, 10))

        self.log_text = tk.Text(
            log_frame, height=10, wrap="word", font=("Consolas", 9), state="disabled"
        )
        self.log_text.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scroll.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scroll.set)

        # Footer
        footer = ttk.Frame(self.root)
        footer.pack(side="bottom", fill="x")
        self.footer_label = ttk.Label(footer, text="", foreground="#888")
        self.footer_label.pack(side="left", padx=12, pady=(0, 6))

    # ------------------------------------------------------------- bindings
    def _bind_repo(self) -> None:
        path = self.settings.repo_path
        if not path or not os.path.isdir(path):
            self._info("Pick the BlueHorizon-Website folder to get started.")
            self._choose_repo()
            return
        self.git = GitOps(path)
        if not self.git.is_repo():
            self._error(f"{path} is not a Git repository.")
            self.git = None
            return
        self.repo_label.configure(text=os.path.basename(path) or path)
        try:
            self.branch_label.configure(text=f"branch: {self.git.current_branch()}")
            remote = self.git.remote_url()
            if remote:
                self._info(f"Connected to remote: {remote}")
        except GitError as e:
            self._error(str(e))
        self._refresh_status_once()

    def _choose_repo(self) -> None:
        chosen = filedialog.askdirectory(
            title="Select the BlueHorizon-Website folder",
            initialdir=self.settings.repo_path or os.path.expanduser("~"),
        )
        if not chosen:
            return
        self.settings.repo_path = chosen
        self.settings.save()
        self._bind_repo()

    # ----------------------------------------------------------------- log
    def _info(self, msg: str) -> None:
        self._write_log("info", msg)

    def _error(self, msg: str) -> None:
        self._write_log("error", msg)

    def _write_log(self, kind: str, msg: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        prefix = "ERR" if kind == "error" else "   "
        line = f"[{ts}] {prefix}  {msg}\n"
        self.log_text.configure(state="normal")
        self.log_text.insert("end", line)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _tick_log_drain(self) -> None:
        # Drain background-thread messages into the GUI text widget
        for kind, msg in self.log.drain():
            self._write_log(kind, msg)
        self.root.after(250, self._tick_log_drain)

    def _tick_status_refresh(self) -> None:
        self._refresh_status_once()
        self.root.after(5000, self._tick_status_refresh)

    def _refresh_status_once(self) -> None:
        if self.git is None:
            self.status_label.configure(text="No repo selected.")
            return
        try:
            status = self.git.status()
            behind, ahead = self.git.behind_ahead()
            parts = []
            if status.is_clean:
                parts.append("✓ Working tree clean")
            else:
                parts.append(f"● {status.total_changes} local change(s)")
            if behind:
                parts.append(f"⬇ {behind} new on GitHub")
            if ahead:
                parts.append(f"⬆ {ahead} ready to publish")
            self.status_label.configure(text="    ".join(parts))
            self.last_commit_label.configure(
                text=f"Last commit: {self.git.last_commit_summary()}"
            )
            ap = (
                f"Auto-pull: every {self.settings.auto_pull_seconds}s"
                if self.settings.auto_pull_enabled
                else "Auto-pull: off"
            )
            self.footer_label.configure(text=ap)
        except GitError as e:
            self.status_label.configure(text=f"Status error: {e}")

    # ------------------------------------------------------------- actions
    def _ensure_repo(self) -> bool:
        if self.git is None:
            messagebox.showwarning(
                APP_TITLE, "Please pick the BlueHorizon-Website folder first."
            )
            return False
        return True

    def _manual_pull(self) -> None:
        if not self._ensure_repo():
            return
        try:
            self.git.fetch()
            behind, _ahead = self.git.behind_ahead()
            if behind == 0:
                self._info("Already up to date — nothing to pull.")
            else:
                self.git.pull()
                self._info(f"Pulled {behind} new commit(s) from GitHub.")
        except GitError as e:
            self._error(str(e))
            messagebox.showerror(APP_TITLE, str(e))
        self._refresh_status_once()

    def _publish_changes(self) -> None:
        if not self._ensure_repo():
            return
        try:
            status = self.git.status()
        except GitError as e:
            self._error(str(e))
            return

        if status.is_clean:
            messagebox.showinfo(APP_TITLE, "No local changes to publish.")
            return

        preview = preview_changes(status)
        proposed_msg = generate_commit_message(status)

        # Confirm with a preview — non-tech-savvy users still benefit from
        # seeing what's about to leave their machine.
        if not messagebox.askyesno(
            APP_TITLE,
            (
                "Ready to publish these changes?\n\n"
                f"{preview}\n\n"
                f"Commit message:\n  {proposed_msg}"
            ),
        ):
            return

        try:
            # Pull first to avoid push rejections
            self.git.fetch()
            behind, _ahead = self.git.behind_ahead()
            if behind:
                self.git.pull()
                self._info(f"Pulled {behind} new commit(s) before publishing.")
            self.git.add_all()
            self.git.commit(proposed_msg)
            self.git.push()
            self._info(f"Published: {proposed_msg}")
            messagebox.showinfo(APP_TITLE, "Changes published! 🎉")
        except GitError as e:
            self._error(str(e))
            messagebox.showerror(APP_TITLE, f"Could not publish:\n\n{e}")
        self._refresh_status_once()

    # ---------------------------------------------------- new page dialogs
    def _new_page(self) -> None:
        if not self._ensure_repo():
            return
        parts = list_parts(self.settings.repo_path)
        if not parts:
            messagebox.showerror(APP_TITLE, "No sections found in _toc.yml.")
            return

        win = tk.Toplevel(self.root)
        win.title("New Page")
        win.transient(self.root)
        win.grab_set()
        win.geometry("420x180")

        ttk.Label(win, text="Section:").pack(anchor="w", padx=14, pady=(14, 4))
        section_var = tk.StringVar()
        captions = [p.caption for p in parts]
        section_combo = ttk.Combobox(
            win, textvariable=section_var, values=captions, state="readonly"
        )
        section_combo.pack(fill="x", padx=14)
        section_combo.current(0)

        ttk.Label(win, text="Page title:").pack(anchor="w", padx=14, pady=(12, 4))
        title_var = tk.StringVar()
        title_entry = ttk.Entry(win, textvariable=title_var)
        title_entry.pack(fill="x", padx=14)
        title_entry.focus_set()

        btns = ttk.Frame(win)
        btns.pack(fill="x", padx=14, pady=14)
        ttk.Button(btns, text="Cancel", command=win.destroy).pack(side="right")
        def _create():
            title = title_var.get().strip()
            section = section_var.get()
            if not title:
                messagebox.showwarning(APP_TITLE, "Please type a page title.")
                return
            try:
                new_path = create_new_page(self.settings.repo_path, section, title)
                self._info(f"Created new page: {os.path.relpath(new_path, self.settings.repo_path)}")
                messagebox.showinfo(APP_TITLE, f"Created:\n{new_path}")
                win.destroy()
            except Exception as e:
                messagebox.showerror(APP_TITLE, str(e))
        ttk.Button(btns, text="Create", command=_create).pack(side="right", padx=(0, 8))

    def _new_subpage(self) -> None:
        if not self._ensure_repo():
            return

        parts = list_parts(self.settings.repo_path)
        if not parts:
            messagebox.showerror(APP_TITLE, "No sections found in _toc.yml.")
            return

        win = tk.Toplevel(self.root)
        win.title("New Sub Page")
        win.transient(self.root)
        win.grab_set()
        win.geometry("480x240")

        ttk.Label(win, text="Section:").pack(anchor="w", padx=14, pady=(14, 4))
        section_var = tk.StringVar()
        section_combo = ttk.Combobox(
            win, textvariable=section_var, values=[p.caption for p in parts], state="readonly"
        )
        section_combo.pack(fill="x", padx=14)

        ttk.Label(win, text="Parent page:").pack(anchor="w", padx=14, pady=(12, 4))
        parent_var = tk.StringVar()
        parent_combo = ttk.Combobox(win, textvariable=parent_var, state="readonly")
        parent_combo.pack(fill="x", padx=14)

        ttk.Label(win, text="Sub-page title:").pack(anchor="w", padx=14, pady=(12, 4))
        title_var = tk.StringVar()
        title_entry = ttk.Entry(win, textvariable=title_var)
        title_entry.pack(fill="x", padx=14)

        chapters_by_part: dict[int, list] = {}

        def _on_section_change(_evt=None):
            part_idx = section_combo.current()
            chapters = list_chapters_in_part(self.settings.repo_path, part_idx)
            chapters_by_part[part_idx] = chapters
            parent_combo.configure(values=[c.title for c in chapters])
            if chapters:
                parent_combo.current(0)
            else:
                parent_var.set("")

        section_combo.bind("<<ComboboxSelected>>", _on_section_change)
        section_combo.current(0)
        _on_section_change()

        btns = ttk.Frame(win)
        btns.pack(fill="x", padx=14, pady=14)
        ttk.Button(btns, text="Cancel", command=win.destroy).pack(side="right")
        def _create():
            title = title_var.get().strip()
            part_idx = section_combo.current()
            chap_idx = parent_combo.current()
            chapters = chapters_by_part.get(part_idx, [])
            if not title:
                messagebox.showwarning(APP_TITLE, "Please type a sub-page title.")
                return
            if chap_idx < 0 or chap_idx >= len(chapters):
                messagebox.showwarning(APP_TITLE, "Pick a parent page.")
                return
            parent_file = chapters[chap_idx].file
            try:
                new_path = create_new_subpage(self.settings.repo_path, parent_file, title)
                self._info(
                    f"Created sub-page under {parent_file}: "
                    f"{os.path.relpath(new_path, self.settings.repo_path)}"
                )
                messagebox.showinfo(APP_TITLE, f"Created:\n{new_path}")
                win.destroy()
            except Exception as e:
                messagebox.showerror(APP_TITLE, str(e))
        ttk.Button(btns, text="Create", command=_create).pack(side="right", padx=(0, 8))
        title_entry.focus_set()

    def _fix_structure(self) -> None:
        if not self._ensure_repo():
            return
        try:
            report = fix_toc_structure(self.settings.repo_path)
        except Exception as e:
            messagebox.showerror(APP_TITLE, str(e))
            return
        self._info(f"Fix Structure: {report.summary().replace(chr(10), ' | ')}")
        messagebox.showinfo(APP_TITLE, report.summary())

    # ----------------------------------------------------------- settings
    def _open_settings(self) -> None:
        win = tk.Toplevel(self.root)
        win.title("Settings")
        win.transient(self.root)
        win.grab_set()
        win.geometry("420x240")

        ttk.Label(win, text="Repo folder:").pack(anchor="w", padx=14, pady=(14, 4))
        path_var = tk.StringVar(value=self.settings.repo_path)
        path_row = ttk.Frame(win)
        path_row.pack(fill="x", padx=14)
        ttk.Entry(path_row, textvariable=path_var).pack(side="left", fill="x", expand=True)
        def _browse():
            p = filedialog.askdirectory(initialdir=path_var.get() or os.path.expanduser("~"))
            if p:
                path_var.set(p)
        ttk.Button(path_row, text="Browse…", command=_browse).pack(side="left", padx=(6, 0))

        auto_var = tk.BooleanVar(value=self.settings.auto_pull_enabled)
        ttk.Checkbutton(
            win, text="Auto-pull updates from GitHub", variable=auto_var
        ).pack(anchor="w", padx=14, pady=(14, 0))

        ttk.Label(win, text="Auto-pull every (seconds):").pack(anchor="w", padx=14, pady=(10, 4))
        secs_var = tk.IntVar(value=self.settings.auto_pull_seconds)
        ttk.Spinbox(win, from_=5, to=600, textvariable=secs_var, width=8).pack(anchor="w", padx=14)

        btns = ttk.Frame(win)
        btns.pack(side="bottom", fill="x", padx=14, pady=14)
        ttk.Button(btns, text="Cancel", command=win.destroy).pack(side="right")
        def _save():
            self.settings.repo_path = path_var.get().strip()
            self.settings.auto_pull_enabled = bool(auto_var.get())
            try:
                self.settings.auto_pull_seconds = max(5, int(secs_var.get()))
            except (TypeError, ValueError):
                self.settings.auto_pull_seconds = 30
            self.settings.save()
            self._bind_repo()
            win.destroy()
        ttk.Button(btns, text="Save", command=_save).pack(side="right", padx=(0, 8))


def main() -> None:
    root = tk.Tk()
    try:
        # Nicer DPI scaling on Windows so the GUI doesn't look fuzzy on HiDPI screens
        if os.name == "nt":
            from ctypes import windll  # type: ignore
            windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    app = App(root)

    def _on_close():
        try:
            app.auto_puller.stop()
        finally:
            root.destroy()
    root.protocol("WM_DELETE_WINDOW", _on_close)
    root.mainloop()


if __name__ == "__main__":
    sys.exit(main() or 0)
