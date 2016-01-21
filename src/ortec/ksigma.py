import numpy as np
import math


class ksigma():
    def __init__(self, background_buffer, middle_buffer, event_buffer):
        self.background_buffer = background_buffer
        self.middle_buffer = middle_buffer
        self.event_buffer = event_buffer
        self.fifo_length = background_buffer + middle_buffer + event_buffer
        self.rolling_fifo = np.zeros(self.fifo_length)
        self.fifo_place = 0
        
        
    def ingress(self, timestamp, spectrum):
        message = {}

        self.rolling_fifo[self.fifo_place] = np.sum(spectrum)
        message['time'] = timestamp
        if self.fifo_place == (self.fifo_length -1.):
            background = np.sum(self.rolling_fifo[(self.middle_buffer+self.event_buffer):])/self.background_buffer
            sigma = math.sqrt(background)
            event = np.sum(self.rolling_fifo[:self.event_buffer])/self.event_buffer
            message['k_stat'] = (event - background) /sigma
            self.rolling_fifo = np.roll(self.rolling_fifo,-1)
        else:
            message['k_stat']=0
            
        if self.fifo_place < (self.fifo_length -1):
            self.fifo_place += 1
            
        
        return message

    



