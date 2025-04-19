import random
import hashlib
from datetime import datetime, timedelta

import polars as pl

class DataSource:
    """
    Handles loading and preprocessing of historical game data using Polars.
    """
    def __init__(self, csv_file: str):
        self.csv_file = csv_file
        self.data = self._load_data()

    def _load_data(self, start_time: str = '07:00:00', end_time: str = '10:00:00') -> pl.DataFrame:
        start_time = datetime.strptime(start_time, "%H:%M:%S").time()
        end_time = datetime.strptime(end_time, "%H:%M:%S").time()
        column_names = [
            "game_round", "date", "time", "server_seed",
            "player_seed_1", "player_seed_2", "player_seed_3",
            "stored_hash", "multiplier"
        ]
        df = pl.read_csv(
            self.csv_file,
            has_header=False,
            new_columns=column_names
        ).select(
            ["game_round", "date", "time", "multiplier"]
        ).filter(
            (pl.col("time") >= str(start_time)) & (pl.col("time") <= str(end_time))
        )
        return df
    
    def load_data(self, start_time: str = '07:00:00', end_time: str = '10:00:00') -> None:
        self.data = self._load_data(start_time=start_time, end_time=end_time)
    
    def get_data_by_date_and_time(self, start_date: str, end_date: str = None, start_time: str = '00:00:00', end_time: str = '23:59:59') -> pl.DataFrame:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else start_date
        start_time = datetime.strptime(start_time, "%H:%M:%S").time()
        end_time = datetime.strptime(end_time, "%H:%M:%S").time()
        return self.data.filter(
            (pl.col("date") >= str(start_date)) &
            (pl.col("date") <= str(end_date)) &
            (pl.col("time") >= str(start_time)) &
            (pl.col("time") <= str(end_time))
        )
    
    def get_data_before_date_and_time(self, start_date: str, look_back: int, start_time: str = '00:00:00', end_time: str = '23:59:59') -> pl.DataFrame:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = start_date - timedelta(days=look_back)
        start_time = datetime.strptime(start_time, "%H:%M:%S").time()
        end_time = datetime.strptime(end_time, "%H:%M:%S").time()
        return self.data.filter(
            (pl.col("date") <= str(start_date)) &
            (pl.col('date') >= str(end_date)) &
            (pl.col("time") >= str(start_time)) &
            (pl.col("time") <= str(end_time))
        )
    
    def repurpose_live_bet_history(self, bet_history_file: str) -> None:
        bet_history: pl.DataFrame = pl.read_json(
            bet_history_file,
        ).select(
            ["date", "time", "multiplier"]
        )
        bet_history = bet_history.with_columns(
            pl.Series("game_round", [random.randint(1, 10000) for _ in range(len(bet_history))])
        )
        self.data = bet_history


if __name__ == '__main__':
    data_source = DataSource(csv_file="sporty_aviator_data.csv")
    # print(data_source.data)
    # print(f"Total number of game rounds: {len(data_source.data)}")
    data_source.repurpose_live_bet_history('live_bet_history/live_bet_history_20250413_081927.json')
    print(data_source.data)
    print(f"Total number of game rounds: {len(data_source.data)}")
