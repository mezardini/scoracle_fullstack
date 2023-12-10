from scoracle.settings import *
import environ
env = environ.Env()
environ.Env.read_env()

SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['scoracle.onrender.com', '127.0.0.1']

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# _psycopg2
