from flask import Blueprint

bp = Blueprint('patients', __name__)

from app.patients import routes