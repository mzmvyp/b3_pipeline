# src/orchestrator.py - Versão Atualizada para Selenium
from datetime import datetime
import logging
from flask import current_app # Import current_app to access app.config

# Importações atualizadas para o novo sistema Selenium
from src.b3_extractor import extrair_dados_ibovespa_selenium
from src.b3_data_processor import processar_dados_ibovespa_selenium
from src.s3_manager import upload_to_s3, check_s3_object_exists

# Configurar logging para o orchestrator
logger = logging.getLogger(__name__)

def run_b3_scraping_and_upload():
    """
    Função principal que orquestra a raspagem dos dados da B3 via Selenium,
    o processamento avançado e o upload para o S3.
    
    Versão atualizada que usa:
    - Selenium para extração (ao invés de download de CSV)
    - Processamento aprimorado com validações
    - Mesma lógica de verificação S3 e upload
    
    Returns:
        bool: True se bem-sucedido, False caso contrário
    """
    logger.info("=" * 60)
    logger.info("🚀 INICIANDO PROCESSO COMPLETO - SELENIUM + S3")
    logger.info("=" * 60)
    
    execution_date = datetime.now() # Data de execução do script
    
    try:
        # Obter configurações da aplicação Flask
        scraping_target_bucket = current_app.config.get('SCRAPING_TARGET_S3_BUCKET')
        aws_region = current_app.config.get('AWS_DEFAULT_REGION')
        
        # Validar configurações obrigatórias
        if not scraping_target_bucket:
            logger.error("❌ Erro: SCRAPING_TARGET_S3_BUCKET não configurado em app.config.")
            return False
            
        if not aws_region:
            logger.error("❌ Erro: AWS_DEFAULT_REGION não configurada em app.config.")
            return False
        
        logger.info(f"📊 Configurações:")
        logger.info(f"   🪣 Bucket S3: {scraping_target_bucket}")
        logger.info(f"   🌍 Região AWS: {aws_region}")
        
        # --- LÓGICA DE VERIFICAÇÃO DE DUPLICAÇÃO INICIAL (ANTES DA EXTRAÇÃO) ---
        # Assumimos que o scraping sempre busca o dado do *dia atual* (execution_date)
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
        
        logger.info(f"🔍 Verificando arquivo S3 para pregão de {date_str}:")
        logger.info(f"   📍 Caminho: s3://{scraping_target_bucket}/{expected_object_key}")
        
        # Verifica se o arquivo já existe no S3 antes de qualquer extração/processamento
        if check_s3_object_exists(scraping_target_bucket, expected_object_key, aws_region):
            logger.info(f"✅ Dados para o pregão de {date_str} já existem no S3.")
            logger.info("⏭️ Extração e processamento ignorados.")
            return True # Retorna True pois o objetivo foi alcançado (dado existe)
        
        logger.info(f"📄 Arquivo não encontrado no S3. Prosseguindo com extração...")
        # --- FIM DA LÓGICA DE VERIFICAÇÃO ANTECIPADA ---
        
        # 1. EXTRAÇÃO VIA SELENIUM
        logger.info("🤖 Iniciando extração de dados via Selenium...")
        
        try:
            df_bruto = extrair_dados_ibovespa_selenium()
            
            if df_bruto.empty:
                logger.error("❌ Nenhum dado foi extraído via Selenium")
                return False
                
            logger.info(f"✅ Extração concluída: {len(df_bruto)} registros brutos")
            
        except Exception as e:
            logger.error(f"❌ Erro durante extração Selenium: {e}")
            return False
        
        # 2. PROCESSAMENTO AVANÇADO
        logger.info("⚙️ Iniciando processamento avançado dos dados...")
        
        try:
            df_processado, relatorio_qualidade = processar_dados_ibovespa_selenium(
                df_bruto, 
                execution_date
            )
            
            if df_processado.empty:
                logger.error("❌ DataFrame processado está vazio")
                if 'erro' in relatorio_qualidade:
                    logger.error(f"   Erro no processamento: {relatorio_qualidade['erro']}")
                return False
            
            logger.info(f"✅ Processamento concluído: {len(df_processado)} registros válidos")
            
            # Log do relatório de qualidade
            if relatorio_qualidade.get('validacao_passou', False):
                logger.info("✅ Validação de qualidade: PASSOU")
            else:
                logger.warning("⚠️ Validação de qualidade: ALERTAS ENCONTRADOS")
            
            if relatorio_qualidade.get('alertas'):
                for alerta in relatorio_qualidade['alertas']:
                    logger.warning(f"   ⚠️ {alerta}")
            
            # Log de métricas importantes
            if 'metricas' in relatorio_qualidade:
                metricas = relatorio_qualidade['metricas']
                participacao_total = metricas.get('participacao_total', 0)
                logger.info(f"📊 Participação total: {participacao_total:.2f}%")
                
                if participacao_total < 95 or participacao_total > 105:
                    logger.warning(f"⚠️ Participação total fora do esperado: {participacao_total:.2f}%")
            
        except Exception as e:
            logger.error(f"❌ Erro durante processamento: {e}")
            return False
        
        # 3. VERIFICAÇÃO FINAL E UPLOAD PARA S3
        logger.info("☁️ Preparando upload para S3...")
        
        # Validar se o DataFrame processado tem a coluna de data
        if 'data_pregao' not in df_processado.columns or df_processado.empty:
            logger.error("❌ DataFrame processado não contém 'data_pregao' ou está vazio")
            return False
        
        # Extrair a data do pregão do DataFrame processado
        data_do_pregao_do_df = df_processado['data_pregao'].iloc[0]
        
        logger.info(f"📅 Data do pregão extraída: {data_do_pregao_do_df}")
        logger.info(f"📦 Registros para upload: {len(df_processado)}")
        
        # Realizar o upload usando a mesma função S3 existente
        logger.info("🚀 Iniciando upload para S3...")
        
        upload_success = upload_to_s3(
            df_processado, 
            scraping_target_bucket, 
            aws_region, 
            data_do_pregao_do_df
        )
        
        if upload_success:
            logger.info("✅ Upload para S3 concluído com sucesso!")
            logger.info("=" * 60)
            logger.info("🎉 PROCESSO COMPLETO FINALIZADO COM SUCESSO!")
            logger.info("=" * 60)
            return True
        else:
            logger.error("❌ Falha no upload para S3")
            return False
    
    except Exception as e:
        logger.error(f"❌ Erro crítico no orchestrator: {e}")
        logger.exception("Detalhes completos do erro:")
        return False

