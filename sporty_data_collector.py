import os
from datetime import datetime
from time import sleep

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from dotenv import load_dotenv
import pickle
import json

load_dotenv()

service = webdriver.ChromeService(executable_path=os.getenv("CHROME_DRIVER_PATH"))
options = webdriver.ChromeOptions()
# options.add_argument(r"user-data-dir=" + "/home/balo/projects/aviator/chrome-data")
driver = webdriver.Chrome(service=service, options=options)
driver.set_window_size(1920, 1080)

def login(driver: webdriver.Chrome):
    driver.get('https://www.sportybet.com/ng/games?source=TopRibbon')
    phone = driver.find_element(By.NAME, "phone")
    phone.send_keys(os.getenv("PHONE"))
    password = driver.find_element(By.NAME, "psd")
    password.send_keys(os.getenv("PASSWORD"))
    login = driver.find_element(By.NAME, "logIn")
    login.click()
    sleep(5)

def launch_aviator(driver: webdriver.Chrome):
    iframe = driver.find_element(By.ID, "games-lobby")
    driver.switch_to.frame(iframe)
    driver.find_element(By.ID, 'game_item19').find_element(By.TAG_NAME, 'img').click()
    sleep(2)
    driver.refresh()
    sleep(15)

def get_data(driver: webdriver.Chrome):
    iframe = driver.find_element(By.ID, "games-lobby")
    driver.switch_to.frame(iframe)
    iframe = driver.find_element(By.CLASS_NAME, "turbo-games-iframe")
    driver.switch_to.frame(iframe)
    latest_game_round_multiplier = None
    while True:
        try:
            payout = driver.find_elements(By.CLASS_NAME, 'payout')[0]
            if payout.find_element(By.CLASS_NAME, 'bubble-multiplier').text.strip()[:-1] == latest_game_round_multiplier:
                print('No new game round')
                continue
            payout.click()
            # WebDriverWait(driver, 10000).until(
            #     EC.visibility_of_element_located((By.CLASS_NAME, 'modal-content'))
            # )
            sleep(12)
            modal_content = driver.find_element(By.CLASS_NAME, 'modal-content')
            modal_header = modal_content.find_element(By.CLASS_NAME, 'modal-header')
            game_round = modal_header.find_element(By.TAG_NAME, 'span').text.strip().split(' ')[-1]
            game_round_time = modal_header.find_element(By.CLASS_NAME, 'header__info-time').text.strip()
            modal_body = modal_content.find_element(By.CLASS_NAME, 'modal-body')
            content = modal_body.find_elements(By.CLASS_NAME, 'content-part')
            server_seed = content[0].find_element(By.TAG_NAME, 'input').get_attribute('value')
            seed_values = content[1].find_elements(By.CLASS_NAME, 'seed-value')
            player_n1_seed = seed_values[0].text.strip()
            player_n2_seed = seed_values[1].text.strip()
            player_n3_seed = seed_values[2].text.strip()
            combined_hash = content[2].find_element(By.TAG_NAME, 'input').get_attribute('value')
            result = content[3].find_elements(By.TAG_NAME, 'span')
            game_round_hex = result[0].text.strip()
            game_round_decimal = result[1].text.strip()
            game_round_multiplier = modal_header.find_element(By.CLASS_NAME, 'bubble-multiplier').text.strip()[:-1]
            latest_game_round_multiplier = game_round_multiplier
            todays_date = datetime.now().strftime('%Y-%m-%d')
            print('Game Round:', game_round)
            print('Game Round Time:', game_round_time)
            print('Server Seed:', server_seed)
            print('Player N1 Seed:', player_n1_seed)
            print('Player N2 Seed:', player_n2_seed)
            print('Player N3 Seed:', player_n3_seed)
            print('Combined Hash:', combined_hash)
            # print('Game Round Hex:', game_round_hex)
            # print('Game Round Decimal:', game_round_decimal)
            print('Game Round Multiplier:', game_round_multiplier)

            with open('sporty_aviator_data.csv', 'a') as file:
                file.write(f"{game_round},{todays_date},{game_round_time},{server_seed},{player_n1_seed},{player_n2_seed},{player_n3_seed},{combined_hash},{game_round_multiplier.replace(',', '')}\n")

            close_button = modal_header.find_element(By.CLASS_NAME, 'close')
            close_button.click()
        except Exception as e:
            print(e)
            continue


if __name__ == '__main__':
    login(driver)
    launch_aviator(driver)
    get_data(driver)

    sleep(100)