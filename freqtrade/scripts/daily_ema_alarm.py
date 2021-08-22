import talib.abstract as ta
from typing import List
from colorama import Fore, Style
import time
import os
import sys
from freqtrade.utils.binance_rest_api import get_candles


def calculate_increase(start: float, final: float) -> float:
    return (final - start) / start * 100

def green(text):
    return f"{Fore.GREEN}{text}{Style.RESET_ALL}"

def red(text):
    return f"{Fore.RED}{text}{Style.RESET_ALL}"


def yellow(text):
    return f"{Fore.YELLOW}{text}{Style.RESET_ALL}"

mode = sys.argv[1]
pairs = sys.argv[2:]
timeframe = "1d"
threshold = 2

initial_ema = 4
max_ema_to_check = 35
lookback_candles = 3

class Result:
    def __init__(self, pair, ema, msg):
        self.pair = pair
        self.ema = ema
        self.msg = msg

last_loop = []

print("RUNNING DAILY EMA ALARM")
while True:
    results: List[Result] = []
    for pair in pairs:
        df = get_candles(pair+"/USDT", timeframe)
        ongoing_price = df["close"].iloc[-1]
        df_with_ongoing_candle = df.copy()
        df.drop(df.tail(1).index,inplace=True)

        distances_to_ema_by_lookback_candles = [[] for _ in range(lookback_candles)]

        for i in range(initial_ema, max_ema_to_check + 1):
            ema = ta.EMA(df, i)
            df["distances"] = (
                (df["low"] - ema) / ema * 100
            ).abs()

            only_lookback_candles_distances = df["distances"].tail(lookback_candles).tolist()
            for j in range(0, len(only_lookback_candles_distances)):
                distances_to_ema_by_lookback_candles[j].append(only_lookback_candles_distances[j])

        closest_emas_by_lookback_candle = []
        for all_ema_distances in distances_to_ema_by_lookback_candles:
            closest_emas_by_lookback_candle.append(
                all_ema_distances.index(min(all_ema_distances)) + initial_ema)
        mode_ema_length = max(set(closest_emas_by_lookback_candle), key=closest_emas_by_lookback_candle.count)

        ongoing_ema = ta.EMA(df_with_ongoing_candle, mode_ema_length).tolist()[-1]
        distance = (ongoing_ema - ongoing_price) / ongoing_price * 100
        if mode == "both":
            if abs(distance) <= threshold:
                results.append(Result(pair, mode_ema_length, 
                f'{pair} is close to ema {mode_ema_length} {round(abs(distance), 2)}'))
        elif mode == "buy":
            if distance < 0 and abs(distance) <= threshold:
                results.append(Result(pair, mode_ema_length, 
                f'{pair} is close to ema {mode_ema_length} {round(abs(distance), 2)}'))
        elif mode == "sell":
            if distance > 0 and abs(distance) <= threshold:
                results.append(Result(pair, mode_ema_length, 
                f'{pair} is close to ema {mode_ema_length} {round(abs(distance), 2)}'))

    new_last_loop = []
    for i in range(initial_ema, max_ema_to_check + 1):
        for result in results:
            if result.ema == i:
                new_last_loop.append(result.pair)
                if result.pair not in last_loop:
                    os.system(
                        f"notify-send \"{result.msg}\"  --urgency critical -i /usr/share/icons/gnome/48x48/actions/stock_about.png")
                print(result.msg)
    last_loop = new_last_loop
    print("----------------------------------------------------------------------------------------")
    time.sleep(60)
