from flask import Blueprint

bp = Blueprint('billing', __name__)

from app.billing import routes