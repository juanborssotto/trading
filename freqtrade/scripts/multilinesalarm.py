import sys
import talib.abstract as ta
from colorama import Fore, Style
import time
import os
from datetime import datetime
import pandas as pd
import freqtrade.vendor.qtpylib.indicators as qtpylib
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
# timeframes = ["1d", "1w"]
timeframes = ["1d"]

def get_next_value_(starting_value, final_value):
    if starting_value > final_value:
        decrease = (starting_value - final_value) / final_value * 100

        new_starting_value = final_value
        next_value = ((decrease / 100) * new_starting_value - new_starting_value) * -1
        return next_value
    increase = (final_value - starting_value) / starting_value * 100

    new_starting_value = final_value
    next_value = (increase / 100) * new_starting_value + new_starting_value
    return next_value

def get_next_value(starting_value, final_value, n):
    #st = starting_value
    #fin = final_value
    next_value = get_next_value_(starting_value, final_value)
    #for _ in range(0, n):
    #    next_value = get_next_value_(st, fin)
    #    st = fin
    #    fin = next_value
    return (next_value - final_value) * n + final_value

def main():
    old_msgs = []
    lookback = 8
    print("RUNNING LINES ALARM")
    while True:
        try:
            new_msgs = []
            for timeframe in timeframes:
                for pair in pairs:
                    df = get_candles(pair+"/USDT", timeframe)
                    for i in range(0, lookback):
                        ongoing_price = df["close"].iloc[-1]
                        # Highs
                        two_candles_back_high = df["high"].iloc[-i-3]
                        one_candle_back_high = df["high"].iloc[-i-2]
                        next_high_threshold = get_next_value(two_candles_back_high, one_candle_back_high, i+1)
                        distance_to_next_high_threshold = (next_high_threshold - ongoing_price) / ongoing_price * 100
                        if -1 < distance_to_next_high_threshold < 1:
                            new_msgs.append(f"{pair} in {timeframe} is close to next high {next_high_threshold} {i}")
                        # Lows
                        two_candles_back_low = df["low"].iloc[-i-3]
                        one_candle_back_low = df["low"].iloc[-i-2]
                        next_low_threshold = get_next_value(two_candles_back_low, one_candle_back_low, i+1)
                        distance_to_next_low_threshold = (next_low_threshold - ongoing_price) / ongoing_price * 100
                        if -1 < distance_to_next_low_threshold < 1:
                            new_msgs.append(f"{pair} in {timeframe} is close to next low {next_low_threshold} {i}")
                        #print(two_candles_back_high, one_candle_back_high, next_high_threshold, distance_to_next_high_threshold)
                        #print(two_candles_back_low, one_candle_back_low, next_low_threshold, distance_to_next_low_threshold)
            for nm in new_msgs:
                if nm not in old_msgs:
                    os.system(
                        #f"notify-send \"{nm}\"  --urgency critical -i /usr/share/icons/gnome/48x48/actions/stock_about.png")
                        f"notify-send \"{nm}\"  -t 4000 -i /usr/share/icons/gnome/48x48/actions/stock_about.png")
                    print(yellow(nm))
            old_msgs = new_msgs
            print("--")
            time.sleep(60)
            print("")
        except Exception as exception:
            print(f"exception {exception}")

main()
