#!/bin/bash

files=$(ls Logs/LiveTest/)

for file in $files; do
   positionornot=$(cat Logs/LiveTest/$file | tail -n 1 | grep "Bought")
   if [[ -n "$positionornot" ]]; then
      echo $positionornot
   fi
done
