// ============================================================
// O.R.C.A. MODAL COMPONENT (Reusable)
// ============================================================

document.addEventListener('alpine:init', () => {
    Alpine.data('modal', () => ({
        // ============================================
        // STATE
        // ============================================
        showModal: false,
        modalType: null,
        modalData: null,
        modalCallback: null,

        // ============================================
        // INIT
        // ============================================
        init() {
            // Listen for open-modal events
            this.$el.addEventListener('open-modal', (e) => {
                this.openModal(e.detail.type, e.detail.data, e.detail.callback);
            });
        },

        // ============================================
        // ACTIONS
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
        }
    }));
});