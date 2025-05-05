import sys
import polars as pl

from bot.backtesting.backtest import Backtester
from bot.casino import Spribe, Sporty, MSport
from bot.data_source import DataSource
from bot.data_source import DecidedMultiplier
from bot.strategy import BettingStrategy
from bot.data_source import BetHistory, RoundResult, LiveBetHistory
from bot.strategy.executor import Executor
from bot.strategy.risk_manager import RiskManager


class EagleShot(BettingStrategy):
    minimum_multiplier: float
    initial_target_multiplier: float
    base_decided_multiplier: DecidedMultiplier = DecidedMultiplier(
        multiplier_for_box_one=1.00,
        multiplier_for_box_two=1.00,
    )

    def scanner(self, multipliers: list[float], initial_target: float = 2.00) -> list[float]:
        """
        Scans a list of multipliers to track unresolved Blue debts.
        For each Blue, checks if a compounding 100% profit (x2, x3, ...) was achieved in the following rounds.
        
        Args:
            multipliers (list of float): List of multipliers.
            initial_target (int): Initial target multiplier to resolve Blue debts.
            
        Returns:
            list of float: List of target multipliers needed to resolve unpaid Blue debts.
        """
        targets = []
        i = 0
        while i < len(multipliers):
            current = multipliers[i]
            
            if 1.00 <= current < 2.00:
                # Start a debt sequence
                target = initial_target  # Initial target: 100% profit
                resolved = False
                for j in range(i + 1, len(multipliers)):
                    if multipliers[j] >= target:
                        resolved = True
                        break
                    else:
                        target += 1  # Increase target by +100%
                if not resolved:
                    targets.append(target)
            
            i += 1

        return targets
    
    def sort(self, multipliers: list[float], minimum_multiplier: float = 10.00) -> list[float]:
        filtered_multipliers = [m for m in multipliers if m >= minimum_multiplier]
        return sorted(filtered_multipliers)

    def decide_multiplier(self, game_data: pl.DataFrame, bet_history: list[BetHistory | LiveBetHistory] = [], restart_strategy: bool = False) -> DecidedMultiplier:
        if restart_strategy:
            self.base_decided_multiplier.multiplier_for_box_one = 1.00
            self.base_decided_multiplier.multiplier_for_box_two = 1.00
            return self.base_decided_multiplier
        
        multipliers = [history.multiplier for history in bet_history]
        target_multipliers = self.scanner(multipliers, self.initial_target_multiplier)
        if len(target_multipliers) > 0:
            sorted_multipliers = self.sort(target_multipliers, self.minimum_multiplier)
            self.log.info(f'Sorted Multipliers: {sorted_multipliers}')
            if len(sorted_multipliers) > 0:
                decided_multiplier = DecidedMultiplier(
                    multiplier_for_box_one=1.00,
                    multiplier_for_box_two=1.00,
                )
                if len(sorted_multipliers) == 1:
                    decided_multiplier.multiplier_for_box_one = sorted_multipliers[0]
                elif len(sorted_multipliers) > 1:
                    decided_multiplier.multiplier_for_box_one = sorted_multipliers[0]
                    decided_multiplier.multiplier_for_box_two = sorted_multipliers[-1]
                return decided_multiplier

        return self.base_decided_multiplier
    

strategy = EagleShot(
    percentage_to_bet_per_round_for_box_one=0.0005,
    percentage_to_bet_per_round_for_box_two=0.0005,
    minimum_multiplier=10.00,
    initial_target_multiplier=2.00,
)
risk_manager = RiskManager(stop_loss=1.0, take_profit=0.05)
data_source = DataSource(csv_file="sporty_aviator_data.csv")
test_casino = Spribe()
live_casino = MSport()

if __name__ == '__main__':
    arg = sys.argv[1]
    if arg == 'live':
        executor = Executor(
            strategy=strategy,
            risk_manager=risk_manager,
            data_source=data_source,
            casino=live_casino,
            iteration_wait_rounds=10,
            # continuous=False,
            # consistent=False,
        )
        executor.execute()
    elif arg == 'test':
        executor = Executor(
            strategy=strategy,
            risk_manager=risk_manager,
            data_source=data_source,
            casino=test_casino,
            iteration_wait_rounds=10,
            # continuous=False,
            # consistent=False,
        )
        executor.execute()
    elif arg == 'backtest':
        backester = Backtester(
            strategy=strategy,
            risk_manager=risk_manager,
            data_source=data_source,
            start_date='2025-03-23',
            initial_balance=20000,
            iteration_wait_rounds=10,
            # continuous=False,
            # consistent=False,
            # live_bet_history_file='live_bet_history/live_bet_history_20250415_125629.json', # 2025-04-15 Sporty
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
            # live_bet_history_file='live_bet_history/live_bet_history_20250420_033632.json', # 2025-04-20 Sporty Real
            # live_bet_history_file='live_bet_history/live_bet_history_20250420_075532.json', # 2025-04-20 Sporty Real
            # live_bet_history_file='live_bet_history/live_bet_history_20250425_103848.json', # 2025-04-25 MSport Real
            # live_bet_history_file='live_bet_history/live_bet_history_20250430_233702.json', # 2025-04-30 MSport Real
            # live_bet_history_file='artificial_live_bet_history/live_bet_history.json'
        )
        backester.run()
