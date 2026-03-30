const fs = require('fs');
const path = require('path');

const DOCS_DIR = path.resolve('docs');
const OUTPUT_PATH = path.join(DOCS_DIR, '_static', 'chatbot-docs-index.json');

function toPosixPath(p) {
  return p.split(path.sep).join('/');
}

function encodePathSegments(relPath) {
  return relPath
    .split('/')
    .map(segment => encodeURIComponent(segment))
    .join('/');
}

function slugifyHeading(text) {
  return String(text || '')
    .trim()
    .toLowerCase()
    .replace(/<[^>]*>/g, '')
    .replace(/[^a-z0-9\s\-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
}

function shouldSkipDir(name) {
  const lower = name.toLowerCase();
  return lower.startsWith('.') || lower === '_build';
}

function isMarkdownFile(name) {
  return name.toLowerCase().endsWith('.md') && !name.startsWith('_');
}

function findMarkdownFiles(absDir, relDir = '') {
  const entries = fs.readdirSync(absDir, { withFileTypes: true });
  const files = [];

  for (const entry of entries) {
    const absPath = path.join(absDir, entry.name);
    const relPath = relDir ? path.join(relDir, entry.name) : entry.name;

    if (entry.isDirectory()) {
      if (shouldSkipDir(entry.name)) {
        continue;
      }
      files.push(...findMarkdownFiles(absPath, relPath));
      continue;
    }

    if (entry.isFile() && isMarkdownFile(entry.name)) {
      files.push({
        absPath,
        relPath: toPosixPath(relPath)
      });
    }
  }

  return files;
}

function parseImageLinks(line) {
  const images = [];
  const regex = /!\[([^\]]*)\]\(([^)]+)\)/g;
  let match;

  while ((match = regex.exec(line)) !== null) {
    images.push({
      alt: (match[1] || '').trim(),
      target: (match[2] || '').trim()
    });
  }

  return images;
}

function resolveAssetPath(mdRelPath, target) {
  if (!target) {
    return null;
  }

  const cleaned = target.split('#')[0].trim();
  if (!cleaned) {
    return null;
  }

  if (/^(https?:|data:|mailto:)/i.test(cleaned)) {
    return cleaned;
  }

  if (cleaned.startsWith('/')) {
    return cleaned.replace(/^\/+/, '');
  }

  const baseDir = path.posix.dirname(mdRelPath);
  const resolved = path.posix.normalize(path.posix.join(baseDir, cleaned));

  if (resolved.startsWith('..')) {
    return null;
  }

  return resolved;
}

function sectionToChunk(section, pageMeta, chunkId) {
  const text = section.lines.join('\n').trim();
  if (!text || text.length < 32) {
    return null;
  }

  return {
    id: `${pageMeta.sourceFile}::${chunkId}`,
    title: pageMeta.title,
    heading: section.heading,
    anchor: section.anchor,
    text,
    sourceFile: pageMeta.sourceFile,
    pageUrl: pageMeta.pageUrl,
    resourcePriority: pageMeta.sourceFile.toLowerCase().startsWith('resources/'),
    images: section.images
  };
}

function buildChunksFromMarkdown(mdRelPath, content) {
  const lines = content.split(/\r?\n/);
  const sourceFile = mdRelPath;
  const pageUrl = encodePathSegments(mdRelPath.replace(/\.md$/i, '.html'));

  const firstHeadingLine = lines.find(line => /^#\s+/.test(line));
  const pageTitle = firstHeadingLine ? firstHeadingLine.replace(/^#\s+/, '').trim() : path.posix.basename(mdRelPath, '.md');

  const pageMeta = {
    title: pageTitle,
    sourceFile,
    pageUrl
  };

  const sections = [];
  let current = {
    heading: pageTitle,
    anchor: slugifyHeading(pageTitle),
    lines: [],
    images: []
  };

  for (const rawLine of lines) {
    const line = rawLine || '';
    const headingMatch = /^(#{1,6})\s+(.+?)\s*$/.exec(line);

    if (headingMatch) {
      sections.push(current);
      const headingText = headingMatch[2].trim();
      current = {
        heading: headingText,
        anchor: slugifyHeading(headingText),
        lines: [],
        images: []
      };
      continue;
    }

    const imageLinks = parseImageLinks(line);
    if (imageLinks.length > 0) {
      for (const image of imageLinks) {
        const resolved = resolveAssetPath(mdRelPath, image.target);
        if (!resolved) {
          continue;
        }

        current.images.push({
          alt: image.alt || 'Reference image',
          path: resolved,
          url: encodePathSegments(resolved)
        });
      }
    }

    const cleanedLine = line
      .replace(/!\[[^\]]*\]\([^)]+\)/g, ' ')
      .replace(/`{1,3}/g, '')
      .trim();

    if (cleanedLine) {
      current.lines.push(cleanedLine);
    }
  }

  sections.push(current);

  let chunkCounter = 0;
  const chunks = [];
  for (const section of sections) {
    const chunk = sectionToChunk(section, pageMeta, chunkCounter);
    if (chunk) {
      chunks.push(chunk);
      chunkCounter += 1;
    }
  }

  return chunks;
}

function buildIndex() {
  if (!fs.existsSync(DOCS_DIR)) {
    throw new Error(`Missing docs directory: ${DOCS_DIR}`);
  }

  const files = findMarkdownFiles(DOCS_DIR)
    .filter(item => item.relPath !== '_toc.yml' && item.relPath !== '_config.yml');

  const allChunks = [];
  for (const file of files) {
    const content = fs.readFileSync(file.absPath, 'utf8');
    const chunks = buildChunksFromMarkdown(file.relPath, content);
    allChunks.push(...chunks);
  }

  return {
    generatedAt: new Date().toISOString(),
    version: 1,
    sourceCount: files.length,
    chunkCount: allChunks.length,
    chunks: allChunks
  };
}

try {
  const index = buildIndex();
  fs.mkdirSync(path.dirname(OUTPUT_PATH), { recursive: true });
  fs.writeFileSync(OUTPUT_PATH, JSON.stringify(index, null, 2), 'utf8');

  console.log(
    `Built chatbot docs index: ${toPosixPath(path.relative(process.cwd(), OUTPUT_PATH))} ` +
      `(${index.chunkCount} chunks from ${index.sourceCount} markdown files).`
  );
} catch (err) {
  console.error('ERROR building chatbot docs index:', err.message || err);
  process.exit(1);
}
