# src/config.py - Versão Corrigida para Problemas de Codificação
import os
from pathlib import Path

def safe_load_dotenv():
    """
    Carrega o arquivo .env de forma segura, tratando problemas de codificação.
    """
    env_file = Path(__file__).parent.parent / '.env'
    
    if not env_file.exists():
        print(f"⚠️ Arquivo .env não encontrado em: {env_file}")
        print("💡 Criando arquivo .env modelo...")
        create_sample_env_file(env_file)
        return False
    
    try:
        # Tentar carregar com python-dotenv
        from dotenv import load_dotenv
        load_dotenv(env_file, encoding='utf-8')
        return True
    except UnicodeDecodeError:
        print("⚠️ Erro de codificação no arquivo .env. Tentando carregar manualmente...")
        return load_env_manually(env_file)
    except ImportError:
        print("⚠️ python-dotenv não instalado. Carregando manualmente...")
        return load_env_manually(env_file)
    except Exception as e:
        print(f"⚠️ Erro ao carregar .env: {e}")
        return load_env_manually(env_file)

def load_env_manually(env_file):
    """
    Carrega o arquivo .env manualmente, tentando diferentes codificações.
    """
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            with open(env_file, 'r', encoding=encoding) as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Pular linhas vazias e comentários
                    if not line or line.startswith('#'):
                        continue
                    
                    # Processar linha no formato KEY=VALUE
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")  # Remove aspas
                        
                        # Definir variável de ambiente se não existir
                        if key and not os.getenv(key):
                            os.environ[key] = value
            
            print(f"✅ Arquivo .env carregado com codificação: {encoding}")
            return True
            
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"❌ Erro ao carregar com {encoding}: {e}")
            continue
    
    print("❌ Não foi possível carregar o arquivo .env com nenhuma codificação")
    return False

def create_sample_env_file(env_path):
    """
    Cria um arquivo .env modelo com as configurações básicas.
    """
    sample_content = """# Configurações B3 — modelo (sem segredos). Copie e renomeie se precisar.
# Preencha localmente; não commite o arquivo .env.

# AWS (preferir IAM role em produção)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_DEFAULT_REGION=sa-east-1

# S3
SCRAPING_TARGET_S3_BUCKET=your-s3-bucket-name

# Selenium
SELENIUM_HEADLESS=true
SELENIUM_TIMEOUT=30

PARQUET_COMPRESSION=snappy
LOG_LEVEL=INFO
FLASK_ENV=production
"""

    try:
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(sample_content)
        print(f"✅ Arquivo .env modelo criado em: {env_path}")
        print("💡 Edite o arquivo .env com suas credenciais AWS antes de continuar")
    except Exception as e:
        print(f"❌ Erro ao criar arquivo .env: {e}")

# Caregar variáveis de ambiente de forma segura
safe_load_dotenv()

