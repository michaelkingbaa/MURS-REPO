__author__ = 'chivers'

import time
import xmltodict as xmld
from messaging.mursGPSMessage import mursGPSMessage
from datetime import datetime
class gpxReplay:

    def __init__(self,gpxFile, client, topic):
        self.topic = topic
        self.gpxMessage = mursGPSMessage('../messaging/mursGPS.avsc', topic, client)
        self.gpxReader = gpxFileReader(gpxFile)

    def replay(self,speed):
        data = {}
        for i in range(self.gpxReader.getLength()):
            data['time'] = self.gpxReader.getTimestamp(i)
            data['latitude'] = self.gpxReader.getLatitude(i)
            data['longitude'] = self.gpxReader.getLongitude(i)
            data['elevation'] = self.gpxReader.getElevation(i)
            self.gpxMessage.publishMessage(data)
            time.sleep(speed)


class gpxFileReader:

    def __init__(self, gpxFile):

        self.lat = []
        self.lon = []
        self.elevation = []
        self.timestamp = []
        self.speed = []
        self.trackLength = []

        try:
            dict = xmld.parse(open(gpxFile,'r'))
            pts = dict['gpx']['trk']['trkseg']['trkpt']
            for n in range(len(pts)):
                self.lat.append(float(pts[n]['@lat']))
                self.lon.append(float(pts[n]['@lon']))
                self.elevation.append(float(pts[n]['ele']))
                dt = datetime.strptime(str(pts[n]['time']),'%Y-%m-%dT%H:%M:%SZ')
                self.timestamp.append(time.mktime(dt.timetuple())-8*3600)
                self.speed.append(pts[n]['extensions']['mytracks:speed'])
                self.trackLength.append(pts[n]['extensions']['mytracks:length'])

        except Exception,e:
            print str(e)


    def getLength(self):
        return len(self.lat)

    def getLatitude(self,ind):
        if ind < len(self.lat) and ind >= 0:
            return self.lat[ind]
        else:
            return None

    def getAllLatitude(self):
        return self.lat

    def getLongitude(self,ind):
        if ind < len(self.lon) and ind >= 0:
            return self.lon[ind]
        else:
            return None

    def getAllElevation(self):
        return self.elevation

    def getElevation(self,ind):
        if ind < len(self.elevation) and ind >= 0:
            return self.elevation[ind]
        else:
            return None

    def getAllTimestamps(self):
        return self.timestamp

    def getTimestamp(self,ind):
        if ind < len(self.timestamp) and ind >= 0:
            return self.timestamp[ind]
        else:
            return None

    def getAllSpeed(self):
        return self.speed

    def getSpeed(self,ind):
        if ind < len(self.speed) and ind >= 0:
            return self.speed[ind]
        else:
            return None

    def getAllTrackLength(self):
        return self.trackLength

    def getTrackLength(self,ind):
        if ind < len(self.trackLength) and ind >= 0:
            return self.trackLength[ind]
        else:
            return None