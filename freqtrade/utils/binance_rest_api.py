import requests
import logging
from pandas import Series, DataFrame
from datetime import datetime
import numpy as np


def get_candles(pair: str, timeframe: str) -> DataFrame:
    pair = pair.replace("/", "")
    url = f"https://api.binance.com/api/v1/klines?symbol={pair}&interval={timeframe}&limit=500"
    response = requests.get(url)
    if not response.ok:
        exception = f"Bad response: Status code {response.status_code} Body {response.json()}"
        logging.exception(f"Exception found when getting ongoing candle for {pair} at {timeframe}: {exception}")
        raise Exception(exception)
    try:
        data = response.json()
        candles = []
        for candle in data:
            candles.append({
                "date": datetime.utcfromtimestamp(int(candle[0] / 1000)),
                "open": np.float64(candle[1]),
                "high": np.float64(candle[2]),
                "low": np.float64(candle[3]),
                "close": np.float64(candle[4]),
                "volume": np.float64(candle[5])
            })
        return DataFrame(candles)
    except Exception as exception:
        raise Exception(f"Exception found when getting ongoing candle for {pair} at {timeframe}: {exception}")


def get_ongoing_candle(pair: str, timeframe: str) -> Series:
    pair = pair.replace("/", "")
    url = f"https://api.binance.com/api/v1/klines?symbol={pair}&interval={timeframe}&limit=1"
    response = requests.get(url)
    if not response.ok:
        exception = f"Bad response: Status code {response.status_code} Body {response.json()}"
        logging.exception(f"Exception found when getting ongoing candle for {pair} at {timeframe}: {exception}")
        raise Exception(exception)
    try:
        data = response.json()
        return Series({
            # "date": datetime.utcfromtimestamp(int(data[0][0] / 1000)),
            'open': np.float64(data[0][1]),
            'high': np.float64(data[0][2]),
            'low': np.float64(data[0][3]),
            'close': np.float64(data[0][4]),
            'volume': np.float64(data[0][5])
        })
    except Exception as exception:
        raise Exception(f"Exception found when getting ongoing candle for {pair} at {timeframe}: {exception}")
