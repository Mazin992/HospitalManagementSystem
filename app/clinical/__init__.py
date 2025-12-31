from flask import Blueprint

bp = Blueprint('clinical', __name__)

from app.clinical import routes