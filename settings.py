from bot_settings import DB_HOST, DB_NAME, DB_PASSWORD, DB_USER, DB_PORT
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': DB_HOST,
        'PORT': DB_PORT,
    }
}

INSTALLED_APPS = (
    'data',
    )

SECRET_KEY = "tz67m6wy(f2^gcr#j*g3zxeyow%(x4#^tqa8-wb(x97^2xpn)#"
TIME_ZONE = 'Asia/Yekaterinburg'
USE_TZ = True
