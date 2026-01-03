import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration"""

    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production-MUST-BE-RANDOM'

    # Database - Build URI from individual environment variables
    @staticmethod
    def get_database_uri():
        """Construct database URI from environment variables"""
        user = os.environ.get('DB_USER', 'xxxx')
        password = os.environ.get('DB_PASSWORD', 'xxx')
        host = os.environ.get('DB_HOST', 'xxxx')
        port = os.environ.get('DB_PORT', '5432')
        db_name = os.environ.get('DB_NAME', 'xxxx')

        return f'postgresql://{user}:{password}@{host}:{port}/{db_name}'

    SQLALCHEMY_DATABASE_URI = get_database_uri.__func__()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # Hospital Information
    HOSPITAL_NAME_AR = os.environ.get('HOSPITAL_NAME_AR') or 'Hospital Name In Arabic Not Exist'
    HOSPITAL_NAME_EN = os.environ.get('HOSPITAL_NAME_EN') or 'Hospital Name In English Not Exist'
    HOSPITAL_ADDRESS_AR = os.environ.get('HOSPITAL_ADDRESS_AR') or 'Address In Arabic Not Exist'
    HOSPITAL_ADDRESS_EN = os.environ.get('HOSPITAL_ADDRESS_EN') or 'Address In English Not Exist'
    HOSPITAL_PHONE = os.environ.get('HOSPITAL_PHONE') or 'Phone Number Not Exist'
    HOSPITAL_EMAIL = os.environ.get('HOSPITAL_EMAIL') or 'Email Not Exist'

    # Currency Information
    CURRENCY_CODE = os.environ.get('CURRENCY_CODE') or 'No Currecy Code'
    CURRENCY_SYMBOL_AR = os.environ.get('CURRENCY_SYMBOL_AR') or 'No Currency Arabic Symbol'
    CURRENCY_SYMBOL_EN = os.environ.get('CURRENCY_SYMBOL_EN') or 'No Currency English Symbol'
    CURRENCY_NAME_AR = os.environ.get('CURRENCY_NAME_AR') or 'No Currency Arabic Name'
    CURRENCY_NAME_EN = os.environ.get('CURRENCY_NAME_EN') or 'No Currency English Name'

    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS

    # Pagination
    RECORDS_PER_PAGE = 20

    # File Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')

    # Flask-Login
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = False

    @staticmethod
    def init_app(app):
        """Initialize application configuration"""
        pass


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

    # Require HTTPS in production
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True

    # Database connection pooling
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }

    @staticmethod
    def init_app(app):
        """Validate production configuration"""
        secret_key = os.environ.get('SECRET_KEY')
        if not secret_key or secret_key == 'dev-secret-key-change-in-production-MUST-BE-RANDOM':
            raise ValueError(
                "SECRET_KEY environment variable must be set to a secure random value in production. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True

    @staticmethod
    def get_test_database_uri():
        """Construct test database URI from environment variables"""
        user = os.environ.get('DB_USER', 'hospital_user')
        password = os.environ.get('DB_PASSWORD', '123')
        host = os.environ.get('DB_HOST', 'localhost')
        port = os.environ.get('DB_PORT', '5432')
        db_name = os.environ.get('DB_TEST_NAME', 'hospital_test_db')

        return f'postgresql://{user}:{password}@{host}:{port}/{db_name}'

    SQLALCHEMY_DATABASE_URI = get_test_database_uri.__func__()
    WTF_CSRF_ENABLED = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
