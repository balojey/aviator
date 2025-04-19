import sys
import polars as pl

from bot.backtesting.backtest import Backtester
from bot.casino.sporty import Sporty
from bot.casino.spribe import Spribe
from bot.data_source import DataSource
from bot.data_source import DecidedMultiplier
from bot.strategy import BettingStrategy
from bot.data_source import BetHistory, RoundResult, LiveBetHistory
from bot.strategy.executor import Executor
from bot.strategy.risk_manager import RiskManager


class LossLurker(BettingStrategy):
    base_decided_multiplier: DecidedMultiplier = DecidedMultiplier(
        multiplier_for_box_one=1.00,
        multiplier_for_box_two=1.00,
    )

    def decide_multiplier(self, game_data: pl.DataFrame, bet_history: list[BetHistory | LiveBetHistory] = [], restart_strategy: bool = False) -> DecidedMultiplier:
        if len(bet_history) > 0 and bet_history[-1].result_one == RoundResult.LOSS:
            self.base_decided_multiplier.multiplier_for_box_one += 1
            lost_rounds = [history for history in bet_history[-3:] if history.result_one == RoundResult.LOSS]
            if bet_history[-1].multiplier < 1.50 and self.base_decided_multiplier.multiplier_for_box_two == 1.00 and len(lost_rounds) == 3:
                self.base_decided_multiplier.multiplier_for_box_two += 1
            if bet_history[-1].result_two == RoundResult.LOSS:
                self.base_decided_multiplier.multiplier_for_box_two += 1
            if bet_history[-1].result_two == RoundResult.WIN:
                self.base_decided_multiplier.multiplier_for_box_two = 1.00
            return self.base_decided_multiplier
        if len(bet_history) > 0 and bet_history[-1].multiplier < 1.30:
            self.base_decided_multiplier.multiplier_for_box_one += 1
            return self.base_decided_multiplier
        if len(bet_history) > 0 and bet_history[-1].result_one == RoundResult.WIN:
            self.base_decided_multiplier.multiplier_for_box_one = 1.00
            self.base_decided_multiplier.multiplier_for_box_two = 1.00
            return self.base_decided_multiplier
        return self.base_decided_multiplier
    

strategy = LossLurker(percentage_to_bet_per_round=0.005)
risk_manager = RiskManager(stop_loss=0.2, take_profit=0.05)
data_source = DataSource(csv_file="sporty_aviator_data.csv")
test_casino = Spribe()
live_casino = Sporty()

if __name__ == '__main__':
    arg = sys.argv[1]
    if arg == 'live':
        executor = Executor(
            strategy=strategy,
            risk_manager=risk_manager,
            data_source=data_source,
            casino=live_casino,
            continuous=False,
            consistent=False,
        )
        executor.execute()
    elif arg == 'test':
        executor = Executor(
            strategy=strategy,
            risk_manager=risk_manager,
            data_source=data_source,
            casino=test_casino,
            continuous=False,
            consistent=False,
        )
        executor.execute()
    elif arg == 'backtest':
        backester = Backtester(
            strategy=strategy,
            risk_manager=risk_manager,
            data_source=data_source,
            start_date='2025-03-28',
            initial_balance=5000,
            continuous=False,
            consistent=False,
            live_bet_history_file='live_bet_history/live_bet_history_20250415_125629.json', # 2025-04-15 Sporty
            # live_bet_history_file='live_bet_history/live_bet_history_20250416_072424.json', # 2025-04-16 Sporty
            # live_bet_history_file='live_bet_history/live_bet_history_20250416_090335.json', # 2025-04-16 Sporty
            # live_bet_history_file='live_bet_history/live_bet_history_20250416_132948.json', # 2025-04-16 Sporty
            # live_bet_history_file='live_bet_history/live_bet_history_20250416_141523.json', # 2025-04-16 Sporty
            # live_bet_history_file='live_bet_history/live_bet_history_20250416_163943.json', # 2025-04-16 Sporty
            # live_bet_history_file='live_bet_history/live_bet_history_20250416_201112.json', # 2025-04-16 Sporty Real
            # live_bet_history_file='live_bet_history/live_bet_history_20250416_211412.json', # 2025-04-16 Sporty Real
            # live_bet_history_file='live_bet_history/live_bet_history_20250417_003634.json', # 2025-04-17 Sporty Real
            # live_bet_history_file='live_bet_history/live_bet_history_20250417_114034.json', # 2025-04-17 Sporty Real
            # live_bet_history_file='live_bet_history/live_bet_history_20250417_164729.json', # 2025-04-17 Sporty Real
        )
        backester.run()
