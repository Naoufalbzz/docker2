# Steps docker automatisation backup script
in folder met Dockerfile
- `docker build -t my-container .`
- `docker run -d --name backup_container my-container`
- `docker exec backup_container ./setup.sh`



1. dockerfile
2. env db_password meegeven met run `docker run -it -e DB_PASSWORD='root' ubu`
3. start cron met `service cron start`
4. `mkdir /src/backups`
5. `echo "0 2 * * * DB_PASSWORD='root' python3 /src/backup_script.py -dn testdb -du root -t MYSQL -b -bd /src/backups >> /var/log/cron.log 2>&1" | crontab -`
6. `tail -f /var/log/cron.log`