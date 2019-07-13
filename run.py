import os
import time
import math
import functools
from datetime import datetime, timezone

from tqdm import tqdm
from selenium import webdriver

import telegram

USUARIO = os.getenv("USUARIO")
PASSWORD = os.getenv("PASSWORD")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_BOT_CHANNEL = os.getenv("TELEGRAM_BOT_CHANNEL")

bot = telegram.Bot(TELEGRAM_BOT_TOKEN)
bot_send_text = functools.partial(bot.send_message, chat_id=TELEGRAM_BOT_CHANNEL)
bot_send_photo = functools.partial(bot.send_photo, chat_id=TELEGRAM_BOT_CHANNEL)

chrome_options = webdriver.chrome.options.Options()
for opt in os.getenv("CHROME_OPTIONS", "").split(","): 
    chrome_options.add_argument(opt)

WEBELEMENT_TIMEOUT = os.getenv("WEBELEMENT_TIMEOUT", 120)

driver = webdriver.Chrome(options=chrome_options)
driver.implicitly_wait(WEBELEMENT_TIMEOUT)

def countdown():
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

def wait_and_click_verde():
    driver.implicitly_wait(0)
    verdes = []
    refreshs = 0
    while not verdes:
        verdes = driver.find_elements_by_css_selector(".calendarCellOpen input")
        time.sleep(1)
        driver.refresh()
        refreshs += 1
    print(f"Refreshs: {refreshs}")
    verdes[-1].click()
    bot_send_text(text="📗 Click turno libre")
    driver.implicitly_wait(WEBELEMENT_TIMEOUT)

if __name__ == '__main__':
    driver.get('https://prenotaonline.esteri.it/login.aspx?cidsede=100086&returnUrl=%2f%2f')

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
    bot_send_text(text="🔪 Calendario 🔪")

    for i in tqdm(range(countdown()), desc="Final countdown"):
        time.sleep(1)

    wait_and_click_verde()
    driver.find_element_by_css_selector("input[value='Confirmación']").click()
    
    # CAPTCHA CONFIRMACION
    bot_send_text(text="🔪 Esperando captcha confirmacion")
    captcha = driver.find_element_by_css_selector("input[value*='aptcha']")
    wait_and_send_captcha()
    captcha.send_keys(input("CAPTCHA: "))
    driver.find_element_by_css_selector("input[value='Confirmación']").click()
