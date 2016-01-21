import numpy as np

class distance():
    def __init__(self, setup_file, background_buffer, middle_buffer, event_buffer):
        self.background_buffer = background_buffer
        self.event_buffer = data_buffer
        self.middle_buffer = middle_buffer
        with open(setup_file,'r') as f:
            self.configuration = json.load(f)
        self.n_dets = len(self.confiration.keys())
        self.fifo_length = background_buffer + middle_buffer + event_buffer
        self.rolling_fifo = np.zeros(self.ndets, self.fifo_length)
        self.fifo_place = 0
        
                
        
    def find_distance(self, data_message):
        message = {}

        for i, key in enumerate(data_message.keys()):
            spectrum = np.array(data_message[key]['spectrum'])
            self.rolling_fifo[i][self.fifo_place] = np.sum(spectrum)
            message['time'] = data_message[key]['time'] #will be repeated 6 times
            