def run_b3_scraping_and_upload_with_retry(max_retries=3, retry_delay=300):
    """
    Versão com retry automático do processo principal.
    
    Args:
        max_retries (int): Número máximo de tentativas
        retry_delay (int): Delay entre tentativas em segundos
        
    Returns:
        bool: True se bem-sucedido, False caso contrário
    """
    import time
    
    for tentativa in range(1, max_retries + 1):
        logger.info(f"🔄 Tentativa {tentativa}/{max_retries}")
        
        try:
            sucesso = run_b3_scraping_and_upload()
            
            if sucesso:
                logger.info(f"✅ Sucesso na tentativa {tentativa}")
                return True
            else:
                if tentativa < max_retries:
                    logger.warning(f"⚠️ Tentativa {tentativa} falhou. Aguardando {retry_delay}s...")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"❌ Todas as {max_retries} tentativas falharam")
                    
        except Exception as e:
            logger.error(f"❌ Erro na tentativa {tentativa}: {e}")
            if tentativa < max_retries:
                logger.warning(f"⚠️ Aguardando {retry_delay}s antes da próxima tentativa...")
                time.sleep(retry_delay)
    
    return False

def run_b3_scraping_with_detailed_report():
    """
    Versão que retorna um relatório detalhado da execução.
    
    Returns:
        dict: Relatório completo da execução
    """
    start_time = datetime.now()
    
    relatorio = {
        'timestamp_inicio': start_time.isoformat(),
        'timestamp_fim': None,
        'duracao_segundos': None,
        'status': 'iniciado',
        'etapas_concluidas': [],
        'estatisticas': {},
        'erros': [],
        'alertas': []
    }
    
    try:
        # Executar processo principal
        sucesso = run_b3_scraping_and_upload()
        
        end_time = datetime.now()
        duracao = (end_time - start_time).total_seconds()
        
        relatorio.update({
            'timestamp_fim': end_time.isoformat(),
            'duracao_segundos': duracao,
            'status': 'sucesso' if sucesso else 'falha'
        })
        
        logger.info(f"📊 Relatório de execução:")
        logger.info(f"   ⏱️ Duração: {duracao:.1f} segundos")
        logger.info(f"   📋 Status: {relatorio['status']}")
        
        return relatorio
        
    except Exception as e:
        end_time = datetime.now()
        duracao = (end_time - start_time).total_seconds()
        
        relatorio.update({
            'timestamp_fim': end_time.isoformat(),
            'duracao_segundos': duracao,
            'status': 'erro_critico',
            'erros': [str(e)]
        })
        
        logger.error(f"❌ Erro crítico: {e}")
        return relatorio

if __name__ == '__main__':
    """
    Bloco de teste que pode ser executado diretamente para debug.
    """
    try:
        from flask import Flask
        from src.config import Config
        
        # Configurar logging para teste
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Criar app Flask temporário para teste
        temp_app = Flask(__name__)
        temp_app.config.from_object(Config)
        
        with temp_app.app_context():
            logger.info("=" * 60)
            logger.info("🧪 TESTANDO ORCHESTRATOR SELENIUM DIRETAMENTE")
            logger.info("=" * 60)
            
            # Teste 1: Execução básica
            logger.info("📋 Teste 1: Execução básica")
            success = run_b3_scraping_and_upload()
            
            if success:
                logger.info("✅ Teste básico: SUCESSO")
            else:
                logger.error("❌ Teste básico: FALHA")
            
            # Teste 2: Execução com relatório detalhado
            logger.info("\n📋 Teste 2: Execução com relatório")
            relatorio = run_b3_scraping_with_detailed_report()
            
            logger.info("📊 Relatório final:")
            for chave, valor in relatorio.items():
                logger.info(f"   {chave}: {valor}")
            
            logger.info("\n" + "=" * 60)
            logger.info("🏁 TESTES DO ORCHESTRATOR CONCLUÍDOS")
            logger.info("=" * 60)
            
    except RuntimeError as e:
        print(f"❌ Não foi possível executar teste direto sem contexto Flask: {e}")
        print("💡 Para testar, rode 'flask run' na raiz do seu projeto.")
    except Exception as e:
        print(f"❌ Erro durante teste do orchestrator: {e}")
        logging.exception("Detalhes completos do erro:")