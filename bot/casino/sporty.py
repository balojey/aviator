import os
from time import sleep

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bot.casino.casino import Casino
from bot.data_source import RoundResult


class Sporty(Casino):
    """
    Interface for interacting with Sporty Casino.
    """

    def __init__(self) -> None:
        super().__init__()
        self.url = 'https://www.sportybet.com/ng/games?source=TopRibbon'
        self.phone = os.getenv("PHONE")
        self.password = os.getenv("PASSWORD")

    def login(self) -> None:
        self.driver = webdriver.Chrome(
            service=webdriver.ChromeService(executable_path=os.getenv("CHROME_DRIVER_PATH")),
            options=webdriver.ChromeOptions()
        )
        self.driver.set_window_size(1920, 1080)
        self.driver.get(self.url)
        phone = self.driver.find_element(By.NAME, "phone")
        phone.send_keys(self.phone)
        password = self.driver.find_element(By.NAME, "psd")
        password.send_keys(self.password)
        login = self.driver.find_element(By.NAME, "logIn")
        login.click()
        sleep(15)

    def launch_aviator(self) -> None:
        """
        Launch the Aviator game.
        """
        iframe = self.driver.find_element(By.ID, "games-lobby")
        self.driver.switch_to.frame(iframe)
        self.driver.find_element(By.ID, 'game_item19').find_element(By.TAG_NAME, 'img').click()
        sleep(30)
        self.driver.refresh()
        sleep(15)
        iframe = self.driver.find_element(By.ID, "games-lobby")
        self.driver.switch_to.frame(iframe)
        iframe = self.driver.find_element(By.CLASS_NAME, "turbo-games-iframe")
        self.driver.switch_to.frame(iframe)
        WebDriverWait(self.driver, 30).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'payout'))
        )


if __name__ == '__main__':
    sporty = Sporty()
    sporty.login()
    # sporty.launch_aviator()
    # print(sporty.driver.current_url)
    # balance = sporty.get_balance()
    # print(balance)
    # while True:
    #     if sporty.is_ready():
    #         # amount_to_bet = round(balance * 0.01)
    #         # sporty.place_bet(amount_to_bet)
    #         # sporty.cash_out(1.05, amount_to_bet)
    #         print(sporty.get_latest_multiplier())