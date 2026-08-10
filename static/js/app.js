// ============================================================
// O.R.C.A. APP – Consolidated (Sprint 0, Step 2)
// ============================================================

document.addEventListener('alpine:init', () => {

    // ============================================================
    // 1. CORE STORE (Shared State)
    // ============================================================
    Alpine.store('chatEngine', {
        messages: [],
        inputMessage: '',
        isLoading: false,
        isStreaming: false,
        streamingContent: '',
        streamingComplete: false,
        currentWorkspaceId: null,
        workspaceType: 'chat',

        get hasMessages() {
            return this.messages.length > 0;
        },

        async sendMessage() {
            if (!this.inputMessage.trim() || this.isLoading) return;

            const msg = this.inputMessage.trim();
            this.inputMessage = '';
            this.isLoading = true;
            this.isStreaming = true;
            this.streamingContent = '';
            this.streamingComplete = false;

            this.messages = [...this.messages, { role: 'user', content: msg }];
            this.scrollToBottom();

            let endpoint = `/api/chat/${this.currentWorkspaceId}/stream/`;
            if (this.workspaceType === 'project') {
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

        async refreshThreads() {
            try {
                const response = await fetch('/api/threads/');
                const data = await response.json();
                window.dispatchEvent(new CustomEvent('threads-refreshed', { detail: data.threads }));
            } catch (e) {}
        },

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

    // ============================================================
    // 2. CHAT WIDGET COMPONENT
    // ============================================================
    Alpine.data('chatWidget', (config = {}) => ({
        workspaceId: config.workspaceId || null,
        workspaceType: config.workspaceType || 'chat',
        title: config.title || 'O.R.C.A.',

        init() {
            const store = Alpine.store('chatEngine');
            store.currentWorkspaceId = this.workspaceId;
            store.workspaceType = this.workspaceType;

            if (this.workspaceType === 'project' && this.workspaceId) {
                this.loadProjectMessages(this.workspaceId);
            }
            if (this.workspaceType === 'chat' && !this.workspaceId) {
                setTimeout(() => store.scrollToBottom(), 100);
            }

            window.addEventListener('threads-refreshed', (e) => {
                if (this.workspaceType === 'chat') {
                    this.$dispatch('threads-updated', e.detail);
                }
            });
        },

        async loadProjectMessages(projectId) {
            try {
                const response = await fetch(`/api/project/${projectId}/messages/`);
                const data = await response.json();
                const store = Alpine.store('chatEngine');
                store.messages = data.messages || [];
                setTimeout(() => store.scrollToBottom(), 100);
            } catch (e) {
                console.error('Failed to load project messages:', e);
            }
        },

        // ============================================
        // NEW: Expose sendMessage from the store
        // ============================================
        sendMessage() {
            this.store.sendMessage();
        },

        // ============================================
        // GETTERS (Computed properties)
        // ============================================
        get store() { return Alpine.store('chatEngine'); },
        get messages() { return this.store.messages; },
        get inputMessage() { return this.store.inputMessage; },
        set inputMessage(value) { this.store.inputMessage = value; },
        get isLoading() { return this.store.isLoading; },
        get isStreaming() { return this.store.isStreaming; },
        get streamingContent() { return this.store.streamingContent; },
        get streamingComplete() { return this.store.streamingComplete; },
        get hasMessages() { return this.store.hasMessages; }
    }));


    // ============================================================
    // 3. BUILDER COMPONENT
    // ============================================================
    Alpine.data('builder', () => ({
        buildPlan: null,
        buildResults: null,
        isBuilding: false,
        isAIPlanning: false,
        aiPlanTaskId: null,
        isUploading: false,

        get store() { return Alpine.store('chatEngine'); },
        get messages() { return this.store.messages; },

        async generateBuildPlan() {
            const lastUserMsg = this.messages.filter(m => m.role === 'user').pop();
            if (!lastUserMsg) {
                alert('Please send a message describing what you want to build first.');
                return;
            }

            this.isBuilding = true;
            try {
                const response = await fetch('/api/builder/preview/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.store.getCsrfToken()
                    },
                    body: JSON.stringify({ description: lastUserMsg.content })
                });
                const data = await response.json();
                if (data.status === 'success') {
                    this.buildPlan = data.plan;
                    this.buildResults = null;
                    if (data.is_mock) this.buildPlan._is_mock = true;
                } else {
                    alert('Failed to generate plan.');
                }
            } catch (e) {
                alert('Error: ' + e.message);
            }
            this.isBuilding = false;
        },

        async generateAIPlan() {
            const lastUserMsg = this.messages.filter(m => m.role === 'user').pop();
            if (!lastUserMsg) {
                alert('Please send a message describing what you want to build first.');
                return;
            }

            this.isAIPlanning = true;
            this.aiPlanTaskId = null;
            this.buildPlan = null;

            try {
                const response = await fetch('/api/builder/ai-plan/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.store.getCsrfToken()
                    },
                    body: JSON.stringify({ description: lastUserMsg.content })
                });
                const data = await response.json();
                if (data.status === 'started') {
                    this.aiPlanTaskId = data.task_id;
                    await this.pollAIPlan();
                } else {
                    alert('Failed to start AI plan generation.');
                    this.isAIPlanning = false;
                }
            } catch (e) {
                alert('Error: ' + e.message);
                this.isAIPlanning = false;
            }
        },

        async pollAIPlan() {
            if (!this.aiPlanTaskId) return;
            try {
                const response = await fetch(`/api/builder/ai-plan/status/${this.aiPlanTaskId}/`);
                const data = await response.json();
                if (data.status === 'completed') {
                    this.buildPlan = data.result;
                    this.buildPlan._is_mock = false;
                    this.isAIPlanning = false;
                    this.aiPlanTaskId = null;
                } else if (data.status === 'failed') {
                    alert('AI plan generation failed: ' + data.error);
                    this.isAIPlanning = false;
                    this.aiPlanTaskId = null;
                } else {
                    setTimeout(() => this.pollAIPlan(), 2000);
                }
            } catch (e) {
                console.error('Polling error:', e);
                setTimeout(() => this.pollAIPlan(), 2000);
            }
        },

        async executeBuildPlan() {
            if (!this.buildPlan) return;
            this.$dispatch('open-modal', {
                type: 'approve_build',
                data: { plan: this.buildPlan },
                callback: async (result) => {
                    await this.confirmExecuteBuild(result.plan);
                }
            });
        },

        async confirmExecuteBuild(plan) {
            this.isBuilding = true;
            try {
                const response = await fetch('/api/builder/execute/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.store.getCsrfToken()
                    },
                    body: JSON.stringify({ plan: plan })
                });
                const data = await response.json();
                if (data.status === 'completed') {
                    this.buildResults = data.results.join('\n');
                    this.buildPlan = null;
                } else {
                    alert('Execution failed.');
                }
            } catch (e) {
                alert('Error: ' + e.message);
            }
            this.isBuilding = false;
        },

        async uploadRequirements(event) {
            const file = event.target.files[0];
            if (!file) return;

            this.isUploading = true;
            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await fetch('/api/builder/upload-requirements/', {
                    method: 'POST',
                    headers: { 'X-CSRFToken': this.store.getCsrfToken() },
                    body: formData
                });
                const data = await response.json();

                if (data.status === 'success') {
                    this.store.inputMessage = data.text;
                    let msg = `Extracted ${data.text.length} chars from ${data.filename}.`;
                    if (data.truncated) {
                        msg += ` ⚠️ Original was ${data.original_length} chars, truncated to fit context.`;
                    }
                    this.$dispatch('show-toast', { icon: '📎', title: 'OCR Complete', message: msg });
                } else {
                    this.$dispatch('show-toast', { icon: '❌', title: 'Upload Failed', message: data.error });
                }
            } catch (e) {
                this.$dispatch('show-toast', { icon: '❌', title: 'Upload Failed', message: e.message });
            }

            this.isUploading = false;
            event.target.value = '';
        }
    }));

    // ============================================================
    // 4. MODAL COMPONENT
    // ============================================================
    Alpine.data('modal', () => ({
        showModal: false,
        modalType: null,
        modalData: null,
        modalCallback: null,

        init() {
            // Listen for open-modal events on window (works across all components)
            window.addEventListener('open-modal', (e) => {
                this.openModal(e.detail.type, e.detail.data, e.detail.callback);
            });
        },

        openModal(type, data, callback) {
            this.modalType = type;
            this.modalData = data;
            this.modalCallback = callback;
            this.showModal = true;
        },

        closeModal() {
            this.showModal = false;
            this.modalType = null;
            this.modalData = null;
            this.modalCallback = null;
        },

        confirmModal() {
            if (this.modalCallback) {
                this.modalCallback(this.modalData);
            }
            this.closeModal();
        }
    }));

}); // end alpine:init

// ============================================================
// SYSTEM METRICS (Independent)
// ============================================================
async function fetchMetrics() {
    try {
        const res = await fetch('/metrics/');
        const data = await res.json();
        const cpuFill = document.getElementById('cpu-fill');
        const ramFill = document.getElementById('ram-fill');
        const cpuText = document.getElementById('cpu-text');
        const ramText = document.getElementById('ram-text');

        if (cpuFill) {
            cpuFill.style.width = data.cpu + '%';
            cpuFill.className = 'metric-bar-fill' + (data.cpu > 80 ? ' danger' : data.cpu > 60 ? ' warning' : '');
        }
        if (cpuText) cpuText.textContent = data.cpu + '%';
        if (ramFill) {
            ramFill.style.width = data.ram + '%';
            ramFill.className = 'metric-bar-fill' + (data.ram > 80 ? ' danger' : data.ram > 60 ? ' warning' : '');
        }
        if (ramText) ramText.textContent = data.ram + '%';
    } catch (e) {}
}

setInterval(fetchMetrics, 2000);
fetchMetrics();