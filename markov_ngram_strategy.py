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
from bot.data_source.round_result import RoundResult
from bot.strategy import BettingStrategy
from bot.strategy.executor import Executor
from bot.strategy.risk_manager import RiskManager


logfire.configure()
logfire.instrument_httpx(capture_all=True)
load_dotenv()


# Celery configuration
celery_app = Celery('markov_ngram_strategy', broker='redis://localhost:6379/0', backend='redis://localhost:6379/1')
    
deepseek = OpenAIModel(
    model_name='deepseek-chat',
    provider=DeepSeekProvider(),
)
agent = Agent(
    deepseek,
    result_type=str,
    system_prompt="""
You are an expert Python programmer with deep knowledge of statistical modeling, N-gram pattern recognition, and probabilistic game prediction systems.

Your task is to write production-ready Python functions based on the input prompt. These functions are used in a real-time algorithmic bot that predicts the category of the next outcome in a game.

Requirements:
- Use clean, readable code and follow Python best practices.
- Do not include any markdown formatting or explanations — return code only.
- Functions must be self-contained and logically complete.
- Prioritize efficiency and simplicity.
""",
    retries=3,
)
Agent.instrument_all()


def clean_code_output(code: str) -> str:
    return re.sub(r"```(?:python)?\n?|```", "", code).strip()

def write_celery_result_to_file(code: str, filename='ngram_predictions.py'):
    print(code)
    print(filename)
    try:
        with open(filename, 'w') as f:
            f.write(code)
        print("N-gram code written to ngram_predictions.py")
    except Exception as e:
        print(f"Error writing to file: {e}")

@celery_app.task(bind=True)
def fetch_ngram_code_from_deepseek(data: list[str], filename="ngram_predictions.py"):
    try:
        print("Fetching N-gram code from DeepSeek...")
        result = agent.run_sync(
            f"""
            You are analyzing the output of an online game called Aviator. The game emits a sequence of categories:
            - 'B' for values between 1.00 and 1.99
            - 'P' for values between 2.00 and 9.99
            - 'Pk' for values above 10.00

            Here's the sequence: {data}

            Write three Python functions:
            - predict_next_is_pk(history: list[str]) -> bool
            - predict_next_is_purple(history: list[str]) -> bool
            - predict_next_is_blue(history: list[str]) -> bool

            Use N-gram logic (bi/tri/quad-grams) from the sequence to implement these. Optionally include:
            - recommend_next_category(history: list[str]) -> str

            Return only raw Python code!
            Do NOT include markdown formatting (like triple backticks or ```python)!
            Do NOT include any explanations or comments!
            """
        )
        code = clean_code_output(result.data)

        write_celery_result_to_file(code)
    except Exception as e:
        print(f"Error in fetch_ngram_code_from_deepseek: {e}")

class PredictionHistory(BaseModel):
    best_guess: str
    markov_probs_b: float
    markov_probs_p: float
    markov_probs_pk: float
    ngram_b: float
    ngram_p: float
    ngram_pk: float
    actual_category: str = None


