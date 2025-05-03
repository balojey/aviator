import random
from time import sleep
from typing_extensions import Any
import logging

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pydantic import BaseModel, HttpUrl, ConfigDict
from bot.data_source import RoundResult


class Casino(BaseModel):
    """
    Interface for interacting with the online casino.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    driver: webdriver.Chrome = None
    url: HttpUrl = ''
    phone: str = None
    password: str = None
    latest_game_round_multiplier: float = None
    log: logging.Logger = None
    previous_multiplier_history: list[float] = []

    def login(self) -> None:
        """
        Log in to the casino website.
        """
        try:
            # Add login logic here
            pass
        except Exception as e:
            print(f"Error during login: {e}")

    def launch_aviator(self) -> None:
        """
        Launch the Aviator game.
        """
        try:
            # Add logic to launch the game here
            pass
        except Exception as e:
            print(f"Error launching Aviator game: {e}")

    def get_balance(self) -> float:
        """
        Get the current balance from the casino website.
        """
        # self.driver.save_screenshot('screenshot.png')
        try:
            balance_text = self.driver.find_element(By.CLASS_NAME, 'balance-amount').text.strip().replace(',', '')
            return float(balance_text)
        except Exception as e:
            print(f"Error getting balance: {e}")
            return 0.0
        
    def cash_out_box_one(self, cash_out_amount: float) -> RoundResult:
        """
        Cash out from box one
        """
        try:
            while self.previous_multiplier_history == self.get_latest_multipliers():
                try:
                    cancel_bet_button = self.driver.find_elements(By.CLASS_NAME, 'bet-control')[0].find_element(By.CLASS_NAME, 'btn-danger')
                except Exception as e:
                    cancel_bet_button = None
                try:
                    cashout_button = self.driver.find_elements(By.CLASS_NAME, 'bet-control')[0].find_element(By.CLASS_NAME, 'btn-warning')
                except Exception as e:
                    cashout_button = None
                try:
                    place_bet_button = self.driver.find_elements(By.CLASS_NAME, 'bet-control')[0].find_element(By.CLASS_NAME, 'btn-success')
                except Exception as e:
                    place_bet_button = None

                if place_bet_button:
                    return RoundResult.LOSS
                elif cancel_bet_button:
                    continue
                elif cashout_button:
                    try:
                        cashout_label = cashout_button.find_elements(By.TAG_NAME, 'label')[1]
                        cashout_value = float(cashout_label.find_elements(By.TAG_NAME, 'span')[0].text.strip().replace(',', ''))
                        if cashout_value >= cash_out_amount:
                            cashout_button.click()
                            return RoundResult.WIN
                    except Exception as e:
                        print(f"Error during cash out attempt: {e}")
                        return RoundResult.LOSS
            return RoundResult.LOSS
        except Exception as e:
            print(f"Error during cash out: {e}")
            return RoundResult.LOSS
        
    def cash_out_box_two(self, cash_out_amount: float) -> RoundResult:
        """
        Cash out from box two
        """
        try:
            while self.previous_multiplier_history == self.get_latest_multipliers():
                try:
                    cancel_bet_button = self.driver.find_elements(By.CLASS_NAME, 'bet-control')[1].find_element(By.CLASS_NAME, 'btn-danger')
                except Exception as e:
                    cancel_bet_button = None
                try:
                    cashout_button = self.driver.find_elements(By.CLASS_NAME, 'bet-control')[1].find_element(By.CLASS_NAME, 'btn-warning')
                except Exception as e:
                    cashout_button = None
                try:
                    place_bet_button = self.driver.find_elements(By.CLASS_NAME, 'bet-control')[1].find_element(By.CLASS_NAME, 'btn-success')
                except Exception as e:
                    place_bet_button = None

                if place_bet_button:
                    return RoundResult.LOSS
                elif cancel_bet_button:
                    continue
                elif cashout_button:
                    try:
                        cashout_label = cashout_button.find_elements(By.TAG_NAME, 'label')[1]
                        cashout_value = float(cashout_label.find_elements(By.TAG_NAME, 'span')[0].text.strip().replace(',', ''))
                        if cashout_value >= cash_out_amount:
                            cashout_button.click()
                            return RoundResult.WIN
                    except Exception as e:
                        print(f"Error during cash out attempt: {e}")
                        return RoundResult.LOSS
            return RoundResult.LOSS
        except Exception as e:
            print(f"Error during cash out: {e}")
            return RoundResult.LOSS

    def place_bet_in_box_one(self, amount: float) -> None:
        """
        Place a bet in the first box
        """
        try:
            actions = ActionChains(self.driver)
            element = self.driver.find_elements(By.CLASS_NAME, 'bet-control')[0].find_element(By.TAG_NAME, 'input')
            actions.click(element).key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).send_keys(Keys.DELETE).perform()
            element.send_keys(str(amount))
            self.driver.find_elements(By.CLASS_NAME, 'bet-control')[0].find_element(By.CLASS_NAME, 'buttons-block').find_element(By.TAG_NAME, 'button').click()
        except Exception as e:
            print(f"Error placing bet: {e}")

    def place_bet_in_box_two(self, amount: float) -> None:
        """
        Place a bet in the second box
        """
        try:
            actions = ActionChains(self.driver)
            element = self.driver.find_elements(By.CLASS_NAME, 'bet-control')[1].find_element(By.TAG_NAME, 'input')
            actions.click(element).key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).send_keys(Keys.DELETE).perform()
            element.send_keys(str(amount))
            self.driver.find_elements(By.CLASS_NAME, 'bet-control')[1].find_element(By.CLASS_NAME, 'buttons-block').find_element(By.TAG_NAME, 'button').click()
        except Exception as e:
            print(f"Error placing bet: {e}")

    def get_latest_multipliers(self) -> list[float]:
        """
        Get the latest round multipliers.
        """
        self.handle_alert()
        try:
            multipliers = self.driver.find_elements(By.CLASS_NAME, 'payout')[:15]
            multipliers = [float(multiplier.text.strip()[:-1].replace(',', '')) for multiplier in multipliers]
            return multipliers
        except Exception as e:
            print(f"Error getting latest multiplier: {e}")
            return []
        
    def is_alert_visible(self) -> bool:
        """
        Check if an element with the class 'alert' is visible.
        """
        try:
            try:
                alert_element = self.driver.find_element(By.CLASS_NAME, 'alert')
            except Exception as e:
                # print(f"Alert element not found: {e}")
                return False
            return alert_element.is_displayed()
        except Exception as e:
            print(f"Error checking alert visibility: {e}")
            return False
        
    def handle_alert(self) -> None:
        """
        Handle alerts visibility
        """
        try:
            if self.is_alert_visible():
                self.log.info("Alert is visible, refreshing the page.")
                self.refresh()
        except Exception as e:
            print(f"Error handling alert visibility: {e}")
        
    def refresh(self) -> None:
        """
        Refresh the page.
        """
        try:
            self.driver.refresh()
            WebDriverWait(self.driver, 25).until(
                EC.visibility_of_element_located((By.CLASS_NAME, 'payout'))
            )
            try:
                latest_multiplier = self.driver.find_elements(By.CLASS_NAME, 'payout')[-1].text.strip()[:-1].replace(',', '')
            except Exception as e:
                self.refresh()
        except Exception as e:
            print(f"Error refreshing page: {e}")