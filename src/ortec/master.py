from threading import Thread
from daq import daq
from Queue import Queue
import time
import zmq
import json
from kafka import SimpleConsumer, KafkaClient, KafkaConsumer


if __name__ == "__main__":
    
    #Setting up messaging queue for graphics and/or sending to sigma
    port = "5556"
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:%s" % port)
    topic = 1001

    #q = Queue()
    #_sentinel = object() #object that signals shutdown
    q_message = Queue()

    #DO THIS LATER
    #perform a check to see if Digibases are plugged in 
    #code is written  so that if check is kwargs=(check=True) is run and there are no digibases, queue returns _sentinel

    
#    thread = Thread(target = daq, kwargs = dict(spoof_digibase = True, time=10))
    thread = Thread(target = daq, args=(q_message,), kwargs = dict(time=3))
    thread.start()

    counter=0

    
    consumer = KafkaConsumer('data_messages',bootstrap_servers=['localhost:9092'])
    
    
    while True:
        
        #sample = q.get()
        counter+=1
        #if sample is _sentinel:
        #    print 'queue is really empty', q.empty()
            #break
        #else:
        #    messagedata = json.dumps(sample)
        #    socket.send("%d %s" % (topic, messagedata))
        #    print sample['15226068']['time'], counter, 'queue'
        #    if counter == 5:
        #        q_message.put('Hi There')
        
        
        
        msg = consumer.next()
        
        #msg = consumer.get_messages(count=1,block=True)
        #print msg

        if msg.value == 'STOP':
            print 'kafka is really empty'
            break
        data = json.loads(msg.value)        
    
        
                    
    
    thread.join()


