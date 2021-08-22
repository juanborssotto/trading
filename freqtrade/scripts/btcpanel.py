import requests
from dataclasses import dataclass
import time
import os
import sys
from datetime import datetime, timedelta
from freqtrade.utils.binance_rest_api import get_candles
from colorama import Fore, Style
import freqtrade.vendor.qtpylib.indicators as qtpylib
import talib.abstract as ta
import os

def bright_red(text):
    return f"{Style.BRIGHT + Fore.RED}{text}{Style.RESET_ALL}"


def bright_green(text):
    return f"{Style.BRIGHT + Fore.GREEN}{text}{Style.RESET_ALL}"


def red(text):
    return f"{Fore.RED}{text}{Style.RESET_ALL}"


def green(text):
    return f"{Fore.GREEN}{text}{Style.RESET_ALL}"


def yellow(text):
    return f"{Fore.YELLOW}{text}{Style.RESET_ALL}"

timeframes = ["1h", "4h", "1d"]

urgency = "-t 5000"

def get_ema12_text(df, status, timeframe):
    ema = ta.EMA(df, 12).tolist()
    current_price = df["close"].iloc[-1]
    current_ema = ema[-1]
    increase_pct_with_current_ema = round((current_price - current_ema) / current_ema * 100, 2)
    if current_price > current_ema:
        if status.is_last_iteration_ema12_green != None and not status.is_last_iteration_ema12_green:
            os.system(
                f"notify-send \"{timeframe} GREEN BTC EMA 12\"  {urgency} -i /usr/share/icons/gnome/48x48/actions/stock_about.png")
        status.is_last_iteration_ema12_green = True
        return green(f'EMA12: {increase_pct_with_current_ema}\n')
    else:
        if status.is_last_iteration_ema12_green != None and status.is_last_iteration_ema12_green:
            os.system(
                f"notify-send \"{timeframe} RED BTC EMA 12\"  {urgency} -i /usr/share/icons/gnome/48x48/actions/stock_about.png")
        status.is_last_iteration_ema12_green = False
        return red(f'EMA12: {increase_pct_with_current_ema}\n')

def get_ema50_text(df, status, timeframe):
    ema = ta.EMA(df, 50).tolist()
    current_price = df["close"].iloc[-1]
    current_ema = ema[-1]
    increase_pct_with_current_ema = round((current_price - current_ema) / current_ema * 100, 2)
    if current_price > current_ema:
        if status.is_last_iteration_ema50_green != None and not status.is_last_iteration_ema50_green:
            os.system(
                f"notify-send \"{timeframe} GREEN BTC EMA 50\"  {urgency} -i /usr/share/icons/gnome/48x48/actions/stock_about.png")
        status.is_last_iteration_ema50_green = True
        return green(f'EMA50: {increase_pct_with_current_ema}\n')
    else:
        if status.is_last_iteration_ema50_green != None and status.is_last_iteration_ema50_green:
            os.system(
                f"notify-send \"{timeframe} RED BTC EMA 50\"  {urgency} -i /usr/share/icons/gnome/48x48/actions/stock_about.png")
        status.is_last_iteration_ema50_green = False
        return red(f'EMA50: {increase_pct_with_current_ema}\n')

def get_ema100_text(df, status, timeframe):
    ema = ta.EMA(df, 100).tolist()
    current_price = df["close"].iloc[-1]
    current_ema = ema[-1]
    increase_pct_with_current_ema = round((current_price - current_ema) / current_ema * 100, 2)
    if current_price > current_ema:
        if status.is_last_iteration_ema100_green != None and not status.is_last_iteration_ema100_green:
            os.system(
                f"notify-send \"{timeframe} GREEN BTC EMA 100\"  {urgency} -i /usr/share/icons/gnome/48x48/actions/stock_about.png")
        status.is_last_iteration_ema100_green = True
        return green(f'EMA100: {increase_pct_with_current_ema}\n')
    else:
        if status.is_last_iteration_ema100_green != None and status.is_last_iteration_ema100_green:
            os.system(
                f"notify-send \"{timeframe} RED BTC EMA 100\"  {urgency} -i /usr/share/icons/gnome/48x48/actions/stock_about.png")
        status.is_last_iteration_ema100_green = False
        return red(f'EMA100: {increase_pct_with_current_ema}\n')

