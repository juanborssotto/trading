import sys
import talib.abstract as ta
from colorama import Fore, Style
import time
import os
from datetime import datetime
import pandas as pd
import freqtrade.vendor.qtpylib.indicators as qtpylib

from freqtrade.utils.binance_rest_api import get_candles

def red(text):
    return f"{Fore.RED}{text}{Style.RESET_ALL}"


def green(text):
    return f"{Fore.GREEN}{text}{Style.RESET_ALL}"


def yellow(text):
    return f"{Fore.YELLOW}{text}{Style.RESET_ALL}"


def get_ema_text(df, length, timeframe):
    ema = ta.EMA(df, length).tolist()
    current_price = df["close"].iloc[-1]
    current_ema = ema[-1]
    increase_pct_with_current_ema = round((current_price - current_ema) / current_ema * 100, 2)
    close = ""
    if increase_pct_with_current_ema >= -0.4 and increase_pct_with_current_ema <= 0.4:
        close = "             IS CLOSE"
    if current_price > current_ema:
        return green(f'EMA{length}: {increase_pct_with_current_ema}{close}\n')
    else:
        return red(f'EMA{length}: {increase_pct_with_current_ema}{close}\n')

def get_vwap_text(df, timeframe):
    vwap = qtpylib.rolling_vwap(df, window=14).tolist()
    current_price = df["close"].iloc[-1]
    current_vwap = vwap[-1]
    increase_pct_with_current_vwap = round((current_price - current_vwap) / current_vwap * 100, 2)
    close = ""
    if increase_pct_with_current_vwap >= -0.4 and increase_pct_with_current_vwap <= 0.4:
        close = "             IS CLOSE"
    if current_price > current_vwap:
        return green(f'VWAP: {increase_pct_with_current_vwap}{close}\n')
    else:
        return red(f'VWAP: {increase_pct_with_current_vwap}{close}\n')

def main():
    # timeframes = ["1h", "4h", "1d"]
    timeframes = ["15m", "1h", "4h"]
    emas = [9, 12, 26, 50, 100]
    # vwap
    pair = sys.argv[1]
    while True:
        try:
            text = ''
            for timeframe in timeframes:
                df = get_candles(f"{pair}/USDT", timeframe)
                text += yellow(f"{timeframe}:\n")
                for length in emas:
                    text += get_ema_text(df, length, timeframe)
                text += get_vwap_text(df, timeframe)
            text = text[:-2]
            print(chr(27) + "[2J")
            print(text)
            time.sleep(3)
        except Exception as exception:
            print(exception)

main()
