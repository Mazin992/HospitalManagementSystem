from flask import Blueprint

bp = Blueprint('appointments', __name__)

from app.appointments import routes