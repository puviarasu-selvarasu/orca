from django.apps import AppConfig
import sys

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        if 'runserver' in sys.argv or 'gunicorn' in sys.argv:
            # ============================================================
            # 1. LOAD THE LLM (Warm Boot)
            # ============================================================
            from chat.llm_wrapper import load_llm
            load_llm()

            # ============================================================
            # 2. START WATCHDOG (Auto-Ingestion - Sprint 2)
            # ============================================================
            try:
                from automation.watcher import start_watcher
                self.watcher = start_watcher()
            except Exception as e:
                print(f"⚠️ Failed to start watchdog: {e}")

            # ============================================================
            # 3. SPRINT 6: SCHEDULE PROMPT OPTIMIZATION (3 AM)
            # ============================================================
            try:
                from apscheduler.schedulers.background import BackgroundScheduler
                from self_improve.prompt_optimizer import optimize_prompts
                
                scheduler = BackgroundScheduler()
                scheduler.add_job(
                    optimize_prompts,
                    'cron',
                    hour=3,
                    minute=0,
                    id='prompt_optimization',
                    replace_existing=True
                )
                scheduler.start()
                print("🧠 Prompt optimizer scheduled for 3 AM daily.")
            except ImportError:
                print("⚠️ APScheduler not installed. Prompt optimization disabled.")
            except Exception as e:
                print(f"⚠️ Failed to start prompt optimizer: {e}")

            # ============================================================
            # 4. SPRINT 6: STARTUP CATCH-UP (Runs if 3 AM was missed)
            # ============================================================
            try:
                from self_improve.models import PromptVariant
                from datetime import date
                from self_improve.prompt_optimizer import optimize_prompts
                
                # Check if any variant has been tested today
                last_tested = PromptVariant.objects.first()
                if last_tested:
                    last_date = last_tested.created_at.date()
                    today = date.today()
                    if last_date < today:
                        print("🔄 Catching up: Running missed prompt optimization...")
                        optimize_prompts()
                    else:
                        print("✅ Prompt optimization already ran today.")
                else:
                    print("🔄 First run: Running prompt optimization...")
                    optimize_prompts()
            except Exception as e:
                print(f"⚠️ Startup optimization check failed: {e}")