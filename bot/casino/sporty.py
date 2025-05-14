import os
from time import sleep

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth

from bot.casino.msport import MSport
from bot.data_source import RoundResult


class Sporty(MSport):
    """
    Interface for interacting with Sporty Casino.
    """

    def __init__(self) -> None:
        super().__init__()
        self.url = 'https://www.sportybet.com/ng/games?source=TopRibbon'
        self.phone = os.getenv("PHONE")
        self.password = os.getenv("PASSWORD")

    def login(self) -> None:
        chrome_options = webdriver.ChromeOptions()
        chrome_service = webdriver.ChromeService(
            executable_path=os.getenv("CHROME_DRIVER_PATH"),
            log_output='chrome_driver_logs.log',
            service_args=['--verbose'],
        )
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_extension('./chrome-build1.13.0-prod.zip')

        self.driver = webdriver.Chrome(
            service=chrome_service,
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
        self.initialize_capmonster()
        self.driver.get(self.url)
        phone = self.driver.find_element(By.NAME, "phone")
        phone.send_keys(self.phone)
        password = self.driver.find_element(By.NAME, "psd")
        password.send_keys(self.password)
        login = self.driver.find_element(By.NAME, "logIn")
        login.click()
        sleep(45)
        self.driver.refresh()
        sleep(15)

    def launch_aviator(self) -> None:
        """
        Launch the Aviator game.
        """
        iframe = self.driver.find_element(By.ID, "games-lobby")
        self.driver.switch_to.frame(iframe)
        self.driver.find_element(By.ID, 'game_item19').find_element(By.TAG_NAME, 'img').click()
        sleep(5)
        iframe = self.driver.find_element(By.CLASS_NAME, "turbo-games-iframe")
        self.driver.switch_to.frame(iframe)
        WebDriverWait(self.driver, 30).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'payout'))
        )

    def refresh(self):
        """
        Refresh the page.
        """
        try:
            self.driver.save_screenshot('error.png')
            self.driver.refresh()
            iframe = self.driver.find_element(By.ID, "games-lobby")
            self.driver.switch_to.frame(iframe)
            WebDriverWait(self.driver, 25).until(
                EC.visibility_of_element_located((By.ID, 'game_item19'))
            )
            self.driver.find_element(By.ID, 'game_item19').find_element(By.TAG_NAME, 'img').click()
            sleep(5)
            iframe = self.driver.find_element(By.CLASS_NAME, "turbo-games-iframe")
            self.driver.switch_to.frame(iframe)
            WebDriverWait(self.driver, 25).until(
                EC.visibility_of_element_located((By.CLASS_NAME, 'payout'))
            )
            try:
                latest_multiplier = self.driver.find_elements(By.CLASS_NAME, 'payout')[-1].text.strip()[:-1].replace(',', '')
            except Exception as e:
                self.refresh()
            self.driver.save_screenshot('error_resolved.png')
        except Exception as e:
            print(f"Error refreshing page: {e}")


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