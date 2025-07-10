#!/usr/bin/env python3
"""
Script de correção rápida para problemas do Selenium no Windows
Execute este script para resolver automaticamente os problemas mais comuns
"""
import os
import sys
import subprocess
import requests
import zipfile
from pathlib import Path

def run_command(command, description):
    """Executa um comando e retorna o resultado."""
    print(f"🔄 {description}...")
    try:
        if isinstance(command, str):
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        else:
            result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(f"✅ {description} - OK")
            return True, result.stdout.strip()
        else:
            print(f"❌ {description} - Erro: {result.stderr.strip()}")
            return False, result.stderr.strip()
    except subprocess.TimeoutExpired:
        print(f"⏳ {description} - Timeout")
        return False, "Timeout"
    except Exception as e:
        print(f"❌ {description} - Exceção: {e}")
        return False, str(e)

def install_dependencies():
    """Instala dependências necessárias."""
    print("\n" + "="*50)
    print("📦 INSTALANDO DEPENDÊNCIAS")
    print("="*50)
    
    dependencies = [
        "selenium==4.15.2",
        "webdriver-manager==4.0.1", 
        "requests==2.31.0",
        "pandas==2.1.1"
    ]
    
    for dep in dependencies:
        success, output = run_command(f"pip install {dep}", f"Instalando {dep}")
        if not success:
            print(f"⚠️ Falha na instalação de {dep}, mas continuando...")

def download_chromedriver():
    """Baixa ChromeDriver manualmente."""
    print("\n" + "="*50)
    print("⬇️ BAIXANDO CHROMEDRIVER")
    print("="*50)
    
    try:
        # Criar diretório
        driver_dir = Path.cwd() / 'drivers'
        driver_dir.mkdir(exist_ok=True)
        print(f"✅ Diretório criado: {driver_dir}")
        
        # Verificar se já existe e funciona
        driver_path = driver_dir / 'chromedriver.exe'
        if driver_path.exists():
            success, output = run_command([str(driver_path), '--version'], "Testando ChromeDriver existente")
            if success:
                print(f"✅ ChromeDriver já existe e funciona: {driver_path}")
                return str(driver_path)
        
        # Obter versão mais recente
        print("🔍 Obtendo versão mais recente...")
        response = requests.get("https://chromedriver.storage.googleapis.com/LATEST_RELEASE", timeout=10)
        version = response.text.strip()
        print(f"✅ Versão mais recente: {version}")
        
        # Download
        url = f"https://chromedriver.storage.googleapis.com/{version}/chromedriver_win32.zip"
        print(f"⬇️ Baixando de: {url}")
        
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        # Salvar e extrair
        zip_path = driver_dir / 'chromedriver.zip'
        with open(zip_path, 'wb') as f:
            f.write(response.content)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(driver_dir)
        
        zip_path.unlink()  # Remove ZIP
        
        if driver_path.exists():
            print(f"✅ ChromeDriver baixado: {driver_path}")
            
            # Testar
            success, output = run_command([str(driver_path), '--version'], "Testando ChromeDriver baixado")
            if success:
                return str(driver_path)
        
        return None
        
    except Exception as e:
        print(f"❌ Erro no download: {e}")
        return None

def test_chrome():
    """Testa se o Chrome está instalado."""
    print("\n" + "="*50)
    print("🌐 TESTANDO GOOGLE CHROME")
    print("="*50)
    
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            success, output = run_command([path, '--version'], f"Testando Chrome em {path}")
            if success:
                print(f"✅ Chrome encontrado e funcionando")
                return True
    
    print("❌ Google Chrome não encontrado ou não funciona")
    print("📥 Baixe e instale de: https://www.google.com/chrome/")
    return False

def test_selenium():
    """Testa Selenium com ChromeDriver."""
    print("\n" + "="*50)
    print("🧪 TESTANDO SELENIUM")
    print("="*50)
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        
        print("✅ Imports do Selenium OK")
        
        # Configurar opções (MODO OCULTO)
        options = Options()
        options.add_argument("--headless")  # MODO OCULTO
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        print("🔒 Testando em modo OCULTO (navegador não aparecerá)")
        
        # Usar ChromeDriver local
        driver_path = Path.cwd() / 'drivers' / 'chromedriver.exe'
        
        if not driver_path.exists():
            print("❌ ChromeDriver local não encontrado")
            return False
        
        # Testar WebDriver
        print("🔧 Criando WebDriver...")
        service = Service(str(driver_path))
        driver = webdriver.Chrome(service=service, options=options)
        
        print("🌐 Testando navegação...")
        driver.get("https://www.google.com")
        title = driver.title
        
        driver.quit()
        
        print(f"✅ Selenium funcionando em modo OCULTO! Título obtido: {title}")
        print("🔒 Navegador executou sem aparecer na tela")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste Selenium: {e}")
        return False

def backup_old_extractor():
    """Faz backup do extrator antigo."""
    old_extractor = Path("src/b3_extractor.py")
    if old_extractor.exists():
        backup_path = Path("src/b3_extractor.py.bak")
        old_extractor.rename(backup_path)
        print(f"✅ Backup do extrator antigo salvo: {backup_path}")

