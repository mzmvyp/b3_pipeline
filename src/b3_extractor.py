# src/b3_selenium_extractor.py - Versão Corrigida para Problemas de WebDriver
from datetime import datetime
import pandas as pd
import logging
import os
import platform
import subprocess
import shutil
from pathlib import Path

# Configuração de logging
logger = logging.getLogger(__name__)

# URL do site da B3
B3_URL = "https://sistemaswebb3-listados.b3.com.br/indexPage/day/IBOV?language=pt-br"

def verificar_chrome_instalado():
    """
    Verifica se o Google Chrome está instalado no sistema.
    
    Returns:
        tuple: (bool, str) - (está_instalado, caminho_ou_erro)
    """
    system = platform.system().lower()
    
    try:
        if system == "windows":
            # Possíveis localizações do Chrome no Windows
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.getenv('USERNAME', '')),
            ]
            
            for path in chrome_paths:
                if os.path.exists(path):
                    return True, path
            
            # Tentar encontrar via registro do Windows
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe") as key:
                    chrome_path = winreg.QueryValue(key, "")
                    if os.path.exists(chrome_path):
                        return True, chrome_path
            except:
                pass
                
        elif system == "linux":
            # Linux
            chrome_commands = ["google-chrome", "google-chrome-stable", "chromium-browser", "chromium"]
            for cmd in chrome_commands:
                if shutil.which(cmd):
                    return True, cmd
                    
        elif system == "darwin":
            # macOS
            chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            if os.path.exists(chrome_path):
                return True, chrome_path
        
        return False, "Chrome não encontrado no sistema"
        
    except Exception as e:
        return False, f"Erro ao verificar Chrome: {e}"

def limpar_cache_webdriver():
    """
    Limpa o cache do webdriver-manager para forçar novo download.
    """
    try:
        # Localizar diretório do cache
        home_dir = Path.home()
        cache_dirs = [
            home_dir / ".wdm",
            home_dir / "AppData" / "Local" / "Temp" / ".wdm",  # Windows
        ]
        
        for cache_dir in cache_dirs:
            if cache_dir.exists():
                logger.info(f"🗑️ Limpando cache WebDriver: {cache_dir}")
                shutil.rmtree(cache_dir, ignore_errors=True)
                
        logger.info("✅ Cache WebDriver limpo")
        
    except Exception as e:
        logger.warning(f"⚠️ Erro ao limpar cache WebDriver: {e}")

def baixar_chromedriver_manual():
    """
    Baixa o ChromeDriver manualmente como fallback.
    
    Returns:
        str: Caminho para o ChromeDriver ou None se falhar
    """
    try:
        import requests
        import zipfile
        import tempfile
        
        # Detectar versão do Chrome
        chrome_version = obter_versao_chrome()
        if not chrome_version:
            return None
        
        # Determinar URL de download baseado na versão
        major_version = chrome_version.split('.')[0]
        
        # URLs da API do ChromeDriver
        if int(major_version) >= 115:
            # Nova API para versões 115+
            api_url = f"https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_{major_version}"
        else:
            # API antiga
            api_url = f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{major_version}"
        
        logger.info(f"🔍 Buscando ChromeDriver para Chrome {chrome_version}")
        
        # Obter versão exata do ChromeDriver
        response = requests.get(api_url, timeout=10)
        if response.status_code != 200:
            return None
            
        driver_version = response.text.strip()
        
        # Determinar plataforma
        system = platform.system().lower()
        arch = platform.architecture()[0]
        
        if system == "windows":
            platform_suffix = "win32" if arch == "32bit" else "win64"
            exe_suffix = ".exe"
        elif system == "linux":
            platform_suffix = "linux64"
            exe_suffix = ""
        elif system == "darwin":
            platform_suffix = "mac64" if arch == "64bit" else "mac32"
            exe_suffix = ""
        else:
            return None
        
        # URL de download
        if int(major_version) >= 115:
            download_url = f"https://storage.googleapis.com/chrome-for-testing-public/{driver_version}/{platform_suffix}/chromedriver-{platform_suffix}.zip"
        else:
            download_url = f"https://chromedriver.storage.googleapis.com/{driver_version}/chromedriver_{platform_suffix}.zip"
        
        logger.info(f"📥 Baixando ChromeDriver de: {download_url}")
        
        # Baixar arquivo
        response = requests.get(download_url, timeout=30)
        if response.status_code != 200:
            return None
        
        # Extrair para diretório temporário
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = Path(temp_dir) / "chromedriver.zip"
            
            with open(zip_path, 'wb') as f:
                f.write(response.content)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Encontrar executável do ChromeDriver
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file.startswith("chromedriver") and file.endswith(exe_suffix):
                        source_path = Path(root) / file
                        
                        # Mover para diretório permanente
                        target_dir = Path.home() / ".chromedriver_manual"
                        target_dir.mkdir(exist_ok=True)
                        target_path = target_dir / f"chromedriver{exe_suffix}"
                        
                        shutil.copy2(source_path, target_path)
                        
                        # Dar permissão de execução (Linux/Mac)
                        if system != "windows":
                            os.chmod(target_path, 0o755)
                        
                        logger.info(f"✅ ChromeDriver salvo em: {target_path}")
                        return str(target_path)
        
        return None
        
    except Exception as e:
        logger.error(f"❌ Erro no download manual do ChromeDriver: {e}")
        return None

