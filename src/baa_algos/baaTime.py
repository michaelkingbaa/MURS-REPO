"""
@file baaTime.py
@author Thomas McCullough
@date January 13, 2015
@brief Simple module for dealing with time, from BAA perspective
@bug No bugs presently known
"""

import datetime
import calendar
from dateutil.parser import parse

def timestampToISOFormat(timestamp):
    """
    @brief Convert a POSIX timestamp to isoformat string

    @param timestamp \c float or \c integer timestamp

    @returns standard iso formatted datestring
    """

    return datetime.datetime.utcfromtimestamp(timestamp).isoformat('T')

def isoFormatToTimestamp(isoString):
    """
    @brief Convert a standard isoformatted time string to a timestamp

    @param isoString \c string

    @retval timestamp \c float or \c integer POSIX timestamp
    """

    ##This feels like a pile of crap...is there a more artful way here?
    try:
        datetimeobj=datetime.datetime.strptime(isoString.strip(),'%Y-%m-%dT%H:%M:%S')
        timestamp = calendar.timegm(datetimeobj.utctimetuple())
        #timetuple objects only have resolution to 1 second, while
        #datetime objects contain microsecond resolution
        #converting to a timetuple just truncates the microseconds
        #simply add them back in the the timestamp
        timestamp += (datetimeobj.microsecond)/1000000.0
    except:
        timestamp=None

    if timestamp is None:
        try:
            datetimeobj=datetime.datetime.strptime(isoString.strip(),'%Y-%m-%dT%H:%M:%S.%f')
            timestamp = calendar.timegm(datetimeobj.utctimetuple()) + (datetimeobj.microsecond)/1000000.0
        except:
            timestamp=None
    if timestamp is None:
        try:
            timestamp = otherStrFormatToTimestamp(isoString)
        except:
            #throw last exception again
            raise
    return timestamp

def otherStrFormatToTimestamp(inString):
    """
    @brief Attempt conversion of timestring with undetermined formatting

    @param inString \c string

    @retval timestamp \c float or \c integer POSIX timestamp
    """

    datetimeobj=parse(inString)
    #timetuple objects only have resolution to 1 second, while
    #datetime objects contain microsecond resolution
    #converting to a timetuple just truncates the microseconds
    #simply add them back in the the timestamp
    return calendar.timegm(datetimeobj.utctimetuple())+(datetimeobj.microsecond)/1000000.0

def getSecondsPastMidnight(timestamp):
    dt=datetime.datetime.utcfromtimestamp(timestamp)
    return dt.hour*3600+dt.minute*60+dt.second+dt.microsecond/1000000.0
