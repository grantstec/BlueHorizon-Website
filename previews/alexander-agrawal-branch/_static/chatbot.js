const QUICK_PROMPTS = [
  'How do I make a new page in Obsidian for this website?',
  'How do I add screenshots/images and make them render correctly?',
  'How do I commit and push changes with GitHub Desktop?',
  'How do I update my branch from main?',
  'How do I submit a pull request to main?'
];

function escapeHtml(str) {
  return String(str || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function makeAbsoluteUrl(relativeUrl) {
  try {
    return new URL(relativeUrl, window.location.origin + '/').toString();
  } catch (_) {
    return relativeUrl;
  }
}

function asList(items) {
  if (!items || items.length === 0) {
    return '';
  }
  return `<ul>${items.map(item => `<li>${item}</li>`).join('')}</ul>`;
}

function renderBotMessage(data) {
  const answer = escapeHtml(data.answer || 'No answer was returned.');

  const citationItems = (data.citations || []).map(citation => {
    const href = citation.url || '#';
    const label = escapeHtml(citation.label || href);
    return `<a href="${href}" target="_blank" rel="noopener noreferrer">${label}</a>`;
  });

  const imageCards = (data.images || []).map(image => {
    const href = image.url || '#';
    const alt = escapeHtml(image.alt || 'Reference image');
    return `
      <a class="bh-chatbot__thumb" href="${href}" target="_blank" rel="noopener noreferrer">
        <img src="${href}" alt="${alt}">
        <span>${alt}</span>
      </a>
    `;
  });

  const sourcesHtml = citationItems.length > 0
    ? `<div class="bh-chatbot__sources"><strong>Sources</strong>${asList(citationItems)}</div>`
    : '';

  const imagesHtml = imageCards.length > 0
    ? `<div class="bh-chatbot__images"><strong>Relevant screenshots</strong><div class="bh-chatbot__thumb-grid">${imageCards.join('')}</div></div>`
    : '';

  return `
    <div>${answer.replace(/\n/g, '<br>')}</div>
    <div class="bh-chatbot__meta">
      ${sourcesHtml}
      ${imagesHtml}
    </div>
  `;
}

function mountChatbot(container) {
  const endpoint = container.dataset.endpoint;
  if (!endpoint) {
    container.innerHTML = '<p>Chatbot endpoint is missing. Add data-endpoint on the chatbot container.</p>';
    return;
  }

  const normalizedEndpoint = makeAbsoluteUrl(endpoint);

  container.classList.add('bh-chatbot');
  container.innerHTML = `
    <div class="bh-chatbot__header">
      <p class="bh-chatbot__title">Website Editing Assistant</p>
      <p class="bh-chatbot__subtitle">Ask how to edit pages. Answers cite docs and screenshots.</p>
    </div>
    <div class="bh-chatbot__messages" id="bh-chatbot-messages"></div>
    <div class="bh-chatbot__quick" id="bh-chatbot-quick"></div>
    <form class="bh-chatbot__form" id="bh-chatbot-form">
      <input class="bh-chatbot__input" id="bh-chatbot-input" type="text" placeholder="Ask a question about editing the website" required>
      <button class="bh-chatbot__send" type="submit">Ask</button>
    </form>
    <div class="bh-chatbot__status" id="bh-chatbot-status">Ready</div>
  `;

  const messagesEl = container.querySelector('#bh-chatbot-messages');
  const quickEl = container.querySelector('#bh-chatbot-quick');
  const formEl = container.querySelector('#bh-chatbot-form');
  const inputEl = container.querySelector('#bh-chatbot-input');
  const statusEl = container.querySelector('#bh-chatbot-status');

  function pushMessage(html, fromUser) {
    const wrapper = document.createElement('div');
    wrapper.className = `bh-chatbot__msg ${fromUser ? 'bh-chatbot__msg--user' : 'bh-chatbot__msg--bot'}`;
    wrapper.innerHTML = html;
    messagesEl.appendChild(wrapper);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  pushMessage(
    'Ask about GitHub Desktop, Obsidian setup, creating pages, images, branch previews, or pull requests.',
    false
  );

  QUICK_PROMPTS.forEach(prompt => {
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = prompt;
    button.addEventListener('click', () => {
      inputEl.value = prompt;
      formEl.requestSubmit();
    });
    quickEl.appendChild(button);
  });

  async function ask(question) {
    statusEl.textContent = 'Thinking...';

    const payload = {
      question,
      mode: 'citations-and-images'
    };

    const response = await fetch(normalizedEndpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`Chatbot request failed with status ${response.status}`);
    }

    const data = await response.json();
    statusEl.textContent = 'Ready';
    return data;
  }

  formEl.addEventListener('submit', async event => {
    event.preventDefault();
    const question = (inputEl.value || '').trim();
    if (!question) {
      return;
    }

    pushMessage(escapeHtml(question), true);
    inputEl.value = '';

    try {
      const data = await ask(question);
      pushMessage(renderBotMessage(data), false);
    } catch (err) {
      statusEl.textContent = 'Error';
      pushMessage(
        `I could not reach the assistant right now. ${escapeHtml(err.message || 'Please try again.')}`,
        false
      );
    }
  });
}

const container = document.getElementById('bh-editing-chatbot');
if (container) {
  mountChatbot(container);
}
