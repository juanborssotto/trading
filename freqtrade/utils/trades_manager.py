from freqtrade.utils.distance import calculate_distance_percentage


class TradeManager:
    def __init__(self, profit_rate: float):
        self.has_open_trade = False
        self.buy_price = None
        self.stop_loss_price = None
        self.profit_price = None
        self.profit_rate = profit_rate

    def open_trade(self, buy_price: float, stop_loss_price: float):
        self.has_open_trade = True
        self.buy_price = buy_price
        self.stop_loss_price = stop_loss_price
        self.profit_price = self.calculate_profit_price()

    def should_stop_loss(self, ongoing_close: float) -> bool:
        return ongoing_close < self.stop_loss_price

    def should_profit(self, ongoing_close: float) -> bool:
        return ongoing_close >= self.profit_price

    def calculate_profit_price(self) -> float:
        stop_loss_percentage = calculate_distance_percentage(self.buy_price, self.stop_loss_price)
        if stop_loss_percentage > 0.7:
            profit_percentage = stop_loss_percentage * self.profit_rate
        else:
            profit_percentage = 1.5
        desired_profit_price = self.buy_price + (self.buy_price * profit_percentage / 100)
        return desired_profit_price

    def close_trade(self):
        self.has_open_trade = False
        self.buy_price = None
        self.stop_loss_price = None
        self.profit_price = None
