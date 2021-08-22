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

pairs = [
    "BCH", 
    "BNB", 
    "CAKE", 
    "CHZ", 
    "DOGE", 
    "DOT", 
    "EOS", 
    "ETH", 
    "FIL", 
    "LINK", 
    "MATIC", 
    "TRX", 
    "UNI", 
    "VET", 
    "XLM", 
    "XRP", 
    "AXS", 
    "ALICE", 
    "SUSHI", 
    "AAVE", 
    "BAKE", 
    "ENJ", 
    "LUNA", 
    "SOL", 
    "ETC",
    "BTC",
]

#pairs = [
#    "BCH", 
#    "BNB", 
#    "BTC",
#    "CAKE",
#    "CHZ",
#    
#]

timeframe = "1h"

threshold = 60

is_notif_sent_during_last_hour = False


class Result:
    def __init__(self, pair, pct):
        self.pair = pair
        self.pct = pct


print("RUNNING VOLUME INCREASE CHECKER")
while True:
    results = []
    for pair in pairs:
        if datetime.now().minute <= 40:
            df = get_candles(pair+"/USDT", timeframe)

            if datetime.now().minute <= 15:
                pct = df["volume"].iloc[-1] * 100 / df["volume"].iloc[-2]
                if pct >= 40:

                    if not is_notif_sent_during_last_hour:
                        is_notif_sent_during_last_hour = True
                        msg = "Volume increase found"
                        os.system(
                            f"notify-send \"{msg}\"  -t 5000 -i /usr/share/icons/gnome/48x48/actions/stock_about.png")

                    results.append(Result(pair, pct))

            #if datetime.now().minute <= 25:
            #    pct = df["volume"].iloc[-1] * 100 / df["volume"].iloc[-2]
            #    if pct > 60:

            #        if not is_notif_sent_during_last_hour:
            #            is_notif_sent_during_last_hour = True
            #            msg = "Volume increase found"
            #            os.system(
            #                f"notify-send \"{msg}\"  --urgency critical -i /usr/share/icons/gnome/48x48/actions/stock_about.png")

            #        msg = f"volume increase in {pair} %{pct} in minute {datetime.now().minute}"
            #        print(green(msg))
            #        if len(sys.argv) > 1:
            #            os.system(
            #                f"notify-send \"{msg}\"  --urgency critical -i /usr/share/icons/gnome/48x48/actions/stock_about.png")

            #if datetime.now().minute <= 10:
            #    pct = df["volume"].iloc[-1] * 100 / df["volume"].iloc[-2]
            #    if pct > 20:

            #        if not is_notif_sent_during_last_hour:
            #            is_notif_sent_during_last_hour = True
            #            msg = "Volume increase found"
            #            os.system(
            #                f"notify-send \"{msg}\"  --urgency critical -i /usr/share/icons/gnome/48x48/actions/stock_about.png")

            #        msg = f"volume increase in {pair} %{pct} in minute {datetime.now().minute}"
            #        print(green(msg))
            #        if len(sys.argv) > 1:
            #            os.system(
            #                f"notify-send \"{msg}\"  --urgency critical -i /usr/share/icons/gnome/48x48/actions/stock_about.png")

            #if datetime.now().minute > 10 and datetime.now().minute <= 20:
            #    pct = df["volume"].iloc[-1] * 100 / df["volume"].iloc[-2]
            #    if pct > 30:

            #        if not is_notif_sent_during_last_hour:
            #            is_notif_sent_during_last_hour = True
            #            msg = "Volume increase found"
            #            os.system(
            #                f"notify-send \"{msg}\"  --urgency critical -i /usr/share/icons/gnome/48x48/actions/stock_about.png")

            #        msg = f"volume increase in {pair} %{pct} in minute {datetime.now().minute}"
            #        print(green(msg))
            #        if len(sys.argv) > 1:
            #            os.system(
            #                f"notify-send \"{msg}\"  --urgency critical -i /usr/share/icons/gnome/48x48/actions/stock_about.png")
        else:
            is_notif_sent_during_last_hour = False
    results.sort(key=lambda x: x.pct, reverse=True)
    for r in results:
        msg = f"volume increase in {pair} %{pct} in minute {datetime.now().minute}"
        print(green(msg))
    time.sleep(40)
    print("")

#df = get_candles("BTC"+"/USDT", timeframe)
#print((datetime.utcnow() - pd.to_datetime(df["date"]).iloc[-1]).seconds)
#print(type(df["date"].to_datetime().iloc[-1]))
