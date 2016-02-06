import logging
import scipy
from scipy.optimize import curve_fit

try:
    import matplotlib
    import matplotlib.pyplot as pyplot
    matplotlib.rc('font', **{'family': 'sans-serif', 'sans-serif': 'Arial', 'weight': 'normal', 'size': 10})
    matplotlib.rc('figure', **{'dpi': 150, 'facecolor': 'white', 'edgecolor': 'white'})
except ImportError:
    logging.warning('No matplotlib available. May cause errors if proceeding carelessly.')


from baaHelperMethods import validateDirectory, makeCalibrationSpline, resolutionEnergyFunction
from baaAnomalyMethods import AveragingTransform


#######################################################################################################################
#  Begin Peak Fitting Methods  #
################################

def fitSetup(pk, resFunc, pkloc=(None, None)):
    """
    Helper function for peak fitting setup.
    """

    resolutionInChannels = resFunc(pk)
    if (pkloc[0] is not None) and (pkloc[1] is not None):
        fitChannelRange = [max(3.*resolutionInChannels, scipy.absolute(pk - pkloc[0]), scipy.absolute(pk - pkloc[1])), ]
    else:
        fitChannelRange = [3.*resolutionInChannels, ]
    return resolutionInChannels, fitChannelRange


def functionalForm1(x, mu, sig, area, slope, constant):
    return slope*x + constant + area*scipy.exp(-0.5*((x - mu)/sig)**2)/(sig*scipy.sqrt(2*scipy.pi))


def functionalForm2(x, mu0, sig0, area0, mu1, sig1, area1, slope, constant):
    linearTerm = slope*x + constant
    gaussian1 = area0*scipy.exp(-0.5*((x - mu0)/sig0)**2)/(sig0*scipy.sqrt(2*scipy.pi))
    gaussian2 = area1*scipy.exp(-0.5*((x - mu1)/sig1)**2)/(sig1*scipy.sqrt(2*scipy.pi))
    return linearTerm + gaussian1 + gaussian2


def fitPeak(spectrum, fitChannelRange, sig0, mu0):
    # get prelimary values
    channelLow = int(max(mu0 - fitChannelRange[0], 0))
    # exclude the overflow, just in case
    channelHigh = int(min(mu0 + fitChannelRange[0] + 1, spectrum.size - 1))
    # make our channel array
    x = scipy.arange(channelLow, channelHigh)
    # get corresponding values
    y = spectrum[channelLow: channelHigh]
    # set up array for use as standard deviation
    y1 = scipy.copy(y)
    y1[y1 == 0] = 1

    # determine initial constant term guess
    constant0 = 0.0*scipy.mean(y)
    # determine initial area guess
    area0 = float(scipy.sum(y)) - constant0*(channelHigh - channelLow)

    try:
        # try to find the real values
        parameterValues, covarianceEstimate = curve_fit(functionalForm1,
                                                        x,
                                                        y,
                                                        p0=(mu0, sig0, area0, 0., constant0),
                                                        sigma=scipy.sqrt(y1),
                                                        absolute_sigma=True
                                                        )
        
        
        return parameterValues, covarianceEstimate, channelLow, channelHigh
    except Exception:
        return None, None, None, None


def fitTwoPeaks(spectrum, fitChannelRange, sig0, mu0, sig1, mu1):
    # get prelimary values
    channelLow = int(max(mu0 - fitChannelRange[0], 0))
    # exclude the overflow, just in case
    channelHigh = int(min(mu1 + fitChannelRange[0] + 1, spectrum.size - 1))
    # make our channel array
    x = scipy.arange(channelLow, channelHigh)
    # get corresponding values
    y = spectrum[channelLow: channelHigh]
    # set up array for use as standard deviation
    y1 = scipy.copy(y)
    y1[y1 == 0] = 1

    # determine initial constant term guess
    constant0 = 0.0*scipy.mean(y)
    # determine initial area guess
    areaCombined = float(scipy.sum(y)) - constant0*(channelHigh - channelLow)
    # begin by assuming that the area is equally split between the two peaks
    # this is really just intended for use with Co-60. Any other use may require
    # something more robust than this...

    try:
        # try to find the real values
        parameterValues, covarianceEstimate = curve_fit(functionalForm2,
                                                        x,
                                                        y,
                                                        p0=(mu0, sig0, 0.5*areaCombined,
                                                            mu1, sig1, 0.5*areaCombined,
                                                            0., constant0),
                                                        sigma=scipy.sqrt(y1),
                                                        absolute_sigma=True)
        return parameterValues, covarianceEstimate, channelLow, channelHigh
    except Exception:
        return None, None, None, None


