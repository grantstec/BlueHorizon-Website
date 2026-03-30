const DEFAULT_MODEL = '@cf/meta/llama-3.1-8b-instruct';
const DEFAULT_TOP_K = 6;

function jsonResponse(body, status = 200, origin = '*') {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Access-Control-Allow-Origin': origin,
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
      'Cache-Control': 'no-store'
    }
  });
}

function normalize(text) {
  return String(text || '').toLowerCase();
}

function tokenize(text) {
  return normalize(text)
    .replace(/[^a-z0-9\s]/g, ' ')
    .split(/\s+/)
    .filter(Boolean);
}

function scoreChunk(chunk, questionTokens) {
  const haystack = normalize(`${chunk.title}\n${chunk.heading}\n${chunk.text}`);
  let score = 0;

  for (const token of questionTokens) {
    if (token.length < 2) {
      continue;
    }

    if (haystack.includes(token)) {
      score += 1;
    }

    if (normalize(chunk.heading).includes(token)) {
      score += 1;
    }
  }

  if (chunk.resourcePriority) {
    score += 2;
  }

  if (chunk.text.length > 300) {
    score += 0.5;
  }

  return score;
}

function uniqueBy(items, keyFn) {
  const seen = new Set();
  const output = [];

  for (const item of items) {
    const key = keyFn(item);
    if (seen.has(key)) {
      continue;
    }
    seen.add(key);
    output.push(item);
  }

  return output;
}

function safeBaseSite(base) {
  if (!base) {
    return '';
  }
  return String(base).replace(/\/+$/, '');
}

function encodePathSegments(pathLike) {
  return String(pathLike || '')
    .replace(/^\/+/, '')
    .split('/')
    .filter(Boolean)
    .map(segment => encodeURIComponent(segment))
    .join('/');
}

function makePublicUrl(base, relPath) {
  if (!relPath) {
    return null;
  }

  if (/^https?:/i.test(relPath)) {
    return relPath;
  }

  const normalized = String(relPath).replace(/^\/+/, '');
  return `${safeBaseSite(base)}/${normalized}`;
}

function makeImageUrl(image, env, siteBaseUrl) {
  const rawPath = image?.path || image?.url;
  if (!rawPath) {
    return null;
  }

  if (/^https?:/i.test(rawPath)) {
    return rawPath;
  }

  const encodedPath = encodePathSegments(rawPath);

  // Prefer raw GitHub docs path because Jupyter Book may relocate built image assets.
  const imageBaseUrl = env.IMAGE_BASE_URL || 'https://raw.githubusercontent.com/grantstec/BlueHorizon-Website/main/docs';
  if (imageBaseUrl) {
    return `${safeBaseSite(imageBaseUrl)}/${encodedPath}`;
  }

  return makePublicUrl(siteBaseUrl, encodedPath);
}

async function loadIndex(env) {
  const indexUrl = env.DOCS_INDEX_URL;
  if (!indexUrl) {
    throw new Error('DOCS_INDEX_URL environment variable is not set.');
  }

  const response = await fetch(indexUrl, {
    cf: {
      cacheTtl: 120,
      cacheEverything: true
    }
  });

  if (!response.ok) {
    throw new Error(`Index fetch failed: ${response.status}`);
  }

  return response.json();
}

function retrieveChunks(index, question, topK) {
  const tokens = tokenize(question);
  const scored = index.chunks
    .map(chunk => ({ chunk, score: scoreChunk(chunk, tokens) }))
    .filter(item => item.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, topK)
    .map(item => item.chunk);

  return scored;
}

function buildContext(chunks) {
  return chunks
    .map((chunk, idx) => {
      return [
        `Source ${idx + 1}`,
        `Title: ${chunk.title}`,
        `Heading: ${chunk.heading}`,
        `Path: ${chunk.sourceFile}`,
        `Anchor: ${chunk.anchor || ''}`,
        `Text: ${chunk.text}`
      ].join('\n');
    })
    .join('\n\n');
}

async function askModel(env, question, context) {
  const model = env.WORKERS_AI_MODEL || DEFAULT_MODEL;
  const response = await env.AI.run(model, {
    messages: [
      {
        role: 'system',
        content:
          'You answer questions about editing the BlueHorizon website. Only use provided context. Keep answers concise and procedural. If context is insufficient, say that and suggest the closest source topic.'
      },
      {
        role: 'user',
        content: `Question:\n${question}\n\nContext:\n${context}`
      }
    ],
    max_tokens: 650,
    temperature: 0.2
  });

  if (typeof response === 'string') {
    return response;
  }

  return response.response || response.result?.response || 'No model response was returned.';
}

function buildCitationsAndImages(chunks, siteBaseUrl, env) {
  const citations = uniqueBy(
    chunks.map(chunk => {
      const anchor = chunk.anchor ? `#${chunk.anchor}` : '';
      const url = makePublicUrl(siteBaseUrl, chunk.pageUrl) + anchor;
      return {
        label: `${chunk.title} -> ${chunk.heading}`,
        url
      };
    }),
    item => item.url
  );

  const images = uniqueBy(
    chunks.flatMap(chunk =>
      (chunk.images || []).map(image => ({
        alt: image.alt || `${chunk.title} image`,
        url: makeImageUrl(image, env, siteBaseUrl)
      }))
    ),
    item => item.url
  ).slice(0, 8);

  return { citations, images };
}

export default {
  async fetch(request, env) {
    const allowOrigin = env.ALLOW_ORIGIN || '*';

    if (request.method === 'OPTIONS') {
      return new Response(null, {
        status: 204,
        headers: {
          'Access-Control-Allow-Origin': allowOrigin,
          'Access-Control-Allow-Methods': 'POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type'
        }
      });
    }

    const url = new URL(request.url);
    if (url.pathname !== '/chat') {
      return jsonResponse({ error: 'Not found' }, 404, allowOrigin);
    }

    if (request.method !== 'POST') {
      return jsonResponse({ error: 'Method not allowed' }, 405, allowOrigin);
    }

    try {
      const body = await request.json();
      const question = String(body.question || '').trim();

      if (!question) {
        return jsonResponse({ error: 'Question is required.' }, 400, allowOrigin);
      }

      const index = await loadIndex(env);
      const chunks = retrieveChunks(index, question, DEFAULT_TOP_K);

      if (chunks.length === 0) {
        return jsonResponse(
          {
            answer: 'I could not find relevant guidance in the current docs. Try asking with terms like Obsidian, GitHub Desktop, branch, or pull request.',
            citations: [],
            images: []
          },
          200,
          allowOrigin
        );
      }

      const context = buildContext(chunks);
      const answer = await askModel(env, question, context);
      const siteBaseUrl = env.SITE_BASE_URL || 'https://grantstec.github.io/BlueHorizon-Website';
      const { citations, images } = buildCitationsAndImages(chunks, siteBaseUrl, env);

      return jsonResponse({ answer, citations, images }, 200, allowOrigin);
    } catch (err) {
      return jsonResponse(
        {
          error: 'Chat request failed.',
          details: err.message || String(err)
        },
        500,
        allowOrigin
      );
    }
  }
};
