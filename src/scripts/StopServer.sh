#!/bin/sh

cd /usr/local/kafka_2.11-0.9.0.0
bin/zookeeper-server-stop.sh &

cd /usr/local/kafka_2.11-0.9.0.0
bin/kafka-server-stop.sh &
