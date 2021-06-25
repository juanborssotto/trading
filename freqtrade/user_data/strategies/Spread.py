# --- Do not remove these libs ---
from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame


# --------------------------------


class Spread(IStrategy):
    """

    author@: Gert Wohlgemuth

    just a skeleton

    """

    # Minimal ROI designed for the strategy.
    # adjust based on market conditions. We would recommend to keep it low for quick turn arounds
    # This attribute will be overridden if the config file contains "minimal_roi"
    minimal_roi = {
        "0": 0.01
    }

    # Optimal stoploss designed for the strategy
    stoploss = -0.25

    # Optimal timeframe for the strategy
    timeframe = '30m'

    results = dict()

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        pair = metadata["pair"]
        # ticker = self.dp.ticker(pair)
        # ongoing_high = ticker['high']
        # ongoing_low = ticker['low']

        def calculate_distance_percentage(current_price: float, green_line_price: float) -> float:
            distance = abs(current_price - green_line_price)
            return distance * 100 / current_price

        # text = f'{pair} ongoing: {calculate_distance_percentage(ongoing_low, ongoing_high)} ' \
        #        f'closed: {calculate_distance_percentage(dataframe["low"].iloc[-1], dataframe["high"].iloc[-1])}'
        # text = f'{pair} {calculate_distance_percentage(dataframe["low"].iloc[-1], dataframe["high"].iloc[-1])}'
        self.results[pair] = calculate_distance_percentage(dataframe["low"].iloc[-1], dataframe["high"].iloc[-1])
        pair_count = 45
        if len(self.results) == pair_count:
            sorted_results = {k: v for k, v in reversed(sorted(self.results.items(), key=lambda item: item[1]))}
            for key, value in sorted_results.items():
                text = f'{key} {value}'
                print(text)
            for key, value in sorted_results.items():
                text = f'"{key}",'
                print(text)

        print(f'{len(self.results)} {pair_count}')
        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
            ),
            'buy'] = 1
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
            ),
            'sell'] = 1
        return dataframe
