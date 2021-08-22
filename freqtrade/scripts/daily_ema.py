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

pairs = sys.argv[1:]
timeframe = "1d"
threshold = 1

initial_ema = 4
max_ema_to_check = 10
lookback_candles = 7

class Result:
    def __init__(self, ema, msg):
        self.ema = ema
        self.msg = msg

print("RUNNING DAILY EMA ALARM")
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
    print(f"{pair} mode ema length is {mode_ema_length}")