def create_env_file():
    """Cria arquivo .env com configurações de modo oculto."""
    print("\n" + "="*50)
    print("📝 CRIANDO ARQUIVO .ENV")
    print("="*50)
    
    env_path = Path('.env')
    
    env_content = """# ==============================================
# CONFIGURAÇÕES AWS (OBRIGATÓRIAS)
# ==============================================
AWS_ACCESS_KEY_ID=sua_access_key_aqui
AWS_SECRET_ACCESS_KEY=sua_secret_key_aqui
AWS_DEFAULT_REGION=sa-east-1

# ==============================================
# CONFIGURAÇÕES S3 (OBRIGATÓRIAS)
# ==============================================
SCRAPING_TARGET_S3_BUCKET=your-s3-bucket-name

# ==============================================
# CONFIGURAÇÕES SELENIUM
# ==============================================
# MODO OCULTO - Navegador não aparece na tela (recomendado)
SELENIUM_HEADLESS=true

# Para DEBUG: ver o navegador funcionando, mude para false
# SELENIUM_HEADLESS=false

SELENIUM_MAX_RETRIES=3
SELENIUM_TIMEOUT=30

# ==============================================
# CONFIGURAÇÕES FLASK
# ==============================================
FLASK_ENV=development
"""
    
    if env_path.exists():
        # Ler arquivo existente e atualizar apenas as configurações do Selenium
        try:
            existing_content = env_path.read_text()
            
            # Se não tem configuração do Selenium, adicionar
            if 'SELENIUM_HEADLESS' not in existing_content:
                existing_content += "\n# Configuração Selenium\nSELENIUM_HEADLESS=true\n"
                env_path.write_text(existing_content)
                print("✅ Configuração SELENIUM_HEADLESS=true adicionada ao .env existente")
            else:
                print("✅ Arquivo .env já existe com configurações Selenium")
                
        except Exception as e:
            print(f"⚠️ Erro ao ler .env existente: {e}")
            print("✅ Criando novo arquivo .env")
            env_path.write_text(env_content)
    else:
        env_path.write_text(env_content)
        print("✅ Arquivo .env criado com configurações padrão")
        print("🔒 SELENIUM_HEADLESS=true configurado (modo oculto)")
        print("⚠️ IMPORTANTE: Configure suas credenciais AWS no arquivo .env")
    
    return True
    """Testa o novo extrator."""
    print("\n" + "="*50)
    print("🕷️ TESTANDO NOVO EXTRATOR B3")
    print("="*50)
    
    try:
        # Importar novo extrator
        sys.path.insert(0, 'src')
        from b3_extractor import fetch_b3_downloaded_csv_content
        
        print("✅ Novo extrator importado com sucesso")
        print("⚠️ Teste completo de scraping pode demorar alguns minutos...")
        print("📊 Para teste completo, execute: python src/b3_extractor.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao importar novo extrator: {e}")
        return False

def test_new_extractor():
    """Testa o novo extrator."""
    print("\n" + "="*50)
    print("🕷️ TESTANDO NOVO EXTRATOR B3")
    print("="*50)
    
    try:
        # Importar novo extrator
        sys.path.insert(0, 'src')
        from b3_extractor import fetch_b3_downloaded_csv_content
        
        print("✅ Novo extrator importado com sucesso")
        print("🔒 Configurado para rodar em modo OCULTO")
        print("⚠️ Teste completo de scraping pode demorar alguns minutos...")
        print("📊 Para teste completo, execute: python src/b3_extractor.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao importar novo extrator: {e}")
        return False

def main():
    """Executa correção completa."""
    print("🔧 CORREÇÃO RÁPIDA - SELENIUM WINDOWS")
    print("Este script vai corrigir automaticamente os problemas do Selenium")
    print("=" * 60)
    
    # 1. Instalar dependências
    install_dependencies()
    
    # 2. Criar/atualizar arquivo .env
    create_env_file()
    
    # 3. Testar Chrome
    chrome_ok = test_chrome()
    
    # 4. Baixar ChromeDriver
    if chrome_ok:
        driver_path = download_chromedriver()
        
        if driver_path:
            # 5. Testar Selenium
            selenium_ok = test_selenium()
            
            if selenium_ok:
                # 6. Backup e teste do novo extrator
                backup_old_extractor()
                extractor_ok = test_new_extractor()
                
                # Resumo final
                print("\n" + "="*60)
                print("📋 RESUMO FINAL")
                print("="*60)
                
                if extractor_ok:
                    print("🎉 CORREÇÃO CONCLUÍDA COM SUCESSO!")
                    print("✅ Todas as verificações passaram")
                    print("🔒 Sistema configurado em MODO OCULTO")
                    print("\n🚀 PRÓXIMOS PASSOS:")
                    print("1. Configure suas credenciais AWS no arquivo .env")
                    print("2. Execute: python src/b3_extractor.py")
                    print("3. Se funcionar, execute: python app.py")
                    print("4. Acesse: http://localhost:5000")
                    print("5. Teste a raspagem completa")
                    
                    print(f"\n📁 ARQUIVOS CRIADOS:")
                    print(f"- ChromeDriver: {driver_path}")
                    print(f"- Backup: src/b3_extractor.py.bak")
                    print(f"- Novo extrator: src/b3_extractor.py")
                    print(f"- Configuração: .env")
                    
                    print(f"\n🔒 MODO NAVEGADOR:")
                    print(f"- PADRÃO: Oculto (SELENIUM_HEADLESS=true)")
                    print(f"- Para ver navegador: mude SELENIUM_HEADLESS=false no .env")
                    print(f"- Guia completo: CONTROLE_NAVEGADOR.md")
                else:
                    print("⚠️ Problemas no novo extrator")
                    print("📋 Verifique os erros acima")
            else:
                print("❌ Selenium não está funcionando")
                print("🔧 Execute: python chrome_diagnostic.py")
        else:
            print("❌ Falha no download do ChromeDriver")
            print("🔧 Tente download manual ou execute chrome_diagnostic.py")
    else:
        print("❌ Google Chrome deve ser instalado primeiro")
        print("📥 Baixe de: https://www.google.com/chrome/")
    
    print("\n" + "="*60)
    print("Correção finalizada!")
    input("Pressione Enter para continuar...")

if __name__ == '__main__':
    main()