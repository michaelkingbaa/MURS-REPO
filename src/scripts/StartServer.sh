#!/bin/sh

cd /usr/local/kafka_2.11-0.9.0.0
bin/zookeeper-server-start.sh config/zookeeper.properties &

cd /usr/local/kafka_2.11-0.9.0.0
bin/kafka-server-start.sh config/server.properties &
