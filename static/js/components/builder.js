// ============================================================
// O.R.C.A. BUILDER COMPONENT (Reusable)
// ============================================================

document.addEventListener('alpine:init', () => {
    Alpine.data('builder', () => ({
        // ============================================
        // STATE
        // ============================================
        buildPlan: null,
        buildResults: null,
        isBuilding: false,
        isAIPlanning: false,
        aiPlanTaskId: null,

        // ============================================
        // COMPUTED
        // ============================================
        get store() {
            return Alpine.store('chatEngine');
        },

        get messages() {
            return this.store.messages;
        },

        // ============================================
        // ACTIONS
        // ============================================

        // Instant Mock Plan
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

        // AI Plan (Background)
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

        // Execute Build Plan
        async executeBuildPlan() {
            if (!this.buildPlan) return;
            
            // Open unified modal (will be handled by modal component)
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

        // OCR Upload
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
});