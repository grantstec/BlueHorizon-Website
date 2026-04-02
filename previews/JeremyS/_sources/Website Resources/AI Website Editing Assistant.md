# AI Website Editing Assistant

Use this assistant for quick answers about editing this website with Obsidian and GitHub Desktop.

It is grounded in this documentation set and returns:
- Step-by-step guidance
- Source page links
- Relevant screenshots from the docs

## Ask The Assistant

<link rel="stylesheet" href="../_static/chatbot.css">

<div
  id="bh-editing-chatbot"
  data-endpoint="https://bluehorizon-docs-chatbot.stecgrant89.workers.dev/chat"
></div>

<script type="module" src="../_static/chatbot.js"></script>

## Setup Notes For Maintainers

1. Deploy the Cloudflare Worker using the repo file at `extra/chatbot-worker/README.md`.
2. Replace `data-endpoint` above with your real worker URL.
3. Keep docs pages and screenshots up to date. The index is rebuilt automatically during CI deploys.

## What It Can Answer Well

- New page creation in Obsidian
- New section and MAIN page setup
- Image/screenshot setup and naming
- GitHub Desktop commit/push flow
- Branch previews and pull requests

## Fallback

If the chatbot is unavailable, use these guides directly:
- [Obsidian Setup and Website Editing](Obsidian%20Setup%20and%20Website%20Editing.md)
- [GitHub Setup and Resources](GitHub%20Setup%20and%20Resources.md)
