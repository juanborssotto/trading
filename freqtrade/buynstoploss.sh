if [ -z "$buy_zone_price_top" ]
  then
    echo "missing buy_zone_price_top"
    exit
fi
if [ -z "$buy_zone_price_bottom" ]
  then
    echo "missing buy_zone_price_bottom"
    exit
fi
if [ -z "$pair" ]
  then
    echo "missing pair"
    exit
fi
if [ -z "$is_dry_run" ]
  then
    echo "missing is_dry_run"
    exit
fi
if [ -z "$stake_amount" ]
  then
    echo "missing stake_amount"
    exit
fi
if [ -z "$binance_key" ]
  then
    echo "missing binance key"
    exit
fi
if [ -z "$binance_secret" ]
  then
    echo "missing binance secret"
    exit
fi
rm buynstoploss.sqlite
cp buynstoplossconfig.json buynstoplossconfigfilled.json && sed -i "s/{buy_zone_price_top}/$buy_zone_price_top/g; s/{buy_zone_price_bottom}/$buy_zone_price_bottom/g; s/{pair}/$pair/g; s/{is_dry_run}/$is_dry_run/g; s/{stake_amount}/$stake_amount/g; s/{binance_key}/$binance_key/g; s/{binance_secret}/$binance_secret/g" buynstoplossconfigfilled.json && freqtrade trade -c buynstoplossconfigfilled.json --strategy BuyNStoploss
