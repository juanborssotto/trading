import requests
import math
import collections

def truncate_ceil(x, base):
    return base * math.ceil(x / base)


def truncate_floor(x, base):
    return base * math.floor(x / base)


def aggregate_ob_asks(ob, aggregated_ob, base):
    key = "asks"
    for n in ob[key]:
        truncated = truncate_ceil(float(n[0]), base)
        if truncated not in aggregated_ob[key]:
            aggregated_ob[key][truncated] = 0
        aggregated_ob[key][truncated] += float(n[1])


def aggregate_ob_bids(ob, aggregated_ob, base):
    key = "bids"
    for n in ob[key]:
        truncated = truncate_floor(float(n[0]), base)
        if truncated not in aggregated_ob[key]:
            aggregated_ob[key][truncated] = 0
        aggregated_ob[key][truncated] += float(n[1])

response = requests.get("https://api.binance.com/api/v3/depth?symbol=ETHUSDT&limit=5000")
ob = response.json()

aggregated_ob = dict()
aggregated_ob["bids"] = collections.OrderedDict()
aggregated_ob["asks"] = collections.OrderedDict()
aggregate_ob_bids(ob, aggregated_ob, 10)
aggregate_ob_asks(ob, aggregated_ob, 10)

print(aggregated_ob)