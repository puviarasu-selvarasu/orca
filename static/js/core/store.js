// ============================================================
// O.R.C.A. CORE STORE (Shared State + Logic)
// ============================================================

document.addEventListener('alpine:init', () => {
    Alpine.store('chatEngine', {
        // ============================================
        // STATE
        // ============================================
        messages: [],
        inputMessage: '',
        isLoading: false,
        isStreaming: false,
        streamingContent: '',
        streamingComplete: false,
        currentWorkspaceId: null,  // null = Dashboard, otherwise Project/Workspace ID
        workspaceType: 'chat',     // 'chat', 'project', 'finance', etc.

        // ============================================
        // COMPUTED (Getters)
        // ============================================
        get hasMessages() {
            return this.messages.length > 0;
        },

        // ============================================
        // ACTIONS (Core Logic)
        // ============================================

        // Send a message to the chat
        async sendMessage() {
            if (!this.inputMessage.trim() || this.isLoading) return;

            const msg = this.inputMessage.trim();
            this.inputMessage = '';
            this.isLoading = true;
            this.isStreaming = true;
            this.streamingContent = '';
            this.streamingComplete = false;

            // Add user message
            this.messages = [...this.messages, { role: 'user', content: msg }];
            this.scrollToBottom();

            // Build API endpoint based on workspace type
            let endpoint = `/api/chat/${this.currentWorkspaceId}/stream/`;
            if (this.workspaceType === 'project') {
                // For project workspace, we'll use a different endpoint
                endpoint = `/api/project/${this.currentWorkspaceId}/chat/stream/`;
            }

            try {
                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCsrfToken()
                    },
                    body: JSON.stringify({ message: msg })
                });

                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n');
                    buffer = lines.pop() || '';

                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const data = line.slice(6);
                            if (data === '[DONE]') {
                                const finalContent = this.streamingContent;
                                this.messages = [...this.messages, { role: 'assistant', content: finalContent }];
                                this.isStreaming = false;
                                this.streamingContent = '';
                                this.streamingComplete = true;
                                this.scrollToBottom();
                                this.refreshThreads();
                            } else {
                                this.streamingContent += data;
                                this.scrollToBottom();
                            }
                        }
                    }
                }
            } catch (e) {
                this.streamingContent = '⚠️ Error: ' + e.message;
                this.streamingComplete = true;
                this.isStreaming = false;
            }

            this.isLoading = false;
            this.isStreaming = false;
        },

        // Refresh threads list (for dashboard)
        async refreshThreads() {
            try {
                const response = await fetch('/api/threads/');
                const data = await response.json();
                // This will be handled by the dashboard component
                // We dispatch a custom event for the component to listen to
                window.dispatchEvent(new CustomEvent('threads-refreshed', { detail: data.threads }));
            } catch (e) {}
        },

        // ============================================
        // UTILITIES
        // ============================================
        scrollToBottom() {
            const el = document.querySelector('#chat-messages');
            if (el) {
                // Use requestAnimationFrame to ensure DOM is fully rendered
                requestAnimationFrame(() => {
                    el.scrollTop = el.scrollHeight;
                });
                // Also set it directly as a fallback
                setTimeout(() => {
                    el.scrollTop = el.scrollHeight;
                }, 50);
            }
        },

        getCsrfToken() {
            const name = 'csrftoken';
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }
    });
});