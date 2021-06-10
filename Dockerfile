FROM python:3.9-slim

RUN apt-get clean \
    && apt-get -y update

RUN apt-get -y install nginx \
    && apt-get -y install python3-dev \
    && apt-get -y install build-essential

COPY . /srv/boardgames
WORKDIR /srv/boardgames/boardgames

RUN chown www-data db

RUN pip install -r ../requirements.txt --src /usr/local/src

COPY nginx.conf /etc/nginx
RUN chmod +x ./start.sh
CMD ["./start.sh"]