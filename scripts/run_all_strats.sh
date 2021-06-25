#!/bin/bash
config=$1
time_range=$2
if [ ! "$config" ]
then
  echo "Missing config filepath argument"
  exit
fi

if [ ! "$time_range" ]
then
  echo "Missing time range argument"
  exit
fi
now="$(date +'%d-%m-%Y_%H:%M:%S')"
for filename in ../freqtrade/user_data/strategies/*.py; do
    strategy=$(echo "$filename" | cut -d"/" -f5 | cut -d"." -f1)
    echo "Running " "$strategy"
    result=$(python ../freqtrade/main.py backtesting --strategy "$strategy" --userdir ../freqtrade/user_data -c "$config" --timerange="$time_range")
    if [ ! "$result" ]
    then
      printf "\e[0;31mError running ${strategy}\n"
      exit
    else
      echo "$result" >> run_all_strats_result/"$now"
      echo "" >> run_all_strats_result/"$now"
    fi
    echo ""
    exit
done