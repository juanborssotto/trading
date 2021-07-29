import talib.abstract as ta
from colorama import Fore, Style
import time
import os

from freqtrade.utils.binance_rest_api import get_candles


def calculate_increase(start: float, final: float) -> float:
    return (final - start) / start * 100

def green(text):
    return f"{Fore.GREEN}{text}{Style.RESET_ALL}"

def red(text):
    return f"{Fore.RED}{text}{Style.RESET_ALL}"


def yellow(text):
    return f"{Fore.YELLOW}{text}{Style.RESET_ALL}"

config = {
    "BTC": 50,
    "CAKE": 100,
    "MATIC": 100,
    "LTC": 100,
    "BCH": 100,
    "ADA": 140,
    "ETC": 160,
    "DOGE": 200,
    "XRP": 100,
}

timeframe = "1h"

print("RUNNING EMA CHECKER")
while True:
    for pair, ema_length in config.items():
        df = get_candles(pair+"/USDT", timeframe)
        ema = ta.EMA(df, ema_length).tolist()
        increase_pct = calculate_increase(ema[-1], df["close"].iloc[-1])
        if increase_pct < 2:
            msg = f"{pair} ema {ema_length}"
            print(msg)
            os.system(
                f"notify-send \"{msg}\"  --urgency critical -i /usr/share/icons/gnome/48x48/actions/stock_about.png")
    time.sleep(300)
