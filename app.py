# app.py
from flask import Flask, render_template
from src.routes.web_routes import web_bp
from src.routes.api_routes import api_bp
from src.config import Config # Importa a classe de configuração

app = Flask(__name__)
app.config.from_object(Config) # Carrega as configurações da classe Config

# Registra os Blueprints
app.register_blueprint(web_bp)
app.register_blueprint(api_bp)

# Context processor para injetar variáveis globais nos templates,
# como o nome do bucket de scraping.
@app.context_processor
def inject_global_vars():
    return dict(
        SCRAPING_TARGET_S3_BUCKET=app.config.get('SCRAPING_TARGET_S3_BUCKET')
    )

if __name__ == '__main__':
    print("Iniciando aplicação Flask...")
    # Usa as configurações de debug e host da classe Config
    app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=5000)