import talib.abstract as ta
from colorama import Fore, Style

from freqtrade.utils.binance_rest_api import get_candles
import numpy as np

import sys

def green(text):
    return f"{Fore.GREEN}{text}{Style.RESET_ALL}"

def red(text):
    return f"{Fore.RED}{text}{Style.RESET_ALL}"


def yellow(text):
    return f"{Fore.YELLOW}{text}{Style.RESET_ALL}"

def print_trend(pair, timeframe):
    df = get_candles(pair, timeframe)
    sar = ta.SAR(df)
    df["sar_trend"] = np.where(
        (sar.shift(1) < df["close"].shift(1)) &
        (sar > df["close"]),
        sar,
        np.nan
    )
    sar_trend = df["sar_trend"].dropna()
    if sar_trend.iloc[-1] < sar_trend.iloc[-2]:
        print(red(f"{timeframe} is in down-trend"))
    else:
        print(green(f"{timeframe} is in up-trend"))

pair = f"{sys.argv[1]}/USDT"
timeframes = ["15m", "30m", "1h", "2h", "4h", "1d", "1w"]
print(yellow(pair))
for t in timeframes:
    print_trend(pair, t)
