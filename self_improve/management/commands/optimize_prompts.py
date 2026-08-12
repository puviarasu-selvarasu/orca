from django.core.management.base import BaseCommand
from self_improve.prompt_optimizer import optimize_prompts

class Command(BaseCommand):
    help = 'Run the prompt optimization loop (Sprint 6)'

    def handle(self, *args, **options):
        self.stdout.write("🧠 Starting prompt optimization...")
        try:
            best = optimize_prompts()
            if best:
                self.stdout.write(self.style.SUCCESS(f"🏆 Best prompt: {best.name} (score: {best.score:.2f})"))
            else:
                self.stdout.write(self.style.WARNING("⚠️ No prompt variants found."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Optimization failed: {e}"))