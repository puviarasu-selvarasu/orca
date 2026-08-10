// ============================================================
// O.R.C.A. CHAT WIDGET (Reusable Component)
// ============================================================

document.addEventListener('alpine:init', () => {
    Alpine.data('chatWidget', (config = {}) => ({
        // ============================================
        // CONFIG
        // ============================================
        workspaceId: config.workspaceId || null,
        workspaceType: config.workspaceType || 'chat',
        title: config.title || 'O.R.C.A.',

        // ============================================
        // INIT
        // ============================================
        init() {
            // Get the core store
            const store = Alpine.store('chatEngine');
            
            // Set workspace context
            store.currentWorkspaceId = this.workspaceId;
            store.workspaceType = this.workspaceType;

            // If this is a project workspace, load project-specific messages
            if (this.workspaceType === 'project' && this.workspaceId) {
                this.loadProjectMessages(this.workspaceId);
            }

            // If this is the dashboard (chat), load dashboard messages
            if (this.workspaceType === 'chat' && !this.workspaceId) {
                // Messages are already loaded via the JSON script tags
                // Just scroll to bottom
                setTimeout(() => store.scrollToBottom(), 100);
            }

            // Listen for thread refresh events
            window.addEventListener('threads-refreshed', (e) => {
                // This will be handled by the dashboard component
                // For now, we just pass it through
                if (this.workspaceType === 'chat') {
                    this.$dispatch('threads-updated', e.detail);
                }
            });
        },

        // ============================================
        // ACTIONS
        // ============================================
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
        // COMPUTED (Getters)
        // ============================================
        get store() {
            return Alpine.store('chatEngine');
        },

        get messages() {
            return this.store.messages;
        },

        get inputMessage() {
            return this.store.inputMessage;
        },

        set inputMessage(value) {
            this.store.inputMessage = value;
        },

        get isLoading() {
            return this.store.isLoading;
        },

        get isStreaming() {
            return this.store.isStreaming;
        },

        get streamingContent() {
            return this.store.streamingContent;
        },

        get streamingComplete() {
            return this.store.streamingComplete;
        }
    }));
});