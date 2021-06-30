# --- Do not remove these libs ---
from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame, Series
from datetime import datetime, timedelta

import numpy as np

from freqtrade.utils.tradingview import generate_tv_url
from freqtrade.utils.binance_rest_api import get_ongoing_candle

from typing import List

import logging

logger = logging.getLogger(__name__)


def calculate_distance_percentage(current_price: float, green_line_price: float) -> float:
    distance = abs(current_price - green_line_price)
    return distance * 100 / current_price


def get_symbol_from_pair(pair: str) -> str:
    return pair.split('/')[0]


class DNSAlarm(IStrategy):
    minimal_roi = {
        "0": 10
    }

    # Optimal stoploss designed for the strategy
    stoploss = -0.99

    # Optimal timeframe for the strategy
    timeframe = '1m'

    # -------
    # ALARM |
    # -------
    alarm_emitted = dict()
    max_bars_back = 500
    max_simultaneous_engulf_patterns = 10
    BTC_ETH = ["BTC", "ETH"]

    def __init__(self, config: dict) -> None:
        self.btc_eth_alert_percentage = float(config['btc_eth_alert_percentage'])
        self.altcoins_alert_percentage = float(config['altcoins_alert_percentage'])
        self.btc_eth_restart_alert_percentage = float(config['btc_eth_restart_alert_percentage'])
        self.altcoins_restart_alert_percentage = float(config['altcoins_restart_alert_percentage'])
        super().__init__(config)

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        pair = metadata["pair"]
        short_df = dataframe.tail(self.max_bars_back)

        if self.dp and \
                self.dp.runmode.value in ('live', 'dry_run'):
            short_df = short_df.append(get_ongoing_candle(pair=pair, timeframe=self.timeframe), ignore_index=True)
        elif self.dp.runmode.value.lower() in ["backtest", "plot"]:
            self.add_backtest_missing_candles(dataframe=short_df)

        previous_range = short_df["open"].shift(1) - short_df["close"].shift(1)

        short_df["bull_engulf_green_line"] = self.calculate_bull_engulf_green_line(
            previous_range=previous_range, dataframe=short_df)
        short_df["bear_engulf_green_line"] = self.calculate_bear_engulf_green_line(
            previous_range=previous_range, dataframe=short_df)

        if self.dp.runmode.value.lower() in ["backtest", "plot"]:
            # ---------------------------
            # to match tradingview plot |
            # ---------------------------
            short_df["bull_engulf_green_line"] = short_df["bull_engulf_green_line"].shift(-1)
            short_df["bear_engulf_green_line"] = short_df["bear_engulf_green_line"].shift(-1)

        ongoing_close = short_df['close'].iloc[-1]
        bull_engulf_green_line_list = short_df["bull_engulf_green_line"].dropna().tail(
            self.max_simultaneous_engulf_patterns).tolist()
        bear_engulf_green_line_list = short_df["bear_engulf_green_line"].dropna().tail(
            self.max_simultaneous_engulf_patterns).tolist()

        self.alarm_bull_green_lines(
            pair=pair, ongoing_close=ongoing_close, bull_engulf_green_line_list=bear_engulf_green_line_list)

        if self.dp.runmode.value in ('live', 'dry_run'):
            return dataframe
        return short_df

    def alarm_bull_and_bear_green_lines(self, pair: str, ongoing_close: float,
                                        bull_engulf_green_line_list: List[float],
                                        bear_engulf_green_line_list: List[float]):
        green_line_list = bull_engulf_green_line_list + bear_engulf_green_line_list
        for green_line_price in green_line_list:
            alarm_emitted_key = f"{pair}-{green_line_price}"
            if alarm_emitted_key not in self.alarm_emitted:
                self.alarm_emitted[alarm_emitted_key] = False
            distance_percentage = calculate_distance_percentage(
                current_price=ongoing_close, green_line_price=green_line_price)
            if self.is_price_in_alert_range(pair=pair, distance_percentage=distance_percentage):
                if not self.alarm_emitted[alarm_emitted_key]:
                    self.alarm_emitted[alarm_emitted_key] = True
                    message = self.build_alert_message(pair=pair, green_line_price=green_line_price)
                    # print(message)
            elif self.is_price_in_restart_alert_range(pair=pair, distance_percentage=distance_percentage):
                self.alarm_emitted[alarm_emitted_key] = False

    def alarm_bull_green_lines(self, pair: str, ongoing_close: float, bull_engulf_green_line_list: List[float]):
        print(bull_engulf_green_line_list)
        for green_line_price in bull_engulf_green_line_list:
            # alarm_emitted_key = f"{pair}-{green_line_price}"
            # if alarm_emitted_key not in self.alarm_emitted:
            #     self.alarm_emitted[alarm_emitted_key] = False
            distance_percentage = calculate_distance_percentage(
                current_price=ongoing_close, green_line_price=green_line_price)
            if self.is_price_in_alert_range(pair=pair, distance_percentage=distance_percentage):
                # if not self.alarm_emitted[alarm_emitted_key]:
                #     self.alarm_emitted[alarm_emitted_key] = True
                message = self.build_alert_message(pair=pair, green_line_price=green_line_price)
                # print(message)
            # elif self.is_price_in_restart_alert_range(pair=pair, distance_percentage=distance_percentage):
            #     self.alarm_emitted[alarm_emitted_key] = False

    def calculate_bull_engulf_green_line(self, previous_range: Series, dataframe: DataFrame) -> Series:
        open = dataframe["open"]
        low = dataframe["low"]
        close = dataframe["close"]

        is_bull_engulf = (
                (previous_range > 0) &
                (close > open.shift(1))
        )

        bull_engulf_low = np.where(low < low.shift(1), low, low.shift(1))

        low_list = low.tolist()
        min_low_to_end = []
        for i in range(0, len(low_list)):
            min_low_to_end.append(min(low_list[i:]))
        dataframe["min_low_to_end"] = min_low_to_end

        return np.where(
            is_bull_engulf &
            (dataframe["min_low_to_end"] >= bull_engulf_low),
            open.shift(1),
            np.nan
        )

    def calculate_bear_engulf_green_line(self, previous_range: Series, dataframe: DataFrame) -> Series:
        open = dataframe["open"]
        high = dataframe["high"]
        close = dataframe["close"]

        is_bear_engulf = (
                (previous_range < 0) &
                (close < open.shift(1))
        )

        bear_engulf_high = np.where(high > high.shift(1), high, high.shift(1))

        high_list = high.tolist()
        max_high_to_end = []
        for i in range(0, len(high_list)):
            max_high_to_end.append(max(high_list[i:]))
        dataframe["max_high_to_end"] = max_high_to_end

        return np.where(
            is_bear_engulf &
            (dataframe["max_high_to_end"] <= bear_engulf_high),
            open.shift(1),
            np.nan
        )

    def add_backtest_missing_candles(self, dataframe: DataFrame):
        from datetime import datetime
        import pytz
        utc = pytz.UTC

        # ------------------------------------------------------------------
        # this is only the append structure, remember to modify the values |
        # ------------------------------------------------------------------
        dataframe.append(
            {"date": utc.localize(datetime(year=2021, month=5, day=31, minute=0, second=0, microsecond=0)),
             "open": 0,
             "high": 0,
             "low": 0,
             "close": 0,
             "volume": 0}, ignore_index=True)

    def is_price_in_alert_range(self, pair: str, distance_percentage: float) -> bool:
        if get_symbol_from_pair(pair).upper() in self.BTC_ETH:
            return distance_percentage < self.btc_eth_alert_percentage
        return distance_percentage < self.altcoins_alert_percentage

    def is_price_in_restart_alert_range(self, pair: str, distance_percentage: float) -> bool:
        if get_symbol_from_pair(pair).upper() in self.BTC_ETH:
            return distance_percentage > self.btc_eth_restart_alert_percentage
        return distance_percentage > self.altcoins_restart_alert_percentage

    def build_alert_message(self, pair: str, green_line_price: float) -> str:
        tv_section = ""
        # try:
        #     tv_url = generate_tv_url(pair=pair, timeframe=self.timeframe)
        #     tv_section = f"\nLink a TradingView: {tv_url}"
        # except Exception as exception:
        #     logger.exception(f"Exception in spring alarm: {exception}")
        if get_symbol_from_pair(pair).upper() in self.BTC_ETH:
            alert_percentage = self.btc_eth_alert_percentage
        else:
            alert_percentage = self.altcoins_alert_percentage
        arg_date = (datetime.utcnow() - timedelta(hours=3)).strftime('%d/%m/%Y %H:%M')
        return f"{pair} se encuentra a menos de {round(alert_percentage, 2)}% " \
               f"de {round(green_line_price, 2)} con fecha " \
               f"{arg_date} ARG" \
               f"{tv_section}"

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
