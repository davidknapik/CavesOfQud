#!/bin/sh


# awk -F. '/INFO - Thawing|INFO - Building/{print $2 "." $4 " " $3 "." $5 " :" $6}'  Player.log

tail -f Player.log | awk -F. '/INFO - Thawing|INFO - Finished Building/{print $2 "." $4 " " $3 "." $5 " :" $6}'