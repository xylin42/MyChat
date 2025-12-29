MEDIA_URL = '/media/'
MEDIA_ROOT = 'media/'
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
STATIC_URL = 'static/'
FORM_RENDERER = 'django.forms.renderers.Jinja2'
AUTH_USER_MODEL = 'mychat.User'
LOGIN_URL = '/login'
DEBUG = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

INSTALLED_APPS = [
   'django.contrib.admin',
   'django.contrib.auth',
   'django.contrib.contenttypes',
   'django.contrib.sessions',
   'django.contrib.messages',
   'django.contrib.staticfiles',
   'mychat',
]

MIDDLEWARE = [
   'django.contrib.sessions.middleware.SessionMiddleware',
   'django.contrib.auth.middleware.AuthenticationMiddleware',
   'mychat.middleware.LoginRequiredMiddleware',
   'django.middleware.csrf.CsrfViewMiddleware',
   'django.contrib.messages.middleware.MessageMiddleware'
]

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
      },
   },
]

SECRET_KEY = 'supersecret'
