from django.apps import AppConfig
import sys

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # Load LLM only when running the server (not during migrations or shell)
        if any(arg in sys.argv for arg in ['runserver', 'gunicorn']):
            try:
                from chat.llm_wrapper import load_llm
                load_llm()
            except Exception as e:
                print(f"⚠️ LLM failed to load at startup: {e}")
                print("   It will load on the first request instead.")