def makeFitPlot(spec, results, tit, outPlot, numChannels=512):
    if pyplot is not None:
        chs = scipy.arange(spec.size)
        fig, axs = pyplot.subplots(nrows=2, ncols=1, figsize=(6, 6))
        if tit is not None:
            axs[0].set_title(tit)
        axs[0].semilogy(chs, spec, 'k')
        axs[1].plot(chs, spec, 'k')

        for result in results:
            en, typ, par, pcov, chlow, chhigh = result
            if par is not None:
                if typ == 1:
                    y1 = functionalForm1(chs[chlow:chhigh], *par)
                    y2 = scipy.maximum(par[3]*chs[chlow:chhigh] + par[4], 1.001)
                elif typ == 2:
                    y1 = functionalForm2(chs[chlow:chhigh], *par)
                    y2 = scipy.maximum(par[6]*chs[chlow:chhigh] + par[7], 1.001)
                axs[0].fill_between(chs[chlow:chhigh], y1, y2, where=(y1 >= y2), facecolor='blue', alpha=0.5)
                axs[1].fill_between(chs[chlow:chhigh], y1, y2, where=(y1 >= y2), facecolor='blue', alpha=0.5)

        axs[0].set_xlim(0, numChannels)
        axs[1].set_xlim(0, numChannels)
        validateDirectory(outPlot)
        pyplot.tight_layout()
        fig.savefig(outPlot)
        pyplot.close(fig)


##############################
#  End Peak Fitting Methods  #
#######################################################################################################################


#######################################################################################################################
#  Begin Peak Finding Methods  #
################################

