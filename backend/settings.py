import os
from pathlib import Path
import environ

# ============================================================================
# 1. ABSOLUTE PATHS (Prevents Windows File-Locking)
# ============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent  # Points to C:\ORCA
DATA_DIR = BASE_DIR / 'data'
MODELS_DIR = BASE_DIR / 'models'

# ============================================================================
# 2. ENVIRONMENT VARIABLES (Secrets Out of GitHub)
# ============================================================================
env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

# ============================================================================
# 3. SECURITY & DEBUG
# ============================================================================
SECRET_KEY = env('SECRET_KEY')
DEBUG = env.bool('DEBUG', default=False)  # FORCE FALSE ON RENDER
ALLOWED_HOSTS = ['*']  # Cloudflare/Render handle routing
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'

# ============================================================================
# 4. DATABASE (Absolute Path)
# ============================================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': DATA_DIR / 'db.sqlite3',
    }
}

# ============================================================================
# 5. INSTALLED APPS (Our Custom Modules)
# ============================================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # O.R.C.A. Custom Apps
    'core.apps.CoreConfig',
    'accounts.apps.AccountsConfig',
    'chat.apps.ChatConfig',
    'rag.apps.RagConfig',
    'sandbox.apps.SandboxConfig',
    'automation.apps.AutomationConfig',
    'oracle.apps.OracleConfig',
    'voice.apps.VoiceConfig',
    'self_improve.apps.SelfImproveConfig',
    #'django_apscheduler',  # We will install this later
]

# ============================================================================
# 6. MIDDLEWARE (With Global Login Lock)
# ============================================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'accounts.decorators.GlobalLoginRequiredMiddleware', # CUSTOM LOCK
    'django.contrib.messages.middleware.MessageMiddleware',
]

ROOT_URLCONF = 'backend.urls'

# ============================================================================
# 7. TEMPLATES
# ============================================================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'

# ============================================================================
# 8. STATIC FILES
# ============================================================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ============================================================================
# 9. DEFAULT AUTO FIELD
# ============================================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================================================
# 10. O.R.C.A. CUSTOM CONFIGURATION
# ============================================================================
GEMINI_API_KEY = env('GEMINI_API_KEY', default='')
LOCAL_MODE = env.bool('LOCAL_MODE', default=True)  # True on PC, False on Render

# Local LLM Paths (will be used in Phase 3)
LLM_MODEL_PATH = MODELS_DIR / 'qwen2.5-1.5b-instruct-q4_k_m.gguf'
# DRAFT_MODEL_PATH = MODELS_DIR / 'tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf'
LLM_CONFIG = {
    'n_ctx': 1024,
    'n_batch': 256,
    'n_threads': 2,
    'n_gpu_layers': 0,
}

CHROMA_PERSIST_DIR = DATA_DIR / 'chroma_db'

LOGOUT_REDIRECT_URL = '/accounts/login/'
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'