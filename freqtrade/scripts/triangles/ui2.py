import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output, State, MATCH, ALL
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
from pandas import Timestamp, DateOffset
import plotly.graph_objects as go
import freqtrade.vendor.qtpylib.indicators as qtpylib

import pickle

import os

def get_func(x1, y1, x2, y2):
    points = [(x1,y1),(x2,y2)]
    x_coords, y_coords = zip(*points)
    A = vstack([x_coords,ones(len(x_coords))]).T
    m, c = lstsq(A, y_coords, rcond=None)[0]
    return m, c

def get_increase(start, final):
    return (final - start) / start * 100


def get_final_by_increase(start, increase):
    return increase / 100 * start + start


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

def get_lines(pair, df, loopback):
    global lines_per_pair
    if pair+"low" not in lines_per_pair:
        return [], []
    low_pair_lines = lines_per_pair[pair+"low"]
    high_pair_lines = lines_per_pair[pair+"high"]
    return low_pair_lines, high_pair_lines

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

    print(best_clear_low_lines)
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

def build_tab(tab_name, fig, index):
    return dcc.Tab(label=tab_name, value=str(index)+"-"+tab_name, children=[
        dcc.Graph(
            id={'type': 'graph', 'index': 0},
            figure=fig,
        )
    ])

def get_closest_high_day_resistance(d_df, current_price):
    df = d_df[(d_df['date'].dt.year >= get_closest_high_day_week_resistance_since_year) & (d_df['date'].dt.month >= get_closest_high_day_week_resistance_since_month)]
    return df[df["high"] > current_price]["high"].min()

def get_closest_high_week_resistance(w_df, current_price):
    df = w_df[(w_df['date'].dt.year >= get_closest_high_day_week_resistance_since_year) & (w_df['date'].dt.month >= get_closest_high_day_week_resistance_since_month)]
    return df[df["high"] > current_price]["high"].min()

old_msgs = []
allowed_pairs = []
notif_status = "" #  empty(both), low, high, no
lines_option = "low" #  empty(both), low, high
interval = 30
open_trades = []
week_df = dict()
day_df = dict()
get_closest_high_day_week_resistance_since_year = 2021
get_closest_high_day_week_resistance_since_month = 5
alarm_threshold = 0.4
fast_mode = False
lines_per_pair = dict()
# deserialize
try:
    with open('lines.dat', 'rb') as f:
        lines_per_pair = pickle.load(f)
except:
    pass


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
@app.callback(Output('tabs', 'children'),
                Input('interval-component', 'n_intervals'))
