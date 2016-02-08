import numpy as np
import json

class direction():
    def __init__(self, setup_file, background_buffer, middle_buffer, event_buffer):
        self.background_buffer = background_buffer
        self.event_buffer = event_buffer
        self.middle_buffer = middle_buffer
        self.configuration = json.load(open(setup_file))
        self.n_dets = len(self.configuration.keys())
        self.fifo_length = background_buffer + middle_buffer + event_buffer
        self.rolling_fifo = np.zeros((self.n_dets, self.fifo_length))
        self.fifo_place = 0
        
                
        
    def ingress(self, data_message):
        message = {}
        tot_nobg = np.zeros(self.n_dets)
        angles = np.zeros(len(data_message.keys()))
        for i, key in enumerate(data_message.keys()):
            spectrum = np.array(data_message[key]['spectrum'])
            self.rolling_fifo[i][self.fifo_place] = np.sum(spectrum)
            message['time'] = data_message[key]['time'] #will be repeated 6 times
            if self.fifo_place == (self.fifo_length -1.):
                background = np.sum(self.rolling_fifo[i][:self.background_buffer])/self.background_buffer
                event = np.sum(self.rolling_fifo[i][(self.background_buffer + self.middle_buffer):])/self.event_buffer
                tot_nobg[i] = event #- background
                #if (event - background) < 0:
                #    tot_nobg[i] = 0
                angles[i] = self.configuration[key]
                
            
                
        if self.fifo_place == (self.fifo_length -1.):
            message['direction'] = self.find_direction(tot_nobg, angles)
            self.rolling_fifo = np.roll(self.rolling_fifo,-1,axis=1)
        else:
            message['direction'] = 0.0

        if self.fifo_place < (self.fifo_length -1):
            self.fifo_place += 1

        return message

    def find_direction(self, array, angles):
        elem = np.argsort(array)
        highest = array[elem[5]]
        high_angle = angles[elem[5]]
        outside_two_elems = np.where(np.logical_or((abs(angles - angles[elem[5]]) == 60),  (abs(angles - angles[elem[5]]) ==300)))
        inside_two_elems = np.argsort(array[outside_two_elems]) #elem 1 will be highest, elem 0 will be lower
        second_highest = array[outside_two_elems[0][inside_two_elems[1]]]
        sec_angle = angles[outside_two_elems[0][inside_two_elems[1]]]
        third_highest = array[outside_two_elems[0][inside_two_elems[0]]]
        third_angle = angles[outside_two_elems[0][inside_two_elems[0]]]
        #print 'highest is ', high_angle, highest, 'second_highest', sec_angle, second_highest, 'third highest', third_angle, third_highest
        #for i in range(6):
        #    print 'the rest', array[i], angles[i]
        meas_angle = high_angle + 2.5* (third_highest - second_highest)/(third_highest + second_highest)*(third_angle - sec_angle)
        print meas_angle
        return meas_angle
