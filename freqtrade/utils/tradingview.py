def generate_tv_url(pair: str, timeframe: str) -> str:
    try:
        tv_pair = generate_tv_pair(pair=pair)
        tv_interval = generate_tv_interval(timeframe=timeframe)
        return f'https://www.tradingview.com/chart/' \
               f'?symbol=binance:{tv_pair}&interval={tv_interval}'
    except Exception as exception:
        raise exception


def generate_tv_pair(pair: str) -> str:
    return pair.replace("/", "")


def generate_tv_interval(timeframe: str) -> str:
    timeframe_dict = {
        '1m': '1',
        '3m': '3',
        '5m': '5',
        '15m': '15',
        '30m': '30',
        '1h': '60',
        '2h': '120',
        '4h': '240',
        '1d': '1440',
        '1w': '1W',
        '1M': '1M'
    }
    if timeframe not in timeframe_dict:
        raise Exception(f"Error generating TradingView interval with timeframe: {timeframe}")
    return timeframe_dict[timeframe]
