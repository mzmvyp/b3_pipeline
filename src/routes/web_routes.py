# src/routes/web_routes.py
from flask import Blueprint, render_template

web_bp = Blueprint('web_bp', __name__)

@web_bp.route('/')
def index():
    return render_template('index.html')

@web_bp.route('/s3_navigator')
def s3_navigator():
    # Certifique-se de passar o S3_BUCKET_NAME se ele for necessário no template s3_navigator.html
    # Como não temos acesso direto às variáveis de ambiente aqui,
    # se o bucket não estiver sendo passado de app.py, você pode ter que importá-lo ou defini-lo aqui.
    # Por enquanto, vou assumir que ele já é acessível no template via Flask-Config ou context_processor
    # Se der erro de S3_BUCKET_NAME no template, avise-me.
    return render_template('s3_navigator.html')

@web_bp.route('/athena_query') # NOVA ROTA AQUI
def athena_query_page():
    return render_template('athena_query.html')