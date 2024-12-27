FROM ubuntu:latest

WORKDIR /src

USER root
RUN apt update -y \
    && apt -y install mysql-client postgresql-client cron nano \
    && apt install -y python3

COPY src/* /src/
COPY crontab.txt /etc/cron.d/my-cron-job
COPY src/setup.sh /src/setup.sh

RUN chmod 0644 /etc/cron.d/my-cron-job && \
    chmod +x /src/backup_script.py 
RUN chmod +x /src/setup.sh
ENTRYPOINT ["tail"]
CMD ["-f", "/dev/null"]