class PeakFinder(object):
    def __init__(self, binEnergies=None, characterizeInitial=None, resCoeffs=[3.0, 0.5, 0.001], numChannels=512):

        channelMapping = scipy.arange(numChannels, dtype=scipy.float64)  # the identity map...kind of dumb. meh.
        outputMapping = [scipy.arange(numChannels, dtype=scipy.float64), ]  # the identity map...kind of dumb. meh.
        if binEnergies is None:
            # create basic estimate for binEnergies
            binEnergies = makeCalibrationSpline(characterizeInitial['energy'], characterizeInitial['channel'])(channelMapping)
            binEnergies[binEnergies < 0.] = 0.
        # create appropriate resolution scale in "channel space"
        res = scipy.cast[scipy.float64](resolutionEnergyFunction(binEnergies, coeffs=resCoeffs))  # resolution in energy space, so divide by "slope"
        slope = scipy.zeros(binEnergies.shape, dtype=scipy.float64)
        slope[:-1] = (binEnergies[1:] - binEnergies[:-1])  # keV / channel
        slope[-1] = slope[-2]
        slope[slope < 0.1] = 0.1  # avoid zero...
        self.scales = res/slope
        scales = [self.scales, ]
        self.transform_0 = AveragingTransform(channelMapping, outputMapping, scales, kernelName='gauss',
                                              channelLimits=[3, numChannels - 5], normalizeKernel=1)
        self.transform_1 = AveragingTransform(channelMapping, outputMapping, scales, kernelName='gauss1',
                                              channelLimits=[3, numChannels - 5], normalizeKernel=1)
        self.transform_2 = AveragingTransform(channelMapping, outputMapping, scales, kernelName='gauss2',
                                              channelLimits=[3, numChannels - 5], normalizeKernel=1)

    def findProspectivePeaks(self, spectrum, beginChannel, endChannel):
        beginChannel = int(beginChannel)
        endChannel = int(endChannel)
        gaussMean = self.transform_0.computeTransform(spectrum)
        gauss1, var1 = self.transform_1.computeTransforms(spectrum)
        gauss2, var2 = self.transform_2.computeTransforms(spectrum)

        gaussFirstDerivative = gauss1/scipy.maximum(scipy.sqrt(var1), self.transform_1.getMinimumStDev())
        gaussSecondDerivative = gauss2/scipy.maximum(scipy.sqrt(var2), self.transform_2.getMinimumStDev())

        multiple1 = 0.12  # empirically determined to be generally safe through some simple test cases
        multiple2 = 0.08  # empirically determined to be generally safe through some simple test cases

        thresh1 = scipy.maximum(multiple1*scipy.sqrt(gaussMean), 3.)
        thresh2 = scipy.maximum(multiple2*scipy.sqrt(gaussMean), 3.)

        peakLocations = []
        deltaPeakLocations = []
        deltaPeakWidths = []

        # Check for positive first derivative, followed by negative first derivative
        # AND
        # check for sufficiently positive second derivative near peak location
        #  - Zero crossing for first derivative is the likely peak location
        #  - Zero crossings of second derivative on each side of potential peak location provide likely peak bounds
        #  - Peak width can be bounded above by [1/4](the width)^2

        # First, find prospective peak locations
        prospectivePeaks = []
        peakBeg = False
        for i in xrange(beginChannel, endChannel):
            if gaussFirstDerivative[i] > thresh1[i]:  # sufficiently steep first derivative
                peakBeg = True
            if (gaussFirstDerivative[i] < 0.) and peakBeg:
                prospectivePeaks.append(i)
                peakBeg = False

        # Circle back and verify these via the second derivative
        for el in prospectivePeaks:
            bound1 = max(int(scipy.ceil(3.*self.scales[el])), 3)  # empirically determined
            derivative1Good = False
            derivative2Good = False

            bound2 = max(int(scipy.ceil(3.*self.scales[el])), 2)  # empirically determined
            curvatureGood = False

            # check that the first derivative goes from sufficiently positive to sufficiently negative in bound1
            for i in xrange(bound1):
                ch1 = el - i
                ch2 = el + i + 1
                if (ch1 >= 0) and (gaussFirstDerivative[ch1] > thresh1[ch1]):
                    derivative1Good = True
                if (ch2 < gaussFirstDerivative.size) and (gaussFirstDerivative[ch2] < -thresh1[ch2]):
                    derivative2Good = True
            # check that the curvature is sufficiently positive in bound2
            for i in xrange(bound2):
                ch1 = el - i
                ch2 = el + i + 1
                if (ch1 >= 0) and (gaussSecondDerivative[ch1] > thresh2[ch1]):
                    curvatureGood = True
                    break
                if (ch2 < gaussSecondDerivative.size) and (gaussSecondDerivative[ch2] > thresh2[ch2]):
                    curvatureGood = True
                    break
            if derivative1Good and derivative2Good and curvatureGood:
                # find zero crossing of fd, note that el is the first negative one
                v1 = gaussFirstDerivative[el - 1]
                v2 = gaussFirstDerivative[el]
                zLoc = float(el) - v2/(v2 - v1)
                peakLocations.append(zLoc)

                # find zero crossings of sd
                c1 = None
                c2 = None
                for i in xrange(bound2):
                    ch1 = el - i
                    ch2 = el + i
                    if (c1 is None) and (ch1 < gaussSecondDerivative.size) and (ch1 >= 0) and (gaussSecondDerivative[ch1] <= 0.):
                        c1 = float(ch1) - gaussSecondDerivative[ch1]/(gaussSecondDerivative[ch1 + 1] - gaussSecondDerivative[ch1])
                    if (c2 is None) and (ch2 < gaussSecondDerivative.size) and (ch2 >= 0) and (gaussSecondDerivative[ch2] <= 0.):
                        c2 = float(ch2) - gaussSecondDerivative[ch2]/(gaussSecondDerivative[ch2 - 1] - gaussSecondDerivative[ch2])
                if (c1 is not None) or (c2 is not None):
                    if c1 is None:
                        c1 = max(0, el - bound2)
                    if c2 is None:
                        c2 = min(spectrum.size, el + bound2)
                    deltaPeakLocations.append((c1, c2))
                    if (c1 is not None) and (c2 is not None):
                        deltaPeakWidths.append(0.25*(c2 - c1)**2)
                    else:
                        deltaPeakWidths.append(None)
                else:
                    deltaPeakLocations.append((None, None))
                    deltaPeakWidths.append(None)
        return peakLocations, deltaPeakLocations, deltaPeakWidths


##############################
#  End Peak Finding Methods  #
#######################################################################################################################


#######################################################################################################################
#  Begin Peak Tracking Methods  #
#################################


