import os
from time import sleep

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
from selenium.webdriver.remote.webelement import WebElement
# import pyautogui as pag

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
        try:
            self.driver.get(self.url)
            phone = self.driver.find_element(By.CLASS_NAME, 'm-quickLogin-comp').find_elements(By.TAG_NAME, 'input')[0]
            phone.send_keys(self.phone)
            password = self.driver.find_element(By.CLASS_NAME, 'm-quickLogin-comp').find_elements(By.TAG_NAME, 'input')[1]
            password.send_keys(self.password)
            login = self.driver.find_element(By.CLASS_NAME, "login")
            login.click()
            sleep(100)
            self.driver.save_screenshot('one.png')
        except:
            self.driver.refresh()
            self.driver.save_screenshot('two.png')
            phone = self.driver.find_element(By.CLASS_NAME, 'm-quickLogin-comp').find_elements(By.TAG_NAME, 'input')[0]
            phone.send_keys(self.phone)
            password = self.driver.find_element(By.CLASS_NAME, 'm-quickLogin-comp').find_elements(By.TAG_NAME, 'input')[1]
            password.send_keys(self.password)
            login = self.driver.find_element(By.CLASS_NAME, "login")
            login.click()
            sleep(100)
            self.driver.save_screenshot('three.png')

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
        WebDriverWait(self.driver, 30).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'payout'))
        )

    def initialize_capmonster(self) -> None:
        """
        Initialize CapMonster
        """
        self.driver.get("chrome://extensions/")
        extensions_manager = self.driver.find_element(By.TAG_NAME, "extensions-manager").shadow_root
        extensions_item_list: WebElement = extensions_manager.find_element(By.CSS_SELECTOR, "extensions-item-list")
        extensions_item: WebElement = extensions_item_list.shadow_root.find_element(By.CSS_SELECTOR, "extensions-item")
        extension_id = extensions_item.get_attribute("id")
        
        self.driver.get(f'chrome-extension://{extension_id}/popup.html')
        self.driver.find_element(By.ID, 'client-key-input').send_keys(os.getenv('CAPMONSTER_API_KEY'))
        self.driver.find_element(By.ID, 'client-key-save-btn').click()

        sleep(10)

if __name__ == '__main__':
    pass