def update_metrics(n):
    global week_df
    global day_df
    global alarm_threshold
    global fast_mode
    if len(week_df) == 0:
        for pair in sys.argv[2:]:
            print(f"getting {pair}")
            w_df = get_candles(pair+"/USDT", "1w")
            d_df = get_candles(pair+"/USDT", "1d")
            week_df[pair] = w_df.iloc[:-1 , :]
            day_df[pair] = d_df.iloc[:-1 , :]
    tabs = []
    timeframe = sys.argv[1]
    default_loopback = 40
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
    for i, pair in enumerate(pairs):
        df = get_candles(pair+"/USDT", timeframe)
        if len(df) < default_loopback:
            loopback = len(df)
        else:
            loopback = default_loopback
        best_clear_low_lines, best_clear_high_lines = get_lines(pair, df, loopback)
        df = df.tail(40)
        fig = go.Figure()
        fig.update_layout(height=800)


        if not fast_mode:
            fig.add_trace(go.Candlestick(x=df['date'],
                            open=df['open'],
                            high=df['high'],
                            low=df['low'],
                            close=df['close']))
            closest_date = df['date'].iloc[-1]
        else:
            fast_df = get_candles(pair+"/USDT", "15m")
            fig.add_trace(go.Candlestick(x=fast_df['date'],
                            open=fast_df['open'],
                            high=fast_df['high'],
                            low=fast_df['low'],
                            close=fast_df['close']))
            closest_date = fast_df['date'].iloc[-1]
            yaxis_threahold = fast_df['close'].iloc[-1] * 0.01
            date_add_1_hour = fast_df['date'].iloc[-1] + DateOffset(hours=1)
            fig.update_layout(
                xaxis=dict(range=[fast_df['date'].iloc[-20], date_add_1_hour]),
                yaxis=dict(range=[
                    fast_df['low'].rolling(20).min().iloc[-1] - yaxis_threahold, 
                    fast_df['high'].rolling(20).max().iloc[-1] + yaxis_threahold])
            )

        for line in best_clear_low_lines:
            x, y = get_x_and_y_low(df, line, loopback)

            x[-1] = closest_date

            fig.add_trace(go.Scatter(x=x, y=y, hoverinfo='skip'))
            increase_pct = get_increase(y[-1], df["close"].iloc[-1], )
            fig.add_annotation(x=x[-1], y=y[-1],
                text=round(increase_pct, 2),
                font=dict(size=12,color="black"),
                showarrow=False,
                xshift=10,
                yshift=0)
        for line in best_clear_high_lines:
            x, y = get_x_and_y_high(df, line, loopback)

            x[-1] = closest_date

            fig.add_trace(go.Scatter(x=x, y=y, hoverinfo='skip'))
            increase_pct = get_increase(df["close"].iloc[-1], y[-1])
            fig.add_annotation(x=x[-1], y=y[-1],
                text=round(increase_pct, 2),
                font=dict(size=12,color="black"),
                showarrow=False,
                xshift=10,
                yshift=0)

        # vwap
        df["vwap"] = qtpylib.rolling_vwap(df, window=14).tolist()
        vwap_dates = df["date"].tolist()
        vwap_dates[-1] = closest_date
        fig.add_trace(go.Scatter(x=vwap_dates, y=df["vwap"].tolist(), hoverinfo='skip'))
        vwap_increase_pct = get_increase(df["vwap"].iloc[-1], df["close"].iloc[-1])
        fig.add_annotation(x=closest_date, y=df["vwap"].tolist()[-1],
            text=round(vwap_increase_pct, 2),
            font=dict(size=12,color="black"),
            showarrow=False,
            xshift=20,
            yshift=0)
            
        # vwap alarm
        #if vwap_increase_pct > 0 and vwap_increase_pct <= alarm_threshold and df["close"].iloc[-2] > df["vwap"].iloc[-2]:
        #    new_msgs.append(f"{pair} {timeframe} close to VWAP")
 
        # open trades
        global open_trades
        if any(pair == open_trade["pair"] for open_trade in open_trades):
            open_trade = None
            for ot in open_trades:
                if ot["pair"] == pair:
                    open_trade = ot
                    break
            # t = f'{round(get_increase(open_trade["stoploss_trigger"], df["close"].iloc[-1]), 2)} {round(get_increase(open_trade["buy_price"], df["close"].iloc[-1]), 2)}'
            profit_pct = round(get_increase(open_trade["buy_price"], df["close"].iloc[-1]), 2)
            t = profit_pct
            fig.add_annotation(x=closest_date, y=df["close"].iloc[-1],
                text=t,
                font=dict(size=12,color="green"),
                showarrow=False,
                xshift=50,
                yshift=0)
            
            # open trade alarms
            if str(profit_pct)[:1] != str(open_trade["last_profit_pct"])[:1]:
                new_msgs.append(f'{pair} profit from {open_trade["last_profit_pct"]} to {profit_pct}')
            open_trade["last_profit_pct"] = profit_pct

        # day and week high resistances
        closest_high_day_resistance = get_closest_high_day_resistance(
            day_df[pair], df["close"].iloc[-1])
        closest_high_week_resistance = get_closest_high_week_resistance(
            week_df[pair], df["close"].iloc[-1])
        fig.add_hline(y=closest_high_day_resistance, line_width=1, line_dash="dash", line_color="grey", opacity=0.5)
        closest_high_day_resistance_increase = get_increase(df["close"].iloc[-1], closest_high_day_resistance)
        fig.add_annotation(x=closest_date, y=closest_high_day_resistance,
            text=f"D {round(closest_high_day_resistance_increase, 2)}",
            font=dict(size=12,color="black"),
            showarrow=False,
            xshift=60,
            yshift=0)
        fig.add_hline(y=closest_high_week_resistance, line_width=1, line_dash="dash", line_color="grey", opacity=0.5)
        closest_high_week_resistance_increase = get_increase(df["close"].iloc[-1], closest_high_week_resistance)
        fig.add_annotation(x=closest_date, y=closest_high_week_resistance,
            text=f"W {round(closest_high_week_resistance_increase, 2)}",
            font=dict(size=12,color="black"),
            showarrow=False,
            xshift=60,
            yshift=0)

        # distance from current low to current price
        distance_from_current_low_to_current_price = get_increase(df["low"].iloc[-1], df["close"].iloc[-1])
        fig.add_annotation(x=closest_date, y=df["low"].iloc[-1],
            text=f"low{round(distance_from_current_low_to_current_price, 2)}",
            font=dict(size=12,color="black"),
            showarrow=False,
            xshift=70,
            yshift=0)

        tabs.append(build_tab(pair, fig, i))

        # lines alarms
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
                    if increase_pct <= alarm_threshold:
                        new_msgs.append(f".{pair} {timeframe} #LOW {increase_pct}")
            if notif_status != "low":
                for line in best_clear_high_lines:
                    m, c = line[2], line[3]
                    line_price = m * loopback + c
                    increase_pct = (line_price - current_price) / current_price * 100
                    #if increase_pct <= 1:
                    #    new_msgs.append(f"{pair} {timeframe} #HIGH {increase_pct}")
                    if increase_pct <= alarm_threshold:
                        new_msgs.append(f".{pair} {timeframe} #HIGH {increase_pct}")

    global old_msgs
    for msg in new_msgs:
        nm_ = msg.split("#")[0]
        old_msgs_ = [msg.split("#")[0] for msg in old_msgs]
        if nm_ not in old_msgs_:
            os.system(
                f"notify-send \"{msg}\"  -t 5000 -i /usr/share/icons/gnome/48x48/actions/stock_about.png")
                # f"notify-send \"{msg}\"  --urgency critical -i /usr/share/icons/gnome/48x48/actions/stock_about.png")
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
        print(f"Stoploss USDT: {order_quantity * order_stoploss}")

        stop_limit_result = client.create_order(
            symbol=pair+'USDT',
            side='SELL',
            type='STOP_LOSS_LIMIT',
            timeInForce='GTC',
            quantity=str(order_quantity),
            price=str(order_stoploss),
            stopPrice=str(order_stoploss_trigger))
        print("Stoploss limit result: ", stop_limit_result)

        open_trades.append({
            'pair': pair,
            'buy_price': avg_buy_price,
            'qty': order_quantity,
            'stoploss': stoploss,
            'stoploss_trigger': stoploss_trigger,
            'last_profit_pct': 0.0,
        })
        
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
    Output('btc-finish-open-trade-div', 'children'),
    Input('btc-finish-open-trade', 'n_clicks'),
    State('tabs', 'value'))
