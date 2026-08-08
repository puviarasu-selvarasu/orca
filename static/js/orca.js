// ============================================================
// O.R.C.A. - Threaded Chat Controller (v4.2 with Toast Notifications)
// ============================================================

function chatApp() {
    return {
        threads: [],
        currentThreadId: null,
        messages: [],
        inputMessage: '',
        isStreaming: false,
        isLoading: false,
        streamingContent: '',
        streamingComplete: false,

        // STATE (Builder)
        buildPlan: null,
        buildResults: null,
        isBuilding: false,

        // STATE (AI Builder)
        isAIPlanning: false,
        aiPlanTaskId: null,

        // STATE (Unified Modal)
        showModal: false,
        modalType: null,
        modalData: null,
        modalCallback: null,

        // ============================================
        // STATE (Toast Notifications - UI Polish)
        // ============================================
        toastVisible: false,
        toastIcon: '✅',
        toastTitle: '',
        toastMessage: '',
        toastTimeout: null,

        // ============================================
        // UNIFIED MODAL METHODS
        // ============================================
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
        },

        // ============================================
        // TOAST METHODS
        // ============================================
        showToast(icon, title, message, duration = 4000) {
            this.toastIcon = icon;
            this.toastTitle = title;
            this.toastMessage = message;
            this.toastVisible = true;
            clearTimeout(this.toastTimeout);
            this.toastTimeout = setTimeout(() => {
                this.toastVisible = false;
            }, duration);
        },

        // ============================================
        // INIT
        // ============================================
        initApp() {
            const threadsElement = document.getElementById('threads-data');
            if (threadsElement) {
                this.threads = JSON.parse(threadsElement.textContent);
            }
            const threadIdElement = document.getElementById('current-thread-id');
            if (threadIdElement) {
                this.currentThreadId = JSON.parse(threadIdElement.textContent);
            }
            const historyElement = document.getElementById('chat-history');
            if (historyElement) {
                this.messages = JSON.parse(historyElement.textContent);
            }
            setTimeout(() => this.scrollToBottom(), 150);
        },

        // ============================================
        // THREAD MANAGEMENT
        // ============================================
        async createNewThread() {
            try {
                const response = await fetch('/api/threads/create/', {
                    method: 'POST',
                    headers: { 'X-CSRFToken': this.getCsrfToken() }
                });
                const data = await response.json();
                this.threads = [{ id: data.id, title: data.title }, ...this.threads];
                this.switchThread(data.id);
            } catch (e) {
                alert('Failed to create new thread: ' + e.message);
            }
        },

        async switchThread(threadId) {
            if (threadId === this.currentThreadId) return;
            this.currentThreadId = threadId;
            await this.loadMessages(threadId);
            setTimeout(() => this.scrollToBottom(), 100);
        },

        deleteThread(threadId) {
            const thread = this.threads.find(t => t.id === threadId);
            if (thread) {
                this.openModal('delete', { threadId: thread.id, threadTitle: thread.title }, (data) => {
                    this.confirmDeleteThread(data.threadId);
                });
            }
        },

        async confirmDeleteThread(threadId) {
            try {
                await fetch(`/api/threads/${threadId}/delete/`, {
                    method: 'DELETE',
                    headers: { 'X-CSRFToken': this.getCsrfToken() }
                });
                this.threads = this.threads.filter(t => t.id !== threadId);
                if (this.threads.length > 0) {
                    this.switchThread(this.threads[0].id);
                } else {
                    this.createNewThread();
                }
            } catch (e) {
                alert('Failed to delete thread: ' + e.message);
            }
        },

        async loadMessages(threadId) {
            try {
                const response = await fetch(`/api/threads/${threadId}/messages/`);
                const data = await response.json();
                this.messages = data.messages || [];
                setTimeout(() => this.scrollToBottom(), 100);
            } catch (e) {
                console.error('Failed to load messages:', e);
            }
        },

        // ============================================
        // SEND MESSAGE
        // ============================================
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

            try {
                const response = await fetch(`/api/chat/${this.currentThreadId}/stream/`, {
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
                                setTimeout(() => this.scrollToBottom(), 100);
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
                this.threads = data.threads || [];
            } catch (e) {}
        },

        // ============================================
        // BUILDER MODE
        // ============================================
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
                        'X-CSRFToken': this.getCsrfToken()
                    },
                    body: JSON.stringify({ description: lastUserMsg.content })
                });
                const data = await response.json();
                if (data.status === 'success') {
                    this.buildPlan = data.plan;
                    this.buildResults = null;
                    if (data.is_mock) {
                        this.buildPlan._is_mock = true;
                    }
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
                        'X-CSRFToken': this.getCsrfToken()
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
            this.openModal('approve_build', { plan: this.buildPlan }, async (data) => {
                await this.confirmExecuteBuild(data.plan);
            });
        },

        async confirmExecuteBuild(plan) {
            this.isBuilding = true;
            try {
                const response = await fetch('/api/builder/execute/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCsrfToken()
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

        // ============================================
        // FILE UPLOAD + OCR (Phase 10) - with Toast
        // ============================================
        isUploading: false,

        async uploadRequirements(event) {
            const file = event.target.files[0];
            if (!file) return;

            this.isUploading = true;
            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await fetch('/api/builder/upload-requirements/', {
                    method: 'POST',
                    headers: { 'X-CSRFToken': this.getCsrfToken() },
                    body: formData
                });
                const data = await response.json();

                if (data.status === 'success') {
                    this.inputMessage = data.text;
                    let msg = `Extracted ${data.text.length} chars from ${data.filename}.`;
                    if (data.truncated) {
                        msg += ` ⚠️ Original was ${data.original_length} chars, truncated to fit context.`;
                    }
                    this.showToast('📎', 'OCR Complete', msg);
                } else {
                    this.showToast('❌', 'Upload Failed', data.error);
                }
            } catch (e) {
                this.showToast('❌', 'Upload Failed', e.message);
            }

            this.isUploading = false;
            event.target.value = '';
        },

        // ============================================
        // UTILITIES
        // ============================================
        scrollToBottom() {
            const el = document.querySelector('#chat-messages');
            if (el) {
                el.scrollTop = el.scrollHeight;
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
    };
}

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