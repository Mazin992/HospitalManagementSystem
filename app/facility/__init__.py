from flask import Blueprint

bp = Blueprint('facility', __name__)

from app.facility import routes