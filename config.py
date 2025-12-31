import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration"""

    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production-MUST-BE-RANDOM'

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'postgresql://hospital_user:123@localhost/hospital_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # Currency Configuration
    CURRENCY = 'SDG'
    CURRENCY_SYMBOL = 'ج.س'  # جنيه سوداني
    CURRENCY_NAME_AR = 'جنيه سوداني'

    # Hospital Information (can be overridden in environment)
    HOSPITAL_NAME = os.environ.get('HOSPITAL_NAME') or 'مستشفى السلام العام'
    HOSPITAL_NAME_EN = os.environ.get('HOSPITAL_NAME_EN') or 'Al-Salam General Hospital'
    HOSPITAL_ADDRESS = os.environ.get('HOSPITAL_ADDRESS') or 'الخرطوم، السودان'
    HOSPITAL_PHONE = os.environ.get('HOSPITAL_PHONE') or '+249 123 456 789'
    HOSPITAL_EMAIL = os.environ.get('HOSPITAL_EMAIL') or 'info@hospital.sd'

    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS

    # Pagination
    RECORDS_PER_PAGE = 20

    # File Upload (for future features)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')

    # Flask-Login
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = False  # Set to True in production

    @staticmethod
    def init_app(app):
        """Initialize application configuration"""
        pass


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True  # Log SQL queries
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
        # Only check SECRET_KEY when production config is actually used
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
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'postgresql://hospital_user:123@localhost/hospital_test_db'
    WTF_CSRF_ENABLED = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}