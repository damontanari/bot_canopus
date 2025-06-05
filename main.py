from selenium import webdriver 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep
from datetime import datetime
from dotenv import load_dotenv
import requests
import os
import tempfile
from resolver_captcha import resolver_recaptcha

# Carregar variáveis de ambiente do .env
load_dotenv()

api_key = os.getenv("API_KEY")
site_key = os.getenv("SITE_KEY")
url_pagina = os.getenv("URL_PAGINA")
bot_token = os.getenv("BOT_TOKEN")
chat_id = os.getenv("CHAT_ID")
usuario = os.getenv("USUARIO")
senha = os.getenv("SENHA")
chromedriver_path = os.getenv("CHROMEDRIVER_PATH")
# Grupos fixos definidos direto no script, separados por ";"
grupos_str = "9115;9116;9206;9207;9208"
grupos = [g.strip() for g in grupos_str.split(";") if g.strip()]

def enviar_telegram(mensagem):
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            data={"chat_id": chat_id, "text": mensagem, "parse_mode": "HTML"}
        )
        print("📩 Mensagem enviada ao Telegram:", response.text)
    except Exception as e:
        print("❌ Falha no envio ao Telegram:", e)

def log(msg):
    print(f"{datetime.now().strftime('%H:%M:%S')} - {msg}")

def main():
    log("🔐 Realizando login...")
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    user_data_dir = tempfile.mkdtemp()
    options.add_argument(f'--user-data-dir={user_data_dir}')

    service = Service(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service, options=options)

    driver.maximize_window()
    driver.get(url_pagina)
    sleep(3)

    driver.find_element(By.XPATH, "//input[@formcontrolname='Usuario']").send_keys(usuario)
    sleep(1)
    driver.find_element(By.XPATH, "//input[@formcontrolname='Senha']").send_keys(senha)
    sleep(1)
    driver.find_element(By.CSS_SELECTOR, "button.submit-button").click()
    sleep(1)

    log("📄 Acessando área de Reserva de Cotas...")
    reserva_cotas = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Reserva de Cotas')]"))
    )
    driver.execute_script("arguments[0].click();", reserva_cotas)
    driver.switch_to.window(driver.window_handles[-1])

    sleep(2)

    contador = 0
    while True:
        for grupo in grupos:
            contador += 1
            log(f"🔄 Iniciando reserva para o grupo {grupo}...")
            enviar_telegram(f"🔄 Iniciando reserva para o grupo <code>{grupo}</code>...")

            try:
                nova_reserva = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[.//span[contains(text(), 'Nova Reserva')]]"))
                )
                driver.execute_script("arguments[0].click();", nova_reserva)
                sleep(1)

                campo_grupo = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//input[@formcontrolname='filterGrupos']"))
                )
                sleep(1)

                tentativas, grupo_digitado = 0, False
                while tentativas < 3 and not grupo_digitado:
                    try:
                        ActionChains(driver).move_to_element(campo_grupo).click().perform()
                        sleep(1)

                        # Limpar campo via JS
                        driver.execute_script("arguments[0].value = '';", campo_grupo)
                        sleep(0.5)

                        # Enviar texto caractere a caractere
                        for char in grupo:
                            campo_grupo.send_keys(char)
                            sleep(0.2)

                        # Disparar eventos para o input ser reconhecido
                        driver.execute_script("""
                            const el = arguments[0];
                            ['input', 'change', 'keydown', 'keyup'].forEach(evt =>
                                el.dispatchEvent(new Event(evt, { bubbles: true }))
                            );
                        """, campo_grupo)
                        sleep(1)

                        valor_atual = campo_grupo.get_attribute("value").strip()
                        if valor_atual == grupo:
                            grupo_digitado = True
                            log(f"✅ Grupo {grupo} digitado no campo de busca com sucesso.")
                            enviar_telegram(f"✅ Grupo <b>{grupo}</b> digitado no campo de busca com sucesso.")
                        else:
                            tentativas += 1
                            log(f"⚠️ Campo preenchido incorretamente ('{valor_atual}'), tentando novamente...")
                    except Exception as e:
                        tentativas += 1
                        log(f"Erro ao tentar digitar grupo {grupo}: {e}")

                if not grupo_digitado:
                    enviar_telegram(f"❌ Falha ao digitar o grupo <b>{grupo}</b> após 3 tentativas.")
                    continue

                log(f"🔍 Procurando célula do grupo {grupo}...")
                try:
                    celulas = WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "mat-cell.cdk-column-dataCadastro"))
                    )
                except Exception as e:
                    log(f"❌ Timeout ou erro ao buscar células: {e}")
                    continue

                grupo_encontrado = False
                for idx, celula in enumerate(celulas):
                    texto = celula.text.strip()
                    log(f" - Celula[{idx}]: '{texto}'")
                    if texto.endswith(grupo):
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", celula)
                        sleep(1)
                        driver.execute_script("arguments[0].click();", celula)
                        grupo_encontrado = True
                        break

                if not grupo_encontrado:
                    enviar_telegram(f"⚠️ Grupo <b>{grupo}</b> não localizado.")
                    try:
                        botao_fechar_modal = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'mat-icon-button') and .//mat-icon[text()='close']]"))
                        )
                        botao_fechar_modal.click()
                        sleep(1)
                    except:
                        pass
                    continue

                log("🤖 Iniciando resolução do reCAPTCHA...")
                token = resolver_recaptcha(api_key, site_key, url_pagina)
                if token:
                    driver.execute_script("""
                        let field = document.getElementById('g-recaptcha-response');
                        if (!field) {
                            field = document.createElement('textarea');
                            field.id = 'g-recaptcha-response';
                            field.name = 'g-recaptcha-response';
                            field.style = 'display:none';
                            document.body.appendChild(field);
                        }
                        field.innerHTML = arguments[0];
                        field.dispatchEvent(new Event('input', { bubbles: true }));
                        field.dispatchEvent(new Event('change', { bubbles: true }));
                    """, token)
                    sleep(3)

                    botao_reservar = WebDriverWait(driver, 15).until(
                        EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Reservar')]"))
                    )
                    driver.execute_script("arguments[0].click();", botao_reservar)
                    enviar_telegram(f"✅ Grupo <b>{grupo}</b> reservado com sucesso.")
                else:
                    enviar_telegram(f"❌ Falha ao resolver o reCAPTCHA para o grupo <b>{grupo}</b>.")
            except Exception as erro:
                enviar_telegram(f"⚠️ Erro inesperado com o grupo <b>{grupo}</b>: {erro}")

            sleep(3)

        enviar_telegram(f"🔁 Ciclo finalizado às {datetime.now().strftime('%H:%M:%S')} após verificar {contador} grupos.")
        driver.refresh()
        sleep(5)

if __name__ == "__main__":
    main()