class Peak(object):
    """
    Holds peak info
    """

    def __init__(self,
                 location=scipy.nan,
                 width=scipy.nan,
                 area=scipy.nan,
                 locationUncertainty=scipy.nan,
                 widthUncertainty=scipy.nan,
                 areaUncertainty=scipy.nan):

        self.location = location
        self.width = width
        self.area = area
        self.locationUncertainty = locationUncertainty
        self.widthUncertainty = widthUncertainty
        self.areaUncertainty = areaUncertainty
        self.peakSize = self.area
        self.peakSizeUncertainty = self.areaUncertainty
        self.fwhm = None

    def fwhmIn(self, bounds):
        fhwm = 235.48*self.width/self.location if self.fwhm is None else self.fwhm
        return bounds[0] <= fhwm <= bounds[1]

    def locationIn(self, bounds):
        return bounds[0] <= self.location <= bounds[1]

    def sizeIn(self, bounds):
        return bounds[0] <= self.peakSize <= bounds[1]

    def _setDuration(self, duration):
        self.peakSize = self.area/duration
        self.peakSizeUncertainty = self.areaUncertainty/duration

    def __repr__(self):
        return '<Peak({!r})>'.format(vars(self))


class FindPeakResult(object):

    """
    Holds the result of a peak search
        'Success':SUCCESS_ENUM value,
        'Bounds':bounds where we looked for the peak,
        'PeaksFound':number of total peaks found in our bounds,
        'ClosePeak':boolean for any peaks 'close' to our presumed peak,
        'PeakMoved':boolean for whether the peak has moved appreciably
                    from the previous location,
        'LargestPeak':boolean for whether our peak is the largest peak
                      in the bounds,
        'WidthChanged':boolean for whether the peak has appreciably
                       changed width,
    """

    def __init__(self,
                 status=None,
                 bounds=None,
                 peaksFound=0,
                 closePeak=False,
                 peakMoved=False,
                 largestPeak=False,
                 widthChanged=False,
                 peak=None,
                 startTime=0,
                 endTime=0,
                 duration=0.0):

        self.status = status
        self.bounds = bounds
        self.peaksFound = peaksFound
        self.closePeak = closePeak
        self.peakMoved = peakMoved
        self.largestPeak = largestPeak
        self.widthChanged = widthChanged
        self._peak = peak
        self.startTime = startTime
        self.endTime = endTime
        self.duration = duration

    @property
    def peak(self):
        return self._peak

    @peak.setter
    def peak(self, peak):
        self._peak = peak
        peak._setDuration(self.duration)

    def __repr__(self):
        return '<FindPeakResult({!r})>'.format(vars(self))


