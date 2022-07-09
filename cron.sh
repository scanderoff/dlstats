# runs COMMAND once a day at random time

COMMAND=". /home/iscander/Desktop/yestats/venv/bin/activate && python /home/iscander/Desktop/yestats/populate_db.py"

crontab -u iscander -l | grep -v "$COMMAND" | crontab -u iscander -

hour=$(( $RANDOM % 23 ))
minute=$(( $RANDOM % 59 ))

(crontab -u iscander -l && echo "$minute $hour * * * $COMMAND") | crontab -u iscander -
