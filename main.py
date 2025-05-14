from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium import webdriver
from tqdm import tqdm
import pandas as pd
import logging
import time

def ler_telefones_csv(caminho_arquivo: str) -> list[str]:
    """ Lê um CSV com uma coluna chamada 'telefone' e retorna uma lista de strings (sem nulos ou espaços em branco) """
    df = pd.read_csv(caminho_arquivo, dtype = str) # força todas as colunas como string
    
    # vai ler o primeiro como telefone
    telefones = df["telefone"].dropna().str.strip().tolist()
    
    return telefones

logging.basicConfig(level = logging.INFO, format = "%(asctime)s [%(levelname)s] %(message)s", handlers = [logging.FileHandler("sms.log", encoding = "utf-8"), logging.StreamHandler()])

logging.getLogger("selenium").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# caminho .csv
phones = ler_telefones_csv("./phonesToBeRead/script_sms.csv")

mensagem = (
    "Está difícil acompanhar os valores do seu cartão consignado? Posso te ajudar a organizar isso, mudando para um banco com parcelas fixas + previsibilidade e ainda com um novo cartão e dinheiro na conta, apenas clique no link: https://wa.me/message/XGZWEYOO3PUXA1 e será redirecionado para um de nossos correspondentes.."
)

def main():
    df = pd.DataFrame(phones, columns = ["telefone"])
    df["status"] = "" # guarda success ou error
    df["timestamp"] = None
    
    logger.info("===> Iniciando o ChromeDriver")
    driver = webdriver.Chrome()
    
    try:
        driver.maximize_window()
        logger.debug("Janela do navegador maximizada.")

        logger.info("Acessando Messages Web")
        driver.get("https://messages.google.com/web")

        logger.info("Aguardando scan do QR Code (até 120s)…")
        
        wait = WebDriverWait(driver, 120)
        
        # aguarda até que o botão “Iniciar chat” exista no DOM, sinal de que você escaneou o QR
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[data-e2e-start-button]")))
        logger.info("QR Code escaneado com sucesso!")

        for idx, numero in enumerate(tqdm(phones, desc = "Enviando SMS", unit = "sms")):
            logger.info(f"Iniciando envio para {numero!r}")
            
            try:
                # clica no “Iniciar chat”
                selector_nova = "mw-fab-link.start-chat > a"
                btn_nova = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector_nova)))

                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn_nova)
                
                try:
                    btn_nova.click()
                    logger.info("Clique normal funcionou no 'Iniciar chat'")
                    
                except WebDriverException:
                    logger.warning("Clique normal falhou, forçando com JS")
                    driver.execute_script("arguments[0].click();", btn_nova)
                    logger.info("Clique forçado funcionou")
                
                # localiza o campo de número 
                selector_num = "input[placeholder*='nome'], input[placeholder*='number']"

                inp_num = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector_num)))
                inp_num.clear()
                inp_num.click()
                inp_num.send_keys(numero)
                
                time.sleep(7)  

                inp_num.send_keys(Keys.ENTER)

                logger.info("Número digitado e enviado.")

                try:
                    caixa_msg = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, "textarea.input")))
                    time.sleep(2)
                    caixa_msg.click()
                    time.sleep(3)
                    caixa_msg.send_keys(mensagem)
                    time.sleep(3)
                    caixa_msg.send_keys(Keys.ENTER)
                    logger.info(f"Mensagem enviada com sucesso para o número {numero}.")
                    
                    campos = driver.find_elements(By.CSS_SELECTOR, "div[contenteditable='true']")
                    
                    for i, c in enumerate(campos):
                        print(f"Caixa {i}: {c.get_attribute('outerHTML')}")
                        
                    df.at[idx, "status"] = "sucesso"
                    
                except TimeoutException:
                    logger.error("Não foi possível localizar a caixa de mensagem.")

                finally:
                    # registrar o horário da tentativaf
                    df.at[idx, "timestamp"] = pd.Timestamp.now()
                    time.sleep(2)

            except TimeoutException:
                logger.error(f"Timeout ao tentar enviar para {numero!r}", exc_info = True)
            
            except Exception:
                logger.exception(f"Erro inesperado ao enviar mensagem para {numero!r}")
                df.at[idx, "status"] = "erro"

    except TimeoutException:
        logger.error("Timeout aguardando o scan do QR Code.", exc_info = True)
        
    except Exception:
        logger.exception("Falha inesperada durante o fluxo principal")
        
    finally:
        logger.info("Encerrando o driver")
        driver.quit()
        
        # gerar o relatório
        df.to_csv("relatorio_sms.csv", index = False)
        print("\n Relatório gerado em relatorio_sms.csv")
        
        # so pra um pedacin
        print(df.head())

if __name__ == "__main__":
    main()