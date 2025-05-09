import os
from time import sleep

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
import pyautogui as pag

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
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_extension('./chrome-build1.13.0-prod.zip')

        self.driver = webdriver.Chrome(
            service=webdriver.ChromeService(executable_path=os.getenv("CHROME_DRIVER_PATH")),
            options=chrome_options,
        )

        stealth(self.driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )

        self.driver.set_window_size(1920, 1080)
        self.driver.get(self.url)
        self.initialize_capmonster()
        self.driver.refresh()
        phone = self.driver.find_element(By.CLASS_NAME, 'm-quickLogin-comp').find_elements(By.TAG_NAME, 'input')[0]
        phone.send_keys(self.phone)
        password = self.driver.find_element(By.CLASS_NAME, 'm-quickLogin-comp').find_elements(By.TAG_NAME, 'input')[1]
        password.send_keys(self.password)
        login = self.driver.find_element(By.CLASS_NAME, "login")
        login.click()
        sleep(60)

    def launch_aviator(self) -> None:
        """
        Launch the Aviator game.
        """
        pag.screenshot('six.png')
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
        WebDriverWait(self.driver, 30).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'payout'))
        )

    def initialize_capmonster(self) -> None:
        """
        Initialize CapMonster
        """
        # while True:
        #     print(pag.position())
        pag.moveTo(1488, 98)
        sleep(3)
        pag.click()
        pag.moveTo(1320, 272)
        sleep(3)
        pag.click()
        pag.moveTo(1088, 253)
        sleep(3)
        pag.click()
        pag.write(os.getenv('CAPMONSTER_API_KEY'))
        sleep(3)
        pag.moveTo(1418, 253)
        sleep(3)
        pag.click()
        sleep(3)
        pag.moveTo(1488, 98)
        sleep(3)
        pag.click()
        sleep(10)


if __name__ == '__main__':
    pass