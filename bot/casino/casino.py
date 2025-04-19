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
        try:
            balance_text = self.driver.find_element(By.CLASS_NAME, 'balance-amount').text.strip().replace(',', '')
            return float(balance_text)
        except Exception as e:
            print(f"Error getting balance: {e}")
            return 0.0

    def is_ready(self) -> bool:
        """
        Check if the Aviator game is ready to accept bets.
        """
        try:
            latest_multiplier = self.get_latest_multiplier()
            if not self.latest_game_round_multiplier:
                self.latest_game_round_multiplier = latest_multiplier
            ready = latest_multiplier != self.latest_game_round_multiplier
            if ready:
                self.latest_game_round_multiplier = latest_multiplier
            return ready
        except Exception as e:
            print(f"Error checking readiness: {e}")
            return False

    def cash_out(self, cash_out_amount: float) -> RoundResult:
        """
        Cash out
        """
        try:
            try:
                WebDriverWait(self.driver, 20).until(
                    EC.visibility_of_element_located((By.CLASS_NAME, 'btn-warning'))
                )
            except Exception as e:
                print(f"Timeout waiting for cashout button: {e}")
                return RoundResult.LOSS
            while self.latest_game_round_multiplier == self.get_latest_multiplier():
                try:
                    cashout_label = self.driver.find_element(By.CLASS_NAME, 'btn-warning').find_elements(By.TAG_NAME, 'label')[1]
                    cashout_value = float(cashout_label.find_elements(By.TAG_NAME, 'span')[0].text.strip().replace(',', ''))
                    if cashout_value >= cash_out_amount:
                        self.driver.find_element(By.CLASS_NAME, 'btn-warning').click()
                        return RoundResult.WIN
                except Exception as e:
                    print(f"Error during cash out attempt: {e}")
                    return RoundResult.LOSS
            return RoundResult.LOSS
        except Exception as e:
            print(f"Error during cash out: {e}")
            return RoundResult.LOSS
        
    def cash_out_box_one(self, cash_out_amount: float) -> RoundResult:
        """
        Cash out from box one
        """
        try:
            try:
                WebDriverWait(self.driver, 20).until(
                    EC.visibility_of_element_located((By.CLASS_NAME, 'btn-warning'))
                )
            except Exception as e:
                print(f"Timeout waiting for cashout button: {e}")
                return RoundResult.LOSS
            while self.latest_game_round_multiplier == self.get_latest_multiplier():
                try:
                    cashout_label = self.driver.find_elements(By.CLASS_NAME, 'bet-control')[0].find_element(By.CLASS_NAME, 'btn-warning').find_elements(By.TAG_NAME, 'label')[1]
                    cashout_value = float(cashout_label.find_elements(By.TAG_NAME, 'span')[0].text.strip().replace(',', ''))
                    if cashout_value >= cash_out_amount:
                        self.driver.find_elements(By.CLASS_NAME, 'bet-control')[0].find_element(By.CLASS_NAME, 'btn-warning').click()
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
            try:
                WebDriverWait(self.driver, 20).until(
                    EC.visibility_of_element_located((By.CLASS_NAME, 'btn-warning'))
                )
            except Exception as e:
                print(f"Timeout waiting for cashout button: {e}")
                return RoundResult.LOSS
            while self.latest_game_round_multiplier == self.get_latest_multiplier():
                try:
                    cashout_label = self.driver.find_elements(By.CLASS_NAME, 'bet-control')[1].find_element(By.CLASS_NAME, 'btn-warning').find_elements(By.TAG_NAME, 'label')[1]
                    cashout_value = float(cashout_label.find_elements(By.TAG_NAME, 'span')[0].text.strip().replace(',', ''))
                    if cashout_value >= cash_out_amount:
                        self.driver.find_elements(By.CLASS_NAME, 'bet-control')[1].find_element(By.CLASS_NAME, 'btn-warning').click()
                        return RoundResult.WIN
                except Exception as e:
                    print(f"Error during cash out attempt: {e}")
                    return RoundResult.LOSS
            return RoundResult.LOSS
        except Exception as e:
            print(f"Error during cash out: {e}")
            return RoundResult.LOSS

    def place_bet(self, amount: float) -> None:
        """
        Place a bet in the Aviator game.
        """
        try:
            actions = ActionChains(self.driver)
            element = self.driver.find_elements(By.CLASS_NAME, 'bet-control')[0].find_element(By.TAG_NAME, 'input')
            actions.click(element).key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).send_keys(Keys.DELETE).perform()
            element.send_keys(str(amount))
            self.driver.find_elements(By.CLASS_NAME, 'bet-control')[0].find_element(By.CLASS_NAME, 'buttons-block').find_element(By.TAG_NAME, 'button').click()
        except Exception as e:
            print(f"Error placing bet: {e}")

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

    def get_latest_multiplier(self) -> float:
        """
        Get the latest round multiplier
        """
        try:
            # multiplier_text = self.driver.find_elements(By.CLASS_NAME, 'payout')[0].find_element(By.CLASS_NAME, 'bubble-multiplier').text.strip()[:-1].replace(',', '')
            multiplier_text = self.driver.find_elements(By.CLASS_NAME, 'payout')[0].text.strip()[:-1].replace(',', '')
            return float(multiplier_text)
        except Exception as e:
            print(f"Error getting latest multiplier: {e}")
            return 0.0
        
    def refresh(self) -> None:
        """
        Refresh the page.
        """
        try:
            self.driver.refresh()
            sleep(30)
        except Exception as e:
            print(f"Error refreshing page: {e}")