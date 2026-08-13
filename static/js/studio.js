// ============================================================
// STUDIO COMPONENT – Dedicated Alpine Component
// ============================================================
document.addEventListener('alpine:init', () => {
    Alpine.data('studioComponent', (config = {}) => ({
        projectId: config.projectId || null,
        projectName: '',
        files: {},
        commands: [],
        messages: [],
        currentFile: null,
        fileContent: '',
        inputMessage: '',
        isLoading: false,
        isStreaming: false,
        streamingContent: '',
        streamingComplete: false,

        init() {
            if (this.projectId) {
                this.loadProject();
            }
        },

        async loadProject() {
            try {
                // ✅ FIX: prepend /studio/
                const response = await fetch(`/studio/api/project/${this.projectId}/`);
                const data = await response.json();
                this.projectName = data.name;
                this.files = data.files;
                this.commands = data.commands;
                this.messages = data.messages;
                // Select first file automatically
                const fileKeys = Object.keys(this.files);
                if (fileKeys.length > 0) {
                    this.openFile(fileKeys[0]);
                }
            } catch (e) {
                console.error('Failed to load project:', e);
            }
        },

        async openFile(path) {
            this.currentFile = path;
            try {
                // ✅ FIX: prepend /studio/
                const response = await fetch(`/studio/api/project/${this.projectId}/file/?path=${encodeURIComponent(path)}`);
                const data = await response.json();
                this.fileContent = data.content || '// Empty file';
            } catch (e) {
                this.fileContent = '// Error loading file';
            }
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

            try {
                // ✅ FIX: prepend /studio/
                const response = await fetch(`/studio/api/project/${this.projectId}/chat/stream/`, {
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
                            } else {
                                this.streamingContent += data;
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
    }));
});