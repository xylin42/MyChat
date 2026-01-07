CACHES = {
   'default': {
      'BACKEND': 'django.core.cache.backends.redis.RedisCache',
      'LOCATION': 'redis://localhost:6379',
      'OPTIONS': {
         # 'CLIENT_CLASS': 'django_redis.client.DefaultClient'
      }
   }
}

INSTALLED_APPS = [
   'daphne',
   'django_eventstream',
   'django_browser_reload',

   'django.contrib.admin',
   'django.contrib.auth',
   'django.contrib.contenttypes',
   'django.contrib.sessions',
   'django.contrib.messages',
   'django.contrib.staticfiles',

   'mychat',
]

MIDDLEWARE = [
   "django_browser_reload.middleware.BrowserReloadMiddleware",

   'django.contrib.sessions.middleware.SessionMiddleware',
   'django.contrib.auth.middleware.AuthenticationMiddleware',

   'mychat.middleware.LoginRequiredMiddleware',

   'django.middleware.csrf.CsrfViewMiddleware',
   'django.contrib.messages.middleware.MessageMiddleware'
]

from .conf.dj_iconify import * # NOQA

EVENTSTREAM_REDIS = {
   'host': 'localhost',
   'port': 6379,
   'db': 0,
}

USE_TZ = True
TIME_ZONE = 'Asia/Shanghai'

CSRF_TRUSTED_ORIGINS = [
   "http://localhost:8080",
   "http://127.0.0.1:8080",
   'http://frp.foxhank.top:31894',
   'http://192.168.31.149:8000'
]

ALLOWED_HOSTS = [
   '192.168.31.149',
   '127.0.0.1',
   'frp.foxhank.top'
]

CHANNEL_LAYERS = {
   'default': {
      'BACKEND': 'channels_redis.core.RedisChannelLayer',
      'CONFIG': {
         'hosts': [('127.0.0.1', 6379)],
      }
   }
}

ASGI_APPLICATION = 'mychat.asgi.application'

MEDIA_URL = '/media/'
MEDIA_ROOT = 'media/'
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
STATIC_URL = 'static/'
FORM_RENDERER = 'django.forms.renderers.Jinja2'
AUTH_USER_MODEL = 'mychat.User'
LOGIN_URL = '/login'
DEBUG = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

ROOT_URLCONF = 'mychat.urls'

DATABASE_ROUTERS = ['mychat.dbrouters.SimpleRouter']
DATABASES = {
   'default': {
      'ENGINE': 'django.db.backends.sqlite3',
      'NAME': 'dbs/mychat.sqlite3',
   },
   'contrib': {
      'ENGINE': 'django.db.backends.sqlite3',
      'NAME': 'dbs/contrib.sqlite3',
   }
}

USE_I18N = False

TEMPLATES = [
   {
      'BACKEND': 'django.template.backends.django.DjangoTemplates',
      'DIRS': [],
      'APP_DIRS': True,
      'OPTIONS': {
         'context_processors': [
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
         ],
         'builtins': [
            'mychat.templatetags.defaulttags',
         ]
      },
   },
]

SECRET_KEY = 'supersecret'
