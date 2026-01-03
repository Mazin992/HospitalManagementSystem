# app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config

db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'يرجى تسجيل الدخول للوصول إلى هذه الصفحة.'
    login_manager.login_message_category = 'warning'

    # Register blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    from app.patients import bp as patients_bp
    app.register_blueprint(patients_bp, url_prefix='/patients')
    from app.appointments import bp as appointments_bp
    app.register_blueprint(appointments_bp, url_prefix='/appointments')
    from app.clinical import bp as clinical_bp
    app.register_blueprint(clinical_bp, url_prefix='/clinical')
    from app.facility import bp as facility_bp
    app.register_blueprint(facility_bp, url_prefix='/facility')
    from app.billing import bp as billing_bp
    app.register_blueprint(billing_bp, url_prefix='/billing')
    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    from app.reports import bp as reports_bp
    app.register_blueprint(reports_bp, url_prefix='/reports')


    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    # Add main routes (dashboard, etc.)
    from app import main
    app.register_blueprint(main.bp)


    # Template context processors
    from datetime import date, datetime


    @app.context_processor
    def inject_utilities():
        return {
            'date': date,
            'now': datetime.now
        }

    @app.context_processor
    def inject_global_vars():
        return {
            'hospital_info': {
                'name_ar': app.config['HOSPITAL_NAME_AR'],
                'name_en': app.config['HOSPITAL_NAME_EN'],
                'address_ar': app.config['HOSPITAL_ADDRESS_AR'],
                'address_en': app.config['HOSPITAL_ADDRESS_EN'],
                'phone': app.config['HOSPITAL_PHONE'],
                'email': app.config['HOSPITAL_EMAIL']
            },
            'currency': {
                'code': app.config['CURRENCY_CODE'],
                'symbol_ar': app.config['CURRENCY_SYMBOL_AR'],
                'symbol_en': app.config['CURRENCY_SYMBOL_EN'],
                'name_ar': app.config['CURRENCY_NAME_AR'],
                'name_en': app.config['CURRENCY_NAME_EN']
            }
        }


    return app
