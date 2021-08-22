from colorama import Fore, Style
import time
import os
import sys
from datetime import datetime
import pandas as pd

from freqtrade.utils.binance_rest_api import get_candles

def yellow(text):
    return f"{Fore.YELLOW}{text}{Style.RESET_ALL}"

def main():
    timeframe = "15m"
    old_msgs = []
    pairs = sys.argv[1:]
    print(f"RUNNING REJECT BITCOIN")
    while True:
        try:
            btc_df = get_candles("BTC/USDT", timeframe)
            btc_close = btc_df["close"].iloc[-2]
            btc_open = btc_df["open"].iloc[-2]
            new_msgs = []
            for pair in pairs:
                df = get_candles(pair+"/USDT", timeframe)
                pair_close = df["close"].iloc[-2]
                pair_open = df["open"].iloc[-2]
                if btc_close < btc_open and pair_close > pair_open or \
                   btc_close > btc_open and pair_close < pair_open:
                    new_msgs.append(f"{pair} rejecting: https://www.binance.com/en/trade/{pair}_USDT?layout=pro&type=spot")
        except Exception as exception:
            print(f"exception {exception}")
        for nm in new_msgs:
            if nm not in old_msgs:
                os.system(
                    f"notify-send \"{nm}\" -t 5000 -i /usr/share/icons/gnome/48x48/actions/stock_about.png")
                print(yellow(nm))
        old_msgs = new_msgs
        time.sleep(30)
        print("")

main()
