import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
import os
from binance import Client


from numpy import ones,vstack
from typing import List
from numpy.linalg import lstsq
from freqtrade.utils.binance_rest_api import get_candles
from dataclasses import dataclass
import sys
from pandas import Timestamp
import plotly.graph_objects as go

import os

def get_func(x1, y1, x2, y2):
    points = [(x1,y1),(x2,y2)]
    x_coords, y_coords = zip(*points)
    A = vstack([x_coords,ones(len(x_coords))]).T
    m, c = lstsq(A, y_coords, rcond=None)[0]
    return m, c

# next_point = m * 20 + c

# 1er min < 2d min
# 1er max > 2d max
# puntos siempre están por encima o debajo de todas las velas que siguen

@dataclass
class Point:
    date: Timestamp
    df_pos: int
    x: int
    y: float
    high: float
    low: float
    close: float

def get_lines(df, loopback):
    n = 0
    points: List[Point] = []
    for i in range(loopback, 0, -1):
        n = n + 1
        points.append(Point(df["date"].iloc[-i], -i, n, df["close"].iloc[-i], df["high"].iloc[-i], df["low"].iloc[-i], df["close"].iloc[-i]))

    clear_low_lines = []
    clear_high_lines = []
    for i in range(0, len(points)):
        for j in range(i+1, len(points)):
            x1, x2 = points[i].x, points[j].x
            low1, low2 = points[i].low, points[j].low
            if low1 < low2:
                m, c = get_func(x1, low1, x2, low2)
                is_clear_low_line = True
                for p in range(i+1, len(points)):
                    if p == j:
                        continue
                    next_value = m * points[p].x + c
                    if points[p].low < next_value:
                        is_clear_low_line = False
                if is_clear_low_line:
                    clear_low_lines.append((points[i], points[j], m, c))

            high1, high2 = points[i].high, points[j].high
            if high1 > high2:
                m, c = get_func(x1, high1, x2, high2)
                is_clear_high_line = True
                for p in range(i+1, len(points)):
                    if p == j:
                        continue
                    next_value = m * points[p].x + c
                    # if points[p].high > next_value:
                    if points[p].close > next_value:
                        is_clear_high_line = False
                if is_clear_high_line:
                    clear_high_lines.append((points[i], points[j], m, c))

    best_clear_low_lines = []
    for line in clear_low_lines:
        is_best = True
        if line[0].x == 1 or line[1].x == 1 or line[0].x == loopback or line[1].x == loopback:
            continue
        point_before_line_1 = points[line[0].x - 2]
        point_after_line_1 = points[line[0].x]
        if point_before_line_1.low < line[0].low or point_after_line_1.low < line[0].low:
            is_best = False

        point_before_line_2 = points[line[1].x - 2]
        point_after_line_2 = points[line[1].x]
        if point_before_line_2.low < line[1].low or point_after_line_2.low < line[1].low:
            is_best = False
        if is_best:
            best_clear_low_lines.append(line)

    best_clear_high_lines = []
    for line in clear_high_lines:
        is_best = True
        if line[0].x == 1 or line[1].x == 1 or line[0].x == loopback or line[1].x == loopback:
            continue
        point_before_line_1 = points[line[0].x - 2]
        point_after_line_1 = points[line[0].x]
        if point_before_line_1.high > line[0].high or point_after_line_1.high > line[0].high:
            is_best = False

        point_before_line_2 = points[line[1].x - 2]
        point_after_line_2 = points[line[1].x]
        if point_before_line_2.high > line[1].high or point_after_line_2.high > line[1].high:
            is_best = False
        if is_best:
            best_clear_high_lines.append(line)

    return best_clear_low_lines, best_clear_high_lines

def get_x_and_y_low(df, line, loopback):
    x = []
    y = []
    x.append(line[0].date)
    x.append(line[1].date)
    y.append(line[0].low)
    y.append(line[1].low)
    m, c = line[2], line[3]
    df_pos = line[1].df_pos
    for i in range(line[1].x + 1, loopback + 1):
        df_pos = df_pos + 1
        y.append(m * i + c)
        x.append(df['date'].iloc[df_pos])
    return x, y