def get_vwap_text(df, status, timeframe):
    vwap = qtpylib.rolling_vwap(df, window=14).tolist()
    current_price = df["close"].iloc[-1]
    current_vwap = vwap[-1]
    increase_pct_with_current_vwap = round((current_price - current_vwap) / current_vwap * 100, 2)
    if current_price > current_vwap:
        if status.is_last_iteration_vwap_green != None and not status.is_last_iteration_vwap_green:
            os.system(
                f"notify-send \"{timeframe} GREEN BTC VWAP\"  {urgency} -i /usr/share/icons/gnome/48x48/actions/stock_about.png")
        status.is_last_iteration_vwap_green = True
        return green(f'VWAP: {increase_pct_with_current_vwap}\n')
    else:
        if status.is_last_iteration_vwap_green != None and status.is_last_iteration_vwap_green:
            os.system(
                f"notify-send \"{timeframe} RED BTC VWAP\"  {urgency} -i /usr/share/icons/gnome/48x48/actions/stock_about.png")
        status.is_last_iteration_vwap_green = False
        return red(f'VWAP: {increase_pct_with_current_vwap}\n')

def get_volume_text(df, threshold, status, timeframe):
    current_volume = df["volume"].iloc[-1]
    max_volume_in_last_50_candles = df["volume"].rolling(50).max().iloc[-1]
    pct_compared_to_max_volume_in_last_50_candles = \
      round(current_volume * 100 / max_volume_in_last_50_candles, 2)
    if pct_compared_to_max_volume_in_last_50_candles >= threshold:
        if status.is_last_iteration_volume_green != None and not status.is_last_iteration_volume_green:
            os.system(
                f"notify-send \"{timeframe} GREEN BTC VOLUME\"  {urgency} -i /usr/share/icons/gnome/48x48/actions/stock_about.png")
        status.is_last_iteration_volume_green = True
        return f"VOLUME: {pct_compared_to_max_volume_in_last_50_candles}\n"
    else:
        status.is_last_iteration_volume_green = False
        return f"VOLUME: {pct_compared_to_max_volume_in_last_50_candles}\n"

def main():
    print(f"RUNNING BTC PANEL")
    @dataclass
    class Status:
        is_last_iteration_ema12_green: bool = None
        is_last_iteration_ema50_green: bool = None
        is_last_iteration_ema100_green: bool = None
        is_last_iteration_vwap_green: bool = None
        is_last_iteration_volume_green: bool = None

    # VOLUME
    threshold = 30

    # pairs = ["BTC", "ETH"]
    pairs = ["BTC"]
    status_manager = dict()
    for pair in pairs:
        for timeframe in timeframes:
            key = f"{pair}{timeframe}"
            status_manager[key] = Status()
            # EMA
            status_manager[key].is_last_iteration_ema12_green = None
            status_manager[key].is_last_iteration_ema50_green = None
            status_manager[key].is_last_iteration_ema100_green = None
            # VWAP
            status_manager[key].is_last_iteration_vwap_green = None
            # VOLUME
            status_manager[key].is_last_iteration_volume_green = None

    while True:
        text = ''
        for pair in pairs:
            text += yellow(f'{pair} PANEL\n')
            for timeframe in timeframes:
                df = get_candles(f"{pair}/USDT", timeframe)
                key = f"{pair}{timeframe}"
                status = status_manager[key]
                text += yellow(f"{timeframe}:\n")
                text += get_ema12_text(df, status, timeframe)
                text += get_ema50_text(df, status, timeframe)
                text += get_ema100_text(df, status, timeframe)
                text += get_vwap_text(df, status, timeframe)
                text += get_volume_text(df, threshold, status, timeframe)
            text += "\n"
        print(chr(27) + "[2J")
        print(text)
        time.sleep(10)

main()
