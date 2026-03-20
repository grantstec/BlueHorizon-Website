const fs = require('fs');
const yaml = require('js-yaml');
const path = require('path');

const DOCS_DIR = path.resolve('docs');
const TOC_PATH = path.join(DOCS_DIR, '_toc.yml');

const PART_CAPTION_OVERRIDES = {
  team: 'Team Information',
  subteams: 'Subteams',
  past_years: 'Past Years',
  resources: 'Resources'
};

const TOP_LEVEL_ORDER = ['team', 'subteams', 'past_years', 'resources'];

function toPosixPath(p) {
  return p.split(path.sep).join('/');
}

function stripMdExtension(relPath) {
  return relPath.replace(/\.md$/i, '');
}

function isMarkdownFile(name) {
  return name.toLowerCase().endsWith('.md');
}

function isMainName(fileStem) {
  return /^main(\s|$)/i.test(fileStem);
}

function compareNames(a, b) {
  const aMain = isMainName(a);
  const bMain = isMainName(b);
  if (aMain !== bMain) {
    return aMain ? -1 : 1;
  }
  return a.localeCompare(b, undefined, { numeric: true, sensitivity: 'base' });
}

function toCaption(dirName) {
  if (PART_CAPTION_OVERRIDES[dirName]) {
    return PART_CAPTION_OVERRIDES[dirName];
  }

  return dirName
    .split(/[_\-\s]+/)
    .filter(Boolean)
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

function shouldSkipDir(name) {
  const lower = name.toLowerCase();
  return lower.startsWith('.') || lower === '_build';
}

function scanFolder(absDir, relDir = '') {
  const entries = fs.readdirSync(absDir, { withFileTypes: true });
  const files = [];
  const children = [];

  for (const entry of entries) {
    const absPath = path.join(absDir, entry.name);
    const relPath = relDir ? path.join(relDir, entry.name) : entry.name;

    if (entry.isDirectory()) {
      if (shouldSkipDir(entry.name)) {
        continue;
      }

      const child = scanFolder(absPath, relPath);
      if (child.hasContent) {
        children.push(child);
      }
      continue;
    }

    if (!entry.isFile()) {
      continue;
    }

    if (!isMarkdownFile(entry.name)) {
      continue;
    }

    if (entry.name.startsWith('_')) {
      continue;
    }

    const relNoExt = stripMdExtension(toPosixPath(relPath));
    const stem = path.basename(entry.name, '.md');
    files.push({ stem, relNoExt });
  }

  files.sort((a, b) => compareNames(a.stem, b.stem));
  children.sort((a, b) => a.name.localeCompare(b.name, undefined, { sensitivity: 'base' }));

  return {
    name: path.basename(absDir),
    relDir: toPosixPath(relDir),
    files,
    children,
    hasContent: files.length > 0 || children.length > 0
  };
}

function getFolderMain(node) {
  const mainCandidates = node.files.filter(file => isMainName(file.stem));
  if (mainCandidates.length !== 1) {
    return null;
  }
  return mainCandidates[0];
}

function buildEntriesForNode(node, excludedFiles = new Set()) {
  const entries = [];

  for (const file of node.files) {
    if (excludedFiles.has(file.relNoExt)) {
      continue;
    }
    entries.push({ file: file.relNoExt });
  }

  for (const child of node.children) {
    const childMainEntry = buildMainEntry(child);
    if (childMainEntry) {
      entries.push(childMainEntry);
      continue;
    }
    entries.push(...buildEntriesForNode(child));
  }

  return entries;
}

function buildMainEntry(node) {
  const mainFile = getFolderMain(node);
  if (!mainFile) {
    return null;
  }

  const excluded = new Set([mainFile.relNoExt]);
  const sections = buildEntriesForNode(node, excluded);
  const entry = { file: mainFile.relNoExt };

  if (sections.length > 0) {
    entry.sections = sections;
  }

  return entry;
}

function buildPartChapters(topFolderNode) {
  const mainEntry = buildMainEntry(topFolderNode);
  if (mainEntry) {
    return [mainEntry];
  }
  return buildEntriesForNode(topFolderNode);
}

function topFolderSort(a, b) {
  const aIdx = TOP_LEVEL_ORDER.indexOf(a.name);
  const bIdx = TOP_LEVEL_ORDER.indexOf(b.name);

  if (aIdx !== -1 && bIdx !== -1) {
    return aIdx - bIdx;
  }
  if (aIdx !== -1) {
    return -1;
  }
  if (bIdx !== -1) {
    return 1;
  }
  return a.name.localeCompare(b.name, undefined, { sensitivity: 'base' });
}

function buildToc() {
  const rootNode = scanFolder(DOCS_DIR, '');
  const introFile = rootNode.files.find(file => file.relNoExt === 'intro');

  const root = introFile ? 'intro' : (rootNode.files[0] ? rootNode.files[0].relNoExt : 'intro');

  const parts = [];

  const topFolders = [...rootNode.children].sort(topFolderSort);
  for (const folderNode of topFolders) {
    const chapters = buildPartChapters(folderNode);
    if (chapters.length === 0) {
      continue;
    }

    parts.push({
      caption: toCaption(folderNode.name),
      chapters
    });
  }

  const topLevelLooseFiles = rootNode.files
    .filter(file => file.relNoExt !== root)
    .map(file => ({ file: file.relNoExt }));

  if (topLevelLooseFiles.length > 0) {
    parts.push({
      caption: 'Pages',
      chapters: topLevelLooseFiles
    });
  }

  return {
    format: 'jb-book',
    root,
    parts
  };
}

try {
  if (!fs.existsSync(DOCS_DIR)) {
    throw new Error(`Missing docs directory: ${DOCS_DIR}`);
  }

  const toc = buildToc();
  const tocYaml = yaml.dump(toc, {
    lineWidth: -1,
    noCompatMode: true,
    sortKeys: false
  });

  fs.writeFileSync(TOC_PATH, tocYaml, 'utf8');
  console.log(`✅ Rebuilt ${toPosixPath(path.relative(process.cwd(), TOC_PATH))} from docs folder structure.`);
} catch (err) {
  console.error('❌ ERROR updating TOC:', err.message || err);
  process.exit(1);
}
