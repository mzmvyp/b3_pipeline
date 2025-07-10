# src/b3_data_processor.py - Versão Atualizada para Selenium
import pandas as pd
import numpy as np
from datetime import datetime
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validar_estrutura_dataframe(df):
    """
    Valida se o DataFrame possui a estrutura esperada dos dados extraídos.
    
    Args:
        df (pd.DataFrame): DataFrame a ser validado
        
    Returns:
        tuple: (bool, list) - (é_válido, erros_encontrados)
    """
    erros = []
    
    # Verificar se DataFrame não está vazio
    if df.empty:
        erros.append("DataFrame está vazio")
        return False, erros
    
    # Colunas obrigatórias esperadas do extrator Selenium
    colunas_obrigatorias = [
        'ticker', 'nome_empresa', 'tipo_acao', 
        'qtde_teorica', 'participacao'
    ]
    
    # Verificar colunas obrigatórias
    colunas_faltantes = [col for col in colunas_obrigatorias if col not in df.columns]
    if colunas_faltantes:
        erros.append(f"Colunas obrigatórias ausentes: {colunas_faltantes}")
    
    # Verificar tipos de dados básicos
    if 'ticker' in df.columns:
        if not df['ticker'].dtype == 'object':
            erros.append("Coluna 'ticker' deve ser do tipo texto")
    
    if 'participacao' in df.columns:
        if not pd.api.types.is_numeric_dtype(df['participacao']):
            erros.append("Coluna 'participacao' deve ser numérica")
    
    if 'qtde_teorica' in df.columns:
        if not pd.api.types.is_numeric_dtype(df['qtde_teorica']):
            erros.append("Coluna 'qtde_teorica' deve ser numérica")
    
    return len(erros) == 0, erros

def limpar_e_validar_dados(df):
    """
    Realiza limpeza e validação dos dados extraídos.
    
    Args:
        df (pd.DataFrame): DataFrame bruto extraído
        
    Returns:
        pd.DataFrame: DataFrame limpo e validado
    """
    logger.info("🧹 Iniciando limpeza e validação dos dados...")
    
    df_limpo = df.copy()
    linhas_iniciais = len(df_limpo)
    
    # 1. Remover linhas com ticker vazio ou inválido
    df_limpo = df_limpo.dropna(subset=['ticker'])
    df_limpo = df_limpo[df_limpo['ticker'].str.strip() != '']
    
    # 2. Filtrar apenas tickers válidos (padrão B3: 4-6 caracteres)
    mask_ticker_valido = df_limpo['ticker'].str.len().between(4, 6)
    df_limpo = df_limpo[mask_ticker_valido]
    
    # 3. Remover caracteres especiais dos tickers
    df_limpo['ticker'] = df_limpo['ticker'].str.upper().str.strip()
    
    # 4. Validar e limpar dados numéricos
    for coluna in ['qtde_teorica', 'participacao']:
        if coluna in df_limpo.columns:
            # Converter para numérico, colocando NaN em valores inválidos
            df_limpo[coluna] = pd.to_numeric(df_limpo[coluna], errors='coerce')
            
            # Remover linhas com valores NaN ou negativos
            df_limpo = df_limpo.dropna(subset=[coluna])
            df_limpo = df_limpo[df_limpo[coluna] >= 0]
    
    # 5. Limpar nomes de empresas
    if 'nome_empresa' in df_limpo.columns:
        df_limpo['nome_empresa'] = df_limpo['nome_empresa'].str.strip()
        df_limpo = df_limpo[df_limpo['nome_empresa'].str.len() > 0]
    
    # 6. Padronizar tipos de ação
    if 'tipo_acao' in df_limpo.columns:
        df_limpo['tipo_acao'] = df_limpo['tipo_acao'].str.upper().str.strip()
    
    # 7. Remover duplicatas (mesma ação)
    df_limpo = df_limpo.drop_duplicates(subset=['ticker'], keep='first')
    
    linhas_finais = len(df_limpo)
    linhas_removidas = linhas_iniciais - linhas_finais
    
    if linhas_removidas > 0:
        logger.info(f"⚠️ Removidas {linhas_removidas} linhas durante a limpeza")
    
    logger.info(f"✅ Limpeza concluída: {linhas_finais} registros válidos")
    
    return df_limpo

