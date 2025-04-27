from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium import webdriver
import logging
import time

logging.basicConfig(level = logging.INFO, format = "%(asctime)s [%(levelname)s] %(message)s", handlers = [logging.FileHandler("sms.log", encoding="utf-8"), logging.StreamHandler()])

logging.getLogger("selenium").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

phones = ["5561991713088", "5561981561420", "5561981155209", "5561991816002"]

message = (
    "Está difícil acompanhar os valores do seu cartão consignado? Posso te ajudar a organizar isso, mudando para um banco com parcelas fixas + previsibilidade e ainda com um novo cartão e dinheiro na conta, apenas clique no link: https://wa.me/message/XGZWEYOO3PUXA1 e será redirecionado para um de nossos correspondentes.."
)

def main():
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

        # loop de envio
        for numero in phones:
            logger.info(f"Iniciando envio para {numero!r}")

            try:
                # clica no “Iniciar chat”
                selector_nova = "mw-fab-link.start-chat > a"
                btn_nova = WebDriverWait(driver, 20).until(
                                                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector_nova))
                                                                                                                                )

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

                inp_num = WebDriverWait(driver, 20).until(
                                                                EC.presence_of_element_located((By.CSS_SELECTOR, selector_num))
                                                                                                                                    )
                inp_num.clear()
                inp_num.click()
                inp_num.send_keys(numero)
                
                time.sleep(7)  

                inp_num.send_keys(Keys.ENTER)

                logger.info("Número digitado e enviado.")

                # localiza a caixa de texto da mensagem e envia
                # caixa_msg = WebDriverWait(driver, 20).until(
                #     EC.presence_of_element_located((By.CSS_SELECTOR, "div[contenteditable='true']"))
                # )
                # caixa_msg.click()
                # caixa_msg.send_keys(mensagem)
                # time.sleep(1)
                # caixa_msg.send_keys(Keys.ENTER)
                # logger.info(f"Mensagem enviada para {numero!r}")
                
                # Espera até que a caixa de mensagem esteja presente e visível
                try:
                    caixa_msg = WebDriverWait(driver, 30).until(
                                                                        EC.presence_of_element_located((By.CSS_SELECTOR, "textarea.input"))
                                                                                                                                                    )
                    time.sleep(2)
                    caixa_msg.click()
                    time.sleep(3)
                    caixa_msg.send_keys(message)
                    time.sleep(3)
                    caixa_msg.send_keys(Keys.ENTER)
                    logger.info(f"Mensagem enviada com sucesso para o número {numero}.")
                    
                    campos = driver.find_elements(By.CSS_SELECTOR, "div[contenteditable='true']")

                    for i, c in enumerate(campos):
                        print(f"Caixa {i}: {c.get_attribute('outerHTML')}")
                    
                except TimeoutException:
                    logger.error("Não foi possível localizar a caixa de mensagem.")


                time.sleep(2)

            except TimeoutException:
                logger.error(f"Timeout ao tentar enviar para {numero!r}", exc_info = True)
            except Exception:
                logger.exception(f"Erro inesperado ao enviar mensagem para {numero!r}")

    except TimeoutException:
        logger.error("Timeout aguardando o scan do QR Code.", exc_info = True)
    except Exception:
        logger.exception("Falha inesperada durante o fluxo principal")
    finally:
        logger.info("Encerrando o driver e finalizando o script")
        driver.quit()

if __name__ == "__main__":
    main()