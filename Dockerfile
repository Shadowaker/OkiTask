# Basic dockerfile for running the programs

FROM ubuntu:22.04

RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get install -y curl

sudo apt-get install python3.9

WORKDIR /okitask

COPY . /okitask

CMD ["bash"]