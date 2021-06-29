# --- Do not remove these libs ---
from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame, Series
from datetime import datetime, timedelta
import os

import numpy as np

from freqtrade.rpc import RPCMessageType
from beepy import beep

from technical.util import resample_to_interval

from typing import List

from colorama import Fore, Style


def calculate_distance_percentage(current_price: float, green_line_price: float) -> float:
    distance = abs(current_price - green_line_price)
    return distance * 100 / current_price


def get_symbol_from_pair(pair: str) -> str:
    return pair.split('/')[0]


def green(text):
    return f"{Fore.GREEN}{text}{Style.RESET_ALL}"


def red(text):
    return f"{Fore.RED}{text}{Style.RESET_ALL}"


class DNSAlarmReporterBTC(IStrategy):
    minimal_roi = {
        "0": 10
    }

    # Optimal stoploss designed for the strategy
    stoploss = -0.99

    # Optimal timeframe for the strategy
    timeframe = '30m'

    # -------
    # ALARM |
    # -------
    alarm_emitted = dict()
    max_bars_back = 500
    max_simultaneous_engulf_patterns = 10
    BTC_ETH = ["BTC", "ETH"]

    df_15m = None
    df_2h = None
    df_4h = None
    df_1d = None
    df_1w = None

    def __init__(self, config: dict) -> None:
        self.btc_eth_alert_percentage = float(config['btc_eth_alert_percentage'])
        self.altcoins_alert_percentage = float(config['altcoins_alert_percentage'])
        self.btc_eth_restart_alert_percentage = float(config['btc_eth_restart_alert_percentage'])
        self.altcoins_restart_alert_percentage = float(config['altcoins_restart_alert_percentage'])
        super().__init__(config)

    def informative_pairs(self):
        return [# ("BTC/USDT", "15m"),
                ("BTC/USDT", "2h"),
                ("BTC/USDT", "4h"),
                ("BTC/USDT", "1d"),
                ("BTC/USDT", "1w"),
                ]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        pair = metadata["pair"]

        df_30m = dataframe
        df_1h = resample_to_interval(df_30m, 60)

        if self.dp and \
                self.dp.runmode.value in ('live', 'dry_run'):
            # self.df_15m = self.dp.get_pair_dataframe(pair="BTC/USDT", timeframe="15m")
            self.df_2h = self.dp.get_pair_dataframe(pair="BTC/USDT", timeframe="2h")
            self.df_4h = self.dp.get_pair_dataframe(pair="BTC/USDT", timeframe="4h")
            if self.df_1d is None:
                self.df_1d = self.dp.get_pair_dataframe(pair="BTC/USDT", timeframe="1d")
            if self.df_1w is None:
                self.df_1w = self.dp.get_pair_dataframe(pair="BTC/USDT", timeframe="1w")

        # df_45m = resample_to_interval(self.df_15m, 45)

        ticker = self.dp.ticker(pair)
        # self.calculate_dns(self.df_15m, ticker, pair, "15m")
        self.calculate_dns(df_30m, ticker, pair, "30m")
        # self.calculate_dns(df_45m, ticker, pair, "45m")
        self.calculate_dns(df_1h, ticker, pair, "1h")
        self.calculate_dns(self.df_2h, ticker, pair, "2h")
        self.calculate_dns(self.df_4h, ticker, pair, "4h")
        self.calculate_dns(self.df_1d, ticker, pair, "1d")
        self.calculate_dns(self.df_1w, ticker, pair, "1w")
        print("")

        return dataframe

    def calculate_dns(self, dataframe, ticker, pair, timeframe):
        short_df = dataframe.tail(self.max_bars_back)

        # if self.dp and \
        #         self.dp.runmode.value in ('live', 'dry_run'):
        #     pass
        #     # short_df = short_df.append(self.get_ongoing_candle(pair), ignore_index=True)
        # elif self.dp.runmode.value.lower() in ["backtest", "plot"]:
        #     self.add_backtest_missing_candles(dataframe=short_df)

        previous_range = short_df["open"].shift(1) - short_df["close"].shift(1)

        short_df["bull_engulf_green_line"] = self.calculate_bull_engulf_green_line(
            previous_range=previous_range, dataframe=short_df)
        short_df["bear_engulf_green_line"] = self.calculate_bear_engulf_green_line(
            previous_range=previous_range, dataframe=short_df)

        short_df["bull_engulf_red_line"] = self.calculate_bull_engulf_red_line(
            previous_range=previous_range, dataframe=short_df)
        short_df["bear_engulf_red_line"] = self.calculate_bear_engulf_red_line(
            previous_range=previous_range, dataframe=short_df)

        # if self.dp.runmode.value.lower() in ["backtest", "plot"]:
        #     # ---------------------------
        #     # to match tradingview plot |
        #     # ---------------------------
        #     short_df["bull_engulf_green_line"] = short_df["bull_engulf_green_line"].shift(-1)
        #     short_df["bear_engulf_green_line"] = short_df["bear_engulf_green_line"].shift(-1)

        ongoing_close = ticker['last']

        bull_engulf_green_line_list = short_df["bull_engulf_green_line"].dropna().tail(
            self.max_simultaneous_engulf_patterns).tolist()
        bear_engulf_green_line_list = short_df["bear_engulf_green_line"].dropna().tail(
            self.max_simultaneous_engulf_patterns).tolist()

        bull_engulf_red_line_list = short_df["bull_engulf_red_line"].dropna().tail(
            self.max_simultaneous_engulf_patterns).tolist()
        bear_engulf_red_line_list = short_df["bear_engulf_red_line"].dropna().tail(
            self.max_simultaneous_engulf_patterns).tolist()

        # green_line_list = bull_engulf_green_line_list + bear_engulf_green_line_list
        # red_line_list = bull_engulf_red_line_list + bear_engulf_red_line_list

        def get_closest_and_smaller(n: float, l: List[float]):
            result = None
            for v in l:
                if v < n:
                    if result is None or (n - v) < (n - result):
                        result = v
            return result

        def get_closest_and_greater(n: float, l: List[float]):
            result = None
            for v in l:
                if v > n:
                    if result is None or (v - n) < (result - n):
                        result = v
            return result

        # closest_demand_green_line = get_closest_and_smaller(ongoing_close, green_line_list)
        # closest_demand_red_line = get_closest_and_smaller(ongoing_close, red_line_list)
        # closest_offer_green_line = get_closest_and_greater(ongoing_close, green_line_list)
        # closest_offer_red_line = get_closest_and_greater(ongoing_close, red_line_list)
        closest_demand_green_line = get_closest_and_smaller(ongoing_close, bull_engulf_green_line_list)
        closest_demand_red_line = get_closest_and_smaller(ongoing_close, bull_engulf_red_line_list)
        closest_offer_green_line = get_closest_and_greater(ongoing_close, bear_engulf_green_line_list)
        closest_offer_red_line = get_closest_and_greater(ongoing_close, bear_engulf_red_line_list)

        if closest_demand_green_line:
            distance_closest_demand_green_line = \
                round(calculate_distance_percentage(ongoing_close, closest_demand_green_line), 2)
        else:
            distance_closest_demand_green_line = "-"

        if closest_demand_red_line:
            distance_closest_demand_red_line = \
                round(calculate_distance_percentage(ongoing_close, closest_demand_red_line), 2)
        else:
            distance_closest_demand_red_line = "-"

        if closest_offer_green_line:
            distance_closest_offer_green_line = \
                round(calculate_distance_percentage(ongoing_close, closest_offer_green_line), 2)
        else:
            distance_closest_offer_green_line = "-"

        if closest_offer_red_line:
            distance_closest_offer_red_line = \
                round(calculate_distance_percentage(ongoing_close, closest_offer_red_line), 2)
        else:
            distance_closest_offer_red_line = "-"

        def any_under_threshold(pair_: str, *distance_percentages):
            result = False
            for d in distance_percentages:
                if d == "-":
                    continue
                if get_symbol_from_pair(pair_).upper() in self.BTC_ETH:
                    if d < self.btc_eth_alert_percentage:
                        result = True
                else:
                    if d < self.altcoins_alert_percentage:
                        result = True
            return result

        desktop_notif_text = f'{pair} {timeframe} BUY: {distance_closest_demand_green_line} {distance_closest_demand_red_line} ' \
                             f'SELL: {distance_closest_offer_green_line} {distance_closest_offer_red_line}'
        text = f'{pair} {timeframe} BUY: {green(distance_closest_demand_green_line)} {red(distance_closest_demand_red_line)} ' \
               f'SELL: {green(distance_closest_offer_green_line)} {red(distance_closest_offer_red_line)}'
        if any_under_threshold(pair, distance_closest_demand_green_line, distance_closest_demand_red_line):
            
            # if os.getenv("beep") == "beep" and timeframe not in ["15m", "30m", "45m"]:
            if os.getenv("beep") == "beep":
                # beep(3)
                os.system(f"notify-send \"{desktop_notif_text.upper()}\" -t 10000 -i /usr/share/icons/gnome/48x48/actions/stock_about.png")
                
            text += "    BUY    "
        if any_under_threshold(pair, distance_closest_offer_green_line, distance_closest_offer_red_line):
            text += "    SELL    "
        print(text)

        # for green_line_price in green_line_list:
        #     alarm_emitted_key = f"{pair}-{green_line_price}"
        #     if alarm_emitted_key not in self.alarm_emitted:
        #         self.alarm_emitted[alarm_emitted_key] = False
        #     distance_percentage = calculate_distance_percentage(
        #         current_price=ongoing_close, green_line_price=green_line_price)
        #     if self.is_price_in_alert_range(pair=pair, distance_percentage=distance_percentage):
        #         if not self.alarm_emitted[alarm_emitted_key]:
        #             self.alarm_emitted[alarm_emitted_key] = True
        #             message = self.build_alert_message(pair=pair, green_line_price=green_line_price)
        #
        #             # ONLY WHEN GREEN LINE IS BELOW
        #             if green_line_price < ongoing_close:
        #                 tv_pair = pair.replace("/", "")
        #                 binance_pair = pair.replace("/", "_")
        #                 # beep(6)
        #                 beep(3)
        #                 os.system(f'xdg-open https://www.binance.com/en/trade/{binance_pair}?layout=pro&type=spot')
        #                 os.system(f'firefox https://www.tradingview.com/chart/?symbol=binance:{tv_pair}')
        #                 print(f'{tv_pair} {green_line_price} {distance_percentage}')
        #
        #     elif self.is_price_in_restart_alert_range(pair=pair, distance_percentage=distance_percentage):
        #         self.alarm_emitted[alarm_emitted_key] = False

    def get_ongoing_candle(self, pair: str) -> Series:
        ticker = self.dp.ticker(pair)
        ongoing_open = ticker['open']
        ongoing_high = ticker['high']
        ongoing_low = ticker['low']
        ongoing_close = ticker['close']
        return Series({
            'volume': 0,  # 0 volume for the on-going candle, does not affect the alarm
            'open': ongoing_open,
            'high': ongoing_high,
            'low': ongoing_low,
            'close': ongoing_close
        })

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

    def calculate_bull_engulf_red_line(self, previous_range: Series, dataframe: DataFrame) -> Series:
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
            bull_engulf_low,
            np.nan
        )

    def calculate_bear_engulf_red_line(self, previous_range: Series, dataframe: DataFrame) -> Series:
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
            bear_engulf_high,
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
        if get_symbol_from_pair(pair).upper() in self.BTC_ETH:
            alert_percentage = self.btc_eth_alert_percentage
        else:
            alert_percentage = self.altcoins_alert_percentage
        return f"{pair} se encuentra a menos de {round(alert_percentage, 2)}% " \
               f"de {round(green_line_price, 2)} con fecha " \
               f"{(datetime.utcnow() - timedelta(hours=3)).strftime('%d/%m/%Y %H:%M')} ARG"

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
