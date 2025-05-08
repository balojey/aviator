import os
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bot.casino.casino import Casino


class Spribe(Casino):
    """
    Interface for interacting with Spribe Demo Casino.
    """

    def __init__(self) -> None:
        super().__init__()
        self.url = 'https://spribe.co/games/aviator'

    def login(self) -> None:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--no-sandbox')
        
        self.driver = webdriver.Chrome(
            service=webdriver.ChromeService(executable_path=os.getenv("CHROME_DRIVER_PATH")),
            options=chrome_options,
        )
        self.driver.set_window_size(1920, 1080)
        self.driver.get(self.url)
        sleep(5)

    def launch_aviator(self) -> None:
        """
        Launch the Aviator game.
        """
        for _ in range(8):
            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ARROW_DOWN)
        self.driver.find_element(By.LINK_TEXT, 'Play Demo').click()
        self.driver.find_element(By.CLASS_NAME, 'modal-dialog').find_elements(By.TAG_NAME, 'button')[0].click()
        self.driver.switch_to.window(self.driver.window_handles[-1])
        WebDriverWait(self.driver, 30).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'payout'))
        )


if __name__ == '__main__':
    spribe = Spribe()
    spribe.login()
    spribe.launch_aviator()
    print(spribe.driver.current_url)
    balance = spribe.get_balance()
    print(balance)
    while True:
        if spribe.is_ready():
            amount_to_bet = round(balance * 0.01)
            spribe.place_bet(amount_to_bet)
            spribe.cash_out(1.05, amount_to_bet)