import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
import os
from binance import Client
import time
import math

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

def get_increase(start, final):
    return (final - start) / start * 100

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
allowed_pairs = []
notif_status = "" #  empty(both), low, high, no
lines_option = "" #  empty(both), low, high
interval = 30

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
@app.callback(Output('tabs', 'children'),
                Input('interval-component', 'n_intervals'))
def update_metrics(n):
    tabs = []
    timeframe = sys.argv[1]
    default_loopback = 25
    global allowed_pairs
    global lines_option
    pairs = []
    for pair in sys.argv[2:]:
        if allowed_pairs:
            if pair.upper() in allowed_pairs:
                pairs.append(pair.upper())
        else:
            pairs.append(pair.upper())
    new_msgs = []
    for pair in pairs:
        df = get_candles(pair+"/USDT", timeframe)
        if len(df) < default_loopback:
            loopback = len(df)
        else:
            loopback = default_loopback
        best_clear_low_lines, best_clear_high_lines = get_lines(df, loopback)
        if (not lines_option and (best_clear_low_lines and best_clear_high_lines)) or \
            (lines_option and lines_option.upper() == "LOW" and best_clear_low_lines) or \
            (lines_option and lines_option.upper() == "HIGH" and best_clear_high_lines):
            df = df.tail(40)
            fig = go.Figure()
            fig.update_layout(height=800)
            fig.add_trace(go.Candlestick(x=df['date'],
                            open=df['open'],
                            high=df['high'],
                            low=df['low'],
                            close=df['close']))
            if not lines_option or (lines_option and lines_option.upper() != "HIGH" and best_clear_low_lines):
                for line in best_clear_low_lines:
                    x, y = get_x_and_y_low(df, line, loopback)
                    fig.add_trace(go.Scatter(x=x, y=y))
                    increase_pct = get_increase(y[-1], df["close"].iloc[-1], )
                    fig.add_annotation(x=x[-1], y=y[-1],
                        text=round(increase_pct, 2),
                        showarrow=False,
                        xshift=10,
                        yshift=-10)
            if not lines_option or (lines_option and lines_option.upper() != "LOW" and best_clear_high_lines):
                for line in best_clear_high_lines:
                    x, y = get_x_and_y_high(df, line, loopback)
                    fig.add_trace(go.Scatter(x=x, y=y))
                    increase_pct = get_increase(df["close"].iloc[-1], y[-1])
                    fig.add_annotation(x=x[-1], y=y[-1],
                        text=round(increase_pct, 2),
                        showarrow=False,
                        xshift=10,
                        yshift=10)
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
                        #if increase_pct <= 1:
                        #    new_msgs.append(f"{pair} {timeframe} #LOW {increase_pct}")
                        if increase_pct <= 0.4:
                            new_msgs.append(f".{pair} {timeframe} #LOW {increase_pct}")
                if notif_status != "low":
                    for line in best_clear_high_lines:
                        m, c = line[2], line[3]
                        line_price = m * loopback + c
                        increase_pct = (line_price - current_price) / current_price * 100
                        #if increase_pct <= 1:
                        #    new_msgs.append(f"{pair} {timeframe} #HIGH {increase_pct}")
                        if increase_pct <= 0.4:
                            new_msgs.append(f".{pair} {timeframe} #HIGH {increase_pct}")
    global old_msgs
    for msg in new_msgs:
        nm_ = msg.split("#")[0]
        old_msgs_ = [msg.split("#")[0] for msg in old_msgs]
        if nm_ not in old_msgs_:
            os.system(
                f"notify-send \"{msg}\"  --urgency critical -i /usr/share/icons/gnome/48x48/actions/stock_about.png")
            print(msg)
    old_msgs = new_msgs
    return tabs

def get_stoploss_and_qty(client, pair, qty, stoploss, stoploss_trigger):
    ticks = {}
    for filt in client.get_symbol_info(pair+'USDT')['filters']:
        if filt['filterType'] == 'PRICE_FILTER':
            ticks['price_step_size'] = filt['tickSize'].find('1') - 1
        if filt['filterType'] == 'LOT_SIZE':
            ticks['lot_step_size'] = filt['stepSize'].find('1') - 1

    order_stoploss = math.floor(stoploss * 10**ticks['price_step_size']) / float(10**ticks['price_step_size'])
    order_stoploss_trigger = math.floor(stoploss_trigger * 10**ticks['price_step_size']) / float(10**ticks['price_step_size'])
    order_quantity = math.floor(qty * 10**ticks['lot_step_size']) / float(10**ticks['lot_step_size'])
    return order_stoploss, order_stoploss_trigger, order_quantity

