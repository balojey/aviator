from datetime import datetime
import re
import os
import sys
from typing_extensions import Any
from time import sleep
import importlib.util
from collections import defaultdict, Counter, deque
import json
from hashlib import sha256

import polars as pl
from pydantic import BaseModel
import logfire
from dotenv import load_dotenv
from celery import Celery
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.deepseek import DeepSeekProvider


from bot.backtesting.backtest import Backtester
from bot.casino import Sporty, Spribe
from bot.data_source import BetHistory, LiveBetHistory
from bot.data_source.data_source import DataSource
from bot.data_source.decided_multiplier import DecidedMultiplier
from bot.data_source.round_result import RoundResult
from bot.strategy import BettingStrategy
from bot.strategy.executor import Executor
from bot.strategy.risk_manager import RiskManager


class PredictionHistory(BaseModel):
    best_guess: str = None
    markov_probs_b: float
    markov_probs_p: float
    markov_probs_pk: float
    actual_category: str = None


class MarkovStrategy(BettingStrategy):
    recent_predictions: list[tuple[str, str, bool]] = []

    def introduce_strategy(self):
        self.log.info(f"""
        Strategy: {self.__repr_name__()}
        Description: A strategy using Markov chains for game prediction.
        Is Backtest? {self.is_backtest}
        Percentage to bet per round: {self.percentage_to_bet_per_round}
        """)
    
    def build_markov_model(self, history: list[str]) -> dict[str, dict[str, float]]:
        transitions = defaultdict(Counter)
        for i in range(len(history) - 1):
            current_state = history[i]
            next_state = history[i + 1]
            transitions[current_state][next_state] += 1

        # Normalize probabilities
        markov_model = {}
        for state, next_counts in transitions.items():
            total = sum(next_counts.values())
            markov_model[state] = {k: v / total for k, v in next_counts.items()}
        
        return markov_model


    def markov_predict_next(self, markov_model: dict[str, dict[str, float]], current_state: str) -> dict[str, float]:
        if current_state not in markov_model:
            return {'B': 0, 'P': 0, 'Pk': 0}
        
        return markov_model[current_state]

    def predict(self, history: list[str]) -> dict[str, float]:
        markov_model = self.build_markov_model(history)
        current_state = history[-1]
        markov_probs = self.markov_predict_next(markov_model, current_state)
        return markov_probs
    
    def record_feedback(self, prediction: str, actual: str):
        hit = prediction == actual or (prediction in ['P', 'Pk'] and actual in ['P', 'Pk'])
        self.recent_predictions.append((prediction, actual, hit))

    def accuracy(self):
        if not self.recent_predictions:
            return 1.0
        return round(sum(hit for _, _, hit in self.recent_predictions) / len(self.recent_predictions), 2)
    
    def save_prediction_history(self) -> None:
        with open(self.prediction_history_storage, 'w') as f:
            f.write(json.dumps([item.model_dump(mode='json') for item in self.prediction_history]))

    def decide_multiplier(self, game_data: pl.DataFrame, bet_history: list[BetHistory | LiveBetHistory] = [], restart_strategy: bool = False) -> float:
        decided_multiplier = DecidedMultiplier(
            multiplier_for_box_one=1.0,
            multiplier_for_box_two=1.0
        )

        if len(bet_history) >= 0:
            categories = [history.multiplier_category for history in bet_history[-45:]]
            markov_probs = self.predict(categories)

            # Rule 1: If markov_probs_p == markov_probs_pk, then choose Pk(10.0)
            if round(markov_probs['P'], 6) == round(markov_probs['Pk'], 6):
                self.log.info('Rule 1: If markov_probs_p == markov_probs_pk, then choose Pk(10.0)')
                decided_multiplier.multiplier_for_box_one = 10.0
                decided_multiplier.multiplier_for_box_two = 2.0
            # Rule 2: If markov_probs_pk * 5 == markov_probs_b, then choose P(2.0)
            elif round(markov_probs['Pk'] * 5, 6) == round(markov_probs['B'], 6):
                self.log.info('Rule 2: If markov_probs_pk * 5 == markov_probs_b, then choose P(2.0)')
                decided_multiplier.multiplier_for_box_one = 2.0
                decided_multiplier.multiplier_for_box_two = 1.5
            # Rule 3: if markov_probs_pk * 4 == markov_probs_b, then choose P(2.0)
            if round(markov_probs['Pk'] * 4, 6) == round(markov_probs['B'], 6):
                self.log.info('Rule 3: if markov_probs_pk * 4 == markov_probs_b, then choose P(2.0)')
                decided_multiplier.multiplier_for_box_one = 2.0
                decided_multiplier.multiplier_for_box_two = 1.5
            # Rule 4: if markov_probs_pk * 2 == markov_probs_p, then choose P(2.0)
            elif round(markov_probs['Pk'] * 2, 6) == round(markov_probs['P'], 6):
                self.log.info('Rule 4: if markov_probs_pk * 2 == markov_probs_p, then choose P(2.0)')
                decided_multiplier.multiplier_for_box_one = 2.0
                decided_multiplier.multiplier_for_box_two = 1.5
            # Rule 5: If markov_probs_b == markov_probs_p, then choose P(2.0)
            elif round(markov_probs['B'], 6) == round(markov_probs['P'], 6):
                self.log.info('Rule 5: If markov_probs_b == markov_probs_p, then choose P(2.0)')
                decided_multiplier.multiplier_for_box_one = 2.0
                decided_multiplier.multiplier_for_box_two = 1.5
            # Rule 6: if markov_probs_pk * 3 == markov_probs_b, then choose P(2.0)
            elif round(markov_probs['Pk'] * 3, 6) == round(markov_probs['B'], 6):
                self.log.info('Rule 6: if markov_probs_pk * 3 == markov_probs_b, then choose P(2.0)')
                decided_multiplier.multiplier_for_box_one = 2.0
                decided_multiplier.multiplier_for_box_two = 1.5
            # Rule 7: if markov_probs_b / 10 == markov_probs_pk, then choose P(2.0)
            elif round(markov_probs['B'] / 10, 6) == round(markov_probs['P'], 6):
                self.log.info('Rule 7: if markov_probs_b / 10 == markov_probs_pk, then choose P(2.0)')
                decided_multiplier.multiplier_for_box_one = 2.0
                decided_multiplier.multiplier_for_box_two = 1.5
            # Rule 8: if markov_probs_p == 0.296296 or 0.259259, then choos Pk(10.0)
            elif round(markov_probs['P'], 6) in [0.296296, 0.259259]:
                self.log.info('Rule 8: if markov_probs_p == 0.296296 or 0.259259, then choose Pk(10.0)')
                multiplier = 10.0
            # Rule 11: if markov_probs_b == 0.428571, then choose P(2.0)
            elif round(markov_probs['B'], 6) == 0.428571:
                self.log.info('Rule 11: if markov_probs_b == 0.428571, then choose P(2.0)')
                decided_multiplier.multiplier_for_box_one = 2.5
                decided_multiplier.multiplier_for_box_two = 2.0
            # Rule 12: if markov_probs_p == 0.413793, then choose P(2.0)
            elif round(markov_probs['P'], 6) == 0.413793:
                self.log.info('Rule 12: if markov_probs_p == 0.413793, then choose P(2.0)')
                decided_multiplier.multiplier_for_box_one = 2.5
                decided_multiplier.multiplier_for_box_two = 2.0
            # Rule 13: if markov_probs_b == 0.478261, then choose P(2.0)
            elif round(markov_probs['B'], 6) == 0.478261:
                self.log.info('Rule 13: if markov_probs_b == 0.478261, then choose P(2.0)')
                decided_multiplier.multiplier_for_box_one = 2.5
                decided_multiplier.multiplier_for_box_two = 2.0
            # Rule 14: if markov_probs_pk == 0.181818, then choose P(2.0)
            elif round(markov_probs['Pk']) == 0.181818:
                self.log.info('Rule 14: if markov_probs_pk == 0.181818, then choose P(2.0)')
                decided_multiplier.multiplier_for_box_one = 2.5
                decided_multiplier.multiplier_for_box_two = 2.0
            # Rule 15: if markov_probs_p / 2.666656 == markov_probs_pk, then choose P(2.0)
            elif round(markov_probs['P'] / 2.666656) == markov_probs['Pk']:
                self.log.info('Rule 15: if markov_probs_p / 2.666656 == markov_probs_pk, then choose P(2.0)')
                decided_multiplier.multiplier_for_box_one = 2.5
                decided_multiplier.multiplier_for_box_two = 2.0
            # Rule 16: if markov_probs_p / 3 == markov_probs_pk, then choose P(2.0)
            elif round(markov_probs['P'] / 3) == markov_probs['Pk']:
                self.log.info('Rule 16: if markov_probs_p / 3 == markov_probs_pk, then choose P(2.0)')
                decided_multiplier.multiplier_for_box_one = 2.0
                decided_multiplier.multiplier_for_box_two = 1.5
            # Rule 18: if markov_probs_b == markov_probs_pk, then choose P(2.0)
            elif round(markov_probs['B'], 6) == round(markov_probs['Pk'], 6):
                self.log.info('Rule 18: if markov_probs_b == markov_probs_pk, then choose P(2.0)')
                decided_multiplier.multiplier_for_box_one = 2.0
                decided_multiplier.multiplier_for_box_two = 1.5
        
        return decided_multiplier

strategy = MarkovStrategy(
    percentage_to_bet_per_round=0.005,
    maximum_num_bet_history_to_categorize=50,
)
risk_manager = RiskManager(stop_loss=0.05, take_profit=0.1)
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
            # continuous=False
        )
        executor.execute()
    elif arg == 'test':
        executor = Executor(
            strategy=strategy,
            risk_manager=risk_manager,
            data_source=data_source,
            casino=test_casino,
            # continuous=False
        )
        executor.execute()
    elif arg == 'backtest':
        backester = Backtester(
            strategy=strategy,
            risk_manager=risk_manager,
            data_source=data_source,
            start_date='2025-03-23',
            initial_balance=3000,
            # continuous=False,
            live_bet_history_file='live_bet_history/live_bet_history_20250415_125629.json', # 2025-04-15 Sporty
        )
        backester.run()