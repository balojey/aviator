from threading import Thread
import queue

from dotenv import load_dotenv

from bot.casino import Spribe
from bot.data_source import DataSource


load_dotenv()

if __name__ == '__main__':
    # spribe = Spribe()
    # spribe.login()
    # spribe.launch_aviator()
    # print(spribe.driver.current_url)
    # balance = spribe.get_balance()
    # print(balance)
    # while True:
    #     if spribe.is_ready():
    #         result_queue = queue.Queue()
    #         amount_to_bet = round(balance * 0.01)
    #         # spribe.place_bet(amount_to_bet)
    #         spribe.place_bet_in_box_one(amount_to_bet)
    #         spribe.place_bet_in_box_two(amount_to_bet)
    #         cash_out_amount_1 = amount_to_bet * 1.05
    #         cash_out_amount_2 = amount_to_bet * 1.10
    #         # spribe.cash_out(cash_out_amount)
    #         def cash_out_box_one():
    #             result = spribe.cash_out_box_one(cash_out_amount_1)
    #             result_queue.put(result)

    #         def cash_out_box_two():
    #             result = spribe.cash_out_box_two(cash_out_amount_2)
    #             result_queue.put(result)

    #         thread_one = Thread(target=cash_out_box_one)
    #         thread_two = Thread(target=cash_out_box_two)

    #         thread_one.start()
    #         thread_two.start()

    #         thread_one.join()
    #         thread_two.join()
    #         result_one = result_queue.get()
    #         result_two = result_queue.get()

    #         print(f"Result from cash_out_box_one: {result_one}")
    #         print(f"Result from cash_out_box_two: {result_two}")

    data_source = DataSource(csv_file="sporty_aviator_data.csv")
    data_source.repurpose_live_bet_history('live_bet_history/live_bet_history_20250414_005208.json')
    print(data_source.data)
    print(f"Total number of game rounds: {len(data_source.data)}")