def obter_versao_chrome():
    """
    Obtém a versão do Chrome instalado.
    
    Returns:
        str: Versão do Chrome ou None se não conseguir obter
    """
    try:
        system = platform.system().lower()
        
        if system == "windows":
            # Tentar via registro
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon") as key:
                    version = winreg.QueryValueEx(key, "version")[0]
                    return version
            except:
                pass
            
            # Tentar via comando
            try:
                result = subprocess.run([
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe", "--version"
                ], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return result.stdout.strip().split()[-1]
            except:
                pass
                
        elif system == "linux":
            commands = ["google-chrome --version", "google-chrome-stable --version", "chromium --version"]
            for cmd in commands:
                try:
                    result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        return result.stdout.strip().split()[-1]
                except:
                    continue
                    
        elif system == "darwin":
            try:
                result = subprocess.run([
                    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--version"
                ], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return result.stdout.strip().split()[-1]
            except:
                pass
        
        return None
        
    except Exception as e:
        logger.warning(f"⚠️ Erro ao obter versão do Chrome: {e}")
        return None

def configurar_driver_robusto():
    """
    Configura o WebDriver com múltiplas estratégias de fallback.
    
    Returns:
        webdriver.Chrome: Driver configurado ou None se falhar
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    
    # Verificar se Chrome está instalado
    chrome_ok, chrome_info = verificar_chrome_instalado()
    if not chrome_ok:
        logger.error(f"❌ Google Chrome não está instalado: {chrome_info}")
        logger.error("💡 Instale o Google Chrome antes de continuar")
        return None
    
    logger.info(f"✅ Chrome encontrado: {chrome_info}")
    
    # Configurar opções do Chrome
    chrome_options = Options()
    
    # Obter opções das configurações
    try:
        from src.config import Config
        options_list = Config.get_chrome_options_list()
        for option in options_list:
            chrome_options.add_argument(option)
    except:
        # Fallback para opções básicas
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
    
    # Adicionar opções específicas para Windows
    if platform.system().lower() == "windows":
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")
    
    # Estratégia 1: Tentar com webdriver-manager
    logger.info("🔧 Estratégia 1: Tentando webdriver-manager...")
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        
        # Instalar/obter ChromeDriver
        driver_path = ChromeDriverManager().install()
        logger.info(f"📍 ChromeDriver obtido: {driver_path}")
        
        # Verificar se o arquivo é válido
        if os.path.exists(driver_path) and os.path.getsize(driver_path) > 1000:
            service = Service(driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("✅ WebDriver configurado com webdriver-manager")
            return driver
        else:
            logger.warning("⚠️ ChromeDriver inválido do webdriver-manager")
            
    except Exception as e:
        logger.warning(f"⚠️ Webdriver-manager falhou: {e}")
    
    # Estratégia 2: Limpar cache e tentar novamente
    logger.info("🔧 Estratégia 2: Limpando cache e tentando novamente...")
    try:
        limpar_cache_webdriver()
        
        from webdriver_manager.chrome import ChromeDriverManager
        driver_path = ChromeDriverManager().install()
        
        if os.path.exists(driver_path) and os.path.getsize(driver_path) > 1000:
            service = Service(driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("✅ WebDriver configurado após limpeza de cache")
            return driver
            
    except Exception as e:
        logger.warning(f"⚠️ Segunda tentativa falhou: {e}")
    
    # Estratégia 3: Download manual
    logger.info("🔧 Estratégia 3: Download manual do ChromeDriver...")
    try:
        driver_path = baixar_chromedriver_manual()
        
        if driver_path and os.path.exists(driver_path):
            service = Service(driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("✅ WebDriver configurado com download manual")
            return driver
            
    except Exception as e:
        logger.warning(f"⚠️ Download manual falhou: {e}")
    
    # Estratégia 4: Tentar ChromeDriver no PATH
    logger.info("🔧 Estratégia 4: Tentando ChromeDriver no PATH...")
    try:
        # Assumir que chromedriver está no PATH
        driver = webdriver.Chrome(options=chrome_options)
        logger.info("✅ WebDriver configurado usando ChromeDriver do PATH")
        return driver
        
    except Exception as e:
        logger.warning(f"⚠️ ChromeDriver do PATH falhou: {e}")
    
    logger.error("❌ Todas as estratégias de configuração do WebDriver falharam")
    return None

def limpar_numero(texto):
    """
    Função para limpar e converter os números do formato brasileiro.
    
    Args:
        texto (str): Texto com número no formato brasileiro
        
    Returns:
        float: Número convertido para float
    """
    try:
        if not texto or texto.strip() == '':
            return 0.0
        numero_limpo = texto.replace('.', '').replace(',', '.')
        return float(numero_limpo)
    except (ValueError, AttributeError) as e:
        logger.warning(f"⚠️ Erro ao converter '{texto}' para número: {e}")
        return 0.0

def extrair_dados_da_pagina_atual(driver):
    """
    Extrai os dados da tabela na página visível no momento.
    
    Args:
        driver: WebDriver do Selenium
        
    Returns:
        list: Lista de dicionários com dados das ações
    """
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException
    
    dados_acoes_pagina = []
    
    try:
        # Espera a tabela estar visível
        tabela = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )
        
        # Pula a primeira linha que é o cabeçalho
        linhas = tabela.find_elements(By.TAG_NAME, "tr")[1:]
        
        for linha in linhas:
            celulas = linha.find_elements(By.TAG_NAME, "td")
            if len(celulas) == 5:
                try:
                    dados_acao = {
                        "ticker": celulas[0].text.strip(),
                        "nome_empresa": celulas[1].text.strip(),
                        "tipo_acao": celulas[2].text.strip(),
                        "qtde_teorica": int(limpar_numero(celulas[3].text.strip())),
                        "participacao": limpar_numero(celulas[4].text.strip()),
                    }
                    dados_acoes_pagina.append(dados_acao)
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao processar linha da tabela: {e}")
                    continue
                    
    except TimeoutException:
        logger.error("❌ A tabela não foi encontrada na página atual")
    except Exception as e:
        logger.error(f"❌ Erro inesperado ao extrair dados da página: {e}")
    
    return dados_acoes_pagina

def navegar_proxima_pagina(driver):
    """
    Navega para a próxima página se disponível.
    
    Args:
        driver: WebDriver do Selenium
        
    Returns:
        bool: True se conseguiu navegar, False se chegou ao fim
    """
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    
    try:
        # Encontra o elemento <li> que contém o botão "Próxima"
        li_proxima_pagina = driver.find_element(By.CSS_SELECTOR, ".pagination-next")
        
        # Se a classe 'disabled' estiver presente, chegamos ao fim
        if 'disabled' in li_proxima_pagina.get_attribute('class'):
            logger.info("📄 Chegamos na última página")
            return False
        
        # Encontra o link <a> dentro do <li> e clica
        botao_proxima_pagina = li_proxima_pagina.find_element(By.TAG_NAME, "a")
        
        # Pega uma referência da tabela atual para esperar ela mudar
        primeiro_codigo_antes = driver.find_element(
            By.CSS_SELECTOR, "tbody tr:first-child td:first-child"
        ).text
        
        botao_proxima_pagina.click()
        logger.info("🔄 Navegando para próxima página...")
        
        # Espera a tabela mudar
        WebDriverWait(driver, 15).until(
            lambda d: d.find_element(
                By.CSS_SELECTOR, "tbody tr:first-child td:first-child"
            ).text != primeiro_codigo_antes
        )
        
        return True
        
    except NoSuchElementException:
        logger.info("📄 Botão 'Próxima' não encontrado - fim da paginação")
        return False
    except TimeoutException:
        logger.error("⏱️ Timeout ao aguardar nova página carregar")
        return False
    except Exception as e:
        logger.error(f"❌ Erro ao navegar para próxima página: {e}")
        return False

def extrair_dados_ibovespa_selenium():
    """
    Função principal para fazer o scraping completo da composição do IBOVESPA.
    
    Returns:
        pd.DataFrame: DataFrame com todos os dados extraídos
    """
    logger.info("🚀 Iniciando extração de dados do IBOVESPA via Selenium")
    
    driver = None
    todos_os_dados = []
    
    try:
        # Configurar driver com estratégias robustas
        driver = configurar_driver_robusto()
        
        if not driver:
            logger.error("❌ Não foi possível configurar o WebDriver")
            return pd.DataFrame()
        
        logger.info(f"🌐 Acessando URL: {B3_URL}")
        driver.get(B3_URL)
        
        # Espera inicial para a primeira página carregar
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import TimeoutException
        
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table"))
        )
        logger.info("✅ Página inicial carregada com sucesso")
        
        pagina_atual = 1
        
        # Loop através de todas as páginas
        while True:
            logger.info(f"📊 Extraindo dados da Página {pagina_atual}...")
            
            # Extrai os dados da página visível
            dados_da_pagina = extrair_dados_da_pagina_atual(driver)
            
            if dados_da_pagina:
                todos_os_dados.extend(dados_da_pagina)
                logger.info(f"✅ {len(dados_da_pagina)} ativos extraídos desta página")
            else:
                logger.warning("⚠️ Nenhum dado encontrado na página atual")
                break
            
            # Tenta navegar para a próxima página
            if not navegar_proxima_pagina(driver):
                break
                
            pagina_atual += 1
        
        # Criar DataFrame com os dados extraídos
        if todos_os_dados:
            df = pd.DataFrame(todos_os_dados)
            
            # Adicionar metadados de extração
            agora = datetime.now()
            df['data_extracao'] = agora.strftime('%Y-%m-%d %H:%M:%S') 
            df['ano'] = agora.year
            df['mes'] = agora.month
            df['dia'] = agora.day
            
            logger.info(f"✅ Extração concluída com sucesso!")
            logger.info(f"📊 Total de ativos extraídos: {len(df)}")
            logger.info(f"📊 Participação total: {df['participacao'].sum():.2f}%")
            
            return df
        else:
            logger.error("❌ Nenhum dado foi extraído")
            return pd.DataFrame()
            
    except TimeoutException:
        logger.error("❌ Timeout: A página inicial não carregou dentro do tempo esperado")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"❌ Erro durante a extração: {e}")
        return pd.DataFrame()
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("🔒 WebDriver encerrado")
            except:
                pass

if __name__ == "__main__":
    # Configurar logging para teste
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logger.info("--- Testando b3_selenium_extractor.py corrigido ---")
    
    # Testar verificação do Chrome
    chrome_ok, chrome_info = verificar_chrome_instalado()
    print(f"Chrome: {'✅' if chrome_ok else '❌'} {chrome_info}")
    
    if chrome_ok:
        # Testar extração
        df_resultado = extrair_dados_ibovespa_selenium()
        
        if not df_resultado.empty:
            print(f"\n✅ Sucesso! {len(df_resultado)} ativos extraídos")
            print("\n📊 Primeiras 5 linhas:")
            print(df_resultado.head())
        else:
            print("❌ Falha na extração dos dados")
    else:
        print("❌ Instale o Google Chrome antes de continuar")
    
    logger.info("--- Teste concluído ---")