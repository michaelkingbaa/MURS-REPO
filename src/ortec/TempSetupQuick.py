import os
from controller import DigiBaseController
from kafka import SimpleProducer, KafkaClient
import time

kafka = KafkaClient('localhost:9092')
producer,topic=SimpleProducer(kafka),'data_messages'
dbc=DigiBaseController(producer,topic)

dbc.setHV("15226047",1100)
#dbc.setHV("15226048",1100)
#dbc.setHV("15226050",1100)
#dbc.setHV("15226057",1100)
#dbc.setHV("15226060",1100)
#dbc.setHV("15226068",1100)
#dbc.getSample(1)
#dbc.set_ULD("15226048",501)
#dbc.get_ULD("15226048")