class Config:
    """
    Configuração centralizada para o sistema B3 com suporte a Selenium.
    Versão robusta que trata problemas de codificação.
    """
    
    # ==========================================
    # FLASK APP SETTINGS
    # ==========================================
    DEBUG = os.getenv('FLASK_ENV', 'production') == 'development'
    TESTING = False

    # AWS — somente via ambiente (.env local ou secrets no CI/deploy); nunca commitar chaves
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID') or ''
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY') or ''
    AWS_DEFAULT_REGION = os.getenv('AWS_DEFAULT_REGION', 'sa-east-1')

    # S3 Bucket - usando valor padrão se não configurado
    SCRAPING_TARGET_S3_BUCKET = os.getenv('SCRAPING_TARGET_S3_BUCKET', 'your-s3-bucket-name')
    
    # Prefixos S3 para organização
    S3_PREFIX_RAW = os.getenv('S3_PREFIX_RAW', 'data')
    S3_PREFIX_PROCESSED = os.getenv('S3_PREFIX_PROCESSED', 'processed')
    
    # ==========================================
    # ATHENA CONFIGURATIONS
    # ==========================================
    ATHENA_DATABASE = os.getenv('ATHENA_DATABASE', 'your_athena_database')
    ATHENA_OUTPUT_LOCATION = os.getenv('ATHENA_OUTPUT_LOCATION', f's3://{SCRAPING_TARGET_S3_BUCKET}/athena-query-results/')
    ATHENA_TABLE_NAME = os.getenv('ATHENA_TABLE_NAME', 'ibovespa_composition')
    
    # ==========================================
    # SELENIUM CONFIGURATIONS
    # ==========================================
    B3_URL = "https://sistemaswebb3-listados.b3.com.br/indexPage/day/IBOV?language=pt-br"
    
    # Configurações do WebDriver
    SELENIUM_HEADLESS = os.getenv('SELENIUM_HEADLESS', 'True').lower() == 'true'
    SELENIUM_TIMEOUT = int(os.getenv('SELENIUM_TIMEOUT', '30'))
    SELENIUM_IMPLICIT_WAIT = int(os.getenv('SELENIUM_IMPLICIT_WAIT', '10'))
    SELENIUM_PAGE_LOAD_TIMEOUT = int(os.getenv('SELENIUM_PAGE_LOAD_TIMEOUT', '30'))
    
    # Configurações do Chrome
    CHROME_OPTIONS = {
        'headless': SELENIUM_HEADLESS,
        'no_sandbox': True,
        'disable_dev_shm_usage': True,
        'disable_gpu': True,
        'window_size': '1920,1080',
        'disable_extensions': True,
        'disable_logging': True,
        'silent': True,
        'disable_web_security': False,
        'disable_features': 'VizDisplayCompositor'
    }
    
    # ==========================================
    # DATA PROCESSING CONFIGURATIONS
    # ==========================================
    PARQUET_ENGINE = os.getenv('PARQUET_ENGINE', 'pyarrow')
    PARQUET_COMPRESSION = os.getenv('PARQUET_COMPRESSION', 'snappy')
    PARTITION_COLUMNS = ['ano', 'mes', 'dia']
    
    # Validação de qualidade
    PARTICIPACAO_TOTAL_MIN = float(os.getenv('PARTICIPACAO_TOTAL_MIN', '95.0'))
    PARTICIPACAO_TOTAL_MAX = float(os.getenv('PARTICIPACAO_TOTAL_MAX', '105.0'))
    PARTICIPACAO_INDIVIDUAL_MAX = float(os.getenv('PARTICIPACAO_INDIVIDUAL_MAX', '15.0'))
    
    # Validação de tickers
    TICKER_LENGTH_MIN = int(os.getenv('TICKER_LENGTH_MIN', '4'))
    TICKER_LENGTH_MAX = int(os.getenv('TICKER_LENGTH_MAX', '6'))
    
    # Número esperado de ativos
    MIN_EXPECTED_ASSETS = int(os.getenv('MIN_EXPECTED_ASSETS', '80'))
    MAX_EXPECTED_ASSETS = int(os.getenv('MAX_EXPECTED_ASSETS', '120'))
    
    # ==========================================
    # LOGGING CONFIGURATIONS
    # ==========================================
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Diretórios
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "dados"
    LOGS_DIR = BASE_DIR / "logs"
    
    # Criar diretórios se não existirem
    try:
        DATA_DIR.mkdir(exist_ok=True)
        LOGS_DIR.mkdir(exist_ok=True)
    except Exception:
        pass  # Ignorar erros de criação de diretório
    
    LOG_FILE = LOGS_DIR / "b3_extraction.log"
    
    # ==========================================
    # RETRY E RATE LIMITING
    # ==========================================
    MAX_RETRY_ATTEMPTS = int(os.getenv('MAX_RETRY_ATTEMPTS', '3'))
    RETRY_DELAY_SECONDS = int(os.getenv('RETRY_DELAY_SECONDS', '5'))
    REQUEST_DELAY_SECONDS = float(os.getenv('REQUEST_DELAY_SECONDS', '1.0'))
    
    # ==========================================
    # CONFIGURAÇÕES POR AMBIENTE
    # ==========================================
    if DEBUG:
        SELENIUM_HEADLESS = False  # Mostrar navegador em desenvolvimento
        LOG_LEVEL = 'DEBUG'
        SELENIUM_TIMEOUT = 60
    
    # ==========================================
    # MÉTODOS DE VALIDAÇÃO
    # ==========================================
    
    @classmethod
    def validate_config(cls):
        """
        Valida as configurações e retorna lista de avisos/erros.
        """
        warnings = []
        
        # Validações AWS
        if not cls.AWS_ACCESS_KEY_ID:
            warnings.append("WARNING: AWS_ACCESS_KEY_ID não configurado. Operações AWS falharão.")
        elif cls.AWS_ACCESS_KEY_ID == '':
            warnings.append("WARNING: AWS_ACCESS_KEY_ID tem valor padrão. Configure suas credenciais reais.")
        
        if not cls.AWS_SECRET_ACCESS_KEY:
            warnings.append("WARNING: AWS_SECRET_ACCESS_KEY não configurado. Operações AWS falharão.")
        elif cls.AWS_SECRET_ACCESS_KEY == '':
            warnings.append("WARNING: AWS_SECRET_ACCESS_KEY tem valor padrão. Configure suas credenciais reais.")
        
        if not cls.SCRAPING_TARGET_S3_BUCKET:
            warnings.append("WARNING: SCRAPING_TARGET_S3_BUCKET não configurado. Upload S3 falhará.")
        elif cls.SCRAPING_TARGET_S3_BUCKET == '':
            warnings.append("WARNING: SCRAPING_TARGET_S3_BUCKET tem valor padrão. Configure seu bucket real.")
        
        # Validações numéricas
        if cls.PARTICIPACAO_TOTAL_MIN >= cls.PARTICIPACAO_TOTAL_MAX:
            warnings.append("ERROR: PARTICIPACAO_TOTAL_MIN deve ser menor que MAX")
        
        if cls.SELENIUM_TIMEOUT < 10:
            warnings.append("WARNING: SELENIUM_TIMEOUT muito baixo - pode causar falhas")
        
        return warnings
    
    @classmethod
    def get_chrome_options_list(cls):
        """
        Retorna lista de opções do Chrome para Selenium.
        """
        options = []
        
        if cls.CHROME_OPTIONS['headless']:
            options.append('--headless')
        
        if cls.CHROME_OPTIONS['no_sandbox']:
            options.append('--no-sandbox')
        
        if cls.CHROME_OPTIONS['disable_dev_shm_usage']:
            options.append('--disable-dev-shm-usage')
        
        if cls.CHROME_OPTIONS['disable_gpu']:
            options.append('--disable-gpu')
        
        if cls.CHROME_OPTIONS['window_size']:
            options.append(f"--window-size={cls.CHROME_OPTIONS['window_size']}")
        
        if cls.CHROME_OPTIONS['disable_extensions']:
            options.append('--disable-extensions')
        
        if cls.CHROME_OPTIONS['disable_logging']:
            options.append('--disable-logging')
        
        if cls.CHROME_OPTIONS['silent']:
            options.append('--silent')
        
        if cls.CHROME_OPTIONS.get('disable_features'):
            options.append(f"--disable-features={cls.CHROME_OPTIONS['disable_features']}")
        
        return options
    
    @classmethod
    def print_config_summary(cls):
        """
        Imprime resumo das configurações.
        """
        print("=" * 70)
        print("⚙️ CONFIGURAÇÕES DO SISTEMA B3")
        print("=" * 70)
        print(f"🌐 Ambiente: {'Desenvolvimento' if cls.DEBUG else 'Produção'}")
        print(f"🌐 URL B3: {cls.B3_URL}")
        print(f"🖥️ Selenium Headless: {cls.SELENIUM_HEADLESS}")
        print(f"⏱️ Timeout Selenium: {cls.SELENIUM_TIMEOUT}s")
        print(f"☁️ Bucket S3: {cls.SCRAPING_TARGET_S3_BUCKET}")
        print(f"🌍 Região AWS: {cls.AWS_DEFAULT_REGION}")
        print(f"🗂️ Engine Parquet: {cls.PARQUET_ENGINE}")
        print(f"📦 Compressão: {cls.PARQUET_COMPRESSION}")
        print(f"📝 Nível de Log: {cls.LOG_LEVEL}")
        print("=" * 70)
    
    @classmethod
    def setup_logging(cls):
        """
        Configura logging básico.
        """
        import logging
        
        try:
            logging.basicConfig(
                level=getattr(logging, cls.LOG_LEVEL, logging.INFO),
                format=cls.LOG_FORMAT,
                handlers=[
                    logging.StreamHandler(),
                    logging.FileHandler(cls.LOG_FILE, encoding='utf-8')
                ]
            )
        except Exception as e:
            # Fallback para logging básico se falhar
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s'
            )
            print(f"⚠️ Erro ao configurar logging completo: {e}")

# ==========================================
# VALIDAÇÃO E SETUP AUTOMÁTICO
# ==========================================

# Executar validação
_validation_warnings = Config.validate_config()
if _validation_warnings:
    print("\n⚠️ AVISOS DE CONFIGURAÇÃO:")
    for warning in _validation_warnings:
        print(f"   {warning}")
    print()

# Configurar logging
try:
    Config.setup_logging()
except Exception as e:
    print(f"⚠️ Erro ao configurar logging: {e}")

# Instância global para compatibilidade
config = Config()

# ==========================================
# TESTE DAS CONFIGURAÇÕES
# ==========================================

if __name__ == "__main__":
    print("🧪 TESTANDO CONFIGURAÇÕES...")
    
    # Exibir resumo
    Config.print_config_summary()
    
    # Validar configurações
    warnings = Config.validate_config()
    if warnings:
        print(f"\n⚠️ {len(warnings)} avisos:")
        for warning in warnings:
            print(f"   - {warning}")
    else:
        print("\n✅ Configurações válidas!")
    
    # Testar opções Chrome
    chrome_options = Config.get_chrome_options_list()
    print(f"\n🚗 Opções Chrome: {len(chrome_options)} configuradas")
    
    print("\n✅ Teste concluído!")
