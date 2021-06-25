# --- Do not remove these libs ---
from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame
import talib.abstract as ta

from technical.pivots_points import pivots_points

import freqtrade.vendor.qtpylib.indicators as qtpylib

from talib import CDLINVERTEDHAMMER, CDLHAMMER

import numpy as np


# --------------------------------

def remove_successive(dataframe: DataFrame, key: str):
    rolling_window = 10
    dataframe[key] = (
            (dataframe[key] == 1) &
            (dataframe[key].shift(1).rolling(rolling_window).sum() == 0)
    ).astype('int')

class LamboStrat(IStrategy):
    # Minimal ROI designed for the strategy.
    # adjust based on market conditions. We would recommend to keep it low for quick turn arounds
    # This attribute will be overridden if the config file contains "minimal_roi"
    minimal_roi = {
        "0": 0.03
    }

    # Optimal stoploss designed for the strategy
    stoploss = -0.2

    # Optimal timeframe for the strategy
    timeframe = '1h'

    buymeanvolumemultiplier = 1
    buymeanvolumewindow = 5
    buyrsivalue = 24
    sellmeanvolumemultiplier = 1
    sellmeanvolumewindow = 3
    sellrsivalue = 38

    foo = 0

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        # pivots = pivots_points(dataframe)
        # dataframe["pivot"] = pivots["pivot"]
        # dataframe["r1"] = pivots["r1"]
        # dataframe["r2"] = pivots["r2"]
        # dataframe["r3"] = pivots["r3"]
        # dataframe["s1"] = pivots["s1"]
        # dataframe["s2"] = pivots["s2"]
        # dataframe["s3"] = pivots["s3"]


        # Accumulation/Distribution
        # dataframe["accumulation_distribution"] = (
        #         (((dataframe["close"] - dataframe["low"]) - (dataframe["high"] - dataframe["close"]))
        #          / (dataframe["high"] - dataframe["low"])) * dataframe["volume"]
        # ).cumsum()
        # dataframe['sma9'] = ta.SMA(dataframe, timeperiod=9, price='accumulation_distribution')
        # dataframe['sma15'] = ta.SMA(dataframe, timeperiod=15, price='accumulation_distribution')


        macd = ta.MACD(dataframe)
        dataframe['macd'] = macd['macd']
        dataframe['macdsignal'] = macd['macdsignal']
        dataframe['macdhist'] = macd["macdhist"]
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)

        # ema 100 stoploss
        # ema100 = ta.EMA(dataframe, timeperiod=100)
        # dataframe["ema100rate"] = ((ema100 - ema100.shift(1)) / ema100.shift(1)) * 100.0
        # dataframe['ema100'] = ta.EMA(dataframe, timeperiod=100)

        # candle patterns
        # inverted_hammer_pattern = CDLINVERTEDHAMMER(
        # dataframe["open"], dataframe["high"], dataframe["low"], dataframe["close"])
        # dataframe["inverted_hammer_pattern"] = inverted_hammer_pattern
        # only_inverted = dataframe[dataframe["inverted_hammer_pattern"] != 0]
        # print(metadata)
        # print(only_inverted[only_inverted["close"] > only_inverted["open"]])
        # input()

        # more_than = dataframe["low"].rolling(5).min() < dataframe["close"]
        # less_than = dataframe["close"] < dataframe["high"].rolling(5).max()
        # dataframe["in_consolidation"] = more_than == less_than

        # for i in range(0, len(dataframe['macd'])):
        #     if dataframe['macd'][i] < 0:
        #         print(dataframe['macd'][i])
        #         print(macd_pcts[i])
        #         print(sums[i])
        #         print(subtractions[i])
        #         input()

        # goes row by row from the last al calculates average with window. acum(values n to n-window) / n-window
        # shift is to push everything by 1. value in 0 becomes NaN and value in 998 becomes value in 999

        dataframe['meanvolumebuy'] = dataframe['volume'].rolling(
            window=self.buymeanvolumewindow).mean().shift(1) * self.buymeanvolumemultiplier
        dataframe['meanvolumesell'] = dataframe['volume'].rolling(
            window=self.sellmeanvolumewindow).mean().shift(1) * self.sellmeanvolumemultiplier

        # FOR HYPEROPT
        # dataframe['meanvolumebuy'] = dataframe['volume'].rolling(window=5).mean().shift(1)
        # dataframe['meanvolumesell'] = dataframe['volume'].rolling(window=10).mean().shift(1)

        # Volume stop + uptrend
        dataframe['sma_6'] = ta.SMA(dataframe, timeperiod=6, price='close')

        dataframe["macd_above_macdsignal"] = (
            (dataframe['macd'] > dataframe['macdsignal'])
        ).astype('int')

        dataframe["volume_condition"] = ( # don't use remove_successive with volume_condition

                # (dataframe['volume'] > dataframe['volume'].shift(1).rolling(5).max()) &
                # (dataframe['volume'].shift(1) > dataframe['volume'].shift(2).rolling(5).mean()) &
                # (dataframe['macd'] < dataframe['macdsignal']) &
                # (dataframe['macd'] < 0.0) &
                # (dataframe['rsi'] < 29.0)

                (dataframe["close"] > dataframe["close"].shift(1)) &
                # change max for mean since max breakes BNB/USDT 20210421 20210424
                (dataframe['volume'].shift(1) > dataframe['volume'].shift(2).rolling(5).mean()) &
                (dataframe['macd'].shift(1) < dataframe['macdsignal'].shift(1)) &
                (dataframe['macd'].shift(1) < 0.0) &
                (dataframe['rsi'].shift(1) < 29.0)
        ).astype('int')
        dataframe["volume_condition"] = dataframe["volume_condition"].shift(-1)
        dataframe["volume_condition"].iloc[-1] = 0


        volume_condition_support = float('nan')
        volume_condition_support_list = []
        for i in range(0, len(dataframe)):
            if dataframe["volume_condition"][i] == 1:
                volume_condition_support = dataframe["close"][i]
            volume_condition_support_list.append(volume_condition_support)
        dataframe["volume_condition_support"] = volume_condition_support_list

        volume_condition_macd = float('nan')
        volume_condition_support_list = []
        for i in range(0, len(dataframe)):
            if dataframe["volume_condition"][i] == 1:
                volume_condition_support = dataframe["close"][i]
            volume_condition_support_list.append(volume_condition_support)
        dataframe["volume_condition_support"] = volume_condition_support_list



        dataframe["phase_a"] = (
                (dataframe["macd_above_macdsignal"].rolling(5).sum() == 5) &
                (dataframe["volume_condition"].rolling(20).sum() >= 1) &
                (dataframe["close"] > dataframe['sma_6'])
        ).astype('int')

        remove_successive(dataframe, "phase_a")


        # For chart
        dataframe["volume_condition_datapoint"] = (
                (dataframe["volume_condition"] * dataframe["low"])
        )
        dataframe["volume_condition_datapoint"] = dataframe["volume_condition_datapoint"].replace([0], float('nan'))

        dataframe["phase_a_datapoint"] = (
            (dataframe["phase_a"] * dataframe["low"])
        )
        dataframe["phase_a_datapoint"] = dataframe["phase_a_datapoint"].replace([0], float('nan'))
        # For chart


        # volume stop + uptrend + test
        support_resistance_window = 6
        support_shift = 1
        resistance_shift = 1

        support_found = (
            (dataframe["low"].shift(support_shift) == dataframe["low"].rolling(support_resistance_window).min())
        )
        last_support = float('nan')
        support_list = []
        for i in range(0, len(dataframe)):
            if support_found[i]:
                last_support = dataframe["low"][i - support_shift]
            support_list.append(last_support)
        dataframe["support"] = support_list

        resistance_found = (
            (dataframe["high"].shift(resistance_shift) == dataframe["high"].rolling(support_resistance_window).max())
        )
        last_resistance = float('nan')
        resistance_list = []
        for i in range(0, len(dataframe)):
            if resistance_found[i]:
                last_resistance = dataframe["high"][i - resistance_shift]
            resistance_list.append(last_resistance)
        dataframe["resistance"] = resistance_list

        phase_a_support = float('nan')
        phase_a_support_list = []
        for i in range(0, len(dataframe)):
            if dataframe["phase_a"][i] == 1:
                phase_a_support = dataframe["support"][i]
            phase_a_support_list.append(phase_a_support)
        dataframe["phase_a_support"] = phase_a_support_list

        phase_a_resistance = float('nan')
        phase_a_resistance_list = []
        for i in range(0, len(dataframe)):
            if dataframe["phase_a"][i] == 1:
                phase_a_resistance = dataframe["resistance"][i]
            phase_a_resistance_list.append(phase_a_resistance)
        dataframe["phase_a_resistance"] = phase_a_resistance_list

        dataframe["test"] = (
            (dataframe["support"] > dataframe["phase_a_support"])
        )

        dataframe["low_crossed_below_phase_a_support"] = qtpylib.crossed_below(
            dataframe['low'], dataframe["phase_a_support"]).astype('int')
        dataframe["high_crossed_above_phase_a_support"] = qtpylib.crossed_above(
            dataframe['low'], dataframe["phase_a_support"]).astype('int')
        dataframe["phase_a_and_spring"] = (
                (dataframe["low_crossed_below_phase_a_support"].rolling(8).sum() >= 1) &
                (dataframe["high_crossed_above_phase_a_support"].rolling(8).sum() >= 1) &
                (dataframe["phase_a"].rolling(60).sum() >= 1)
        ).astype('int')

        remove_successive(dataframe, "phase_a_and_spring")


        # for chart
        dataframe["spring_datapoint"] = (
            (dataframe["phase_a_and_spring"] * dataframe["low"])
        )
        dataframe["spring_datapoint"] = dataframe["spring_datapoint"].replace([0], float('nan'))
        # for chart


        dataframe["phase_a_and_spring_and_test"] = (
                (dataframe["phase_a_and_spring"].rolling(15).sum() >= 1) &
                (dataframe["test"] == 1)
        ).astype('int')
        remove_successive(dataframe, "phase_a_and_spring_and_test")


        # for chart
        dataframe["test_datapoint"] = (
            (dataframe["phase_a_and_spring_and_test"] * dataframe["low"])
        )
        dataframe["test_datapoint"] = dataframe["test_datapoint"].replace([0], float('nan'))
        # for chart


        dataframe["buy_criteria"] = (
                (dataframe["phase_a_and_spring_and_test"] == 1)
        ).astype('int')



        # jump the creek
        dataframe["phase_a_and_spring_and_test_and_jump"] = (
                (dataframe["phase_a_and_spring_and_test"].rolling(50).sum() >= 1) &
                (dataframe["support"] >= dataframe["phase_a_resistance"])
        ).astype('int')
        remove_successive(dataframe, "phase_a_and_spring_and_test_and_jump")


        # for chart
        dataframe["jump_datapoint"] = (
            (dataframe["phase_a_and_spring_and_test_and_jump"] * dataframe["low"])
        )
        dataframe["jump_datapoint"] = dataframe["jump_datapoint"].replace([0], float('nan'))
        # for chart


        dataframe["buy_criteria"] = (
                (dataframe["phase_a_and_spring_and_test_and_jump"] == 1)
        ).astype('int')
        remove_successive(dataframe, "buy_criteria")



        # For backtesting
        # Volume condition
        # should_buy = [False] * len(dataframe)
        # for i in range(0, len(dataframe)):
        #     recent = dataframe[0:i + 1]
        #     volume_condition = (recent['volume'] > recent['volume'].shift(1).rolling(20).max())[i]
        #     macd_condition = (recent['macd'] < recent['macdsignal'])[i]
        #     should_buy[i] = volume_condition and macd_condition
        #
        # dataframe["should_buy"] = should_buy
        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["buy_criteria"] == 1)
            ),
            'buy'] = 1
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
            ),
            'sell'] = 1
        return dataframe
