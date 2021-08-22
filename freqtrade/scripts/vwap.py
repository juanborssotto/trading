import requests
import time
import os
import sys
from datetime import datetime, timedelta
from freqtrade.utils.binance_rest_api import get_candles
from colorama import Fore, Style
import freqtrade.vendor.qtpylib.indicators as qtpylib

pairs = []
for i in range(1, len(sys.argv)):
    pairs.append(sys.argv[i])
timeframe = "15m"

print(f"RUNNING VWAP CHECKER: {pairs}")
while True:
    for pair in pairs:
        df = get_candles(pair+"/USDT", timeframe)
        vwap = qtpylib.rolling_vwap(df, window=14).tolist()
        print(vwap[-1])
    time.sleep(60)
    print("")
