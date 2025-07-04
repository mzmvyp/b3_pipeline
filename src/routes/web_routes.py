# src/routes/web_routes.py
from flask import Blueprint, render_template

web_bp = Blueprint('web_bp', __name__)

@web_bp.route('/')
def index():
    return render_template('index.html')

@web_bp.route('/s3_navigator')
def s3_navigator():
    return render_template('s3_navigator.html')

@web_bp.route('/athena_query') # NOVA ROTA AQUI
def athena_query_page():
    return render_template('athena_query.html')

@web_bp.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@web_bp.route('/analytics')
def analytics():
    return render_template('analytics.html')