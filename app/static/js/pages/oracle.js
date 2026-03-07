/* 
  ORACLE.JS
  AI Chat Interface — production: client_id, conversation_id, resume, error UX
*/

import { api, session } from '../app.js';
import { escapeHtml, safeMarkdown } from '../utils.js';

// Persist conversation_id for resume (session storage per tab)
const CONV_KEY = 'taxgod_oracle_conversation_id';

function getConversationId() {
    return sessionStorage.getItem(CONV_KEY) || null;
}
function setConversationId(id) {
    if (id) sessionStorage.setItem(CONV_KEY, id);
    else sessionStorage.removeItem(CONV_KEY);
}

export default {
    render() {
        return `
            <div class="oracle-container grid grid-2" style="height: calc(100vh - 140px); overflow: hidden;">
                
                <!-- Chat Column -->
                <div class="chat-column" style="display: flex; flex-direction: column; height: 100%;">
                    <!-- Chat History (Scroll) -->
                    <div id="chat-history" class="scroll-container" style="flex: 1; overflow-y: auto; margin-bottom: var(--spacing-md); display: flex; flex-direction: column; gap: var(--spacing-md);">
                        <!-- Welcome Message -->
                        <div class="message system">
                            <div class="message-avatar">🏛️</div>
                            <div class="message-content">
                                <div class="message-bubble">
                                    Greetings, mortal. I am the Oracle of Tax. Ask me of your burdens, and I shall consult the sacred laws.
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Input Area -->
                    <div class="chat-input-area card" style="padding: var(--spacing-md);">
                        <form id="chat-form" style="display: flex; gap: var(--spacing-md);">
                            <input type="text" id="chat-input" class="form-control" placeholder="Ask a tax question..." autocomplete="off">
                            <button type="submit" class="btn btn-primary">
                                <svg viewBox="0 0 24 24" style="width: 20px; height: 20px; fill: currentColor;"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
                                Consult
                            </button>
                        </form>
                        <div class="input-options" style="margin-top: var(--spacing-sm); display: flex; gap: var(--spacing-md); font-size: 12px; color: #666;">
                            <label><input type="checkbox" id="req-citations" checked> Require Citations</label>
                            <span id="model-badge" class="badge badge-gold" style="margin-left: auto;">Model: GPT-4o</span>
                        </div>
                    </div>
                </div>

                <!-- Citations Column (Sacred Texts) -->
                <div class="citations-column card" style="display: flex; flex-direction: column; height: 100%; background: #fffcf5;">
                    <div class="card-header">
                        <span class="card-title">Sacred Texts (Citations)</span>
                        <span class="badge badge-warning" id="citation-count">0 Sources</span>
                    </div>
                    <div id="citations-list" style="flex: 1; overflow-y: auto; padding-right: var(--spacing-sm);">
                        <div class="empty-state" style="text-align: center; color: #999; margin-top: 40px;">
                            <div style="font-size: 40px; margin-bottom: 10px;">📜</div>
                            <p>No scrolls consulted yet.</p>
                        </div>
                    </div>
                </div>

            </div>
        `;
    },

    async init() {
        const form = document.getElementById('chat-form');
        const input = document.getElementById('chat-input');
        const history = document.getElementById('chat-history');
        const citationsList = document.getElementById('citations-list');
        const citationCount = document.getElementById('citation-count');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const query = input.value.trim();
            if (!query) return;

            // Add User Message
            this.appendMessage('user', query);
            input.value = '';

            // Add Loading State
            const loadingId = this.appendLoading();
            
            // Scroll to bottom
            history.scrollTop = history.scrollHeight;

            try {
                const clientId = session.getClientId();
                const conversationId = getConversationId();
                const res = await api.post('/api/v1/chat/query', {
                    query,
                    client_id: clientId,
                    conversation_id: conversationId || undefined,
                    require_citations: document.getElementById('req-citations').checked
                });

                document.getElementById(loadingId)?.remove();

                if (res) {
                    this.appendMessage('ai', res.content, res.confidence);
                    this.updateCitations(res.citations || []);
                    if (res.conversation_id) {
                        setConversationId(res.conversation_id);
                    }
                    this.updateModelBadge(res.model_used);
                } else {
                    this.appendMessage('system', 'The Oracle is silent. (API Error)');
                }
            } catch (err) {
                console.error(err);
                document.getElementById(loadingId)?.remove();
                const msg = err && err.message ? err.message : 'A divine error occurred.';
                this.appendMessage('system', msg);
            }
            
            history.scrollTop = history.scrollHeight;
        });
    },

    appendMessage(role, text, confidence = null) {
        const history = document.getElementById('chat-history');
        const div = document.createElement('div');
        div.className = `message ${role}`;
        
        let avatar = '🏛️';
        if (role === 'user') avatar = '👤';
        if (role === 'ai') avatar = '🦉';

        let confidenceHtml = '';
        if (confidence) {
            const pct = Math.round(confidence * 100);
            let color = 'green';
            if (pct < 80) color = 'orange';
            if (pct < 50) color = 'red';
            confidenceHtml = `<div class="confidence-meter" style="font-size: 10px; margin-top: 5px; color: ${color};">Confidence: ${pct}%</div>`;
        }

        const formattedText = safeMarkdown(text);

        div.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                <div class="message-bubble">${formattedText}</div>
                ${confidenceHtml}
            </div>
        `;
        history.appendChild(div);
    },

    appendLoading() {
        const history = document.getElementById('chat-history');
        const id = 'loading-' + Date.now();
        const div = document.createElement('div');
        div.id = id;
        div.className = 'message ai loading';
        div.innerHTML = `
            <div class="message-avatar">🦉</div>
            <div class="message-content">
                <div class="message-bubble" style="font-style: italic; color: #666;">
                    Consulting the archives...
                </div>
            </div>
        `;
        history.appendChild(div);
        return id;
    },

    updateModelBadge(modelUsed) {
        const badge = document.getElementById('model-badge');
        if (badge && modelUsed) badge.textContent = `Model: ${modelUsed}`;
    },

    updateCitations(citations) {
        const list = document.getElementById('citations-list');
        const count = document.getElementById('citation-count');
        
        if (!citations || citations.length === 0) {
            count.textContent = '0 Sources';
            return;
        }

        count.textContent = `${citations.length} Sources`;
        list.innerHTML = '';

        citations.forEach(cit => {
            const item = document.createElement('div');
            item.className = 'citation-card';
            item.innerHTML = `
                <div class="citation-header">
                    <span class="citation-ref">${escapeHtml(cit.reference)}</span>
                    <span class="badge badge-gold">${escapeHtml(cit.type || 'IRC')}</span>
                </div>
                <div class="citation-title">${escapeHtml(cit.title || '')}</div>
                <div class="citation-summary">${escapeHtml(cit.summary || '')}</div>
            `;
            list.appendChild(item);
        });
    }
};
