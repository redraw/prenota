import os
import time
import math
import logging
import functools
from datetime import datetime, timezone

import telegram
from tqdm import tqdm

from selenium import webdriver
from selenium.webdriver.remote.remote_connection import LOGGER
LOGGER.setLevel(logging.INFO)

USUARIO = os.getenv("USUARIO")
PASSWORD = os.getenv("PASSWORD")
SEDE = os.getenv("SEDE")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_BOT_CHANNEL = os.getenv("TELEGRAM_BOT_CHANNEL")

bot = telegram.Bot(TELEGRAM_BOT_TOKEN)
bot_send_text = functools.partial(bot.send_message, chat_id=TELEGRAM_BOT_CHANNEL)
bot_send_photo = functools.partial(bot.send_photo, chat_id=TELEGRAM_BOT_CHANNEL)

chrome_options = webdriver.chrome.options.Options()
for opt in os.getenv("CHROME_OPTIONS", "").split(","):
    if opt: chrome_options.add_argument(opt)

WEBELEMENT_TIMEOUT = os.getenv("WEBELEMENT_TIMEOUT", 120)

driver = webdriver.Chrome(options=chrome_options, service_log_path="chromedriver.log")
driver.implicitly_wait(WEBELEMENT_TIMEOUT)

def get_countdown():
    utc_now = datetime.now(timezone.utc)
    utc_22_00 = datetime.now(timezone.utc).replace(hour=22, minute=0, second=0, microsecond=0)
    total = (utc_22_00 - utc_now).total_seconds()
    return math.floor(total) - int(os.getenv("MANIJA", "0"))

def wait_and_send_captcha(filename="captcha.png"):
    captcha = driver.find_element_by_css_selector("img[src*='captcha']")
    while not captcha.is_displayed():
        time.sleep(0.1)
    captcha.screenshot(filename)
    bot_send_photo(photo=open(filename, "rb"))

def wait_and_click_libre():
    driver.implicitly_wait(0)
    libres = []
    refreshs = 0
    while not libres:
        driver.refresh()
        refreshs += 1
        libres = driver.find_elements_by_css_selector(".calendarCellOpen input")
    print(f"Total refreshs: {refreshs}")
    libres[-1].click()
    bot_send_text(text="📗 Click dia libre")
    driver.implicitly_wait(WEBELEMENT_TIMEOUT)

if __name__ == '__main__':
    driver.get(f"https://prenotaonline.esteri.it/login.aspx?cidsede={SEDE}&returnUrl=%2f%2f")

    # LOGIN
    bot_send_text(text="🔒 Login")
    driver.find_element_by_name("BtnLogin").click()
    driver.find_element_by_name("UserName").send_keys(USUARIO)
    driver.find_element_by_name("Password").send_keys(PASSWORD)

    captcha = driver.find_element_by_name("loginCaptcha")
    wait_and_send_captcha()
    captcha.send_keys(input("CAPTCHA: "))
    driver.find_element_by_css_selector("input[value='Login']").click()

    # Navegando hacia el calendario
    driver.find_element_by_css_selector("input[value='Solicite un Turno']").click()
    driver.find_element_by_css_selector("input[value='Ciudadania']").click()
    driver.find_element_by_css_selector("input[value='Confirmación']").click()

    # CALENDARIO
    countdown = get_countdown()
    bot_send_text(text=f"🔪 Calendario (esperando {countdown}s)🔪")

    for i in tqdm(range(countdown), desc="Final countdown"):
        time.sleep(1)

    wait_and_click_libre()
    driver.find_element_by_css_selector("input[name='Confirmación']").click()
    
    # CAPTCHA CONFIRMACION
    bot_send_text(text="🔪 Esperando captcha confirmacion")
    captcha = driver.find_element_by_css_selector("input[name*='captcha']")
    wait_and_send_captcha()
    captcha.send_keys(input("CAPTCHA: "))
    driver.find_element_by_css_selector("input[value='Confirmación']").click()
