from django.apps import AppConfig
import sys

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # ============================================================
        # 1. LOAD THE LLM (Warm Boot - Existing Functionality)
        # ============================================================
        if 'runserver' in sys.argv or 'gunicorn' in sys.argv:
            # ============================================================
            # 2. START THE WATCHDOG (Auto-Ingestion - Sprint 2 Addition)
            # ============================================================
            try:
                from chat.llm_wrapper import load_llm
                load_llm()

                from automation.watcher import start_watcher
                self.watcher = start_watcher()
            except ImportError:
                print("⚠️ Watchdog not available. Skipping auto-ingest.")
            except Exception as e:
                print(f"⚠️ Failed to start watchdog: {e}")