def findOurPeak(spec,
                resFunc,
                peakFinder,
                lastLoc=None,
                lastWidth=None,
                deltaThreshold=1.0,
                bounds=[140., 400.],
                duration=0.0,
                startTime=0,
                endTime=0):
    """
    Function for finding our desired peak. The above functions all feed this peak.

    Args:
        spec - numpy array of the spectrum
        resFunc - function for the (approximate) resolution of the detector (in channels)
        peakFinder - a PeakFinder instance, appropriate for this detector
        lastLoc - last location for the peak, or None
        lastWidth - last width of the peak, or None
        deltaThreshold - threshold for when the peak moving is significant,
                         relative to the width of the peak, i.e. a value of 1.0
                         means that the peak being found one width away the
                         \p lastLoc is significant
        bounds - list of the form [channel lower bound, channel upper bound]
                 inside which to look for the peak
        duration - The duration of the spectrum
        startTime - The start time
        endTime - The end time

    Returns:
        FindPeakResult
    """

    def findClosePeaks(resFunc, peakList, theIndex):
        if len(peakList) == 1:
            return False, -1.
        else:
            myPeak = peakList[theIndex]
            sig = resFunc(myPeak.location)
            distanceLimit = 8.  # standard deviations
        for i, pk in enumerate(peakList):
            if (i != theIndex):
                distance = scipy.absolute(myPeak.location - pk.location)/sig
                if (distance < distanceLimit) and (pk.area > 0.3*myPeak.area):
                    return True, distance
        return False, 0.

    result = FindPeakResult(status='PEAK_NOT_FOUND',
                            bounds=bounds,
                            duration=duration,
                            startTime=startTime,
                            endTime=endTime)

    # First, find all the peaks within the bounds
    peakLocs, deltaPeakLocs, deltaPeakWidths = peakFinder.findProspectivePeaks(spec, bounds[0], bounds[1])

    

    # Now, fit the peaks
    fittedPeaks = []

    for pk, pkloc in zip(peakLocs, deltaPeakLocs):
        resolutionInChannels, fitChannelRange = fitSetup(pk, resFunc, pkloc)
        parameterValues, covarianceEstimate, channelLow, channelHigh = fitPeak(spec,
                                                                                   fitChannelRange,
                                                                                   resolutionInChannels,
                                                                                   pk)
        
        if parameterValues is not None:
            prospPeak = Peak(location=parameterValues[0],
                             width=parameterValues[1],
                             area=parameterValues[2],
                             locationUncertainty=scipy.sqrt(covarianceEstimate[0][0]),
                             widthUncertainty=scipy.sqrt(covarianceEstimate[1][1]),
                             areaUncertainty=scipy.sqrt(covarianceEstimate[2][2]))
            
            # require that the result is meaningful
            if (prospPeak.width > 0.) and (prospPeak.area > 0.) and \
                    scipy.isreal(prospPeak.locationUncertainty) and \
                    scipy.isreal(prospPeak.widthUncertainty) and \
                    scipy.isreal(prospPeak.areaUncertainty):
                prospPeak._setDuration(duration)
                fittedPeaks.append(prospPeak)


    result.peaksFound = len(fittedPeaks)
    # sort list in descending order based on area
    areaPeaks = sorted(fittedPeaks, key=lambda x: x.area, reverse=True)

    if result.peaksFound < 1:  # No peaks found!
        return result
    elif lastLoc is None:
        # use the largest peak found
        fittedPeaks = sorted(fittedPeaks, key=lambda x: x.area, reverse=True)
        # Are there any other close peaks?
        closePeak, pkDist = findClosePeaks(resFunc, areaPeaks, 0)
        if not closePeak:  # assume that we are good to go!
            result.status = 'OK'
            result.largestPeak = True
            result.peak = areaPeaks[0]
        else:
            result.status = 'INDETERMINATE_PEAKS'
            result.largestPeak = False
            result.peak = Peak()
        return result
    else:
        if lastWidth is None:
            noWidth = True
            lastWidth = resFunc(lastLoc)
        else:
            noWidth = False

        # sort list in ascending order based on distance from previous location
        locationPeaks = sorted(fittedPeaks, key=lambda x: scipy.absolute(x.location - lastLoc))

        # try to use the closest peak to the previous location
        pk = locationPeaks[0]
        # has the peak moved appreciably?
        peakMoved = (scipy.absolute(pk.location - lastLoc) > deltaThreshold*resFunc(lastLoc))
        # has the width changed appreciably?
        widthChanged = (scipy.absolute(pk.width - lastWidth) > 0.3*resFunc(lastLoc))
        # is this the largest peak
        largestPeak = (pk.area >= areaPeaks[0].area)
        # are there any other peaks close?
        closePeak, peakDistance = findClosePeaks(resFunc, locationPeaks, 0)

        result.peakMoved = peakMoved
        result.widthChanged = widthChanged
        result.largestPeak = largestPeak
        result.closePeak = closePeak

        if not peakMoved and not widthChanged and largestPeak:
            result.peak = pk
            result.status = 'OK'
        elif not peakMoved and not widthChanged and not largestPeak:
            if peakDistance > 6.:  # assume good to go...
                result.peak = pk
                result.status = 'OK'
            else:
                # no faith
                result.peak = Peak()
                result.status = 'INDETERMINATE_PEAKS'
        elif not peakMoved and widthChanged and largestPeak:
            # assume good to go in this case
            result.peak = pk
            result.status = 'OK'
        elif not peakMoved and widthChanged and not largestPeak:
            if closePeak:
                # no faith
                result.peak = Peak()
                result.status = 'INDETERMINATE_PEAKS'
            else:
                # assume good to go in this case
                result.peak = pk
                result.status = 'OK'
        elif peakMoved and not widthChanged and largestPeak:
            # assume good
            result.peak = pk
            result.status = 'OK'
        elif peakMoved and not widthChanged and not largestPeak:
            # no faith
            result.peak = Peak()
            result.status = 'INDETERMINATE_PEAKS'
        elif peakMoved and widthChanged:
            if len(locationPeaks) == 1:
                # assume good, what can we do?
                result.peak = pk
                result.status = 'OK'
            else:
                # no faith
                result.peak = Peak()
                result.status = 'INDETERMINATE_PEAKS'
        return result

