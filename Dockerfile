FROM python:3.9-slim as builder

RUN apt-get clean \
    && apt-get -y update

RUN apt-get -y install python3-dev \
    && apt-get -y install build-essential

COPY requirements.txt requirements.txt

RUN pip install --prefix="/install" --no-warn-script-location -r requirements.txt


FROM python:3.9-slim

RUN apt-get clean \
    && apt-get -y update

COPY . /srv/boardgames
WORKDIR /srv/boardgames/boardgames

RUN chown www-data db

COPY --from=builder /install /usr/local

RUN chmod +x ./start.sh
CMD ["./start.sh"]
