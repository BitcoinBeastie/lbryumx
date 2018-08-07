# buster is the only one so far that has python3.7
FROM debian:buster-slim
#FROM python:3.7-slim-stretch

ARG user=lbry

# create an unprivileged user
RUN groupadd -g 999 $user && useradd -r -u 999 -g $user $user
RUN mkdir -p /home/$user/
RUN chown -R $user:$user /home/$user/

# install python, pip, git and clean up
RUN apt-get update && apt-get -y --no-install-recommends install git python3.7 python3.7-dev python3-pip && rm -rf /var/lib/apt/lists/*

# create and chown database dir
ARG db_dir=/database
RUN mkdir -p $db_dir
RUN chown -R $user:$user $db_dir

# change into our user
USER $user
WORKDIR /home/$user

# RUN pip3 install -U pip (broken on pip 10 https://github.com/pypa/pip/issues/5240)
RUN python3.7 -m pip install --upgrade pip setuptools

# get our electrumx packages branch
RUN mkdir projects/
RUN git clone -b master https://github.com/kyuupichan/electrumx.git projects/electrumx
RUN python3.7 -m pip install --user -e projects/electrumx/.

# get lbryumx
COPY . projects/lbryumx
USER root
RUN chown -R $user:$user .
USER $user
WORKDIR projects/lbryumx
RUN python3.7 -m pip install --user -r requirements.txt
RUN python3.7 -m pip install --user -e . && rm ~/.cache -rf

# entry point
ARG host=0.0.0.0
ARG tcp_port=50001
ARG daemon_url=http://lbry:lbry@localhost:9245/
VOLUME $db_dir
ENV TCP_PORT=$tcp_port
ENV HOST=$host
ENV COIN=LBC
ENV DAEMON_URL=$daemon_url
ENV DB_DIRECTORY=$db_dir
ENV BANDWIDTH_LIMIT=1000000000000000000000000000000000000000000
ENV MAX_SESSIONS=1000000000
ENTRYPOINT ["python3.7"]
CMD ["lbryumx_server.py"]
