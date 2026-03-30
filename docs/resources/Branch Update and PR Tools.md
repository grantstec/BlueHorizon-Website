# Branch Update and PR Tools

Use this page for quick GitHub actions while reviewing your preview website.

## Current Branch Helper

<div style="border:1px solid #d8dee9; border-radius:10px; padding:14px; background:#f8fbff;">
  <p><strong>Detected/Selected branch:</strong> <span id="bh-branch-value">loading...</span></p>
  <p id="bh-tool-note">Detecting preview branch...</p>

  <div style="display:flex; gap:8px; flex-wrap:wrap; margin:8px 0 12px;">
    <input id="bh-branch-input" type="text" placeholder="your-branch-name" style="padding:8px; min-width:260px; border:1px solid #b9c6df; border-radius:6px;">
    <button id="bh-set-branch" type="button" style="padding:8px 12px; border:1px solid #95a7ca; border-radius:6px; background:#fff; cursor:pointer;">Use branch</button>
    <button id="bh-copy-branch" type="button" style="padding:8px 12px; border:1px solid #95a7ca; border-radius:6px; background:#fff; cursor:pointer;">Copy branch</button>
  </div>

  <div style="display:flex; gap:10px; flex-wrap:wrap;">
    <a id="bh-pr-link" href="#" target="_blank" rel="noopener noreferrer" style="display:inline-block; padding:8px 12px; border-radius:6px; text-decoration:none; background:#0e4c99; color:#fff;">Open PR to main</a>
    <a id="bh-run-single-link" href="#" target="_blank" rel="noopener noreferrer" style="display:inline-block; padding:8px 12px; border-radius:6px; text-decoration:none; background:#ffffff; color:#1f2d45; border:1px solid #95a7ca;">Run update for one branch</a>
    <a id="bh-run-all-link" href="#" target="_blank" rel="noopener noreferrer" style="display:inline-block; padding:8px 12px; border-radius:6px; text-decoration:none; background:#ffffff; color:#1f2d45; border:1px solid #95a7ca;">Run update for all branches</a>
  </div>
</div>

<script type="module" src="../_static/branch-tools.js"></script>

## How The Buttons Work

- Open PR to main: Opens GitHub compare page with your branch prefilled.
- Run update for one branch: Opens GitHub Actions workflow to merge main into a target branch.
- Run update for all branches: Opens GitHub Actions workflow that attempts to merge main into every non-main branch.

## Important Notes

- GitHub login is required for these write actions.
- Merge conflicts cannot be auto-resolved and will be reported in workflow summary.
- This page is safe for preview users because it does not store tokens in the website.
