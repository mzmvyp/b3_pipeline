# athena_service.py
import boto3
import time
import pandas as pd
from io import StringIO
import os 

# =========================================================================
# CONFIGURAÇÕES - AJUSTE ESTAS VARIÁVEIS CONFORME SEU AMBIENTE
# =========================================================================

# Nome do seu database Athena
ATHENA_DATABASE = 'techchallenge_db' 

# Bucket S3 para resultados de query Athena.
# *** CORRIGIDO O NOME DO BUCKET AQUI! ***
ATHENA_OUTPUT_LOCATION = 's3://athena-query-results-willian-bovespa-us-east-2/' 

# Nome do seu Workgroup Athena. 'primary' é o padrão, mas verifique se você usa outro.
ATHENA_WORKGROUP = 'primary' 

# Região da AWS, confirmada como us-east-2
AWS_REGION = 'us-east-2' 

# =========================================================================
# INICIALIZAÇÃO DOS CLIENTES BOTO3 COM A REGIÃO ESPECIFICADA
# =========================================================================

# Inicializa o cliente Athena especificando a região
athena_client = boto3.client('athena', region_name=AWS_REGION)

# Inicializa o cliente S3 especificando a região (também é uma boa prática)
s3_client = boto3.client('s3', region_name=AWS_REGION)

# =========================================================================
# FUNÇÃO DE EXECUÇÃO DE QUERY ATHENA
# =========================================================================

def execute_athena_query(query: str):
    """
    Executa uma consulta SQL no AWS Athena, espera pela conclusão e retorna os resultados.

    Args:
        query (str): A string SQL a ser executada no Athena.

    Returns:
        list[list[str]]: Uma lista de listas contendo os cabeçalhos e os dados da query.
                         Retorna uma lista vazia se for uma query DDL/DML sem resultados.

    Raises:
        Exception: Se a query falhar, for cancelada ou se houver problemas de acesso/leitura.
    """
    try:
        # Inicia a execução da query
        response = athena_client.start_query_execution(
            QueryString=query,
            QueryExecutionContext={
                'Database': ATHENA_DATABASE
            },
            ResultConfiguration={
                'OutputLocation': ATHENA_OUTPUT_LOCATION
            },
            WorkGroup=ATHENA_WORKGROUP
        )
        query_execution_id = response['QueryExecutionId']
        print(f"Query Athena iniciada com ID: {query_execution_id}")

        # Loop para verificar o status da query até a conclusão
        while True:
            query_status_response = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
            status = query_status_response['QueryExecution']['Status']['State']
            print(f"Status da query '{query_execution_id}': {status}")

            if status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                break
            time.sleep(5) # Espera 5 segundos antes de verificar novamente

        if status == 'SUCCEEDED':
            # Obtém informações detalhadas da execução da query
            query_execution_details = query_status_response['QueryExecution']
            result_location = query_execution_details['ResultConfiguration']['OutputLocation']
            statement_type = query_execution_details.get('StatementType', 'UNKNOWN')
            data_scanned_bytes = query_execution_details['Statistics'].get('DataScannedInBytes', 0)

            # Verificar se é uma query DDL/DML que não retorna dados (ex: CREATE TABLE, INSERT INTO)
            # e não escaneou dados significativos.
            if statement_type in ['DDL', 'DML'] and data_scanned_bytes == 0:
                print("Consulta DDL/DML executada com sucesso, nenhum dado para retornar.")
                return [] # Retorna lista vazia para indicar sucesso sem dados

            # Extrair o nome do arquivo de resultado do S3
            # O result_location é algo como s3://seu-bucket/path/to/results/query_execution_id.csv
            # Precisamos do bucket e da chave (o caminho dentro do bucket)
            
            # Divide o ATHENA_OUTPUT_LOCATION para obter o nome do bucket e o prefixo (pasta)
            # Remove 's3://' e divide por '/'
            parsed_output_location = ATHENA_OUTPUT_LOCATION.replace('s3://', '').split('/', 1)
            output_bucket_name = parsed_output_location[0]
            output_prefix = parsed_output_location[1] if len(parsed_output_location) > 1 else ''

            # Extrai o caminho completo da chave do arquivo de resultado do S3
            # O result_location inclui o bucket e o prefixo base, precisamos do resto
            # Ex: s3://my-bucket/results/query_id.csv -> key = results/query_id.csv
            result_key = result_location.replace(f"s3://{output_bucket_name}/", "")
            
            # Verifica se o resultado é um arquivo CSV (comum para Athena)
            if not result_key.endswith('.csv'):
                # Para queries que não geram CSV (ex: EXPLAIN, ou alguns erros)
                # O Athena pode gerar um arquivo _SUCCESS, ou nenhum arquivo.
                print(f"Aviso: O resultado da query não é um arquivo CSV. Local: {result_location}")
                # Tentativa de ler o conteúdo bruto, se houver (para logs de erro ou pequenas saídas)
                try:
                    obj = s3_client.get_object(Bucket=output_bucket_name, Key=result_key)
                    raw_content = obj['Body'].read().decode('utf-8')
                    # Retorna como uma única linha de texto se não for CSV
                    return [[raw_content]] 
                except Exception as s3_error:
                    print(f"Não foi possível ler o conteúdo bruto em {result_location}: {s3_error}")
                    return [] # Nenhum resultado válido encontrado ou lido.
            
            # Baixar o arquivo CSV de resultados
            try:
                obj = s3_client.get_object(Bucket=output_bucket_name, Key=result_key)
            except s3_client.exceptions.NoSuchKey:
                raise Exception(f"Arquivo de resultado não encontrado no S3: {result_location}. "
                                f"Verifique as permissões ou se a query realmente gerou um arquivo.")
            except Exception as s3_error:
                raise Exception(f"Erro ao baixar o arquivo de resultado do S3 ({result_location}): {s3_error}")
            
            # Ler o CSV com pandas e retornar como lista de listas
            csv_string = obj['Body'].read().decode('utf-8')
            
            # Usar pd.read_csv. Adaptação para evitar o UserWarning sobre 'low_memory'
            df = pd.read_csv(StringIO(csv_string), low_memory=False)
            
            # Converter DataFrame para uma lista de listas (incluindo cabeçalhos)
            # Certifica-se de que todos os itens são strings para consistência
            data_list = [df.columns.astype(str).tolist()] + df.values.astype(str).tolist()
            
            return data_list
        else:
            # A query falhou ou foi cancelada
            reason = query_execution_details['Status'].get('StateChangeReason', 'Motivo desconhecido.')
            error_message = query_execution_details['Status'].get('AthenaError', {}).get('ErrorMessage', '')
            
            full_error_msg = f"Query Athena falhou ou foi cancelada ({status}): {reason}"
            if error_message:
                full_error_msg += f" Detalhes do Erro: {error_message}"
            
            raise Exception(full_error_msg)

    except athena_client.exceptions.InvalidRequestException as e:
        print(f"Erro de Requisição Inválida no Athena (provavelmente localização S3 ou região): {e}")
        raise Exception(f"Erro de configuração do Athena (localização S3 ou região): {e}")
    except Exception as e:
        print(f"Erro inesperado ao executar consulta Athena: {e}")
        raise e