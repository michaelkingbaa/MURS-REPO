import logging
import time

import scipy

from baaHelperMethods import expandSpectrum, makeCalibrationSpline, resolutionChannelsFunction
from baaPeakMethods import Peak, PeakFinder, FindPeakResult, findOurPeak
from mursPeakSettings import DEFAULT_CHARACTERIZATION
from mursPeakSettings import DEFAULT_SETTINGS


class Calibration(object):
    """
    This should just be temporary, while the actual MURS structure comes into existence
    """
    def __init__(self,
                 sensorId,
                 status,
                 startTime,
                 endTime,
                 referenceEnergy,
                 referenceChannel=None,
                 referenceChannelUncertainty=None,
                 binEnergies=None,
                 sumSpectrum=None,
                 integrationTime=None,
                 peak=None):

        self.sensorId = sensorId
        self.status = status
        self.startTime = startTime
        self.endTime = endTime
        self.referenceEnergy = referenceEnergy
        self.referenceChannel = referenceChannel
        self.referenceChannelUncertainty = referenceChannelUncertainty
        self.binEnergies = binEnergies
        self.sumSpectrum = sumSpectrum
        self.integrationTime = integrationTime
        self.peak = peak


class PeakTracker:
    """
    Class intended to locate/track a given NORM peak channel location in a gamma
    spectrum. The mostly likely application for normal circumstances is the
    1460 keV peak from K-40, since this is the most reliably present and large
    enough for the use in question. Note that a few non-NORM sources can interfere
    with this process.
    """

    def __init__(self,
                 handler,
                 sensorId,  # presumed a string
                 makeBinEnergies=False,
                 spectralChannels=1024,
                 sensorCharacterization=None,   # dictionary of appropriate format
                 ):

        # init members
        self.handler = handler
        # must have a publish()
        self.sensorId = sensorId
        if sensorCharacterization is None:
            self.characterization = DEFAULT_CHARACTERIZATION
            logging.info('Using the default characterization for sensor {}'.format(self.sensorId))
        else:
            self.characterization = sensorCharacterization
        self.idString = '6bdde6ad-9557-938b-0301-23f486fe35ac'
        self.spectralChannels = spectralChannels

        self.makeBinEnergies = makeBinEnergies

        for key in ['nominalRange', 'integrationLimit', 'peakBounds', 'badPeakBounds', 'countRange',
                    'widthBounds', 'badWidthBounds', 'peakSizeBounds', 'referenceEnergy', 'messageAge']:
            setattr(self, key, DEFAULT_SETTINGS[key])
        self.lastTime = None
        self.lastPeakLocation = None
        self.lastPeakWidth = None
        self.integrationLimitLow = self.integrationLimit * .5
        self.integrationLimitHigh = self.integrationLimit * 2.
        self.searchBounds = [[None, None], self.peakBounds, self.badPeakBounds]

        channels = self.characterization['channel']
        energies = self.characterization['energy']
        resolutionCoefficients = self.characterization['resolution_coefficients']

        self.resolutionFunction = resolutionChannelsFunction(energies, channels, coeffs=resolutionCoefficients)
        binEnergies = makeCalibrationSpline(energies, channels)(scipy.arange(self.spectralChannels))
        binEnergies[binEnergies < 0] = 0.
        self.peakFinder = PeakFinder(binEnergies=binEnergies,
                                     resCoeffs=resolutionCoefficients,
                                     numChannels=self.spectralChannels)
        self.initializeSpectrum()  # get ready
        logging.info('Initialized Peak Tracking for {}'.format(self.sensorId))

    def initializeSpectrum(self, beginTime=None, spectrum=None, realTime=None):
        """
        Helper function for reinitialization
        """

        self.spectrum = scipy.zeros((self.spectralChannels,), dtype=scipy.float64)
        self.totalTime = 0.
        self.beginTime = beginTime
        if (spectrum is not None) and (realTime is not None):
            self.spectrum += spectrum
            self.totalTime += realTime

    def publishResult(self, resOut):
        # TODO: replace the hand-jammed Calibration() object with the appropriate MURS messaging objects
        if resOut is None:
            # nothing to do
            return

        # Construct the calibration details object
        calibration = Calibration(self.sensorId,
                                  resOut.status,
                                  resOut.startTime,
                                  resOut.endTime,
                                  self.referenceEnergy,
                                  sumSpectrum=self.spectrum,
                                  integrationTime=self.totalTime,
                                  peak=resOut.peak)

        peak = resOut.peak
        if (peak is None) or scipy.isnan(peak.location) or scipy.isnan(peak.locationUncertainty):
            # this should be redundant
            calibration.referenceChannel = None
            calibration.referenceChannelUncertainty = None
            calibration.binEnergies = None
        else:
            calibration.referenceChannel = peak.location
            calibration.referenceChannelUncertainty = peak.locationUncertainty
            if self.makeBinEnergies:
                # get the characterization
                energies = self.characterization['energy']
                channels = self.characterization['channel']
                multiplier = peak.location/self.characterization['reference_channel']
                binEnergies = makeCalibrationSpline(energies, channels, multiplier=multiplier)(scipy.arange(self.spectralChannels))
                binEnergies[binEnergies < 0] = 0
                calibration.binEnergies = binEnergies
