# src/routes/api_routes.py
import datetime # Adicione esta importação para usar datetime.now()
from flask import Blueprint, request, jsonify, current_app
from src.s3_manager import list_s3_contents_by_prefix, list_all_s3_buckets, check_s3_object_exists, upload_to_s3 # Funções do S3
from src.orchestrator import run_b3_scraping_and_upload # Orquestrador para o scraping
from src.athena_service import execute_athena_query # Funções do Athena

api_bp = Blueprint('api_bp', __name__, url_prefix='/api')

@api_bp.route('/scrape_and_upload', methods=['POST'])
def scrape_trigger():
    """
    Endpoint da API para disparar o processo de raspagem de dados da B3
    e o upload do arquivo Parquet resultante para o S3.
    """
    print("Requisição para disparar raspagem recebida.")
    try:
        # A função run_b3_scraping_and_upload deve gerenciar a criação do cliente S3 internamente
        # ou receber o cliente S3 e o nome do bucket como argumentos.
        # Se ela já funciona, não precisamos passar nada extra aqui.
        success = run_b3_scraping_and_upload()
        if success:
            return jsonify({"status": "success", "message": "Raspagem e upload para S3 concluídos com sucesso!"})
        else:
            return jsonify({"status": "error", "message": "Falha na raspagem ou upload para S3. Verifique os logs do servidor."}), 500
    except Exception as e:
        current_app.logger.error(f"Erro no endpoint /api/scrape_and_upload: {e}", exc_info=True)
        return jsonify({"status": "error", "message": f"Erro interno do servidor: {str(e)}"}), 500

@api_bp.route('/list_buckets', methods=['GET'])
def api_list_buckets():
    """
    Endpoint da API para listar todos os buckets S3.
    """
    print("Requisição para listar buckets S3 recebida.")
    aws_region = current_app.config.get('AWS_DEFAULT_REGION')
    if not aws_region:
        current_app.logger.error("Erro: AWS_DEFAULT_REGION não configurada para listar buckets.")
        return jsonify({"error": "Região AWS não configurada."}), 500
    try:
        # Passando aws_region para a função list_all_s3_buckets, conforme seu código
        buckets = list_all_s3_buckets(aws_region)
        return jsonify({"buckets": buckets}), 200
    except Exception as e:
        current_app.logger.error(f"Erro no endpoint /api/list_buckets: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@api_bp.route('/list_s3_path', methods=['POST'])
def api_list_s3_path():
    """
    Endpoint da API para listar o conteúdo (prefixes e objetos) de um dado bucket e prefixo.
    Recebe 'bucket_name' e 'prefix' (opcional) no corpo da requisição JSON.
    """
    data = request.get_json()
    bucket_name = data.get('bucket_name')
    prefix = data.get('prefix', '')

    if not bucket_name:
        return jsonify({"error": "Nome do bucket é obrigatório."}), 400
    
    aws_region = current_app.config.get('AWS_DEFAULT_REGION')
    if not aws_region:
        current_app.logger.error("Erro: AWS_DEFAULT_REGION não configurada para listar conteúdo S3.")
        return jsonify({"error": "Região AWS não configurada."}), 500
    
    print(f"Requisição para listar conteúdo S3 para bucket: {bucket_name}, prefixo: {prefix}")
    try:
        # Passando aws_region para a função list_s3_contents_by_prefix
        contents = list_s3_contents_by_prefix(bucket_name, prefix, aws_region)
        return jsonify({"contents": contents}), 200
    except Exception as e:
        current_app.logger.error(f"Erro no endpoint /api/list_s3_path: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@api_bp.route('/athena_query', methods=['POST'])
def api_athena_query():
    """
    Endpoint da API para executar uma consulta Athena.
    Recebe 'query' (string SQL bruta) no corpo da requisição JSON.
    """
    data = request.get_json()
    raw_query = data.get('query')

    if not raw_query:
        return jsonify({"status": "error", "message": "A consulta SQL é obrigatória."}), 400

    try:
        print(f"Recebida consulta Athena: {raw_query}")
        # A função execute_athena_query deve obter as configs Athena do current_app.config internamente
        results = execute_athena_query(raw_query) 
        return jsonify({"status": "success", "results": results})
    except Exception as e:
        current_app.logger.error(f"Erro ao executar query Athena: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


## Nova Rota: `/verificar-dados-existentes`

@api_bp.route('/verificar-dados-existentes', methods=['GET'])
def verificar_dados_existentes():
    """
    Verifica se o arquivo do dia para os dados do pregão da B3 já existe no S3.
    Retorna JSON com 'exists' (boolean) e uma 'message'.
    """
    scraping_target_bucket = current_app.config.get('SCRAPING_TARGET_S3_BUCKET')
    aws_region = current_app.config.get('AWS_DEFAULT_REGION')

    if not scraping_target_bucket or not aws_region:
        current_app.logger.error("Erro de configuração: Bucket S3 ou Região AWS ausente.")
        return jsonify({"exists": False, "message": "Erro de configuração: Bucket S3 ou Região AWS ausente."}), 500

    # Pega a data atual do sistema (hoje)
    # datetime.datetime.now().date() é o correto para usar datetime do módulo datetime
    today = datetime.datetime.now().date() 
    year_str = today.strftime('%Y')
    month_str = today.strftime('%m')
    day_str = today.strftime('%d')
    date_str = today.strftime('%Y-%m-%d')

    # Nome do arquivo Parquet e estrutura de partição, conforme seu código
    file_name = f"ibovespa_{date_str}.parquet"
    expected_object_key = f"data/year={year_str}/month={month_str}/day={day_str}/{file_name}"

    print(f"Verificando existência do arquivo S3: s3://{scraping_target_bucket}/{expected_object_key} na região {aws_region}")

    try:
        # Chama a função do s3_manager para verificar a existência do objeto
        file_exists = check_s3_object_exists(scraping_target_bucket, expected_object_key, aws_region)
        
        if file_exists:
            print(f"Arquivo {expected_object_key} ENCONTRADO no S3.")
            return jsonify({"exists": True, "message": f"Dados para o pregão de {date_str} já existem no S3. Não é necessário raspar novamente."})
        else:
            print(f"Arquivo {expected_object_key} NÃO encontrado no S3.")
            return jsonify({"exists": False, "message": f"Dados para o pregão de {date_str} não encontrados no S3. Clique para iniciar a raspagem."})
    except Exception as e:
        current_app.logger.error(f"Erro ao verificar arquivo S3 no endpoint /api/verificar-dados-existentes: {e}", exc_info=True)
        return jsonify({"exists": False, "message": f"Erro interno ao verificar a existência do arquivo: {str(e)}"}), 500