import requests
import time
import os
import sys
from datetime import datetime, timedelta

coins = dict()
for i in range(1, len(sys.argv), 3):
    coins[sys.argv[i]] = {
        "down": "-" if sys.argv[i + 1] == "-" else float(sys.argv[i + 1]),
        "up": "-" if sys.argv[i + 2] == "-" else float(sys.argv[i + 2]),
    }

last_hour = datetime.now().hour
print(f"RUNNING PRICE ALARMS: {coins}")
while True:
    for coin, thresholds in coins.items():
        price = float(requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={coin}USDT").json()["price"])
        if thresholds["down"] != "-" and price < thresholds["down"]:
            msg = f'PRICE ALARM: {coin} is below threshold: {thresholds["down"]}'
            print(msg)
            os.system(
                f"notify-send \"{msg}\"  --urgency critical -i /usr/share/icons/gnome/48x48/actions/stock_about.png")
        if thresholds["up"] != "-" and price > thresholds["up"]:
            msg = f'PRICE ALARM: {coin} is above threshold: {thresholds["up"]}'
            print(msg)
            os.system(
                f"notify-send \"{msg}\"  --urgency critical -i /usr/share/icons/gnome/48x48/actions/stock_about.png")
    time.sleep(15)
    print("")
    if last_hour == datetime.now().hour and datetime.now().minute > 49:
        msg = "10 MINUTES FOR ONE HOUR"
        os.system(
            f"notify-send \"{msg}\"  --urgency critical -i /usr/share/icons/gnome/48x48/actions/stock_about.png")
        last_hour = (datetime.now() + timedelta(hours=1)).hour