class MarkovNgramStrategy(BettingStrategy):
    prediction_module: Any = None
    game_count: int = 0
    recent_predictions: list[tuple[str, str, bool]] = []
    rounds_skipped: int = 0
    loss_streak_detected: bool = False
    maximum_num_bet_history_to_categorize: int
    ngram_generation_interval: int
    prediction_history: list[PredictionHistory] = []
    prediction_history_storage: str = f'data/prediction_history_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

    def __init__(self, percentage_to_bet_per_round: float, maximum_num_bet_history_to_categorize: int, ngram_generation_interval: int):
        super().__init__(
            percentage_to_bet_per_round=percentage_to_bet_per_round,
            maximum_num_bet_history_to_categorize=maximum_num_bet_history_to_categorize,
            ngram_generation_interval=ngram_generation_interval,
        )
        self.recent_predictions = deque(maxlen=50)

    def introduce_strategy(self):
        self.log.info(f"""
        Strategy: {self.__repr_name__()}
        Description: A hybrid strategy using Markov chains and N-gram pattern recognition for game prediction.
        Is Backtest? {self.is_backtest}
        Percentage to bet per round: {self.percentage_to_bet_per_round}
        Maximum number of bet history to categorize: {self.maximum_num_bet_history_to_categorize}
        N-gram generation interval: {self.ngram_generation_interval}
        Prediction history storage: {self.prediction_history_storage}
        """)

    def load_prediction_module(self, path='ngram_predictions.py'):
        if not os.path.exists(path):
            raise FileNotFoundError("N-gram prediction module not found.")

        spec = importlib.util.spec_from_file_location("ngram_predictions", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.prediction_module = module

    def request_ngram_update(self, category_sequence: list[str]):
        # Request N-gram code update from DeepSeek
        fetch_ngram_code_from_deepseek.delay(category_sequence)

    def convert_bet_history_to_dataframe(self, bet_history: list[BetHistory | LiveBetHistory]) -> pl.DataFrame:
        data = [{"multiplier": bh.multiplier, "date": bh.date, 'time': bh.time} for bh in bet_history]
        df = pl.DataFrame(data)
        return df

    def categorize_bet_history(self, bet_history: list[BetHistory | LiveBetHistory]) -> list[str]:
        df = self.convert_bet_history_to_dataframe(bet_history)
        new_categories = []
        old_categories = list(df.get_column('multiplier'))
        for i in old_categories:
            if 1.00 <= i <= 1.99:
                new_categories.append('B')
            elif 2.00 <= i <= 9.99:
                new_categories.append('P')
            else:
                new_categories.append('Pk')
        return new_categories
    
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

    def hybrid_predict(self, history: list[str], weight_ngram=0.6, weight_markov=0.4) -> str:
        markov_model = self.build_markov_model(history)
        current_state = history[-1]
        markov_probs = self.markov_predict_next(markov_model, current_state)

        # N-gram binary predictions
        ngram_scores = {
            'Pk': 1 if self.prediction_module.predict_next_is_pk(history) else 0,
            'P': 1 if self.prediction_module.predict_next_is_purple(history) else 0,
            'B': 1 if self.prediction_module.predict_next_is_blue(history) else 0,
        }

        # Combine scores
        final_scores = {}
        for category in ['Pk', 'P', 'B']:
            final_scores[category] = (weight_ngram * ngram_scores[category]) + (weight_markov * markov_probs.get(category, 0))

        # Choose the best
        best_guess = max(final_scores, key=final_scores.get)
        self.prediction_history.append(PredictionHistory(
            best_guess=best_guess,
            markov_probs_b=markov_probs['B'],
            markov_probs_p=markov_probs['P'],
            markov_probs_pk=markov_probs['Pk'],
            ngram_b=ngram_scores['B'],
            ngram_p=ngram_scores['P'],
            ngram_pk=ngram_scores['Pk']
        ))
        return best_guess
    
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
        self.game_count += 1
        self.log.info(f"Game count: {self.game_count}")
        category_sequence = self.categorize_bet_history(bet_history[-self.maximum_num_bet_history_to_categorize:])
        multiplier = 1.0

        # Check for a streak of 2 losses
        # if len(bet_history) >= 2 and bet_history[-1].result == RoundResult.LOSS and bet_history[-2].result == RoundResult.LOSS:
        #     self.log.info("Streak of 2 losses detected.")
        #     self.loss_streak_detected = True

        if len(bet_history) > 0 and self.game_count > (abs(self.maximum_num_bet_history_to_categorize) + 3) and not self.loss_streak_detected:
            self.record_feedback(
                'B' if 1.00 <= bet_history[-1].decided_multiplier <= 1.99 else 'P' if 2.00 <= bet_history[-1].decided_multiplier <= 9.99 else 'Pk',
                category_sequence[-1]
            )
            self.log.info(f"Accuracy: {self.accuracy()}")
            self.prediction_history[-1].actual_category = category_sequence[-1]
            self.save_prediction_history()

        if self.game_count >= (abs(self.maximum_num_bet_history_to_categorize) + 3) and not self.loss_streak_detected:
            try:
                self.load_prediction_module()
            except FileNotFoundError:
                self.log.info('File not found')
                return multiplier  # Default multiplier if predictions not ready

            best_guess = self.hybrid_predict(category_sequence)
            self.log.info(f"Prediction: {self.prediction_history[-1]}")
            multiplier = 1.0 if best_guess == 'B' else 2.0
                
        if self.game_count > abs(self.maximum_num_bet_history_to_categorize) and self.game_count % self.ngram_generation_interval == 1:
            # Request N-gram update every 50 games after the first 200
            self.log.info("Requesting N-gram update...")
            self.request_ngram_update(category_sequence)

        if self.loss_streak_detected:
            self.rounds_skipped += 1
            self.log.info('Skipping round')
            if self.rounds_skipped >= 10:
                self.loss_streak_detected = False
                self.rounds_skipped = 0
        
        return multiplier
    
    def after_game_round_during_backtesting(self):
        if self.game_count == (abs(self.maximum_num_bet_history_to_categorize) + 1):
            sleep(15)
        if self.game_count >= abs(self.maximum_num_bet_history_to_categorize):
            sleep(3)

strategy = MarkovNgramStrategy(
    percentage_to_bet_per_round=0.001,
    maximum_num_bet_history_to_categorize=50,
    ngram_generation_interval=50
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
            start_date='2025-03-28',
            initial_balance=1000,
            # continuous=False
        )
        backester.run()