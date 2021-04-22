#!/bin/bash

files=$(ls Logs/LiveTest/)

for file in $files; do
   positionornot=$(cat Logs/LiveTest/$file | grep "Money" | awk '{$18=substr($18,0,7);$9=substr($9,0,7);$12=substr($12,0,8); print($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$14,$15,$18,$19)}' | tac | sort -u -k 10,10 | sort -k 15,15 | grep -n -e "-" -e "|")
   if [[ -n "$positionornot" ]]; then
      echo $positionornot
   fi
done
