import requests
import time
import os
import sys
from datetime import datetime

coins = dict()
for i in range(1, len(sys.argv), 2):
    coins[sys.argv[i]] = float(sys.argv[i + 1])

last_hour = datetime.now().hour
print(f"RUNNING PRICE ALARMS: {coins}")
while True:
    for coin, threshold in coins.items():
        price = float(requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={coin}USDT").json()["price"])
        if price > threshold:
            msg = f"PRICE ALARM: {coin} is above threshold: {threshold}"
            print(msg)
            #os.system(
            #    f"notify-send \"{msg}\"  --urgency critical -i /usr/share/icons/gnome/48x48/actions/stock_about.png")
    time.sleep(60)
    print("")
    if last_hour != datetime.now().hour:
        msg = "ONE HOUR HAS PASSED"
        os.system(
            f"notify-send \"{msg}\"  --urgency critical -i /usr/share/icons/gnome/48x48/actions/stock_about.png")
        last_hour = datetime.now().hour
