# BlueHorizon Desktop

A simple Windows app for editing the BlueHorizon Jupyter Book website
**without ever touching Git or the GitHub Actions UI**.

Once it's running, you can leave it open in the background while you write
in Obsidian. It:

- Pulls the latest content from GitHub every 30 seconds so your Obsidian
  vault always shows the team's most recent edits.
- Lets you click **Publish Changes** to commit + push everything with a
  smart auto-generated message — no typing required.
- Adds **New Page** and **New Sub Page** buttons that put files in the
  *right* folder so the website renders correctly (no more "meeting notes
  one folder too deep" issue).
- Has a **Fix Structure** button that deduplicates `_toc.yml` captions and
  fixes folder-casing mismatches if anything ever drifts again.

---

## For end users — running the app

1. Download `BlueHorizonDesktop.exe` (built once by whoever maintains
   this repo, see below).
2. Double-click it. The first time it opens it'll ask you to pick the
   `BlueHorizon-Website` folder on your computer.
3. Leave the window open while you work in Obsidian. That's it.

### What the buttons do

| Button | What happens |
|---|---|
| 📤 Publish Changes | Stages every change, generates a commit message based on what changed, and pushes to GitHub. The site rebuild kicks off automatically. |
| 📝 New Page | Asks for a section + title, creates the `.md` file in the right folder, and adds it to `_toc.yml`. |
| ↪ New Sub Page | Same as above but nested under an existing page. The new file lives in the **same folder** as its parent so rendering is never broken by extra nesting. |
| 🧹 Fix Structure | One-click cleanup of `_toc.yml`: merges duplicate captions, removes duplicate entries, fixes folder casing. Safe to run any time. |
| ↻ Pull now | Manually pull the latest from GitHub right now (it also happens every 30s in the background). |
| ⚙ Settings… | Change the repo folder, turn auto-pull on/off, change the pull interval. |

The app shows a live status line:

- `✓ Working tree clean` — nothing to publish yet
- `● 3 local changes` — you have edits that haven't been pushed
- `⬇ 2 new on GitHub` — someone else pushed; you'll receive them on the next pull tick
- `⬆ 1 ready to publish` — your commits exist locally but haven't reached GitHub

### Requirements

- **Git** for Windows must be installed and on PATH:
  <https://git-scm.com/download/win>
- Your normal GitHub auth (HTTPS credential helper or SSH key) must already
  be working — the app uses your existing setup.

---

## For maintainers — building the .exe

You only need to do this when you change the Python source.

```cmd
cd desktop-app
build_exe.bat
```

The script:

1. Creates a `.venv/` virtual environment if one doesn't exist.
2. Installs PyInstaller.
3. Runs PyInstaller against `BlueHorizon.spec`.

The result lands at `desktop-app\dist\BlueHorizonDesktop.exe`. Share that
file with your teammates — they don't need Python installed to run it.

### Running from source (no build needed)

If you just want to test changes quickly:

```cmd
cd desktop-app
python main.py
```

Python 3.10+ is recommended. Tkinter is bundled with the standard Python
installer for Windows.

---

## Project layout

```
desktop-app/
├── main.py            # Tkinter GUI
├── git_ops.py         # subprocess wrapper around the `git` CLI
├── page_ops.py        # _toc.yml parser + page creation + structure fixer
├── commit_msg.py      # local heuristic commit-message generator
├── config.py          # JSON-on-disk settings (in user's home dir)
├── BlueHorizon.spec   # PyInstaller spec
├── build_exe.bat      # one-click build script
├── requirements.txt
└── README.md          # this file
```

Settings are stored at `%USERPROFILE%\.bluehorizon-desktop.json`.

---

## Troubleshooting

**"Git is not installed or not on PATH"**
Install Git for Windows from <https://git-scm.com/download/win>, then restart the app.

**"Could not publish: ... rejected ... fetch first"**
Click **↻ Pull now**, resolve any conflict in Obsidian, then **📤 Publish Changes** again.

**"Auto-pull skipped — you have local changes"**
This is on purpose: the app won't rebase over your in-progress edits. Publish your changes
or revert them, and the next auto-pull tick will succeed.

**A new page I made doesn't appear on the site**
After publishing, the GitHub Action takes 1–2 minutes to rebuild and redeploy the site.
Refresh the live site after a couple of minutes.