def get_x_and_y_high(df, line, loopback):
    x = []
    y = []
    x.append(line[0].date)
    x.append(line[1].date)
    y.append(line[0].high)
    y.append(line[1].high)
    m, c = line[2], line[3]
    df_pos = line[1].df_pos
    for i in range(line[1].x + 1, loopback + 1):
        df_pos = df_pos + 1
        y.append(m * i + c)
        x.append(df['date'].iloc[df_pos])
    return x, y

def build_tab(tab_name, fig):
    return dcc.Tab(label=tab_name, value="tab-"+tab_name, children=[
        dcc.Graph(
            figure=fig,
        )
    ])

old_msgs = []
banned_pairs = []
notif_status = "" #  empty(both), low, high, no

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
@app.callback(Output('tabs', 'children'),
                Input('interval-component', 'n_intervals'))
def update_metrics(n):
    tabs = []
    timeframe = sys.argv[1]
    default_loopback = 25
    global banned_pairs
    pairs = []
    for pair in sys.argv[2:]:
        if pair.upper() not in banned_pairs:
            pairs.append(pair.upper())
    new_msgs = []
    for pair in pairs:
        df = get_candles(pair+"/USDT", timeframe)
        if len(df) < default_loopback:
            loopback = len(df)
        else:
            loopback = default_loopback
        best_clear_low_lines, best_clear_high_lines = get_lines(df, loopback)
        if best_clear_low_lines and best_clear_high_lines:

            df = df.tail(40)
            fig = go.Figure()
            fig.update_layout(height=800)
            fig.add_trace(go.Candlestick(x=df['date'],
                            open=df['open'],
                            high=df['high'],
                            low=df['low'],
                            close=df['close']))
 
            for line in best_clear_low_lines:
                x, y = get_x_and_y_low(df, line, loopback)
                fig.add_trace(go.Scatter(x=x, y=y))
            for line in best_clear_high_lines:
                x, y = get_x_and_y_high(df, line, loopback)
                fig.add_trace(go.Scatter(x=x, y=y))
            tabs.append(build_tab(pair, fig))

            # alarms
            global notif_status
            if notif_status != "no":
                current_price = df["close"].iloc[-1]
                if notif_status != "high":
                    for line in best_clear_low_lines:
                        m, c = line[2], line[3]
                        line_price = m * loopback + c
                        increase_pct = (current_price - line_price) / line_price * 100
                        if increase_pct <= 1:
                            new_msgs.append(f"{pair} close to {line_price}")
                        if increase_pct <= 0.3:
                            new_msgs.append(f"{pair} SUPER CLOSE to {line_price}")
                if notif_status != "low":
                    for line in best_clear_high_lines:
                        m, c = line[2], line[3]
                        line_price = m * loopback + c
                        increase_pct = (line_price - current_price) / current_price * 100
                        if increase_pct <= 1:
                            new_msgs.append(f"{pair} close to {line_price}")
                        if increase_pct <= 0.3:
                            new_msgs.append(f"{pair} SUPER CLOSE to {line_price}")
    global old_msgs
    for msg in new_msgs:
        if msg not in old_msgs:
            os.system(
                f"notify-send \"{msg}\"  --urgency critical -i /usr/share/icons/gnome/48x48/actions/stock_about.png")
            print(msg)
    old_msgs = new_msgs
    return tabs

