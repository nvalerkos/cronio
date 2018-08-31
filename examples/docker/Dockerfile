FROM mysql:5.7
env MYSQL_ROOT_PASSWORD=guest 
env MYSQL_DATABASE=contacts
ADD init.sql /docker-entrypoint-initdb.d
RUN apt-get update && \
	apt-get install -y python && \
	apt-get install -y python-pip
RUN apt-get install -y cron
RUN pip install cronio
# Add crontab file in the cron directory
ADD crontab /etc/cron.d/hello-cron
# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/hello-cron
# Create the log file to be able to run tail
RUN touch /var/log/cron.log
RUN mkdir -p /opt/cronio
ADD cronio_worker.py /opt/cronio/
# Add the command "service cron start" to docker entrypoint.
RUN sed -i '2iservice cron start' /usr/local/bin/docker-entrypoint.sh
