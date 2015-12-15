import zmq
import time
import json
import numpy as np

#Setting up messaging queue for graphics and/or sending to sigma
port = "5556"
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:%s" % port)
topic = 1001

for i in range(1000):
    print 'sending msg #{0}'.format(i)
    sample={'123':{'time':time.time(),'spectrum':[1 for i in range(1024)]}}
    msg=json.dumps(sample)
    print msg
    socket.send("%s %s".format(topic,msg))
    time.sleep(1)
