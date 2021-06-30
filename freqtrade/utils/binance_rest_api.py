import requests
import logging
from pandas import Series


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
            'open': float(data[0][1]),
            'high': float(data[0][2]),
            'low': float(data[0][3]),
            'close': float(data[0][4]),
            'volume': float(data[0][5])
        })
    except Exception as exception:
        raise Exception(f"Exception found when getting ongoing candle for {pair} at {timeframe}: {exception}")
