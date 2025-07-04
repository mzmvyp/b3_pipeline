# src/orchestrator.py
from datetime import datetime
from flask import current_app # Import current_app to access app.config
from src.b3_extractor import fetch_b3_downloaded_csv_content
from src.b3_data_processor import parse_and_clean_csv_data
from src.s3_manager import upload_to_s3, check_s3_object_exists # Importa a nova função de verificação

def run_b3_scraping_and_upload():
    """
    Função principal que orquestra a raspagem dos dados da B3,
    o processamento e o upload para o S3.
    """
    print("Executando o processo completo de raspagem e upload para S3...")
    execution_date = datetime.now() # Esta é a data de *execução* do script.

    # Obter o bucket de scraping e a região da configuração da aplicação
    scraping_target_bucket = current_app.config.get('SCRAPING_TARGET_S3_BUCKET')
    aws_region = current_app.config.get('AWS_DEFAULT_REGION')

    if not scraping_target_bucket:
        print("Erro: SCRAPING_TARGET_S3_BUCKET não configurado em app.config.")
        return False
    if not aws_region:
        print("Erro: AWS_DEFAULT_REGION não configurada em app.config.")
        return False

    # --- LÓGICA DE VERIFICAÇÃO DE DUPLICAÇÃO INICIAL (ANTES DO DOWNLOAD) ---
    # Assumimos que o scraping sempre busca o dado do *dia atual* (execution_date).
    # Se o scraping puder buscar datas históricas, esta lógica precisaria ser adaptada
    # para aceitar um parâmetro de data.
    data_do_pregao_para_verificacao = execution_date.date() # Pega apenas a data (YYYY-MM-DD)

    # Componentes da data para construir o caminho particionado do S3
    year_str = data_do_pregao_para_verificacao.strftime('%Y')
    month_str = data_do_pregao_para_verificacao.strftime('%m')
    day_str = data_do_pregao_para_verificacao.strftime('%d')
    date_str = data_do_pregao_para_verificacao.strftime('%Y-%m-%d') # Para o nome do arquivo

    # Constrói o nome do arquivo final no S3
    file_name = f"ibovespa_{date_str}.parquet"
    # Constrói o caminho completo do objeto no S3, incluindo as partições
    expected_object_key = f"data/year={year_str}/month={month_str}/day={day_str}/{file_name}"

    print(f"Verificando existência do arquivo S3 para o pregão de {date_str} em: s3://{scraping_target_bucket}/{expected_object_key}")

    # Verifica se o arquivo já existe no S3 antes de qualquer download/processamento
    if check_s3_object_exists(scraping_target_bucket, expected_object_key, aws_region):
        print(f"Dados para o pregão de {date_str} já existem no S3. Download e processamento ignorados.")
        return True # Retorna True pois o objetivo foi alcançado (dado existe)
    # --- FIM DA LÓGICA DE VERIFICAÇÃO ANTECIPADA ---

    # Se o arquivo não existe no S3, procede com o download e processamento
    # 1. Extração: Baixa o conteúdo CSV bruto
    csv_content = fetch_b3_downloaded_csv_content()
    
    if csv_content:
        # 2. Processamento: Limpa e transforma o CSV em DataFrame
        # A 'execution_date' é passada para o processador para metadados se necessário
        processed_df = parse_and_clean_csv_data(csv_content, execution_date)
        
        if not processed_df.empty:
            # Revalida a 'data_do_pregao' do DataFrame para garantir que é do tipo correto
            # e que o DF não está vazio antes de tentar acessar 'iloc[0]'
            if 'data_do_pregao' in processed_df.columns and not processed_df.empty:
                data_do_pregao_do_df = processed_df['data_do_pregao'].iloc[0]
                
                # O upload agora usará a data extraída do DF, que deve ser a mesma da verificação inicial
                print(f"Arquivo para o pregão de {date_str} não encontrado no S3. Realizando upload...")
                return upload_to_s3(processed_df, scraping_target_bucket, aws_region, data_do_pregao_do_df)
            else:
                print("DataFrame processado não contém 'data_do_pregao' ou está vazio. Upload cancelado.")
                return False
        else:
            print("DataFrame processado está vazio, upload para S3 cancelado.")
    else:
        print("Conteúdo CSV não pôde ser extraído, processo de raspagem abortado.")
    
    return False

if __name__ == '__main__':
    try:
        from flask import Flask
        from src.config import Config
        temp_app = Flask(__name__)
        temp_app.config.from_object(Config)

        with temp_app.app_context():
            print("--- Testando src/orchestrator.py diretamente com contexto simulado ---")
            print("\nExecutando o fluxo completo de raspagem e upload:")
            success = run_b3_scraping_and_upload()
            if success:
                print("Fluxo completo concluído com sucesso!")
            else:
                print("Fluxo completo falhou.")

            print("\n--- Teste de src/orchestrator.py concluído ---")

    except RuntimeError as e:
        print(f"Não foi possível rodar o bloco __main__ diretamente sem contexto Flask: {e}")
        print("Para testar, rode 'flask run' na raiz do seu projeto.")