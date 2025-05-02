import logging
from datetime import datetime
from time import sleep

from pydantic import BaseModel, ConfigDict

from bot.strategy import BettingStrategy, RiskManager
from bot.data_source import DataSource, BetHistory, RoundResult, IterationHistory, DecidedMultiplier


logging.basicConfig(
    filename=f'logs/backtest/run_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class Backtester(BaseModel):
    """A class to backtest a strategy."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    strategy: BettingStrategy
    risk_manager: RiskManager
    data_source: DataSource
    start_date: str
    end_date: str = None
    look_back: int = 2
    start_time: str = '00:00:00'
    end_time: str = '23:59:59'
    initial_balance: float
    current_balance: float = 0.0
    bet_history: list[BetHistory] = []
    iteration_history: list[IterationHistory] = []
    consistent: bool = True
    continuous: bool = True
    live_bet_history_file: str = None
    iteration_wait_rounds: int = 0

    def run(self):
        """Simulates running the strategy on historical data."""
        self.strategy.log = logging
        self.risk_manager.log = logging
        self.strategy.is_backtest = True
        self.strategy.introduce_strategy()
        self.current_balance = self.initial_balance
        self.risk_manager.balance_for_stop_loss = self.initial_balance
        if self.live_bet_history_file:
            self.data_source.repurpose_live_bet_history(self.live_bet_history_file)
            historical_data = self.data_source.data.to_dicts()
        else:
            historical_data = self.data_source.get_data_by_date_and_time(
                start_date=self.start_date,
                end_date=self.end_date,
                start_time=self.start_time,
                end_time=self.end_time
            ).to_dicts()
        iteration = 1
        restart_strategy = False
        iteration_wait_rounds_count = 0
        for hd in historical_data:
            self.current_balance = round(self.current_balance, 2)
            if not self.live_bet_history_file:
                data = self.data_source.get_data_before_date_and_time(
                    start_date=hd['date'],
                    look_back=self.look_back,
                    start_time=self.start_time,
                    end_time=self.end_time
                )
            if not self.risk_manager.check_risk(self.initial_balance, self.current_balance) and self.continuous:
                logging.info('Restarting strategy')
                profit = (self.current_balance - self.initial_balance) if self.current_balance > self.initial_balance else 0.0
                loss = (self.initial_balance - self.current_balance) if self.initial_balance > self.current_balance else 0.0
                profit_percentage = (profit / self.initial_balance) * 100 if profit > 0 else 0.0
                loss_percentage = (loss / self.initial_balance) * 100 if loss > 0 else 0.0
                self.iteration_history.append(ih := IterationHistory(
                    profit=profit,
                    loss=loss,
                    iteration=iteration,
                    profit_percentage=profit_percentage,
                    loss_percentage=loss_percentage
                ))
                logging.info(ih)
                restart_strategy = True
                self.initial_balance = self.current_balance
                self.risk_manager.balance_for_stop_loss = self.initial_balance
                iteration += 1
                iteration_wait_rounds_count = self.iteration_wait_rounds
            if self.risk_manager.check_risk(self.initial_balance, self.current_balance) and iteration_wait_rounds_count <= 0:
                try:
                    decided_multiplier: DecidedMultiplier = self.strategy.decide_multiplier(game_data=data if not self.live_bet_history_file else historical_data, bet_history=self.bet_history, restart_strategy=restart_strategy)
                except Exception as e:
                    print(e)
                    decided_multiplier = DecidedMultiplier(
                        multiplier_for_box_one=1.00,
                        multiplier_for_box_two=1.00
                    )
                
                logging.info(f'Box One Multiplier: {decided_multiplier.multiplier_for_box_one}')
                logging.info(f'Box Two Multiplier: {decided_multiplier.multiplier_for_box_two}')

                bet_amount_for_box_one = self.strategy.calculate_bet_amount_for_box_one(balance=self.initial_balance if self.consistent else self.current_balance)
                bet_amount_for_box_two = self.strategy.calculate_bet_amount_for_box_two(balance=self.initial_balance if self.consistent else self.current_balance)
                if bet_amount_for_box_one < 10.00:
                    bet_amount_for_box_one = 10.00
                if bet_amount_for_box_two < 10.00:
                    bet_amount_for_box_two = 10.00
                if decided_multiplier.multiplier_for_box_one > 1.0:
                    self.current_balance -= bet_amount_for_box_one
                    if decided_multiplier.multiplier_for_box_one <= hd['multiplier']:
                        self.current_balance += bet_amount_for_box_one * decided_multiplier.multiplier_for_box_one
                if decided_multiplier.multiplier_for_box_two > 1.0:
                    self.current_balance -= bet_amount_for_box_two
                    if decided_multiplier.multiplier_for_box_two <= hd['multiplier']:
                        self.current_balance += bet_amount_for_box_two * decided_multiplier.multiplier_for_box_two
                result_one = RoundResult.DRAW if decided_multiplier.multiplier_for_box_one == 1.0 else (
                    RoundResult.WIN if decided_multiplier.multiplier_for_box_one > 1.0 and decided_multiplier.multiplier_for_box_one <= hd['multiplier'] else RoundResult.LOSS
                )
                result_two = RoundResult.DRAW if decided_multiplier.multiplier_for_box_two == 1.0 else (
                    RoundResult.WIN if decided_multiplier.multiplier_for_box_two > 1.0 and decided_multiplier.multiplier_for_box_two <= hd['multiplier'] else RoundResult.LOSS
                )

                self.bet_history.append(bh := BetHistory(
                    round_number=hd['game_round'],
                    date=hd['date'],
                    time=hd['time'],
                    bet_amount_for_box_one=bet_amount_for_box_one,
                    bet_amount_for_box_two=bet_amount_for_box_two,
                    multiplier=hd['multiplier'],
                    decided_multiplier=decided_multiplier,
                    result_one=result_one,
                    result_two=result_two,
                    initial_balance=self.initial_balance,
                    current_balance=(self.current_balance),
                    multiplier_category='B' if 1.00 <= hd['multiplier'] <= 1.99 else 'P' if 2.00 <= hd['multiplier'] <= 9.99 else 'Pk',
                    decided_multiplier_one_category='B' if 1.00 <= decided_multiplier.multiplier_for_box_one <= 1.99 else 'P' if 2.00 <= decided_multiplier.multiplier_for_box_one <= 9.99 else 'Pk',
                    decided_multiplier_two_category='B' if 1.00 <= decided_multiplier.multiplier_for_box_two <= 1.99 else 'P' if 2.00 <= decided_multiplier.multiplier_for_box_two <= 9.99 else 'Pk',
                ))
                logging.info(bh)

                winnings_1 = [history for history in self.bet_history if history.result_one == RoundResult.WIN]
                winnings_2 = [history for history in self.bet_history if history.result_two == RoundResult.WIN]
                total_winnings = len(winnings_1) + len(winnings_2)
                logging.info(f'Total Number of Winnings: {total_winnings}')

                restart_strategy = False
            else:
                iteration_wait_rounds_count -= 1
                self.bet_history.append(bh := BetHistory(
                    round_number=hd['game_round'],
                    date=hd['date'],
                    time=hd['time'],
                    bet_amount_for_box_one=bet_amount_for_box_one,
                    bet_amount_for_box_two=bet_amount_for_box_two,
                    multiplier=hd['multiplier'],
                    decided_multiplier=DecidedMultiplier(multiplier_for_box_one=1.00, multiplier_for_box_two=1.0),
                    result_one=RoundResult.DRAW,
                    result_two=RoundResult.DRAW,
                    initial_balance=self.initial_balance,
                    current_balance=(self.current_balance),
                    multiplier_category='B' if 1.00 <= hd['multiplier'] <= 1.99 else 'P' if 2.00 <= hd['multiplier'] <= 9.99 else 'Pk',
                    decided_multiplier_one_category='B' if 1.00 <= decided_multiplier.multiplier_for_box_one <= 1.99 else 'P' if 2.00 <= decided_multiplier.multiplier_for_box_one <= 9.99 else 'Pk',
                    decided_multiplier_two_category='B' if 1.00 <= decided_multiplier.multiplier_for_box_two <= 1.99 else 'P' if 2.00 <= decided_multiplier.multiplier_for_box_two <= 9.99 else 'Pk',
                ))
                logging.info(bh)
                logging.info(f'Waiting for {iteration_wait_rounds_count} of {self.iteration_wait_rounds} rounds to place a bet')
            self.strategy.after_game_round_during_backtesting()
        if not self.continuous:
            profit = (self.current_balance - self.initial_balance) if self.current_balance > self.initial_balance else 0.0
            loss = (self.initial_balance - self.current_balance) if self.initial_balance > self.current_balance else 0.0
            profit_percentage = (profit / self.initial_balance) * 100 if profit > 0 else 0.0
            loss_percentage = (loss / self.initial_balance) * 100 if loss > 0 else 0.0
            self.iteration_history.append(ih := IterationHistory(
                profit=profit,
                loss=loss,
                iteration=iteration,
                profit_percentage=profit_percentage,
                loss_percentage=loss_percentage
            ))
            logging.info(ih)
        

    def get_results(self):
        """Returns the results of the backtest."""
        return {
            'iteration_history': self.iteration_history,
            'bet_history': self.bet_history,
        }