const REPO_OWNER = 'grantstec';
const REPO_NAME = 'BlueHorizon-Website';

function parsePreviewBranchSlug(pathname) {
  const match = pathname.match(/\/previews\/([^/]+)/i);
  if (!match) {
    return '';
  }
  return decodeURIComponent(match[1]);
}

function byId(id) {
  return document.getElementById(id);
}

function fillLinks(branch) {
  const clean = (branch || '').trim();

  const prLink = byId('bh-pr-link');
  const runSingleLink = byId('bh-run-single-link');
  const runAllLink = byId('bh-run-all-link');
  const deployAllPreviewsLink = byId('bh-deploy-all-previews-link');
  const branchValue = byId('bh-branch-value');
  const note = byId('bh-tool-note');

  const encoded = encodeURIComponent(clean);
  const compareUrl = `https://github.com/${REPO_OWNER}/${REPO_NAME}/compare/main...${encoded}?expand=1`;
  const singleWorkflowUrl = `https://github.com/${REPO_OWNER}/${REPO_NAME}/actions/workflows/merge-main-into-branch.yml`;
  const allWorkflowUrl = `https://github.com/${REPO_OWNER}/${REPO_NAME}/actions/workflows/merge-main-into-all-branches.yml`;
  const deployAllPreviewsWorkflowUrl = `https://github.com/${REPO_OWNER}/${REPO_NAME}/actions/workflows/deploy-all-branch-previews.yml`;

  prLink.href = compareUrl;
  prLink.textContent = clean ? `Open PR from ${clean} to main` : 'Open PR to main (set branch first)';

  runSingleLink.href = singleWorkflowUrl;
  runAllLink.href = allWorkflowUrl;
  if (deployAllPreviewsLink) {
    deployAllPreviewsLink.href = deployAllPreviewsWorkflowUrl;
  }

  branchValue.textContent = clean || 'not detected';

  note.textContent = clean
    ? `Branch detected: ${clean}. For update workflow, choose Run workflow and set target_branch=${clean}.`
    : 'Could not detect preview branch from this URL. Enter branch name manually below.';
}

function initTools() {
  const branchInput = byId('bh-branch-input');
  const setBranchButton = byId('bh-set-branch');
  const copyBranchButton = byId('bh-copy-branch');

  const guessed = parsePreviewBranchSlug(window.location.pathname);
  branchInput.value = guessed;
  fillLinks(guessed);

  setBranchButton.addEventListener('click', () => {
    fillLinks(branchInput.value);
  });

  copyBranchButton.addEventListener('click', async () => {
    const text = (branchInput.value || '').trim();
    if (!text) {
      return;
    }

    try {
      await navigator.clipboard.writeText(text);
      copyBranchButton.textContent = 'Copied';
      setTimeout(() => {
        copyBranchButton.textContent = 'Copy branch';
      }, 1200);
    } catch (_) {
      copyBranchButton.textContent = 'Copy failed';
      setTimeout(() => {
        copyBranchButton.textContent = 'Copy branch';
      }, 1200);
    }
  });
}

initTools();
