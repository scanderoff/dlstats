# runs COMMAND once a day at random time

COMMAND=". /home/iscander/Desktop/yestats/venv/bin/activate && python /home/iscander/Desktop/yestats/populate_db.py"

crontab -l | grep -v "$COMMAND" | crontab -

hour=$(( $RANDOM % 23 ))
minute=$(( $RANDOM % 59 ))

(crontab -l && echo "$minute $hour * * * $COMMAND") | crontab -
