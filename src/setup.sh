#!/bin/bash
service cron start

mkdir /src/backups

echo -e "* * * * * DB_PASSWORD='root' python3 /src/backup_script.py -dn testdb -du root -t MYSQL -b -bd /src/backups >> /var/log/cron.log 2>&1\n* * * * * DB_PASSWORD='root' python3 /src/backup_script.py -bd /src/backups -r 14 -dn testdb -du root -t MYSQL >> /var/log/cron.log 2>&1" | crontab -

exec "$@"