def enriquecer_dados(df, data_execucao=None):
    """
    Adiciona colunas derivadas e metadados aos dados.
    
    Args:
        df (pd.DataFrame): DataFrame limpo
        data_execucao (datetime, optional): Data de execução. Defaults to datetime.now()
        
    Returns:
        pd.DataFrame: DataFrame enriquecido
    """
    logger.info("💎 Enriquecendo dados com metadados e colunas derivadas...")
    
    if data_execucao is None:
        data_execucao = datetime.now()
    
    df_enriquecido = df.copy()
    
    # Metadados temporais
    df_enriquecido['data_pregao'] = data_execucao.date()
    df_enriquecido['timestamp_processamento'] = data_execucao
    
    # Colunas para particionamento
    df_enriquecido['ano'] = data_execucao.year
    df_enriquecido['mes'] = data_execucao.month
    df_enriquecido['dia'] = data_execucao.day
    
    # Análises derivadas
    if 'participacao' in df_enriquecido.columns:
        # Ranking por participação
        df_enriquecido = df_enriquecido.sort_values('participacao', ascending=False)
        df_enriquecido['ranking_participacao'] = range(1, len(df_enriquecido) + 1)
        
        # Participação acumulada
        df_enriquecido['participacao_acumulada'] = df_enriquecido['participacao'].cumsum()
        
        # Classificação por tamanho de participação
        def classificar_participacao(valor):
            if valor >= 5.0:
                return 'Grande'
            elif valor >= 2.0:
                return 'Média'
            elif valor >= 1.0:
                return 'Pequena'
            else:
                return 'Micro'
        
        df_enriquecido['classe_participacao'] = df_enriquecido['participacao'].apply(classificar_participacao)
    
    # Informações sobre o setor (baseado no ticker - simplificado)
    if 'ticker' in df_enriquecido.columns:
        def inferir_setor_basico(ticker):
            """Inferência básica de setor baseada em padrões conhecidos"""
            ticker = ticker.upper()
            if ticker.startswith(('PETR', 'PRIO')):
                return 'Petróleo e Gás'
            elif ticker.startswith(('VALE', 'CSNA')):
                return 'Mineração'
            elif ticker.startswith(('ITUB', 'BBDC', 'BBAS', 'SANB')):
                return 'Bancos'
            elif ticker.startswith(('ABEV', 'JBSS')):
                return 'Consumo'
            elif ticker.startswith(('MGLU', 'LREN')):
                return 'Varejo'
            else:
                return 'Outros'
        
        df_enriquecido['setor_inferido'] = df_enriquecido['ticker'].apply(inferir_setor_basico)
    
    logger.info(f"✅ Dados enriquecidos com {len(df_enriquecido.columns)} colunas")
    
    return df_enriquecido

def validar_qualidade_dados(df):
    """
    Realiza validações de qualidade nos dados processados.
    
    Args:
        df (pd.DataFrame): DataFrame processado
        
    Returns:
        dict: Relatório de qualidade dos dados
    """
    logger.info("🔍 Validando qualidade dos dados...")
    
    relatorio = {
        'total_registros': len(df),
        'validacao_passou': True,
        'alertas': [],
        'metricas': {}
    }
    
    if df.empty:
        relatorio['validacao_passou'] = False
        relatorio['alertas'].append("DataFrame vazio após processamento")
        return relatorio
    
    # Verificar participação total
    if 'participacao' in df.columns:
        participacao_total = df['participacao'].sum()
        relatorio['metricas']['participacao_total'] = participacao_total
        
        # IBOVESPA deve somar próximo a 100%
        if participacao_total < 95 or participacao_total > 105:
            relatorio['alertas'].append(
                f"Participação total fora do esperado: {participacao_total:.2f}% "
                "(esperado: 95-105%)"
            )
    
    # Verificar se há tickers duplicados
    if 'ticker' in df.columns:
        tickers_duplicados = df['ticker'].duplicated().sum()
        if tickers_duplicados > 0:
            relatorio['alertas'].append(f"Encontrados {tickers_duplicados} tickers duplicados")
    
    # Verificar valores extremos
    if 'participacao' in df.columns:
        participacao_max = df['participacao'].max()
        participacao_min = df['participacao'].min()
        
        relatorio['metricas']['participacao_maxima'] = participacao_max
        relatorio['metricas']['participacao_minima'] = participacao_min
        
        if participacao_max > 15:  # Nenhuma ação deveria ter mais que ~15% do índice
            relatorio['alertas'].append(f"Participação máxima muito alta: {participacao_max:.2f}%")
        
        if participacao_min < 0:
            relatorio['alertas'].append(f"Participação negativa encontrada: {participacao_min:.2f}%")
    
    # Resumo final
    if len(relatorio['alertas']) > 3:
        relatorio['validacao_passou'] = False
    
    logger.info(f"📊 Validação concluída: {len(relatorio['alertas'])} alertas encontrados")
    
    return relatorio

