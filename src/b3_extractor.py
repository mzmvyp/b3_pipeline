# src/b3_extractor.py
from playwright.sync_api import sync_playwright
import io
import os
import tempfile

# URL do site da B3
B3_URL = "https://sistemaswebb3-listados.b3.com.br/indexPage/day/IBOV?language=pt-br"

def fetch_b3_downloaded_csv_content():
    """
    Usa Playwright para carregar a página da B3, clica no botão "Download",
    e captura o arquivo CSV baixado em memória.
    Retorna o conteúdo do CSV como uma string (latin-1).
    """
    print("Iniciando a captura do download do CSV com Playwright...")
    
    csv_content = None
    browser = None 

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True) # Use headless=True para produção
            page = browser.new_page()
            
            print(f"Navegando para: {B3_URL}")
            page.goto(B3_URL, timeout=60000, wait_until='networkidle')

            print("Esperando pelo link de download...")
            
            with page.expect_download() as download_info:
                print("Clicando no link de download...")
                page.click("a:has-text(\"Download\")", timeout=60000) 
            
            download = download_info.value
            
            with tempfile.TemporaryDirectory() as tmpdir:
                temp_file_path = os.path.join(tmpdir, download.suggested_filename)
                
                print(f"Salvando download temporariamente em: {temp_file_path}")
                download.save_as(temp_file_path)
                
                with open(temp_file_path, 'rb') as f:
                    csv_bytes = f.read()
                
                print(f"Download '{download.suggested_filename}' salvo e lido para a memória.")
            
            csv_content = csv_bytes.decode('latin-1') 

        except Exception as e:
            print(f"Ocorreu um erro durante a extração Playwright: {e}")
            return None 
        finally:
            if browser: 
                browser.close()
            
    return csv_content

if __name__ == '__main__':
    print("--- Testando src/b3_extractor.py diretamente ---")
    raw_csv = fetch_b3_downloaded_csv_content()
    if raw_csv:
        print(f"Conteúdo CSV bruto extraído (primeiros 500 caracteres):\n{raw_csv[:500]}...")
    else:
        print("Falha na extração do CSV.")
    print("--- Teste de b3_extractor.py concluído ---")