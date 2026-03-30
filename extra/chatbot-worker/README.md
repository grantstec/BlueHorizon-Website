# Cloudflare Worker Setup For BlueHorizon Docs Chatbot

This worker keeps the chatbot free and live while hiding model config from the website frontend.

Important runtime note:
- The chatbot runs on Cloudflare's servers (edge), not on your laptop.
- Your laptop is only used to deploy updates.
- After deployment, the chatbot continues working even when your laptop is offline.

## 1) Install Wrangler

```bash
npm install -g wrangler
wrangler login
```

## 2) Deploy Worker

From this folder (`extra/chatbot-worker`):

```bash
wrangler deploy
```

This command uploads your worker to Cloudflare. It does not keep running on your computer.

After deploy, your endpoint is:

```text
https://<your-worker>.workers.dev/chat
```

## 3) Update The Website Chatbot Page

Open:
- `docs/resources/AI Website Editing Assistant.md`

Replace `data-endpoint` with your real worker URL.

## 4) Environment Variables

The included `wrangler.toml` already sets these defaults:
- `DOCS_INDEX_URL`: points to the generated docs index on GitHub Pages
- `SITE_BASE_URL`: base URL used for source and screenshot links
- `ALLOW_ORIGIN`: CORS origin control
- `WORKERS_AI_MODEL`: free Workers AI model name
- `IMAGE_BASE_URL`: raw GitHub docs base for screenshot links (prevents Jupyter Book image-path 404s)

## 5) Notes

- The docs index is generated during GitHub Actions deploy.
- If you change repository or site URL, update `DOCS_INDEX_URL` and `SITE_BASE_URL`.
- If you want branch preview support, set a separate worker var pointing to a branch preview index URL.