#        return calibration
        self.handler.publishMessage(calibration)

    def movementCheck(self, resOut):
        if self.lastPeakLocation is None:
            return

        peak = resOut.peak
        locationMovement = scipy.absolute(peak.location - self.lastPeakLocation)
        if locationMovement > 1.:
            # the peak has moved...
            logging.warn('Times - {0!s}<{1!s}, Detector - {2!s}, '\
                         'Discovered peak has moved farther than expected {3!s} -> {4!s}!'.format(resOut.startTime,
                                                                                            resOut.endTime,
                                                                                            self.sensorId,
                                                                                            self.lastPeakLocation,
                                                                                            resOut.peak.location))

        # TODO: publish the appropriate message if this is bad

        # TODO: Possibly surpress the result if you don't like this?

    def locationCheck(self, resOut):
        peak = resOut.peak
        if (peak is None) or scipy.isnan(peak.location):
            logging.error('Peak finding failure, Times {0!s}<{1!s}, Detector - {2!s}'.format(resOut.startTime,
                                                                                             resOut.endTime,
                                                                                             self.sensorId))
            # TODO: publish the appropriate message if this is bad
        elif peak.locationIn(self.badPeakBounds) and not peak.locationIn(self.peakBounds):
            # the peak location is out of bounds
            logging.warn('Times - {0!s}<{1!s}, Detector - {2!s}, '\
                         'Discovered location {3:0.3f} is out of '\
                         'acceptable bounds!'.format(resOut.startTime,
                                                     resOut.endTime,
                                                     self.sensorId,
                                                     resOut.peak.location))
            # TODO: publish the appropriate message if this is bad

    def widthCheck(self, resOut):
        peak = resOut.peak
        if not peak.fwhmIn(self.widthBounds):
            logging.warn('Times - {0!s}<{1!s}, Detector - {2!s}, '\
                         'Discovered peak width is out of '\
                         'acceptable bounds!'.format(resOut.startTime,
                                                     resOut.endTime,
                                                     self.sensorId))

    def processMessage(self, timeIn, realTime, thisSpectrum, messageId=None):
        """
        Stub for messaging input
        """

        # Fish out the inputs required for processSpectrum()
        #timeIn = None
        #realTime = None
        #thisSpectrum = None

        self.processSpectrum(timeIn, realTime, thisSpectrum)

    def processSpectrum(self, timeIn, realTime, thisSpectrum):
        """
        Method which processes the peak finding effort
        """

        if self.beginTime is None:
            self.beginTime = timeIn

        if (self.lastTime is not None) and (timeIn - self.lastTime > self.messageAge):
            # this is too large a gap between messages, so reset
            logging.warn('Large gap ({} -> {}) for sensor {}. Resetting.'.format(self.lastTime,
                                                                                 timeIn,
                                                                                 self.sensorId))
            resOut = FindPeakResult(startTime=self.beginTime,
                                    endTime=timeIn,
                                    duration=self.totalTime,
                                    status='MESSAGE_GAP')
            # Re-initialize the effort
            self.publishResult(resOut)
            self.initializeSpectrum(beginTime=timeIn, spectrum=thisSpectrum, realTime=realTime)
            self.lastTime = timeIn
            return
        else:
            self.lastTime = timeIn

        windowLength = timeIn - self.beginTime
        if windowLength < self.integrationLimit:
            self.spectrum += thisSpectrum
            self.totalTime += realTime
            # keep trucking!
            return

        if self.totalTime < self.integrationLimitLow:
            if windowLength > self.integrationLimitHigh:
                # not enough data, and too much is missing; just return junk message and reset
                resOut = FindPeakResult(startTime=self.beginTime,
                                        endTime=timeIn,
                                        duration=self.totalTime,
                                        status='NOT_ENOUGH_DATA')
                self.publishResult(resOut)
                self.initializeSpectrum(beginTime=timeIn, spectrum=thisSpectrum, realTime=realTime)
                return
            else:
                # not quite enough data, but not too many holes
                self.spectrum += thisSpectrum
                self.totalTime += realTime
                # TODO: what should I do here?
                return

        # we have enough data, so proceed
        countRate = scipy.sum(self.spectrum) / float(self.totalTime)
        if (countRate < self.countRange[0]):
            # too low of count rate, just start over
            logging.warn('Times - {0!s}<{1!s}, Detector - {2!s}, '\
                         'Count Rate Too Low {3:0.4f} < {4:0.4f}'.format(self.beginTime,
                                                                         timeIn,
                                                                         self.sensorId,
                                                                         countRate,
                                                                         self.countRange[0]))
            resOut = FindPeakResult(startTime=self.beginTime,
                                    endTime=timeIn,
                                    duration=self.totalTime,
                                    status='COUNT_RATE_OUT_OF_BOUNDS')
            # Re-initialize the effort
            self.publishResult(resOut)
            self.initializeSpectrum(beginTime=timeIn, spectrum=thisSpectrum, realTime=realTime)
            return
        elif countRate > self.countRange[1]:
            # too high of count rate, just start over
            logging.warn('Times - {0!s}<{1!s}, Detector - {2!s}, '\
                         'Count Rate Too High {3:0.4f} > {4:0.4f}'.format(self.beginTime,
                                                                          timeIn,
                                                                          self.sensorId,
                                                                          countRate,
                                                                          self.countRange[1]))
            resOut = FindPeakResult(startTime=self.beginTime,
                                    endTime=timeIn,
                                    duration=self.totalTime,
                                    status='COUNT_RATE_OUT_OF_BOUNDS')
            # Re-initialize the effort
            self.publishResult(resOut)
            self.initializeSpectrum(beginTime=timeIn, spectrum=thisSpectrum, realTime=realTime)
            return

        # The count rate is appropriate, try finding and fitting the peak
        resOut = None
        if self.lastPeakLocation is not None:
            # try a reasonable range from the last location
            eWidth = self.resolutionFunction(self.lastPeakLocation)
            self.searchBounds[0][0] = max(self.lastPeakLocation - self.nominalRange*eWidth, 0)
            self.searchBounds[0][1] = min(self.lastPeakLocation + self.nominalRange*eWidth, 505)
        else:
            self.searchBounds[0][0] = None
            self.searchBounds[0][1] = None

        for bounds in self.searchBounds:
            if bounds[0] is not None and bounds[1] is not None:
                resOut = findOurPeak(self.spectrum,
                                     self.resolutionFunction,
                                     self.peakFinder,
                                     lastLoc=self.lastPeakLocation,
                                     lastWidth=self.lastPeakWidth,
                                     deltaThreshold=1.0,
                                     bounds=bounds,
                                     duration=self.totalTime,
                                     startTime=self.beginTime,
                                     endTime=timeIn
                                     )

                # do we like this result?
                if (resOut is not None) and (resOut.peaksFound > 0) and resOut.peak.sizeIn(self.peakSizeBounds):
                    break

        if resOut is None:
            # the peak search crapped out, reinitialize and publish failure message
            resOut = FindPeakResult(status='PEAK_NOT_FOUND',
                                    duration=self.totalTime,
                                    startTime=self.beginTime,
                                    endTime=timeIn)
            self.publishResult(resOut)
            self.initializeSpectrum(beginTime=timeIn, spectrum=thisSpectrum, realTime=realTime)
            return
        elif resOut.status != 'OK':
            # the search results were unsatisfying, reinitialize and publish failure message
            self.publishResult(resOut)
            self.initializeSpectrum(beginTime=timeIn, spectrum=thisSpectrum, realTime=realTime)
            return
        # All other cases, we got a peak and it seems preliminarily OK
        logging.info('Times - {0!s}<{1!s}, Detector - {2!s}, '
                     'Discovered peak location {3:0.3f} +/- {4:0.3f}, '
                     'width {5:0.3f} +/-  {6:0.3f}, '
                     'area {7:0.3f} +/- {8:0.3f}'.format(resOut.startTime,
                                                         resOut.endTime,
                                                         self.sensorId,
                                                         resOut.peak.location,
                                                         resOut.peak.locationUncertainty,
                                                         resOut.peak.width,
                                                         resOut.peak.widthUncertainty,
                                                         resOut.peak.area,
                                                         resOut.peak.areaUncertainty))
        if not resOut.peak.sizeIn(self.peakSizeBounds):
            # peak count rate is determined to be unreasonable for any use
            resOut.status = 'PEAK_RATE_OUT_OF_BOUNDS'
            logging.error('Rejecting for {}, since peak rate out of bounds ({} not in {})'.format(self.sensorId,
                                                                                                  resOut.peak.peakSize,
                                                                                                  self.peakSizeBounds)
)
            resOut.peak = Peak()
            self.publishResult(resOut)
            self.initializeSpectrum(beginTime=timeIn, spectrum=thisSpectrum, realTime=realTime)
            return

        if not resOut.peak.fwhmIn(self.badWidthBounds):
            # peak width is determined to be unreasonable for any use
            logging.warn('Rejecting for {}, since width is out of feasible bounds'.format(self.sensorId))
            resOut.status = 'PEAK_WIDTH_OUT_OF_BOUNDS'
            resOut.peak = Peak()
            self.publishResult(resOut)
            self.initializeSpectrum(beginTime=timeIn, spectrum=thisSpectrum, realTime=realTime)
            return

        # everything is suitable for usage in making a legitimate sensor settings object
        self.publishResult(resOut)
        # Now, determine any appropriate fault status
        self.movementCheck(resOut)
        self.locationCheck(resOut)
        self.widthCheck(resOut)

        self.lastPeakLocation = resOut.peak.location
        self.lastPeakWidth = resOut.peak.width
        # Re-initialize the effort
        self.initializeSpectrum(beginTime=timeIn, spectrum=thisSpectrum, realTime=realTime)