def buy_button_clicked(btn, selected_tab):
    pair = selected_tab.split("-")[1]
    global open_trades
    if any(pair == open_trade["pair"] for open_trade in open_trades):
        open_trade = None
        for ot in open_trades:
            if ot["pair"] == pair:
                open_trade = ot
                break
        open_trades.remove(open_trade)
    return []


@app.callback(
    Output('input-allowed-pairs-div', 'children'), 
    Input('input-allowed-pairs', 'value'))
def buy_button_clicked(input_value):
    global allowed_pairs
    if not input_value:
        allowed_pairs = []
        return []
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
    global fast_mode
    if check_value:
        fast_mode = True
        allowed_pairs_before_fast_mode = allowed_pairs
        interval_before_fast_mode = interval
        allowed_pairs = [pair.split("-")[1]]
        interval = 2
    else:
        fast_mode = False
        allowed_pairs = allowed_pairs_before_fast_mode
        interval = interval_before_fast_mode
    return interval

@app.callback(
    Output('dropdown-alarm-threshold-div', 'children'), 
    Input('dropdown-alarm-threshold', 'value'))
def buy_button_clicked(input_value):
    global alarm_threshold
    alarm_threshold = float(input_value)
    return []

current_line_creation_data = []

@app.callback(
    Output('graph-div', 'children'),
    Input({'type': 'graph', 'index': ALL}, 'clickData'),
    State('tabs', 'value'),
    State('input-lines-option', 'value'),
    State('create-lines-mode', 'value'))
