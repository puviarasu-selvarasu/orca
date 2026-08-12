// ============================================================
// JARVIS COMPONENT – Reusable Voice/Vision Interface
// ============================================================

document.addEventListener('alpine:init', () => {
    Alpine.data('jarvisComponent', (config = {}) => ({
        // ============================================
        // STATE
        // ============================================
        isRecording: false,
        isProcessing: false,
        isSpeaking: false,
        language: config.language || 'en',
        mediaRecorder: null,
        audioChunks: [],
        threadId: null,
        store: Alpine.store('chatEngine'),

        // ============================================
        // INIT (Automatically fetches thread)
        // ============================================
        async init() {
            this.store.currentWorkspaceId = null;
            this.store.workspaceType = 'jarvis';
            await this.getOrCreateThread();
            console.log('🎤 JARVIS Component Initialized. Thread:', this.threadId);
        },

        // ============================================
        // THREAD MANAGEMENT
        // ============================================
        async getOrCreateThread() {
            try {
                const response = await fetch('/api/jarvis/thread/', {
                    headers: { 'X-CSRFToken': this.store.getCsrfToken() }
                });
                const data = await response.json();
                if (data.id) {
                    this.threadId = data.id;
                }
            } catch (e) {
                console.error('❌ Failed to get JARVIS thread:', e);
            }
        },

        // ============================================
        // LANGUAGE TOGGLE
        // ============================================
        toggleLanguage() {
            this.language = this.language === 'en' ? 'ta' : 'en';
        },

        // ============================================
        // VOICE (STT)
        // ============================================
        async toggleRecording() {
            if (this.isRecording) {
                this.stopRecording();
            } else {
                this.startRecording();
            }
        },

        async startRecording() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                this.mediaRecorder = new MediaRecorder(stream);
                this.audioChunks = [];
                this.mediaRecorder.ondataavailable = (event) => {
                    if (event.data.size > 0) this.audioChunks.push(event.data);
                };
                this.mediaRecorder.onstop = async () => {
                    const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
                    await this.sendAudioToSTT(audioBlob);
                    stream.getTracks().forEach(track => track.stop());
                };
                this.mediaRecorder.start();
                this.isRecording = true;
            } catch (e) {
                alert('Microphone access denied.');
            }
        },

        stopRecording() {
            if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
                this.mediaRecorder.stop();
                this.isRecording = false;
            }
        },

        async sendAudioToSTT(audioBlob) {
            this.isProcessing = true;
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.wav');
            formData.append('language', this.language);

            try {
                const response = await fetch('/api/stt/', {
                    method: 'POST',
                    headers: { 'X-CSRFToken': this.store.getCsrfToken() },
                    body: formData
                });
                const data = await response.json();
                if (data.text) {
                    await this.processTextToSpeech(data.text);
                }
            } catch (e) {
                console.error('❌ STT error:', e);
            }
            this.isProcessing = false;
        },

        // ============================================
        // BRAIN (LLM)
        // ============================================
        async processTextToSpeech(text) {
            if (!this.threadId) {
                console.error('❌ No thread ID for JARVIS');
                return;
            }
            this.isProcessing = true;
            try {
                const response = await fetch(`/api/chat/${this.threadId}/stream/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.store.getCsrfToken()
                    },
                    body: JSON.stringify({ message: text })
                });

                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let fullText = '';
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
                                // Stream finished
                            } else {
                                fullText += data;
                            }
                        }
                    }
                }

                if (fullText) {
                    await this.speakText(fullText);
                }
            } catch (e) {
                console.error('❌ LLM error:', e);
            }
            this.isProcessing = false;
        },

        // ============================================
        // SPEECH (TTS)
        // ============================================
        async speakText(text) {
            this.isSpeaking = true;
            try {
                const response = await fetch(`/api/tts/?text=${encodeURIComponent(text)}&language=${this.language}`);
                const audioBlob = await response.blob();
                const audioUrl = URL.createObjectURL(audioBlob);
                const audio = new Audio(audioUrl);
                audio.onended = () => {
                    this.isSpeaking = false;
                };
                audio.play();
            } catch (e) {
                console.error('❌ TTS error:', e);
                this.isSpeaking = false;
            }
        },

        // ============================================
        // VISION (Physical)
        // ============================================
        async lookAround() {
            this.isProcessing = true;
            try {
                const response = await fetch('/api/vision/physical/', {
                    method: 'POST',
                    headers: { 'X-CSRFToken': this.store.getCsrfToken() }
                });
                const data = await response.json();
                if (data.description) {
                    await this.speakText(data.description);
                }
            } catch (e) {
                console.error('❌ Vision error:', e);
            }
            this.isProcessing = false;
        }
    }));
});