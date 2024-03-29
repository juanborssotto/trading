# --- Do not remove these libs ---
from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame, Series
from datetime import datetime, timedelta
import os

from colorama import Fore, Style

import numpy as np

from freqtrade.rpc import RPCMessageType
from beepy import beep
import freqtrade.vendor.qtpylib.indicators as qtpylib
from technical.util import resample_to_interval

def green(text):
    return f"{Fore.GREEN}{text}{Style.RESET_ALL}"


def calculate_distance_percentage(current_price: float, green_line_price: float) -> float:
    distance = abs(current_price - green_line_price)
    return distance * 100 / current_price


def get_symbol_from_pair(pair: str) -> str:
    return pair.split('/')[0]


class VWAPAlarm5M(IStrategy):
    minimal_roi = {
        "0": 10
    }

    # Optimal stoploss designed for the strategy
    stoploss = -0.99

    # Optimal timeframe for the strategy
    timeframe = '5m'
    process_only_new_candles = True

    alarm_emitted = dict()

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        pair = metadata["pair"]
        if pair not in self.alarm_emitted:
            self.alarm_emitted[pair] = False
        # ticker = self.dp.ticker(pair)
        # ongoing_close = ticker['last']
        # ongoing_volume = float(ticker["info"]["volume"]) - float(dataframe["volume"].rolling(23).sum().iloc[-1])

        dataframe['vwap'] = qtpylib.rolling_vwap(dataframe, window=14)

        # ongoing_candle = Series({
        #     'volume': ongoing_volume,
        #     'close': ongoing_close
        # })
        # df_2h = df_2h.append(ongoing_candle, ignore_index=True)

        # ----------------------------------------------------------------
        # Candle closes above vwap, previous candle closed below vwap    |
        # ----------------------------------------------------------------
        pct = 0.2
        vwap = dataframe["vwap"].iloc[-1]
        current_close = dataframe["close"].iloc[-1]
        previous_vwap = dataframe["vwap"].iloc[-2]
        previous_close = dataframe["close"].iloc[-2]
        if previous_close < previous_vwap and current_close > vwap:
            if not self.alarm_emitted[pair]:
                binance_pair = pair.replace("/", "_")
                ticker = self.dp.ticker(pair)
                last_price = ticker['last']
                distance = calculate_distance_percentage(last_price, vwap)
                if distance <= pct:
                    beep(3)
                    binance_link = f'https://www.binance.com/en/trade/{binance_pair}?layout=pro&type=spot'
                    # os.system(f'xdg-open https://www.binance.com/en/trade/{binance_pair}?layout=pro&type=spot')
                    print(green(f'{pair} {round(calculate_distance_percentage(last_price, vwap), 2)} {binance_link}'))
            self.alarm_emitted[pair] = True
        else:
            self.alarm_emitted[pair] = False

        # -------------------
        # Price breaks vwap |
        # -------------------
        # if df_2h["close"].iloc[-1] > df_2h["vwap"].iloc[-1]:
        #     if not self.alarm_emitted[pair]:
        #         binance_pair = pair.replace("/", "_")
        #         beep(3)
        #         os.system(f'xdg-open https://www.binance.com/en/trade/{binance_pair}?layout=pro&type=spot')
        #     self.alarm_emitted[pair] = True
        # else:
        #     self.alarm_emitted[pair] = False
        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
            ), 'buy'] = 1
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
            ),
            'sell'] = 1
        return dataframe