def processar_dados_ibovespa_selenium(df_bruto, data_execucao=None):
    """
    Função principal para processar dados extraídos via Selenium.
    
    Args:
        df_bruto (pd.DataFrame): DataFrame bruto extraído pelo Selenium
        data_execucao (datetime, optional): Data de execução
        
    Returns:
        tuple: (DataFrame processado, relatório de qualidade)
    """
    logger.info("🚀 Iniciando processamento completo dos dados do IBOVESPA")
    
    if data_execucao is None:
        data_execucao = datetime.now()
    
    # 1. Validar estrutura inicial
    estrutura_valida, erros_estrutura = validar_estrutura_dataframe(df_bruto)
    if not estrutura_valida:
        logger.error(f"❌ Estrutura inválida: {erros_estrutura}")
        return pd.DataFrame(), {'erro': 'Estrutura inválida', 'detalhes': erros_estrutura}
    
    # 2. Limpar e validar dados
    df_limpo = limpar_e_validar_dados(df_bruto)
    if df_limpo.empty:
        logger.error("❌ Nenhum dado válido após limpeza")
        return pd.DataFrame(), {'erro': 'Nenhum dado válido após limpeza'}
    
    # 3. Enriquecer dados
    df_processado = enriquecer_dados(df_limpo, data_execucao)
    
    # 4. Validar qualidade final
    relatorio_qualidade = validar_qualidade_dados(df_processado)
    
    logger.info("✅ Processamento concluído com sucesso")
    logger.info(f"📊 Registros processados: {len(df_processado)}")
    
    return df_processado, relatorio_qualidade

if __name__ == '__main__':
    logger.info("--- Testando b3_data_processor.py atualizado ---")
    
    # Criar dados de teste simulando saída do Selenium
    dados_teste = {
        'ticker': ['ABEV3', 'ITUB4', 'VALE3', 'PETR4', 'BBDC4'],
        'nome_empresa': ['AMBEV S/A', 'ITAUUNIBANCO', 'VALE', 'PETROBRAS', 'BRADESCO'],
        'tipo_acao': ['ON', 'PN', 'ON', 'PN', 'PN'],
        'qtde_teorica': [4234567890, 3123456789, 2567890123, 1890123456, 1567890123],
        'participacao': [5.123, 4.567, 3.890, 3.234, 2.890],
        'data_extracao': [datetime.now()] * 5,
        'ano': [2025] * 5,
        'mes': [7] * 5,
        'dia': [9] * 5
    }
    
    df_teste = pd.DataFrame(dados_teste)
    
    logger.info("📊 Testando com dados simulados:")
    print(df_teste)
    
    # Processar dados
    df_processado, relatorio = processar_dados_ibovespa_selenium(df_teste)
    
    if not df_processado.empty:
        print("\n✅ Dados processados com sucesso:")
        print(df_processado.head())
        
        print(f"\n📊 Colunas disponíveis: {list(df_processado.columns)}")
        print(f"\n🎯 Relatório de qualidade:")
        for chave, valor in relatorio.items():
            print(f"   {chave}: {valor}")
    else:
        print("❌ Falha no processamento")
        print(f"Relatório de erro: {relatorio}")
    
    logger.info("--- Teste concluído ---")