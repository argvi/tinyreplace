#!/usr/bin/env bash

TRP_DATA_DIR=$1
CANVAS_CHECKPOINTS_DIR=$2
DATA_ORDER_CSV=$3

echo Collecting data...
for num in $(seq -w -s " " 0 78);
do echo Downloading and converting 2022_place_canvas_history-0000000000$num.csv.gzip;
   curl https://placedata.reddit.com/data/canvas-history/2022_place_canvas_history-0000000000$num.csv.gzip | gzip -d | ./trp > $TRP_DATA_DIR/2022_place_canvas_history-0000000000$num.trp;
   echo $(./trp -d < $TRP_DATA_DIR/2022_place_canvas_history-0000000000$num.trp | head -n 2 | tail -n 1 | cut -d , -f 1),$num >> $DATA_ORDER_CSV;
done

echo Sorting data in chronological order...
sort -o $DATA_ORDER_CSV{,}

for num in $(cat $DATA_ORDER_CSV | cut -d , -f 2);
do echo Building canvas checkpoint from 2022_place_canvas_history-0000000000$num.trp;
   python3 build_canvas.py $CANVAS_CHECKPOINTS_DIR/$num.png $prev_canvas < $TRP_DATA_DIR/2022_place_canvas_history-0000000000$num.trp;
   prev_canvas=$CANVAS_CHECKPOINTS_DIR/$num.png
done
