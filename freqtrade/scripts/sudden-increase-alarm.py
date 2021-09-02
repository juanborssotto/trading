import time
import os
import sys
from datetime import datetime, timedelta
from freqtrade.utils.binance_rest_api import get_candles
from colorama import Fore, Style
import freqtrade.vendor.qtpylib.indicators as qtpylib

def calculate_increase(start: float, final: float) -> float:
    return (final - start) / start * 100

pairs = sys.argv[1:]
timeframe = "15m"

print(f"RUNNING SUDDEN INCREASE ALARM: {pairs}")
old_msgs = []
while True:
    new_msgs = []
    for pair in pairs:
        df = get_candles(pair+"/USDT", timeframe)
        vwap = qtpylib.rolling_vwap(df, window=14).tolist()
        vwap_increase = calculate_increase(vwap[-3], vwap[-2])
        if vwap_increase >= 0.5:
            new_msgs.append(f"{pair} sudden increase found {vwap_increase}")
    for msg in new_msgs:
        nm_ = msg.split("found")[0]
        old_msgs_ = [msg.split("found")[0] for msg in old_msgs]
        if nm_ not in old_msgs_:
            os.system(
                f"notify-send \"{msg}\"  --urgency critical -i /usr/share/icons/gnome/48x48/actions/stock_about.png")
                # f"notify-send \"{msg}\"  -t 5000 -i /usr/share/icons/gnome/48x48/actions/stock_about.png")
            print(msg)
    old_msgs = new_msgs
    time.sleep(60)
    print("")
