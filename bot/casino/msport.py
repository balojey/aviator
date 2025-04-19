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


class MSport(Casino):
    """
    Interface for interacting with MSport Casino.
    """

    def __init__(self) -> None:
        super().__init__()
        self.url = 'https://www.msport.com/ng/web'
        self.phone = os.getenv("MSPORT_PHONE")
        self.password = os.getenv("PASSWORD")

    def login(self) -> None:
        self.driver = webdriver.Chrome(
            service=webdriver.ChromeService(executable_path=os.getenv("CHROME_DRIVER_PATH")),
            options=webdriver.ChromeOptions()
        )
        self.driver.set_window_size(1920, 1080)
        self.driver.get(self.url)
        phone = self.driver.find_element(By.CLASS_NAME, 'm-quickLogin-comp').find_elements(By.TAG_NAME, 'input')[0]
        phone.send_keys(self.phone)
        password = self.driver.find_element(By.CLASS_NAME, 'm-quickLogin-comp').find_elements(By.TAG_NAME, 'input')[1]
        password.send_keys(self.password)
        login = self.driver.find_element(By.CLASS_NAME, "login")
        login.click()
        sleep(15)

    def launch_aviator(self) -> None:
        """
        Launch the Aviator game.
        """
        self.driver.find_elements(By.CLASS_NAME, 'nav-item')[4].click()
        sleep(15)
        for _ in range(10):
            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ARROW_DOWN)
        sleep(5)
        actions = ActionChains(self.driver)
        actions.move_to_element(self.driver.find_element(By.CLASS_NAME, 'game-hot-area').find_elements(By.CLASS_NAME, 'm-game-item-mask')[-1]).perform()
        sleep(5)
        self.driver.find_element(By.CLASS_NAME, 'game-hot-area').find_elements(By.CLASS_NAME, 'm-game-item-mask')[-1].find_element(By.CLASS_NAME, 'play-btn-now').click()
        self.driver.switch_to.window(self.driver.window_handles[-1])
        sleep(30)


if __name__ == '__main__':
    pass