# src/b3_data_processor.py
import pandas as pd
import io
from datetime import datetime # Importação correta da classe datetime

def parse_and_clean_csv_data(csv_text, execution_date):
    """
    Processa o texto CSV, limpa os dados e retorna um DataFrame do Pandas.
    Recuperado do seu script original.
    """
    if not csv_text:
        print("Texto do CSV está vazio. Não há nada para processar.")
        return pd.DataFrame()
    print("Iniciando parse e limpeza dos dados do CSV...")
    try:
        df = pd.read_csv(
            io.StringIO(csv_text),
            sep=';',
            encoding='latin-1',
            skiprows=2,     # Pula as 2 primeiras linhas de metadados
            skipfooter=2,   # Pula as 2 últimas linhas (rodapé)
            engine='python' # Necessário para usar skipfooter
        )
    except Exception as e:
        print(f"Erro ao ler o CSV com o Pandas: {e}")
        return pd.DataFrame()

    expected_columns = ['ticker', 'nome_empresa', 'tipo_acao', 'qtde_teorica', 'participacao']
    
    # Esta lógica para ajustar colunas é importante se houver colunas 'Unnamed' extras
    if len(df.columns) > len(expected_columns) and 'Unnamed:' in str(df.columns[-1]):
        df = df.iloc[:, :len(expected_columns)]
    
    if len(df.columns) == len(expected_columns):
        df.columns = expected_columns
    else:
        print(f"Aviso: O número de colunas do CSV ({len(df.columns)}) não corresponde ao esperado ({len(expected_columns)}).")
        print("Colunas encontradas:", df.columns.tolist())
        return pd.DataFrame() 

    for col in ['qtde_teorica', 'participacao']:
        if col in df.columns:
            # Garante que substitui tanto o ponto quanto a vírgula antes de converter para numérico
            # O replace do ponto deve ser primeiro para evitar que "1.234,56" vire "1,234.56" incorretamente.
            df[col] = df[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # === AQUI ESTÁ A MUDANÇA PRINCIPAL: NOME DA COLUNA ===
    df['data_do_pregao'] = execution_date.date() # Mudado de 'data_pregao' para 'data_do_pregao'
    print("Limpeza e transformação concluídas.")
    return df

if __name__ == '__main__':
    print("--- Testando src/b3_data_processor.py diretamente ---")
    sample_csv_content = """
IBOVESPA - Componentes da Carteira Teórica
Atualizado em 21/06/2025

Ticker;Nome da Empresa;Tipo;Qtde. Teórica;Part. (%)
ABEV3;AMBEV S/A;ON;4.234.567.890;5,123
ITUB4;ITAUUNIBANCO;PN;3.123.456.789;4,567
VALE3;VALE;ON;2.567.890.123;3,890
TOTAL;
"""
    test_date = datetime.now()
    processed_df = parse_and_clean_csv_data(sample_csv_content, test_date)
    
    if not processed_df.empty:
        print("DataFrame processado (primeiras 5 linhas):")
        print(processed_df.head())
        print("\nInformações do DataFrame:")
        print(processed_df.info())
        # Verifique se a coluna 'data_do_pregao' está presente e correta no teste
        if 'data_do_pregao' in processed_df.columns:
            print(f"\nValor da 'data_do_pregao': {processed_df['data_do_pregao'].iloc[0]}")
        else:
            print("\nColuna 'data_do_pregao' não encontrada no DataFrame de teste!")
    else:
        print("Falha no processamento do DataFrame de teste.")
    print("--- Teste de b3_data_processor.py concluído ---")