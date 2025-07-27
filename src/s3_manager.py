# src/s3_manager.py
import os
import boto3
from botocore.exceptions import ClientError
import pandas as pd
import io
from datetime import datetime # Certifique-se de importar datetime

# Remova esta inicialização global se ela estiver causando algum problema
# s3_client = boto3.client('s3')

def check_s3_object_exists(bucket_name, object_key, aws_region):
    """
    Verifica se um objeto específico existe em um bucket S3.
    """
    # É bom inicializar o cliente aqui para garantir que a região seja sempre usada
    s3_client_for_check = boto3.client('s3', region_name=aws_region)
    try:
        s3_client_for_check.head_object(Bucket=bucket_name, Key=object_key)
        print(f"Objeto '{object_key}' já existe no bucket '{bucket_name}'.")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            print(f"Objeto '{object_key}' não encontrado no bucket '{bucket_name}'.")
            return False
        else:
            # Outro erro que não seja 404 (ex: permissão negada)
            print(f"Erro ao verificar objeto S3 '{object_key}': {e}")
            raise # Propaga o erro se não for apenas 'não encontrado'

# ******************************************************************************
# CORREÇÃO CRÍTICA AQUI: A função AGORA RECEBE 'processing_date' DIRETAMENTE
# ******************************************************************************
def upload_to_s3(dataframe, bucket_name, aws_region, processing_date):
    """
    Converte um DataFrame do Pandas para o formato Parquet e faz o upload para um bucket S3,
    usando um caminho baseado na data de processamento FORNECIDA e estrutura de partição.
    """
    try:

        # Formata a data para o nome do arquivo (ex: 2025-07-02)
        date_str = datetime.strptime(processing_date, '%Y-%m-%d')
        
        # ******************************************************************************
        # CORREÇÃO CRÍTICA AQUI: Usar a estrutura de partição exata do seu log
        # ******************************************************************************
        # Ex: data/year=2025/month=07/day=02/ibovespa_2025-07-02.parquet
        year_str = date_str.strftime('%Y')
        month_str = date_str.strftime('%m')
        day_str = date_str.strftime('%d')
        
        file_name = f"ibovespa_{date_str.strftime('%Y-%m-%d')}.parquet" # Nome do arquivo final
        object_key = f"data/year={year_str}/month={month_str}/day={day_str}/{file_name}"

        parquet_buffer = io.BytesIO()
        dataframe.to_parquet(parquet_buffer, index=False, engine='pyarrow', compression='snappy')
        parquet_buffer.seek(0)

        s3_client_for_upload = boto3.client('s3', region_name=aws_region)
        s3_client_for_upload.upload_fileobj(parquet_buffer, bucket_name, object_key)

        print(f"DataFrame processado enviado para s3://{bucket_name}/{object_key}")
        return True
    except Exception as e:
        print(f"Erro ao fazer upload para S3: {e}")
        return False

# --- SUAS OUTRAS FUNÇÕES DE list_all_s3_buckets, list_s3_contents_by_prefix, get_all_data_from_s3, list_s3_history_files AINDA IRÃO AQUI ---
# Mantenha-as como estão, mas remova a inicialização global s3_client = boto3.client('s3') no topo do arquivo.
# Cada função deve inicializar seu próprio cliente se precisar de região_name, ou você pode passar.
# Para simplicidade e consistência, é melhor que cada função passe a aws_region para o boto3.client('s3', region_name=aws_region).

def list_all_s3_buckets(aws_region): # Adicione aws_region aqui
    """
    Lista todos os buckets S3 na conta configurada.
    Retorna uma lista de strings com os nomes dos buckets.
    """
    s3_client_for_list_buckets = boto3.client('s3', region_name=aws_region)
    print("Listando todos os buckets S3...")
    try:
        response = s3_client_for_list_buckets.list_buckets()
        buckets = [bucket['Name'] for bucket in response['Buckets']]
        print(f"Encontrados {len(buckets)} buckets.")
        return buckets
    except Exception as e:
        print(f"Erro ao listar buckets S3: {e}")
        raise

