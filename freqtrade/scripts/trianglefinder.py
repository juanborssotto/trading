from numpy import ones,vstack
from typing import List
from numpy.linalg import lstsq
from freqtrade.utils.binance_rest_api import get_candles
from dataclasses import dataclass
import sys
from pandas import Timestamp

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
    x: int
    y: float
    high: float
    low: float

def get_lines(pair, timeframe, loopback):
    df = get_candles(pair+"/USDT", timeframe)

    n = 0
    points: List[Point] = []
    for i in range(loopback, 0, -1):
        n = n + 1
        points.append(Point(df["date"].iloc[-i], n, df["close"].iloc[-i], df["high"].iloc[-i], df["low"].iloc[-i]))

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
                    clear_low_lines.append((points[i], points[j]))

            high1, high2 = points[i].high, points[j].high
            if high1 > high2:
                m, c = get_func(x1, high1, x2, high2)
                is_clear_high_line = True
                for p in range(i+1, len(points)):
                    if p == j:
                        continue
                    next_value = m * points[p].x + c
                    if points[p].high > next_value:
                        is_clear_high_line = False
                if is_clear_high_line:
                    clear_high_lines.append((points[i], points[j]))

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

def main():
    timeframe = "1d"
    loopback = 20
    pairs = sys.argv[1:]
    for pair in pairs:
        best_clear_low_lines, best_clear_high_lines = get_lines(pair, timeframe, loopback)
        if best_clear_low_lines and best_clear_high_lines:
            print(pair)
            for line in best_clear_low_lines:
                print(line[0].date, line[1].date)
            print("---")
            for line in best_clear_high_lines:
                print(line[0].date, line[1].date)
            print("")

main()