def display_hover_data(clickedPoint, tabs_value, lines_opt, create_lines_opt):
    index = tabs_value.split("-")[0]
    if index == "tab":
        return []
    index = int(index)
    point = clickedPoint[index]
    if not point:
        return []
    pair = tabs_value.split("-")[1]
    global current_line_creation_data
    global lines_per_pair

    if create_lines_opt == "insert":
        current_line_creation_data.append(
            Point(point['points'][0]['x'], 
            (41 - (point['points'][0]['pointIndex'] + 1)) * -1, 
            point['points'][0]['pointIndex'] + 1, 
            point['points'][0]['close'],
            point['points'][0]['high'], 
            point['points'][0]['low'], 
            point['points'][0]['close']))

        if len(current_line_creation_data) == 2:
            if pair+"low" not in lines_per_pair:
                lines_per_pair[pair+"low"] = []
                lines_per_pair[pair+"high"] = []
            if lines_opt == "low":
                m, c = get_func(
                    current_line_creation_data[0].x, 
                    current_line_creation_data[0].low, 
                    current_line_creation_data[1].x, 
                    current_line_creation_data[1].low)
            else:
                m, c = get_func(
                    current_line_creation_data[0].x, 
                    current_line_creation_data[0].high, 
                    current_line_creation_data[1].x, 
                    current_line_creation_data[1].high)
            lines_per_pair[pair+lines_opt].append((current_line_creation_data[0], current_line_creation_data[1], m, c))

            # serialize
            with open('lines.dat', 'wb') as f:
                pickle.dump(lines_per_pair, f)
            current_line_creation_data = []
    else:
        x_ = point['points'][0]['pointIndex'] + 1
        elem_to_delete = None
        for line in lines_per_pair[pair+lines_opt]:
            if line[0].x == x_:
                elem_to_delete = line
        if elem_to_delete:
            lines_per_pair[pair+lines_opt].remove(elem_to_delete)
            # serialize
            with open('lines.dat', 'wb') as f:
                pickle.dump(lines_per_pair, f)
        current_line_creation_data = []
    return []

@app.callback(
    Output('tabs-div', 'children'),
    Input('tabs', 'value'))
def tabs_clicked(tabs_value):
    global current_line_creation_data
    current_line_creation_data = []
    return []

def main():
    app.layout = html.Div([
        html.Div(id='buy-btc-div'),
        html.Div(id='graph-div'),
        html.Div(id='input-allowed-pairs-div'),
        html.Div(id='input-notifications-status-div'),
        html.Div(id='input-lines-option-div'),
        html.Div(id='btc-finish-open-trade-div'),
        html.Div(id='dropdown-alarm-threshold-div'),
        html.Div(id='tabs-div'),
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
            value='low',
            placeholder="Notif.",
            style={'display': 'inline-block', 'width': 120}),
        dcc.Input(id="input-refresh-secs", type="text", placeholder="Refresh secs", value="30"),
        html.Span("LineMode"),
        dcc.Dropdown(id="input-lines-option", options=[
            {'label': 'Low', 'value': 'low'}, 
            {'label': 'High', 'value': 'high'}], 
            value='low',
            placeholder="LineMode", 
            style={'display': 'inline-block', 'width': 120}),
        dcc.Dropdown(id="create-lines-mode", options=[
            {'label': 'Insert', 'value': 'insert'}, 
            {'label': 'Delete', 'value': 'delete'}], 
            value='insert',
            placeholder="CreateLinesMode", 
            style={'display': 'inline-block', 'width': 120}),
        dcc.Checklist(id="check-fastmode", options=[
            {'label': 'Fast', 'value': 'fast'}], 
            style={'display': 'inline-block'}),
        html.Button('Fin.OpenTrades', id='btc-finish-open-trade', n_clicks=0, style={'width': 90, 'font-size': 8, 'padding': 0}),
        dcc.Dropdown(id="dropdown-alarm-threshold", options=[
            {'label': '0.1', 'value': '0.1'}, 
            {'label': '0.2', 'value': '0.2'}, 
            {'label': '0.3', 'value': '0.3'}, 
            {'label': '0.4', 'value': '0.4'},],
            value='0.4',
            placeholder="Threshold", 
            style={'display': 'inline-block', 'width': 120}),
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
    elif t == "1h":
        port = 8053
    app.run_server(debug=True, port=port)

if __name__ == '__main__':
    main()