def list_s3_contents_by_prefix(bucket_name, current_prefix="", aws_region=None): # Adicione aws_region
    """
    Lista os 'pastas' (prefixes) e arquivos (objetos) em um determinado prefixo S3.
    Retorna uma lista de dicionários com 'type' ('prefix' ou 'file') e 'name', size e last_modified.
    """
    s3_client_for_list_contents = boto3.client('s3', region_name=aws_region) # Usar cliente local
    print(f"Listando conteúdo para bucket: {bucket_name}, prefixo: {current_prefix}")
    contents = []
    
    prefix_for_listing = current_prefix
    if prefix_for_listing and not prefix_for_listing.endswith('/'):
        if '.' not in os.path.basename(prefix_for_listing):
            prefix_for_listing += '/'
    
    try:
        response = s3_client_for_list_contents.list_objects_v2( # Usar cliente local
            Bucket=bucket_name,
            Prefix=prefix_for_listing,
            Delimiter='/' 
        )

        if 'CommonPrefixes' in response:
            for common_prefix in response['CommonPrefixes']:
                name = common_prefix['Prefix'][len(prefix_for_listing):].strip('/')
                if name:
                    contents.append({'type': 'prefix', 'name': name, 'size': None, 'last_modified': None})

        if 'Contents' in response:
            for obj in response['Contents']:
                if obj['Key'] == prefix_for_listing:
                    continue
                
                name = obj['Key'][len(prefix_for_listing):]
                if name:
                    contents.append({
                        'type': 'file', 
                        'name': name, 
                        'size': obj['Size'], 
                        'last_modified': obj['LastModified'].isoformat()
                    })
        
        contents.sort(key=lambda x: (x['type'] == 'file', x['name'].lower()))
        print(f"Encontrados {len(contents)} itens para o prefixo '{current_prefix}'.")
        return contents
    except Exception as e:
        print(f"Erro ao listar conteúdo S3 para prefixo '{current_prefix}': {e}")
        raise

def get_all_data_from_s3(bucket_name, prefix='data/', aws_region=None): # Adicione aws_region
    """
    Lista todos os arquivos Parquet no S3 dentro do prefixo de partição
    e os carrega em um único DataFrame, adicionando metadados como 'data_arquivo' e 'nome_arquivo_s3'.
    """
    s3_client_for_get_data = boto3.client('s3', region_name=aws_region) # Usar cliente local
    all_data_frames = []
    print(f"Listando e carregando todos os dados do bucket S3: {bucket_name}/{prefix}")
    try:
        paginator = s3_client_for_get_data.get_paginator('list_objects_v2') # Usar cliente local
        pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix) 
        
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    key = obj['Key']
                    if key.endswith('.parquet'):
                        print(f"Baixando {key} do S3...")
                        response = s3_client_for_get_data.get_object(Bucket=bucket_name, Key=key) # Usar cliente local
                        parquet_bytes = response['Body'].read()
                        
                        df = pd.read_parquet(io.BytesIO(parquet_bytes), engine='pyarrow')
                        
                        parts = key.split('/')
                        date_from_path = None
                        file_name = parts[-1] 

                        year_val = None
                        month_val = None
                        day_val = None

                        for part in parts:
                            if part.startswith('year='):
                                year_val = part.split('=')[1]
                            elif part.startswith('month='):
                                month_val = part.split('=')[1]
                            elif part.startswith('day='):
                                day_val = part.split('=')[1]
                        
                        if year_val and month_val and day_val:
                            try:
                                date_from_path = f"{year_val}-{month_val.zfill(2)}-{day_val.zfill(2)}"
                            except ValueError:
                                pass 

                        df['data_arquivo'] = date_from_path 
                        df['nome_arquivo_s3'] = file_name 
                        all_data_frames.append(df)
            
        if all_data_frames:
            final_all_df = pd.concat(all_data_frames, ignore_index=True)
            final_all_df['data_arquivo'] = pd.to_datetime(final_all_df['data_arquivo'])
            final_all_df = final_all_df.sort_values(by='data_arquivo', ascending=False).reset_index(drop=True)
            return final_all_df
        return pd.DataFrame()
    except Exception as e:
        print(f"Erro ao carregar todos os dados do S3: {e}")
        raise

def list_s3_history_files(bucket_name, prefix='data/', aws_region=None): # Adicione aws_region
    """
    Lista todos os arquivos Parquet no S3 dentro do prefixo de partição 'data/',
    retornando uma lista de dicionários com a data da partição e o nome do arquivo.
    """
    s3_client_for_history = boto3.client('s3', region_name=aws_region) # Usar cliente local
    history_files = []
    print(f"Listando histórico de arquivos no bucket S3: {bucket_name}/{prefix}")
    try:
        paginator = s3_client_for_history.get_paginator('list_objects_v2') # Usar cliente local
        pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix) 
        
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    key = obj['Key']
                    if key.endswith('.parquet'):
                        parts = key.split('/')
                        
                        year_val = None
                        month_val = None
                        day_val = None
                        file_name = parts[-1] 

                        for part in parts:
                            if part.startswith('year='):
                                year_val = part.split('=')[1]
                            elif part.startswith('month='):
                                month_val = part.split('=')[1]
                            elif part.startswith('day='):
                                day_val = part.split('=')[1]
                        
                        if year_val and month_val and day_val:
                            try:
                                date_partition_str = f"{year_val}-{month_val.zfill(2)}-{day_val.zfill(2)}"
                                history_files.append({
                                    'data_particao': date_partition_str,
                                    'nome_arquivo': file_name
                                })
                            except ValueError:
                                pass 

        history_files.sort(key=lambda x: x['data_particao'], reverse=True)
        return history_files
    except Exception as e:
        print(f"Erro ao listar histórico de arquivos no S3: {e}")
        raise