from binance import Client
import os

api_key = os.getenv('BINANCE_TRADE_API_KEY')
api_secret = os.getenv('BINANCE_TRADE_API_SECRET')

client = Client(api_key, api_secret)

try:
    #market_buy_result = client.order_market_buy(
    #    symbol='BTCUSDT',
    #    quoteOrderQty=20)

    market_buy_result = {'symbol': 'BTCUSDT', 'orderId': 7274865379, 'orderListId': -1, 'clientOrderId': '55rdxu13fR0Oqk3qLzhCxv', 'transactTime': 1629673054979, 'price': '0.00000000', 'origQty': '0.00040700', 'executedQty': '0.00040700', 'cummulativeQuoteQty': '19.99953637', 'status': 'FILLED', 'timeInForce': 'GTC', 'type': 'MARKET', 'side': 'BUY', 'fills': [{'price': '49138.91000000', 'qty': '0.00040700', 'commission': '0.00000041', 'commissionAsset': 'BTC', 'tradeId': 1019583212}]}
    avg_buy_price = None
    acum_price = 0
    acum_qty = 0
    acum_commission = 0
    order_fills = market_buy_result['fills']
    for f in order_fills:
        acum_price += float(f['price'])
        acum_qty += float(f['qty'])
        acum_commission += float(f['commission'])
    avg_buy_price = acum_price / len(order_fills)
    full_qty = acum_qty - acum_commission

    def my_round(n: str, n_decimals: int):
        if '.' not in n:
            return n
        s = n.split('.')
        whole = s[0]
        decimals = s[1]
        decimals = decimals[:n_decimals]
        return f"{whole}.{decimals}"

    stoploss_pct = 2
    stoploss = abs((stoploss_pct / 100) * avg_buy_price - avg_buy_price)
    stoploss_trigger = (0.05 / 100 * stoploss) + stoploss
    #stop_limit_result = client.create_order(
    #    symbol='BTCUSDT',
    #    side='SELL',
    #    type='STOP_LOSS_LIMIT',
    #    timeInForce='GTC',
    #    quantity=my_round(str(full_qty), 6),
    #    price=my_round(str(stoploss), 2),
    #    stopPrice=my_round(str(stoploss_trigger), 2))
    
    print("Market buy filled successfully: ", market_buy_result)
    print("Stoploss limit filled successfully: ", stop_limit_result)
except Exception as exception:
    print(f"exception ocurred: {exception}")
