# src/routes/api_routes.py
import datetime # Adicione esta importação para usar datetime.now()
from flask import Blueprint, request, jsonify, current_app
from src.s3_manager import list_s3_contents_by_prefix, list_all_s3_buckets, check_s3_object_exists, upload_to_s3 # Funções do S3
from src.orchestrator import run_b3_scraping_and_upload # Orquestrador para o scraping
from src.athena_service import execute_athena_query # Funções do Athena
import base64
import io
import matplotlib
matplotlib.use('Agg')  # Backend não-interativo para servidor
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime

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
    
    @api_bp.route('/analytics/overview', methods=['GET'])
    def analytics_overview():
        """
        Endpoint para análise geral do Ibovespa (equivalente à célula 3 do notebook)
        """
    try:
        # Dados simulados (mesmos do notebook)
        mock_data = [
            ("PETR4", "PETROBRAS", "PN", 1234567890, 8.47, "2025-01-06"),
            ("VALE3", "VALE", "ON", 987654321, 7.23, "2025-01-06"),
            ("ITUB4", "ITAUUNIBANCO", "PN", 567890123, 6.81, "2025-01-06"),
            ("BBDC4", "BRADESCO", "PN", 456789012, 5.94, "2025-01-06"),
            ("ABEV3", "AMBEV", "ON", 789012345, 4.12, "2025-01-06"),
            ("WEGE3", "WEG", "ON", 234567890, 3.85, "2025-01-06"),
            ("RENT3", "LOCALIZA", "ON", 345678901, 3.21, "2025-01-06"),
            ("LREN3", "LOJAS RENNER", "ON", 123456789, 2.94, "2025-01-06"),
            ("MGLU3", "MAGAZINE LUIZA", "ON", 678901234, 2.67, "2025-01-06"),
            ("JBSS3", "JBS", "ON", 890123456, 2.43, "2025-01-06"),
            ("SUZB3", "SUZANO", "ON", 334455667, 2.18, "2025-01-06"),
            ("RAIL3", "RUMO", "ON", 223344556, 1.95, "2025-01-06"),
            ("HAPV3", "HAPVIDA", "ON", 112233445, 1.72, "2025-01-06"),
            ("KLBN11", "KLABIN", "UNT", 445566778, 1.49, "2025-01-06"),
            ("EMBR3", "EMBRAER", "ON", 556677889, 1.26, "2025-01-06")
        ]
        
        # Criar DataFrame
        columns = ["ticker", "nome_empresa", "tipo_acao", "qtde_teorica", "participacao", "data_do_pregao"]
        df = pd.DataFrame(mock_data, columns=columns)
        
        # Estatísticas básicas
        stats = {
            'total_companies': len(df),
            'total_participation': round(df['participacao'].sum(), 1),
            'avg_participation': round(df['participacao'].mean(), 2),
            'std_participation': round(df['participacao'].std(), 2),
            'top_5': df.nlargest(5, 'participacao')[['ticker', 'nome_empresa', 'participacao']].to_dict('records')
        }
        
        # Gerar gráficos
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Gráfico 1: Barras horizontais
        df_sorted = df.sort_values('participacao', ascending=True)
        colors = plt.cm.viridis(np.linspace(0, 1, len(df_sorted)))
        bars = ax1.barh(range(len(df_sorted)), df_sorted['participacao'], color=colors)
        ax1.set_yticks(range(len(df_sorted)))
        ax1.set_yticklabels(df_sorted['ticker'])
        ax1.set_xlabel('Participação (%)')
        ax1.set_title('Participação das Ações no Ibovespa', fontsize=14, fontweight='bold')
        ax1.grid(axis='x', alpha=0.3)
        
        # Gráfico 2: Pizza top 7
        top_7 = df.nlargest(7, 'participacao')
        others_sum = df[~df['ticker'].isin(top_7['ticker'])]['participacao'].sum()
        pie_data = top_7['participacao'].tolist() + [others_sum]
        pie_labels = top_7['ticker'].tolist() + ['Outros']
        
        ax2.pie(pie_data, labels=pie_labels, autopct='%1.1f%%', startangle=90)
        ax2.set_title('Concentração (Top 7 + Outros)', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        # Converter gráfico para base64
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()
        
        return jsonify({
            'status': 'success',
            'stats': stats,
            'chart': img_base64,
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro em analytics_overview: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api_bp.route('/analytics/by_type', methods=['GET'])
def analytics_by_type():
    """
    Análise por tipo de ação (equivalente à célula 4 do notebook)
    """
    try:
        # Mesmos dados
        mock_data = [
            ("PETR4", "PETROBRAS", "PN", 1234567890, 8.47, "2025-01-06"),
            ("VALE3", "VALE", "ON", 987654321, 7.23, "2025-01-06"),
            ("ITUB4", "ITAUUNIBANCO", "PN", 567890123, 6.81, "2025-01-06"),
            ("BBDC4", "BRADESCO", "PN", 456789012, 5.94, "2025-01-06"),
            ("ABEV3", "AMBEV", "ON", 789012345, 4.12, "2025-01-06"),
            ("WEGE3", "WEG", "ON", 234567890, 3.85, "2025-01-06"),
            ("RENT3", "LOCALIZA", "ON", 345678901, 3.21, "2025-01-06"),
            ("LREN3", "LOJAS RENNER", "ON", 123456789, 2.94, "2025-01-06"),
            ("MGLU3", "MAGAZINE LUIZA", "ON", 678901234, 2.67, "2025-01-06"),
            ("JBSS3", "JBS", "ON", 890123456, 2.43, "2025-01-06"),
            ("SUZB3", "SUZANO", "ON", 334455667, 2.18, "2025-01-06"),
            ("RAIL3", "RUMO", "ON", 223344556, 1.95, "2025-01-06"),
            ("HAPV3", "HAPVIDA", "ON", 112233445, 1.72, "2025-01-06"),
            ("KLBN11", "KLABIN", "UNT", 445566778, 1.49, "2025-01-06"),
            ("EMBR3", "EMBRAER", "ON", 556677889, 1.26, "2025-01-06")
        ]
        
        columns = ["ticker", "nome_empresa", "tipo_acao", "qtde_teorica", "participacao", "data_do_pregao"]
        df = pd.DataFrame(mock_data, columns=columns)
        
        # Análise por tipo
        type_stats = {}
        for tipo in df['tipo_acao'].unique():
            subset = df[df['tipo_acao'] == tipo]
            type_stats[tipo] = {
                'count': len(subset),
                'total_participation': round(subset['participacao'].sum(), 1),
                'avg_participation': round(subset['participacao'].mean(), 2),
                'companies': subset[['ticker', 'nome_empresa', 'participacao']].to_dict('records')
            }
        
        # Gerar gráfico
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))
        
        # Gráfico 1: Pizza participação total
        tipo_participacao = df.groupby('tipo_acao')['participacao'].sum()
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
        ax1.pie(tipo_participacao.values, labels=tipo_participacao.index, autopct='%1.1f%%', 
                colors=colors, startangle=90)
        ax1.set_title('Participação Total por Tipo')
        
        # Gráfico 2: Quantidade por tipo
        tipo_count = df.groupby('tipo_acao').size()
        bars = ax2.bar(tipo_count.index, tipo_count.values, color=colors)
        ax2.set_title('Quantidade por Tipo')
        ax2.set_ylabel('Número de Ações')
        for bar, value in zip(bars, tipo_count.values):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                     str(value), ha='center', va='bottom', fontweight='bold')
        
        # Gráfico 3: Participação média
        tipo_media = df.groupby('tipo_acao')['participacao'].mean()
        bars3 = ax3.bar(tipo_media.index, tipo_media.values, color=colors)
        ax3.set_title('Participação Média por Tipo')
        ax3.set_ylabel('Participação Média (%)')
        for bar, value in zip(bars3, tipo_media.values):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                     f'{value:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        
        # Converter para base64
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()
        
        return jsonify({
            'status': 'success',
            'type_stats': type_stats,
            'chart': img_base64,
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro em analytics_by_type: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api_bp.route('/analytics/concentration', methods=['GET'])
def analytics_concentration():
    """
    Análise de concentração (equivalente à célula 5 do notebook)
    """
    try:
        # Mesmos dados
        mock_data = [
            ("PETR4", "PETROBRAS", "PN", 1234567890, 8.47, "2025-01-06"),
            ("VALE3", "VALE", "ON", 987654321, 7.23, "2025-01-06"),
            ("ITUB4", "ITAUUNIBANCO", "PN", 567890123, 6.81, "2025-01-06"),
            ("BBDC4", "BRADESCO", "PN", 456789012, 5.94, "2025-01-06"),
            ("ABEV3", "AMBEV", "ON", 789012345, 4.12, "2025-01-06"),
            ("WEGE3", "WEG", "ON", 234567890, 3.85, "2025-01-06"),
            ("RENT3", "LOCALIZA", "ON", 345678901, 3.21, "2025-01-06"),
            ("LREN3", "LOJAS RENNER", "ON", 123456789, 2.94, "2025-01-06"),
            ("MGLU3", "MAGAZINE LUIZA", "ON", 678901234, 2.67, "2025-01-06"),
            ("JBSS3", "JBS", "ON", 890123456, 2.43, "2025-01-06"),
            ("SUZB3", "SUZANO", "ON", 334455667, 2.18, "2025-01-06"),
            ("RAIL3", "RUMO", "ON", 223344556, 1.95, "2025-01-06"),
            ("HAPV3", "HAPVIDA", "ON", 112233445, 1.72, "2025-01-06"),
            ("KLBN11", "KLABIN", "UNT", 445566778, 1.49, "2025-01-06"),
            ("EMBR3", "EMBRAER", "ON", 556677889, 1.26, "2025-01-06")
        ]
        
        columns = ["ticker", "nome_empresa", "tipo_acao", "qtde_teorica", "participacao", "data_do_pregao"]
        df = pd.DataFrame(mock_data, columns=columns)
        
        # Análise de concentração
        df_concentration = df.sort_values('participacao', ascending=False).reset_index(drop=True)
        df_concentration['participacao_acumulada'] = df_concentration['participacao'].cumsum()
        df_concentration['posicao'] = range(1, len(df_concentration) + 1)
        
        # Calcular pontos importantes
        def find_concentration_point(target_pct):
            result = df_concentration[df_concentration['participacao_acumulada'] >= target_pct]
            return result['posicao'].iloc[0] if len(result) > 0 else len(df_concentration)
        
        pos_50 = find_concentration_point(50)
        pos_80 = find_concentration_point(80)
        hhi = (df['participacao'] ** 2).sum()
        
        concentration_stats = {
            'pos_50': pos_50,
            'pos_80': pos_80,
            'hhi': round(hhi, 0),
            'concentration_level': 'Alta' if hhi > 2500 else 'Moderada' if hhi > 1500 else 'Baixa',
            'top_5_accumulated': round(df_concentration.head(5)['participacao'].sum(), 1)
        }
        
        # Gerar gráfico
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Curva de concentração
        ax1.plot(df_concentration['posicao'], df_concentration['participacao_acumulada'], 
                linewidth=4, color='navy', marker='o', markersize=6)
        ax1.axhline(y=50, color='red', linestyle='--', alpha=0.7, label='50%')
        ax1.axhline(y=80, color='orange', linestyle='--', alpha=0.7, label='80%')
        ax1.axvline(x=pos_50, color='red', linestyle=':', alpha=0.7)
        ax1.axvline(x=pos_80, color='orange', linestyle=':', alpha=0.7)
        ax1.set_title('Curva de Concentração do Ibovespa')
        ax1.set_xlabel('Posição')
        ax1.set_ylabel('Participação Acumulada (%)')
        ax1.grid(alpha=0.3)
        ax1.legend()
        
        # Gráfico de Pareto
        colors_pareto = ['gold' if i < 3 else 'lightblue' if i < 7 else 'lightgray' 
                        for i in range(len(df_concentration))]
        ax2.bar(df_concentration['posicao'], df_concentration['participacao'], 
               color=colors_pareto, alpha=0.8)
        ax2.set_title('Participação Individual (Pareto)')
        ax2.set_xlabel('Posição')
        ax2.set_ylabel('Participação (%)')
        
        # Labels para top 5
        for i in range(min(5, len(df_concentration))):
            ticker = df_concentration.loc[i, 'ticker']
            participacao = df_concentration.loc[i, 'participacao']
            ax2.text(i+1, participacao + 0.15, f'{ticker}\n{participacao:.1f}%', 
                    ha='center', va='bottom', fontweight='bold', fontsize=8)
        
        plt.tight_layout()
        
        # Converter para base64
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()
        
        return jsonify({
            'status': 'success',
            'concentration_stats': concentration_stats,
            'chart': img_base64,
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro em analytics_concentration: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500