import freqtrade.vendor.qtpylib.indicators as qtpylib
import pandas as pd
import numpy as np
from colorama import Fore, Style
import time
import os
import sys
from freqtrade.utils.binance_rest_api import get_candles

coins = sys.argv[1:]

timeframes = ["4h", "1h", "15m"]

print("RUNNING DOWNTREND TRIANGLE")
for t in timeframes:
    for coin in coins:
        df = get_candles(f"{coin}/USDT", t)
        df["pivots_high"] = np.where(
            (df["high"].shift(2) < df["high"]) &
            (df["high"].shift(1) < df["high"]) &
            (df["high"].shift(-1) < df["high"]) &
            (df["high"].shift(-2) < df["high"]),
            df["high"],
            np.nan
        )
        n = 2
        n_last_pivots_high = df[df["pivots_high"].notnull()]["pivots_high"].tail(n).tolist()

        is_downtrend = True
        for i in range(0, len(n_last_pivots_high) - 1):
            if n_last_pivots_high[i] < n_last_pivots_high[i + 1]:
                is_downtrend = False
        if is_downtrend:
            print(f"{coin} in {t} is downtrend")
    print("")
