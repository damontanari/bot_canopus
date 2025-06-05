from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from time import sleep
from datetime import datetime
from dotenv import load_dotenv
import requests
import os
import tempfile

load_dotenv()

api_key = os.getenv("API_KEY")
site_key = os.getenv("SITE_KEY")
url_pagina = os.getenv("URL_PAGINA")
bot_token = os.getenv("BOT_TOKEN")
chat_id = os.getenv("CHAT_ID")
usuario = os.getenv("USUARIO")
senha = os.getenv("SENHA")
chromedriver_path = os.getenv("CHROMEDRIVER_PATH")

def enviar_telegram(mensagem):
    try:
        requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            data={"chat_id": chat_id, "text": mensagem, "parse_mode": "HTML"}
        )
    except Exception:
        pass

def iniciar_reservas(grupos, log_widget, progress_callback=None):
    """
    grupos: lista de grupos para reservar
    log_widget: objeto da interface com método log(msg)
    progress_callback: função que recebe um float (0.0 a 1.0) para atualizar a progress bar (opcional)
    """
    def log(msg):
        print(msg)
        log_widget.log(msg)

    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--start-maximized')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument(f'--user-data-dir={tempfile.mkdtemp()}')

    driver = webdriver.Chrome(service=Service(chromedriver_path), options=options)
    driver.get(url_pagina)
    sleep(3)

    log("🔐 Efetuando login...")
    driver.find_element(By.XPATH, "//input[@formcontrolname='Usuario']").send_keys(usuario)
    driver.find_element(By.XPATH, "//input[@formcontrolname='Senha']").send_keys(senha)
    driver.find_element(By.CSS_SELECTOR, "button.submit-button").click()
    sleep(3)

    total = len(grupos)
    for idx, grupo in enumerate(grupos, start=1):
        try:
            log(f"🔄 Reservando para grupo {grupo}")
            driver.get(url_pagina)
            sleep(2)

            # Clica no botão "Nova Reserva"
            botao = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[.//span[contains(text(), 'Nova Reserva')]]"))
            )
            driver.execute_script("arguments[0].click();", botao)
            sleep(2)

            # Campo de busca
            busca = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="mat-input-1"]'))
            )
            busca.clear()
            busca.send_keys(grupo)
            sleep(1)

            try:
                celulas = WebDriverWait(driver, 5).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "mat-cell.cdk-column-dataCadastro"))
                )
            except:
                log(f"⚠️ Nenhuma reserva encontrada para grupo {grupo}, voltando ao início...")
                enviar_telegram(f"⚠️ Nenhuma reserva para o grupo <b>{grupo}</b>.")

                # Fecha modal se aberto para evitar sobreposição
                try:
                    fechar = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'mat-icon-button') and .//mat-icon[text()='close']]"))
                    )
                    driver.execute_script("arguments[0].click();", fechar)
                    sleep(1)
                except:
                    pass

                driver.get(url_pagina)
                sleep(2)
                # Atualiza progress
                if progress_callback:
                    progress_callback(idx / total)
                continue

            log(f"✅ Reservas localizadas para o grupo {grupo}")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", celulas[0])
            sleep(0.5)
            driver.execute_script("arguments[0].click();", celulas[0])
            sleep(1)

            # Fecha modal para próxima iteração
            try:
                fechar = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'mat-icon-button') and .//mat-icon[text()='close']]"))
                )
                driver.execute_script("arguments[0].click();", fechar)
                sleep(1)
            except:
                pass

            driver.get(url_pagina)
            sleep(2)

            # Atualiza progresso
            if progress_callback:
                progress_callback(idx / total)

        except Exception as e:
            log(f"❌ Erro ao reservar para grupo {grupo}: {e}")
            try:
                driver.get(url_pagina)
                sleep(2)
            except:
                pass
            if progress_callback:
                progress_callback(idx / total)
            continue

    log("✅ Processo finalizado.")
    try:
        driver.quit()
    except Exception:
        pass
