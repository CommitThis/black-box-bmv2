FROM ubuntu:18.04

WORKDIR /opt/p4
RUN apt update && apt install git -y && \
    git clone https://github.com/jafingerhut/p4-guide.git
RUN apt install lsb-release sudo -y
RUN ./p4-guide/bin/install-p4dev-v3.sh

RUN apt-get clean
COPY ./wait.sh /opt/wait.sh
