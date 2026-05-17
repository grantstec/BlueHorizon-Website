@echo off
REM ---------------------------------------------------------------------------
REM One-shot complete recovery + publish.
REM
REM Run this ONCE when you see "could not unlink ... BlueHorizonDesktop.exe"
REM or any other git error caused by a partially-failed publish.
REM
REM Why the desktop app can't recover from inside itself: the chain of broken
REM states involves overwriting the very .exe that's running. Windows refuses
REM to delete a running .exe, so the app can't fix the problem while it's
REM open. This script does the recovery while the .exe is closed.
REM
REM Steps:
REM   1. Kill the running BlueHorizonDesktop.exe so nothing's locked.
REM   2. Abort any half-finished rebase/merge.
REM   3. Delete stale refs (MERGE_AUTOSTASH etc.) that block future pulls.
REM   4. Untrack build artifacts that should never have been in git.
REM   5. Commit the .gitignore / .gitattributes / untracking changes.
REM   6. Pull from origin (now safe — .exe is closed).
REM   7. Push everything.
REM
REM After this finishes, reopen BlueHorizonDesktop.exe normally — it will
REM never hit this problem again because the .exe is no longer tracked
REM in git.
REM ---------------------------------------------------------------------------

setlocal
pushd "%~dp0\.."

echo.
echo === [1/7] Closing any running BlueHorizonDesktop.exe ===
taskkill /F /IM BlueHorizonDesktop.exe >nul 2>&1
REM Give Windows a moment to release the file handle
timeout /t 2 /nobreak >nul

echo.
echo === [2/7] Aborting any in-progress rebase / merge ===
git rebase --abort 2>nul
git merge --abort 2>nul

echo.
echo === [3/7] Clearing stale rebase state ===
git update-ref -d MERGE_AUTOSTASH 2>nul
git update-ref -d REBASE_HEAD 2>nul
git update-ref -d CHERRY_PICK_HEAD 2>nul
if exist ".git\rebase-apply" rmdir /S /Q ".git\rebase-apply" 2>nul
if exist ".git\rebase-merge" rmdir /S /Q ".git\rebase-merge" 2>nul
if exist ".git\MERGE_HEAD" del /F /Q ".git\MERGE_HEAD" 2>nul
if exist ".git\MERGE_MSG" del /F /Q ".git\MERGE_MSG" 2>nul

echo.
echo === [4/7] Untracking build artifacts ===
git rm -r --cached --ignore-unmatch desktop-app/dist 2>nul
git rm -r --cached --ignore-unmatch desktop-app/build 2>nul
git rm -r --cached --ignore-unmatch desktop-app/__pycache__ 2>nul
git rm -r --cached --ignore-unmatch desktop-app/.venv 2>nul

echo.
echo === [5/7] Staging all changes ===
git add -A
git status --short

echo.
echo === [6/7] Committing cleanup ===
git commit -m "Recover: untrack build artifacts and normalize line endings" 2>nul
REM If there was nothing to commit, that's fine — proceed.

echo.
echo === [7/7] Pulling from origin and pushing ===
git pull --rebase origin main
if errorlevel 1 (
    echo.
    echo Pull failed. Most common cause: merge conflicts on text files.
    echo Open the affected files, resolve the conflicts in your editor,
    echo save them, then run:    git rebase --continue
    echo And finally:            git push
    pause
    exit /b 1
)

git push
if errorlevel 1 (
    echo.
    echo Push failed. You can run `git push` manually from this folder
    echo to retry.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Recovery complete!
echo.
echo You can now reopen BlueHorizonDesktop.exe and use it normally.
echo Build artifacts are gitignored, so this problem won't recur.
echo ============================================================
echo.

popd
endlocal
pause