def market_buy_and_set_stop_limit(pair, usdt_to_spend, stoploss_pct):
    api_key = os.getenv('BINANCE_TRADE_API_KEY')
    api_secret = os.getenv('BINANCE_TRADE_API_SECRET')
    
    client = Client(api_key, api_secret)
    
    try:
        market_buy_result = client.order_market_buy(
            symbol=pair+'USDT',
            quoteOrderQty=usdt_to_spend)
    
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
    
        stoploss = abs((stoploss_pct / 100) * avg_buy_price - avg_buy_price)
        stoploss_trigger = (0.05 / 100 * stoploss) + stoploss
        stop_limit_result = client.create_order(
            symbol=pair+'USDT',
            side='SELL',
            type='STOP_LOSS_LIMIT',
            timeInForce='GTC',
            quantity=my_round(str(full_qty), 6),
            price=my_round(str(stoploss), 2),
            stopPrice=my_round(str(stoploss_trigger), 2))
        
        print("Market buy filled successfully: ", market_buy_result)
        print("Stoploss limit filled successfully: ", stop_limit_result)
        print(f"avg-buy: {avg_buy_price} qty: {full_qty} stoploss-trigger: {stoploss_trigger} stoploss: {stoploss}")
    except Exception as exception:
        print(f"exception ocurred: {exception}")


@app.callback(
    Output('buy-btc-div', 'children'),
    Input('buy-btn', 'n_clicks'),
    State('tabs', 'value'),
    State('input-optional-pair', 'value'),
    State('input-usdt', 'value'),
    State('input-stoploss', 'value'))
def buy_button_clicked(btn, selected_tab, input_optional_pair, input_usdt, input_stoploss):
    if not input_usdt or not input_stoploss:
        return []
    if not input_optional_pair:
        pair = selected_tab.split("-")[1]
    else:
        pair = input_optional_pair.upper()
    market_buy_and_set_stop_limit(pair, float(input_usdt), float(input_stoploss))
    return []

@app.callback(
    Output('input-banned-pairs-div', 'children'), 
    Input('input-banned-pairs', 'value'))
def buy_button_clicked(input_value):
    if not input_value:
        return []
    global banned_pairs
    banned_pairs = []
    for pair in input_value.split(","):
        banned_pairs.append(pair.upper())
    if len(banned_pairs) == 1 and len(banned_pairs[0]) == 1:
        banned_pairs = []
    return []

@app.callback(
    Output('input-notifications-status-div', 'children'), 
    Input('input-notifications-status', 'value'))
def buy_button_clicked(input_value):
    if not input_value:
        return []
    global notif_status
    if len(input_value) == 1:
        notif_status = ""
    else:
        notif_status = input_value.lower()
        if notif_status == "no":
            global old_msgs
            old_msgs = []
    return []

def main():
    app.layout = html.Div([
        html.Div(id='buy-btc-div'),
        html.Div(id='input-banned-pairs-div'),
        html.Div(id='input-notifications-status-div'),
        dcc.Input(id="input-optional-pair", type="text", placeholder="optional pair"),
        dcc.Input(id="input-usdt", type="text", placeholder="usdt"),
        dcc.Input(id="input-stoploss", type="text", placeholder="stoploss"),
        html.Button('Buy', id='buy-btn', n_clicks=0),
        dcc.Input(id="input-banned-pairs", type="text", placeholder="Banned Pairs"),
        dcc.Input(id="input-notifications-status", type="text", placeholder="Notif.(no,low,high)"),
        dcc.Tabs(id="tabs"), 
        dcc.Interval(
            id='interval-component',
            interval=30*1000,
            n_intervals=0
        )])
    t = sys.argv[1]
    port = 8050
    if t == "4h":
        port = 8051
    elif t == "1w":
        port = 8052
    app.run_server(debug=True, port=port)

if __name__ == '__main__':
    main()

# FOR TESTING UPDATES
#timeframe = "1m"
#pairs = sys.argv[1:]
#for pair in pairs:
#    df = get_candles(pair+"/USDT", timeframe)
#    df = df.tail(40)
#    fig = go.Figure()
#    fig.update_layout(height=800)
#    fig.add_trace(go.Candlestick(x=df['date'],
#        open=df['open'],
#        high=df['high'],
#        low=df['low'],
#        close=df['close']))
#    tabs.append(build_tab(pair, fig))