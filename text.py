import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

# --- Configurare Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Datele Dumneavoastră ---
HEYGEN_LOGIN_URL = "https://app.heygen.com/login"
USER_EMAIL = "igs013740@gmail.com"
USER_PASSWORD = "Parola.1234" 
VIDEO_TEXT = "Acest test a funcționat. Robotul a scris acest text și acum va crea un videoclip."

# --- Inițializare WebDriver ---
driver = None
try:
    logging.info("Inițializare driver Chrome...")
    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--start-maximized")
    
    service = ChromeService()
    driver = webdriver.Chrome(service=service, options=options)
    logging.info("Driver Chrome inițializat.")

    # --- Login ---
    logging.info(f"Navigare la: {HEYGEN_LOGIN_URL}")
    driver.get(HEYGEN_LOGIN_URL)
    wait = WebDriverWait(driver, 30)

    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="email"]'))).send_keys(USER_EMAIL)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="password"]'))).send_keys(USER_PASSWORD)
    time.sleep(1)
    wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(.,"Sign In")]'))).click()

    wait.until(EC.presence_of_element_located((By.XPATH, '//button[contains(.,"Create video")]')))
    logging.info("Login efectuat cu succes.")

    # --- PROCESUL DE CREARE VIDEO ---
    logging.info("Începere proces de creare video...")

    # Pas 1: Click pe "Create video".
    wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(.,"Create video")]'))).click()
    logging.info("Click pe butonul 'Create video'.")

    # Pas 2: Așteaptă și alege "Landscape".
    landscape_mode_selector = (By.XPATH, '//button[contains(.,"Create landscape video")]')
    wait.until(EC.element_to_be_clickable(landscape_mode_selector)).click()
    logging.info("Opțiunea 'Create landscape video' a fost selectată.")

    # ---- AICI SUNT MODIFICĂRILE IMPORTANTE ----

    # Pas 3: Așteaptă să apară elementul placeholder "Type your script here" și fă click pe el.
    # Folosim un XPath care caută orice element (*) ce conține textul respectiv.
    script_placeholder_selector = (By.XPATH, '//*[contains(text(), "Type your script")]')
    logging.info("Așteptare zonă de script...")
    script_placeholder = wait.until(EC.element_to_be_clickable(script_placeholder_selector))
    script_placeholder.click()
    logging.info("Click pe zona de script pentru a o activa.")

    # Pas 4: Acum că zona e activă, căutăm elementul <textarea> care a apărut.
    # Adesea, acesta nu are un placeholder, dar este acum vizibil și activ.
    active_textarea_selector = (By.CSS_SELECTOR, 'textarea.focus-visible') # Sau un alt selector mai specific, de ex. 'div.ProseMirror > textarea'
    logging.info("Așteptare câmp de text activ...")
    text_area = wait.until(EC.presence_of_element_located(active_textarea_selector))
    
    # Pas 5: Introducem textul.
    text_area.clear()
    text_area.send_keys(VIDEO_TEXT)
    logging.info("Textul a fost introdus.")
    time.sleep(2)

    # Pas 6: Apăsăm "Submit".
    submit_button_selector = (By.XPATH, '//button[contains(.,"Submit")]')
    wait.until(EC.element_to_be_clickable(submit_button_selector)).click()
    logging.info("Click pe butonul 'Submit'.")
    
    # Pas 7: Gestionăm posibila fereastră de confirmare.
    try:
        confirm_popup_button_selector = (By.XPATH, '//div[contains(@class, "rc-dialog")]//button[contains(.,"Submit")]')
        confirm_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(confirm_popup_button_selector))
        confirm_button.click()
        logging.info("Click pe butonul de confirmare finală.")
    except TimeoutException:
        logging.info("Nu a apărut o fereastră de confirmare suplimentară.")

    logging.info("SUCCES! Cererea de creare video a fost trimisă.")
    logging.info("Browser-ul se va închide în 20 de secunde.")
    time.sleep(20)

except (TimeoutException, NoSuchElementException, StaleElementReferenceException) as e:
    error_type = type(e).__name__
    logging.error(f"PUNCT SLAB: A apărut o eroare de tip '{error_type}'.")
    logging.error("Verificați selectorul pentru ultimul pas sau dacă interfața s-a schimbat.")
    try:
        screenshot_path = "screenshot_eroare.png"
        driver.save_screenshot(screenshot_path)
        logging.info(f"Captură de ecran salvată ca '{screenshot_path}'.")
    except Exception as screenshot_error:
        logging.error(f"Nu s-a putut salva captura de ecran: {screenshot_error}")
    time.sleep(15)
except Exception as e:
    logging.error(f"A apărut o eroare neașteptată: {e}")
    time.sleep(15)
finally:
    if driver:
        logging.info("Închidere driver Chrome.")
        driver.quit()