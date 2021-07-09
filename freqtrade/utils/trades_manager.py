def calculate_profit_price(buy_price: float, stop_loss: float, profit_rate: float) -> float:
    return buy_price + (buy_price * 0.2 / 100.0) + (buy_price * (stop_loss * profit_rate) / 100)


class TradeManager:
    def __init__(self, profit_rate: float):
        self.has_open_trade = False
        self.buy_price = None
        self.stop_loss = None
        self.profit_price = None
        self.profit_rate = profit_rate

    def open_trade(self, buy_price: float, stop_loss: float):
        self.has_open_trade = True
        self.buy_price = buy_price
        self.stop_loss = stop_loss
        self.profit_price = calculate_profit_price(
            buy_price=buy_price, stop_loss=stop_loss, profit_rate=self.profit_rate)

    def should_stop_loss(self, ongoing_close: float) -> bool:
        return ongoing_close < self.stop_loss

    def should_profit(self, ongoing_close: float) -> bool:
        return ongoing_close >= self.profit_price

    def close_trade(self):
        self.has_open_trade = False
        self.buy_price = None
        self.stop_loss = None
        self.profit_price = None
