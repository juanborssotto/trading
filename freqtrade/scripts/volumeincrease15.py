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

timeframe = "15m"

is_notif_sent_during_last_hour = False
triple_pattern_is_notif_sent_during_last_hour = False

class Result:
    def __init__(self, pair, pct):
        self.pair = pair
        self.pct = pct


def main():
    old_msgs = []
    print("RUNNING VOLUME INCREASE CHECKER")
    while True:
        try:
            new_msgs = []
            for pair in pairs:
                df = get_candles(pair+"/USDT", timeframe)
                secs_since = (datetime.utcnow() - pd.to_datetime(df["date"]).iloc[-1]).seconds

                current_volume = df["volume"].iloc[-1]
                max_volume_in_last_50_candles = df["volume"].rolling(50).max().iloc[-1]
                pct_compared_to_max_volume_in_last_50_candles = \
                    round(current_volume * 100 / max_volume_in_last_50_candles, 2)
                if pct_compared_to_max_volume_in_last_50_candles >= 25:
                    new_msgs.append(f"BIG VOLUME in {pair}: %{pct_compared_to_max_volume_in_last_50_candles}")

                ## Three increasing green
                #if df["close"].iloc[-3] > df["open"].iloc[-3] and \
                #    df["close"].iloc[-2] > df["open"].iloc[-2] and \
                #    df["close"].iloc[-1] > df["open"].iloc[-1] and \
                #    df["volume"].iloc[-1] > df["volume"].iloc[-3] and \
                #    df["volume"].iloc[-2] > df["volume"].iloc[-3]:
                #    msg = "Triple volume pattern found"
                #    #os.system(
                #    #    f"notify-send \"{msg}\"  --urgency critical -i /usr/share/icons/gnome/48x48/actions/stock_about.png")
                #    print(yellow(f"triple pattern in {pair} in minute {datetime.now().minute}"))

                ## patrón 2 velas: 1era vela roja, 2da vela verde que supera en 100% al volumen a la vela anterior
                ## también probar 2-3 velas rojas primero con volumen en aumento y disminución y luego una vela verde que supera en vol.
                #if df["close"].iloc[-3] < df["open"].iloc[-3] and \
                #    df["close"].iloc[-2] < df["open"].iloc[-2] and \
                #    df["close"].iloc[-1] > df["open"].iloc[-1] and \
                #    df["volume"].iloc[-3] > df["volume"].iloc[-2] and \
                #    df["volume"].iloc[-1] > df["volume"].iloc[-2]:
                #    msg = "Invert with volume found"
                #    #os.system(
                #    #    f"notify-send \"{msg}\"  --urgency critical -i /usr/share/icons/gnome/48x48/actions/stock_about.png")
                #    print(yellow(f"invert with volume found in {pair} in minute {datetime.now().minute}"))

                ## patrón 3 velas: 1ra y 2da velas rojas con volumen decayendo, vela actual con close mayor a última vela roja
                #if df["close"].iloc[-3] < df["open"].iloc[-3] and \
                #    df["close"].iloc[-2] < df["open"].iloc[-2] and \
                #    df["close"].iloc[-1] > df["open"].iloc[-1] and \
                #    df["volume"].iloc[-3] > df["volume"].iloc[-2]:
                #    msg = "Invert found"
                #    #os.system(
                #    #    f"notify-send \"{msg}\"  --urgency critical -i /usr/share/icons/gnome/48x48/actions/stock_about.png")
                #    print(yellow(f"invert pattern found in {pair} in minute {datetime.now().minute}"))





                #if secs_since <= 60 * 5.5:
                #    pct = df["volume"].iloc[-1] * 100 / df["volume"].iloc[-2]
                #    if pct >= 50:
                #        if not is_notif_sent_during_last_hour:
                #            is_notif_sent_during_last_hour = True
                #            msg = "Volume increase found"
                #            os.system(
                #                f"notify-send \"{msg}\"  --urgency critical -i /usr/share/icons/gnome/48x48/actions/stock_about.png")
                #        results.append(Result(pair, pct))

                #if secs_since <= 60 * 8.2:
                #    pct = df["volume"].iloc[-1] * 100 / df["volume"].iloc[-2]
                #    if df["volume"].iloc[-1] > df["volume"].iloc[-2]:
                #        if not is_notif_sent_during_last_hour:
                #            is_notif_sent_during_last_hour = True
                #            msg = "Volume increase found"
                #            os.system(
                #                f"notify-send \"{msg}\"  --urgency critical -i /usr/share/icons/gnome/48x48/actions/stock_about.png")
                #        results.append(Result(pair, pct))
                #else:
                #    is_notif_sent_during_last_hour = False
            for nm in new_msgs:
                nm_ = nm.split(":")[0]
                old_msgs_ = [msg.split(":")[0] for msg in old_msgs]
                if nm_ not in old_msgs_:
                    os.system(
                        f"notify-send \"{nm_}\" -t 5000 -i /usr/share/icons/gnome/48x48/actions/stock_about.png")
                print(yellow(nm))
            old_msgs = new_msgs
            time.sleep(15)
            print("")
        except Exception as exception:
            print(f"exception {exception}")

main()
