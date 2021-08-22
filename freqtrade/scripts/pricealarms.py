import requests
import time
import os
import sys
from datetime import datetime, timedelta

coins = dict()
for i in range(1, len(sys.argv), 2):
    coins[sys.argv[i]] = float(sys.argv[i + 1])

def main():
    old_msgs = []
    last_hour = datetime.now().hour
    print(f"RUNNING PRICE ALARMS: {coins}")
    while True:
        try:
            new_msgs = []
            for coin, threshold in coins.items():
                price = float(requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={coin}USDT").json()["price"])
                if price >= threshold:
                    msg = f"PRICE ALARM: {coin} is above threshold: {threshold}"
                    new_msgs.append(msg)
            for nm in new_msgs:
                if nm not in old_msgs:
                    os.system(
                        f"notify-send \"{nm}\" --urgency critical -i /usr/share/icons/gnome/48x48/actions/stock_about.png")
                print(nm)
            old_msgs = new_msgs
            time.sleep(15)
            print("")
            #if last_hour == datetime.now().hour and datetime.now().minute > 49:
            #    msg = "10 MINUTES FOR ONE HOUR"
            #    os.system(
            #        f"notify-send \"{msg}\"  --urgency critical -i /usr/share/icons/gnome/48x48/actions/stock_about.png")
            #    last_hour = (datetime.now() + timedelta(hours=1)).hour
        except Exception as exception:
            print(f"exception {exception}")

main()