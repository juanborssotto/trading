import talib.abstract as ta
from colorama import Fore, Style
import time
import os
import sys
from datetime import datetime
import pandas as pd

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

class Result:
    def __init__(self, pair, pct):
        self.pair = pair
        self.pct = pct


print("RUNNING VOLUME INCREASE CHECKER")
results = []
for pair in pairs:
    df = get_candles(pair+"/USDT", timeframe)
    pct = df["volume"].iloc[-1] * 100 / df["volume"].iloc[-2]
    results.append(Result(pair, pct))
results.sort(key=lambda x: x.pct, reverse=True)
for r in results:
    msg = f"{r.pair} %{round(r.pct, 2)}"
    print(green(msg))