def market_buy_and_set_stop_limit(pair, usdt_to_spend, stoploss_pct):
    api_key = os.getenv('BINANCE_TRADE_API_KEY')
    api_secret = os.getenv('BINANCE_TRADE_API_SECRET')
    
    client = Client(api_key, api_secret)
    
    try:
        market_buy_result = client.order_market_buy(
            symbol=pair+'USDT',
            quoteOrderQty=usdt_to_spend)
        print("Market buy result: ", market_buy_result)
    
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
        stoploss = abs((stoploss_pct / 100) * avg_buy_price - avg_buy_price)
        stoploss_trigger = (0.05 / 100 * stoploss) + stoploss

        print("avg buy price ", avg_buy_price)
        print("full qty ", full_qty)
        print("stoploss ", stoploss)
        print("stoploss trigger ", stoploss_trigger)

        order_stoploss, order_stoploss_trigger, order_quantity = get_stoploss_and_qty(
            client, pair, full_qty, stoploss, stoploss_trigger
        )
        print("order_quantity ", order_quantity)
        print("order_stoploss ", order_stoploss)
        print("order_stoploss_trigger ", order_stoploss_trigger)

        stop_limit_result = client.create_order(
            symbol=pair+'USDT',
            side='SELL',
            type='STOP_LOSS_LIMIT',
            timeInForce='GTC',
            quantity=str(order_quantity),
            price=str(order_stoploss),
            stopPrice=str(order_stoploss_trigger))
        print("Stoploss limit result: ", stop_limit_result)
        
        print("Market buy filled successfully")
        print("Stoploss limit filled successfully")
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
    Output('input-allowed-pairs-div', 'children'), 
    Input('input-allowed-pairs', 'value'))
def buy_button_clicked(input_value):
    if not input_value:
        return []
    global allowed_pairs
    allowed_pairs = []
    for pair in input_value.split(" "):
        allowed_pairs.append(pair.upper())
    if len(allowed_pairs) == 1 and len(allowed_pairs[0]) == 1:
        allowed_pairs = []
    return []

@app.callback(
    Output('input-notifications-status-div', 'children'), 
    Input('input-notifications-status', 'value'))
def buy_button_clicked(input_value):
    global notif_status
    notif_status = input_value.lower()
    if notif_status == "no":
        global old_msgs
        old_msgs = []
    print(notif_status)
    return []

@app.callback(
    Output("interval-component", "interval"),
    [Input("input-refresh-secs", "value")]
)
def update_interval(value):
    default_value = 30*1000
    new_interval = default_value
    try:
        v = int(value) * 1000
        if v >= 2000:
            new_interval = v
        else:
            new_interval = default_value
    except Exception as exception:
        pass
        new_interval = default_value
    global interval
    interval = new_interval / 1000
    return new_interval

@app.callback(
    Output('input-lines-option-div', 'children'), 
    Input('input-lines-option', 'value'))
def buy_button_clicked(input_value):
    global lines_option
    lines_option = input_value.lower()
    return []

allowed_pairs_before_fast_mode = []
interval_before_fast_mode = None

@app.callback(
    Output("input-refresh-secs", "value"),
    Input('check-fastmode', 'value'),
    State('tabs', 'value'))
def buy_button_clicked(check_value, pair):
    global allowed_pairs
    global allowed_pairs_before_fast_mode
    global interval
    global interval_before_fast_mode
    if check_value:
        allowed_pairs_before_fast_mode = allowed_pairs
        interval_before_fast_mode = interval
        allowed_pairs = [pair.split("-")[1]]
        interval = 2
    else:
        allowed_pairs = allowed_pairs_before_fast_mode
        interval = interval_before_fast_mode
    return interval

def main():
    app.layout = html.Div([
        html.Div(id='buy-btc-div'),
        html.Div(id='input-allowed-pairs-div'),
        html.Div(id='input-notifications-status-div'),
        html.Div(id='input-lines-option-div'),
        dcc.Input(id="input-optional-pair", type="text", placeholder="optional pair"),
        dcc.Input(id="input-usdt", type="text", placeholder="usdt"),
        dcc.Input(id="input-stoploss", type="text", placeholder="stoploss"),
        html.Button('Buy', id='buy-btn', n_clicks=0),
        dcc.Input(id="input-allowed-pairs", type="text", placeholder="Allowed Pairs"),
        html.Span("Notif."),
        dcc.Dropdown(id="input-notifications-status", 
        options=[
            {'label': 'All', 'value': ''}, 
            {'label': 'No', 'value': 'no'}, 
            {'label': 'Low', 'value': 'low'},
            {'label': 'High', 'value': 'high'}], 
            value='',
            placeholder="Notif.",
            style={'display': 'inline-block', 'width': 120}),
        dcc.Input(id="input-refresh-secs", type="text", placeholder="Refresh secs", value="30"),
        html.Span("LineMode"),
        dcc.Dropdown(id="input-lines-option", options=[
            {'label': 'Both', 'value': ''}, 
            {'label': 'Low', 'value': 'low'}, 
            {'label': 'High', 'value': 'high'}], 
            value='',
            placeholder="LineMode", 
            style={'display': 'inline-block', 'width': 120}),
        dcc.Checklist(id="check-fastmode", options=[
            {'label': 'Fast', 'value': 'fast'}], 
            style={'display': 'inline-block'}),
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