from kafka import SimpleConsumer, KafkaClient, KafkaConsumer

wanted_client = 'localhost:9092'
while not 'test' in KafkaClient(wanted_client).topic_partitions.keys():
    print 'waiting for Data Client'
    time.sleep(1)

consumer = KafkaConsumer('test', bootstrap_servers=wanted_client)

for msg in consumer:
    print msg.value
