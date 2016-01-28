import logging
import scipy

import scipy.sparse
from scipy.integrate import quad
from scipy.stats import poisson

DEFAULT_COHERENT_BINS = scipy.array([0.0, 1.5, 3.0, 5.0, 7.0, 9.0, 11.0, 13.5,
                                     16.0, 18.5, 21.0, 23.5, 26.0, 29.0, 32.0, 35.0,
                                     38.0, 41.0, 44.0, 47.5, 51.0, 54.5, 58.0, 61.5,
                                     65.0, 69.0, 73.0, 77.0, 81.0, 85.0, 89.0, 93.0,
                                     97.0, 101.5, 106.0, 110.5, 115.0, 119.5, 124.0, 129.0,
                                     134.0, 139.0, 144.0, 149.0, 154.0, 159.0, 164.0, 169.5,
                                     175.0, 180.5, 186.0, 191.5, 197.0, 203.0, 209.0, 215.0,
                                     221.0, 227.0, 233.0, 239.0, 245.0, 251.5, 258.0, 264.5,
                                     271.0, 277.5, 284.0, 290.5, 297.0, 304.0, 311.0, 318.0,
                                     325.0, 332.0, 339.0, 346.0, 353.0, 360.5, 368.0, 375.5,
                                     383.0, 390.5, 398.0, 406.0, 414.0, 422.0, 430.0, 438.0,
                                     446.0, 454.0, 462.0, 470.5, 479.0, 487.5, 496.0, 504.5,
                                     513.0, 521.5, 530.0, 539.0, 548.0, 557.0, 566.0, 575.0,
                                     584.0, 593.5, 603.0, 612.5, 622.0, 631.5, 641.0, 650.5,
                                     660.0, 670.0, 680.0, 690.0, 700.0, 710.0, 720.0, 730.5,
                                     741.0, 751.5, 762.0, 772.5, 783.0, 793.5, 804.0, 815.0,
                                     826.0, 837.0, 848.0, 859.0, 870.0, 881.5, 893.0, 904.5,
                                     916.0, 927.5, 939.0, 951.0, 963.0, 975.0, 987.0, 999.0,
                                     1011.0, 1023.0, 1035.0, 1047.5, 1060.0, 1072.5, 1085.0, 1097.5,
                                     1110.0, 1123.0, 1136.0, 1149.0, 1162.0, 1175.0, 1188.0, 1201.5,
                                     1215.0, 1228.5, 1242.0, 1255.5, 1269.0, 1283.0, 1297.0, 1311.0,
                                     1325.0, 1339.0, 1353.0, 1367.5, 1382.0, 1396.5, 1411.0, 1425.5,
                                     1440.0, 1455.0, 1470.0, 1485.0, 1500.0, 1515.0, 1530.0, 1545.5,
                                     1561.0, 1576.5, 1592.0, 1607.5, 1623.0, 1639.0, 1655.0, 1671.0,
                                     1687.0, 1703.0, 1719.0, 1735.5, 1752.0, 1768.5, 1785.0, 1802.0,
                                     1819.0, 1836.0, 1853.0, 1870.0, 1887.0, 1904.5, 1922.0, 1939.5,
                                     1957.0, 1974.5, 1992.0, 2010.0, 2028.0, 2046.0, 2064.0, 2082.5,
                                     2101.0, 2119.5, 2138.0, 2156.5, 2175.0, 2194.0, 2213.0, 2232.0,
                                     2251.0, 2270.0, 2289.0, 2308.5, 2328.0, 2347.5, 2367.0, 2387.0,
                                     2407.0, 2427.0, 2447.0, 2467.5, 2488.0, 2508.5, 2529.0, 2549.5,
                                     2570.0, 2591.0, 2612.0, 2633.0, 2654.0, 2675.5, 2697.0, 2718.5,
                                     2740.0, 2762.0, 2784.0, 2806.0, 2828.0, 2850.0, 2872.0, 2894.0],
                                    dtype=scipy.float64)


#######################################################################################################################
#  Begin Buffering Methods  #
#############################


class SimpleBuffer:
    def __init__(self, shape, dtype=scipy.float64, calculateSums=None, recalculateFrequency=None):
        # intended for buffers containing floating point data
        try:
            self.recalculateFrequency = int(recalculateFrequency)
        except:
            self.recalculateFrequency = None

        self.dtype = dtype  # what scipy data type

        if calculateSums is None:
            self.calculateSums = None
            mandatoryLength = None
        else:
            self.calculateSums = scipy.copy(calculateSums)
            mandatoryLength = scipy.amax(self.calculateSums)

        if len(shape) == 1:
            self._length = shape[0]  # how many elements?
            self._size = 1
        elif len(shape) == 2:
            self._length = shape[0]
            self._size = shape[1]
        else:
            raise ValueError('A buffer for data of higher than one dimension is not permitted')

        if (mandatoryLength is not None) and (self._length < mandatoryLength):
            raise ValueError('Buffer length given as {0:d} but calculateSums has element '
                             '{0:d}'.format(self._length,mandatoryLength))

        self.initialize()  # initialization procedure

    def initialize(self):
        # note that _currentPosition always points to the NEXT spot,
        # typically the oldest measurement
        self._currentPosition = 0
        self._buffer = scipy.zeros((self._length, self._size), dtype=self.dtype)
        self._pushEvents = 0

        if self.calculateSums is not None:
            self._sums = []

            for el in self.calculateSums:
                self._sums.append(scipy.zeros((self._size, ), dtype=self.dtype))
        else:
            self._sums = None

    def recalculateSums(self, oldMeasurement):
        if self.calculateSums is None:
            return
        if self.isFull() and (self.recalculateFrequency is not None) and \
                ((self._pushEvents % self.recalculateFrequency) == 0):
            # it's time to scrap the sums...
            self._sums = []
            for el in self.calculateSums:
                newSum = scipy.zeros((self._size, ), dtype=self.dtype)
                absIndices = self._getAbsoluteIndices(scipy.arange(el))
                newSum[:] = scipy.sum(self._buffer[absIndices, :], axis=0)
                self._sums.append(newSum)
        else:
            for i, relIndex in enumerate(self.calculateSums):
                # the new element, just added is self.getElement(1)
                # the oldest is self.getElement(relIndex + 1)
                new = self.getElement(1, copy=False)
                if relIndex == self._length:
                    if oldMeasurement is None:
                        self._sums[i] += new
                    else:
                        self._sums[i] += (new - oldMeasurement)
                else:
                    old = self.getElement(relIndex + 1, copy=False)
                    if old is None:
                        self._sums[i] += new
                    else:
                        self._sums[i] += (new - old)

    def isFull(self):
        return (self._pushEvents >= self._length)

    def push(self, new):
        old = None
        if self.isFull():
            # replace the old value with the new, and return the old value
            old = scipy.copy(self._buffer[self._currentPosition])
            self._buffer[self._currentPosition] = new
        else:
            # nothing to replace, since we aren't yet full
            self._buffer[self._currentPosition] = new
        # increment the positioning
        self._pushEvents += 1
        self._currentPosition = ((self._currentPosition + 1) % self._length)
        # recalculate the sums, if necessary
        self.recalculateSums(old)
        return old

    def _getAbsoluteIndex(self, relativeIndex):
        if (self.isFull() and (relativeIndex > self._length)) or \
                (not self.isFull() and (relativeIndex > self._pushEvents)):
            # relativeIndex is too big
            return None
        else:
            return (((self._currentPosition - relativeIndex) + self._length) % self._length)

    def _getAbsoluteIndices(self, relativeIndices):
        if self.isFull():
            badIndices = (relativeIndices > self._length)
        else:
            badIndices = (relativeIndices > self._pushEvents)

        if scipy.any(badIndices):
            return None
        else:
            return ((self._currentPosition - relativeIndices + self._length) % self._length)

    def getElement(self, relativeIndex, copy=True):
        # relativeIndex is a reference to how many entries into the past
        absoluteIndex = self._getAbsoluteIndex(relativeIndex)

        if absoluteIndex is not None:
            if self._size > 1:
                if copy:
                    return scipy.copy(self._buffer[absoluteIndex, :])
                else:
                    return self._buffer[absoluteIndex, :]
            else:  # will be a primitive, no need to consider copying
                return self._buffer[absoluteIndex, 0]
        else:
            return None

    def getSum(self, index, copy=True):
        if self.calculateSums is None:
            raise ValueError("No sum is calculated")
        if index >= self.calculateSums.size:
            raise ValueError("Sum index out of bounds")

        if self._pushEvents > self.calculateSums[index]:
            if self._size > 1:
                if copy:
                    return scipy.copy(self._sums[index])
                else:
                    return self._sums[index]
            else:
                # will be a primitive, no need to copy
                return self._sums[index][0]
        else:
            return None


###########################
#  End Buffering Methods  #
######################################################################################################################

#######################################################################################################################
#  Begin Transform Methods  #
#############################


class BaseTransform(object):
    def __init__(self):
        raise NotImplementedError

    def setChannelMapping(self, channelMapping):
        """
        Set the interpretation for the bins for the incoming arrays - plays the role of setting the calibration
        """

        raise NotImplementedError

    def getChannelLimits(self):
        """
        Get the valid range of channels, this transform MUST respect this limit
        """

        return self.channelLimits

    def getTotalOutputChannels(self):
        """
        Get the total size of the output transform
        """

        return self.totalOutputChannels

    def getOutputChannels(self):
        """
        Get a list of arrays, corresponding to channels in the output array which correspond to the appropriate 'depth'
        """

        return self.outputChannels

    def getOverlapScale(self):
        """
        Cheap method for estimating correlation in output channels - ignore this unless you have a good reason
        """

        return self.scales

    def getOutputMapping(self):
        """
        Gets list of arrays providing the mapping for the output coordinates
        (i.e. interpretation in the mapped coordinates)
        """

        return self.outputMapping

    def getMinimumStDev(self):
        """
        Get the value to impose as the presumed minimum standard deviation for each element of the output transform
        """

        return self.minimumStDeviation

    def computeTransform(self, arr):
        """
        Transform the input array
        """

        raise NotImplementedError

    def computeVarianceTransform(self, arr):
        """
        Provide the transform which corresponds to the variance estimate
        """

        raise NotImplementedError

    def computeTransforms(self, arr):
        """
        Simply provides (transform, varianceTransform)
        """

        raise NotImplementedError


class BinStructureTransform(BaseTransform):
    """
    To transform the bin structure to a desired structure
    """
    def __init__(self, channelMapping, desiredRebinning, channelLimits=None):
        if channelLimits is None:
            self.channelLimits = [0, len(channelMapping)]
        else:
            self.channelLimits = [int(channelLimits[0]), int(channelLimits[1])]

        # Basically just for required inheritance, possibly not terribly useful for anything but a very specific purpose
        self.outputMapping = [scipy.copy(desiredRebinning), ]
        self.totalOutputChannels = self.outputMapping[0].size
        self.outputChannels = [scipy.arange(self.totalOutputChannels), ]
        self.scales = scipy.ones((self.totalOutputChannels, ))
        self.minimumStDeviation = scipy.ones((self.totalOutputChannels, ))
        self.setChannelMapping(channelMapping)

    def setChannelMapping(self, channelMapping):
        self.channelMapping = scipy.copy(channelMapping)
        self.inputChannelSize = self.channelMapping.size

        transValues = []
        inputChanValues = []
        outputChanValues = []

        curInputChannel = self.channelLimits[0]
        for outChan in xrange(self.totalOutputChannels-1):
            # determine channel energy range
            outEnergyBegin = self.outputMapping[0][outChan]
            outEnergyEnd = self.outputMapping[0][outChan+1]
            # determine appropriate multiplier for input channels
            try:
                if (outEnergyEnd < self.channelMapping[self.channelLimits[0]]):
                    pass
            except:
                print outEnergyEnd
                print self.channelLimits
                print self.channelMapping.shape
                # print self.channelMapping[self.channelLimits[0]]

            if (outEnergyEnd < self.channelMapping[self.channelLimits[0]]):
                # we haven't gotten to the usable part yet
                # there isn't really anything to do, just put a placeholder
                transValues.append(0.)
                inputChanValues.append(curInputChannel)
                outputChanValues.append(outChan)
            elif (curInputChannel >= self.inputChannelSize - 1):
                curInputChannel = self.inputChannelSize - 1
                # we ran out of channels
                transValues.append(0.)
                inputChanValues.append(self.inputChannelSize - 1)
                outputChanValues.append(outChan)
            elif (curInputChannel >= self.channelLimits[1] - 1):
                curInputChannel = self.channelLimits[1] - 1
                # we've gotten past the usable part
                transValues.append(0.)
                inputChanValues.append(curInputChannel)
                outputChanValues.append(outChan)
            else:
                cont = True
                while cont:
                    if curInputChannel == self.inputChannelSize - 1:
                        cont = False
                    # find our current channel's energy range
                    if (curInputChannel < self.inputChannelSize - 1):
                        currentEnergyBegin = self.channelMapping[curInputChannel]
                        currentEnergyEnd = self.channelMapping[curInputChannel + 1]
                        chanWidth = float(currentEnergyEnd - currentEnergyBegin)
                    else:
                        currentEnergyBegin = self.channelMapping[curInputChannel]
                        currentEnergyEnd = self.channelMapping[curInputChannel]
                        chanWidth = 1.0

                    if (currentEnergyBegin >= outEnergyBegin) and (currentEnergyEnd <= outEnergyEnd):
                        # our channel is completely contained in the range
                        transValues.append(1.)
                        inputChanValues.append(curInputChannel)
                        outputChanValues.append(outChan)
                        # increment, and keep going
                        curInputChannel += 1
                    elif (currentEnergyBegin < outEnergyBegin) and (currentEnergyEnd <= outEnergyEnd):
                        # our channel is too long on the front only
                        transValues.append(float(currentEnergyEnd - outEnergyBegin)/chanWidth)
                        inputChanValues.append(curInputChannel)
                        outputChanValues.append(outChan)
                        # increment, and keep going
                        curInputChannel += 1
                    elif (currentEnergyBegin >= outEnergyBegin) and (currentEnergyEnd > outEnergyEnd):
                        # our channel is too long on the rear only
                        transValues.append(float(outEnergyEnd - currentEnergyBegin)/chanWidth)
                        inputChanValues.append(curInputChannel)
                        outputChanValues.append(outChan)
                        # do not increment, and stop
                        cont = False
                    elif (currentEnergyBegin < outEnergyBegin) and (currentEnergyEnd > outEnergyEnd):
                        # our channel entirely contains the range
                        transValues.append(float(outEnergyEnd - outEnergyBegin)/chanWidth)
                        inputChanValues.append(curInputChannel)
                        outputChanValues.append(outChan)
                        # do not increment, and stop
                        cont = False
                    elif (currentEnergyEnd < outEnergyBegin):
                        # our channel is too low - just increment and continue
                        curInputChannel += 1
                    else:
                        cont = False
        else:
            # handle the last bit - i.e. overflow channels
            if curInputChannel < self.channelLimits[1] - 1:
                outChan = self.totalOutputChannels - 1
                if transValues[-1] < 1.:
                    transValues.append(1.0 - transValues[-1])
                    inputChanValues.append(curInputChannel)
                    outputChanValues.append(outChan)
                for j in xrange(curInputChannel+1, self.channelLimits[1]):
                    transValues.append(1.)
                    inputChanValues.append(j)
                    outputChanValues.append(outChan)

        matrixSize = (self.inputChannelSize, self.totalOutputChannels)
        rowArray = scipy.array(inputChanValues, dtype=scipy.uint16)
        colArray = scipy.array(outputChanValues, dtype=scipy.uint16)
        mat = scipy.sparse.coo_matrix((scipy.array(transValues, dtype=scipy.float64), (rowArray, colArray)), matrixSize)
        # Convert to compressed column format, for fast multiplication on the right
        self.matrix = mat.tocsc()

    def computeTransform(self, arr):
        if arr.shape[-1] != self.inputChannelSize:
            raise ValueError("Input spectra does not have final dimension of "
                             "the size specified by inputChannelSize")
        if len(arr.shape) == 2:
            return arr * self.matrix
        elif len(arr.shape) == 1:
            return (scipy.reshape(arr, (1, self.inputChannelSize)) * self.matrix).flatten()
        else:
            raise ValueError("Input with more than two dimensions cannot be transformed")

    def computeVarianceTransform(self, arr):
        return self.computeTransform(arr)

    def computeTransforms(self, arr):
        return self.computeTransform(arr), self.computeVarianceTransform(arr)


class RebinningTransform(BaseTransform):
    def __init__(self, channelMapping, initialRebin, depth=5, channelLimits=None):
        self._initialRebin = scipy.copy(initialRebin)  # rebinning in mapped (energy) space
        self.depth = depth
        self.actualDepth = None
        if channelLimits is None:
            # all valid by default, exclude nothing
            self.channelLimits = [0, channelMapping.size]
        else:
            self.channelLimits = channelLimits


        self.extendAtEnd = True  # use the remaining valid channels tacked on at the end of the initial transform

        self.scales = None
        self.channelMapping = None  # the "interpretation" of channels to the appropriate space (i.e. energy)
        self.firstBins = None  # helper variable
        self.subsequentBinning = None  # helper method
        self.outputMapping = None  # identifies the appropriate coordinates for the output
        self.outputChannels = None  # identifies the channels associated with each scale level
        self.totalOutputChannels = None  # how many element in the transformed coordinates
        self.minimumStDeviation = None

        self.setChannelMapping(channelMapping)
        self.inputChannelSize = self.channelMapping.size

    def setChannelMapping(self, channelMapping):
        self.channelMapping = scipy.copy(channelMapping)
        self.firstBins = []
        self.outputChannels = []

        mappedRanges = [[], ]
        cumulativeChannels = []
        scales = []

        # define our initial binning effort, just go in order
        # no overlapping permitted here
        firstChannel = self.channelLimits[0]
        for i in xrange(self._initialRebin.size - 1):
            beginCoordinate = self._initialRebin[i]
            endCoordinate = self._initialRebin[i + 1]
            # find appropriate channels in input spectrum
            if beginCoordinate < self.channelMapping[self.channelLimits[-1] - 1]:
                # this can possibly be achieved
                lastChannel = self.channelLimits[1]
                for j in xrange(firstChannel, self.channelLimits[1]-1):
                    nominalCoord = 0.5*(self.channelMapping[j] + self.channelMapping[j+1])
                    if nominalCoord > endCoordinate:
                        lastChannel = j
                        break
                self.firstBins.append([firstChannel, lastChannel])
                scales.append(1.0)
                mappedRanges[0].append([beginCoordinate, endCoordinate])
            else:
                # this energy range exceeds the calibration for the spectrum
                lastChannel = self.channelLimits[1]
                self.firstBins.append([lastChannel, lastChannel])
                scales.append(1.0)
                mappedRanges[0].append([beginCoordinate, endCoordinate])
            firstChannel = lastChannel
        if self.extendAtEnd:
            # use the rest of the channels for the final initial rebin
            #  - yields the same number of initial bins as the input initialRebin
            #  - otherwise, there will be one fewer initial bin
            firstChannel = self.firstBins[-1][-1]
            lastChannel = self.channelLimits[1]
            beginCoordinate = self._initialRebin[-1]
            endCoordinate = max(beginCoordinate, self.channelMapping[lastChannel-1])

            self.firstBins.append([firstChannel, lastChannel])
            scales.append(1.0)
            mappedRanges[0].append([beginCoordinate, endCoordinate])

        self.scales = [scipy.array(scales), ]
        self.outputMapping = [scipy.zeros((len(scales),))]
        for i, ena in enumerate(mappedRanges[0]):
            self.outputMapping[0][i] = 0.5*(ena[0] + ena[1])
        cumulativeChannels.append(len(scales))
        self.outputChannels.append(scipy.arange(len(scales)))

        # continue for the subsequent scales
        subsequentBinning = []
        possibleDepth = 0
        for depth in xrange(self.depth):
            thisBinning = []  # channels in the first rebinned object
            scales = []
            mappedCoords = []
            stride = 2**depth

            if depth == 0:
                length = len(self.firstBins)
            else:
                length = len(subsequentBinning[-1])

            if stride < length:
                for i in xrange(length):
                    nxt = i + stride
                    if nxt < length:
                        thisBinning.append([i, nxt])
                        scales.append(float(2**(depth+1)))
                        mappedCoords.append([mappedRanges[depth][i][0], mappedRanges[depth][nxt][1]])
                    else:
                        break
                subsequentBinning.append(thisBinning)
                mappedRanges.append(mappedCoords)
                self.scales.append(scipy.array(scales))
                self.outputMapping.append(scipy.zeros((len(scales), )))
                for i, ena in enumerate(mappedCoords):
                    self.outputMapping[-1][i] = 0.5*(ena[0] + ena[1])
                cumulativeChannels.append(cumulativeChannels[depth] + len(scales))
                self.outputChannels.append(scipy.arange(cumulativeChannels[depth], cumulativeChannels[depth+1]))
                possibleDepth = depth + 1
            else:
                break
        self.actualDepth = possibleDepth
        if self.actualDepth < self.depth:
            logging.warning('Actual depth in RebinningTransform object different from desired %s to %s, due to feasibility' % (self.actualDepth, self.depth))


        # define the rebinning definition into it's final form, so it's a reference to the appropriate channels
        # in the transform array
        #  (transform channel, first index in sum, second index in sum)
        self.subsequentBinning = scipy.zeros((cumulativeChannels[-1] - cumulativeChannels[0], 3), dtype=scipy.uint16)

        curTotal = 0
        for i in xrange(self.actualDepth):
            shift1 = cumulativeChannels[i]  # the number of channels already defined
            if i == 0:
                shift2 = 0  # the beginning index of the previous effort
            else:
                shift2 = cumulativeChannels[i - 1]
            for j, el in enumerate(subsequentBinning[i]):
                self.subsequentBinning[curTotal, :] = [j + shift1, el[0] + shift2, el[1] + shift2]
                curTotal += 1
        self.totalOutputChannels = cumulativeChannels[-1]
        self.minimumStDeviation = scipy.ones((self.totalOutputChannels,))

    def computeTransform(self, arr):
        """
        Computes transform of input array(s)
        """

        if arr.shape[-1] != self.inputChannelSize:
            print arr.shape[-1], self.inputChannelSize
            raise ValueError("Input spectra does not have final dimension of "
                             "the size specified by inputChannelSize")

        if len(arr.shape) == 2:  # multiple measurements
            out = scipy.zeros((arr.shape[0], self.totalOutputChannels))
            for i, el in enumerate(self.firstBins):
                out[:, i] = scipy.sum(arr[:, el[0]: el[1]], axis=1)
            for el in self.subsequentBinning:
                out[:, el[0]] = (out[:, el[1]] + out[:, el[2]])
            return out
        elif len(arr.shape) == 1:
            out = scipy.zeros((self.totalOutputChannels,))
            for i, el in enumerate(self.firstBins):
                out[i] = scipy.sum(arr[el[0]: el[1]])
            for el in self.subsequentBinning:
                out[el[0]] = (out[el[1]] + out[el[2]])
            return out
        else:
            raise ValueError("Input with more than two dimensions cannot be transformed")

    def computeVarianceTransform(self, arr):
        """
        Computes variance transform of input array(s)
        """

        return self.computeTransform(arr)

    def computeTransforms(self, arr):
        """
        Computes both transforms of input array(s)
        """

        trans = self.computeTransform(arr)
        return trans, scipy.copy(trans)


class AveragingTransform(BaseTransform):
    KERNELS = ('square', 'gauss', 'gauss1', 'gauss2')

    def __init__(self, channelMapping, outputMapping, scales, kernelName='gauss', channelLimits=None, normalizeKernel=1):
        """
        A linear transformation object - the input array is averaged using a gaussian kernel in 'mapped space',
        where channelMapping describes the interpretation of the array.
        """

        kernN = kernelName.lower()
        if kernN in AveragingTransform.KERNELS:
            self.kernelName = kernN
        else:
            self.kernelName = 'gauss'

        # list of energy arrays, interpreted as base point for transform
        self.outputMapping = outputMapping
        # list of "scale" arrays, interpreted as scale at each base point
        # scales and outputMapping must have same array structure
        self.scales = scales
        self.totalOutputChannels = 0
        self.outputChannels = []
        for el in scales:
            self.outputChannels.append(scipy.arange(self.totalOutputChannels, self.totalOutputChannels + el.size))
            self.totalOutputChannels += el.size

        if channelLimits is None:
            # simply exclude overflow
            self.channelLimits = [0, channelMapping.size - 1]
        else:
            self.channelLimits = channelLimits
        self.normalizeKernel = normalizeKernel

        self.setChannelMapping(channelMapping)

    def _getKernelArray(self, en, scal, chs, initialCondition):
        begMapped = self.beginMappedArray - en
        endMapped = self.endMappedArray - en

        if self.kernelName == 'square':
            support = [-1., 1.]
            kfunc = lambda x: 1.0

        elif self.kernelName == 'gauss1':
            support = [-4., 4.]
            kfunc = lambda x: x*scipy.exp(-x*x/2.0)

        elif self.kernelName == 'gauss2':
            support = [-5., 5.]
            kfunc = lambda x: (1 - x*x)*scipy.exp(-x*x/2.0)

        else:
            self.kernelName == 'gauss'
            support = [-3., 3.]
            kfunc = lambda x: scipy.exp(-x*x/2.0)

        boolc = ((begMapped <= support[1]*scal) & (endMapped >= support[0]*scal) & (begMapped < endMapped))
        boolf = (initialCondition & boolc)

        if scipy.any(boolf):
            t_chs = chs[boolf]
            t_coefficients = scipy.zeros(t_chs.shape, dtype=scipy.float64)

            t_beg = begMapped[boolf]
            t_end = endMapped[boolf]
            t_beg[0] = max(t_beg[0], support[0]*scal)
            t_end[-1] = min(t_end[-1], support[1]*scal)

            for i in xrange(t_chs.size):
                lim1 = t_beg[i]
                lim2 = t_end[i]
                if lim1 < lim2:
                    wght, w_err = quad(kfunc, lim1/scal, lim2/scal)
                    t_coefficients[i] = wght
                else:
                    t_coefficients[i] = 0.0

            if self.normalizeKernel > 0:
                # normalize in "channel" space
                ctot = scipy.sum(scipy.absolute(t_coefficients))
                if ctot > 0:
                    t_coefficients /= ctot
                    # calculate "mapped coordinate" normalization factor, if necessary
                    if self.normalizeKernel == 2:
                        t_weights = scipy.zeros(t_chs.shape, dtype=scipy.float64)
                        t_weights[:] = 1.
                        t_weights[0] = min(1.0, (t_end[0]-t_beg[0])/(self.endMappedArray[t_chs[0]]-self.beginMappedArray[t_chs[0]]))
                        t_weights[-1] = min(1.0, (t_end[-1]-t_beg[-1])/(self.endMappedArray[t_chs[-1]]-self.beginMappedArray[t_chs[-1]]))

                        for i in xrange(t_beg.size):
                            wght = (t_end[i] - t_beg[i])  # difference in mapped space
                            if wght > 0.:
                                t_weights[i] /= wght
                            else:
                                t_weights[i] = 1.

                        t_coefficients *= t_weights
            # print t_coefficients
            minSig = scipy.amax(scipy.absolute(t_coefficients))
            return list(t_chs), list(t_coefficients), list(t_coefficients*t_coefficients), minSig
        else:
            return None, None, None, 1.0

    def setChannelMapping(self, channelMappingIn):
        channelMapping = scipy.copy(channelMappingIn)

        self.inputChannelSize = channelMapping.size
        self.beginMappedArray = scipy.copy(channelMapping)
        self.endMappedArray = scipy.zeros(self.beginMappedArray.shape)
        self.endMappedArray[:-1] = self.beginMappedArray[1:]
        # no good comes from the overflow channel here
        self.endMappedArray[-1] = self.beginMappedArray[-1]

        chs = scipy.arange(channelMapping.size)
        initialBool = ((chs >= self.channelLimits[0]) & (chs < self.channelLimits[1]))

        transValues = []
        vtransValues = []
        inputChanValues = []
        outputChanValues = []
        minimumStDevs = []

        currentOutputChan = 0
        for scaleArray, energyArray in zip(self.scales, self.outputMapping):
            for scl, en in zip(scaleArray, energyArray):
                chans, weights, vweights, minSig = self._getKernelArray(en, scl, chs, initialBool)
                minimumStDevs.append(minSig)
                if chans is not None:
                    transValues += weights
                    vtransValues += vweights
                    inputChanValues += chans
                    outputChanValues += [currentOutputChan, ]*len(chans)
                else:  # it's infeasible, just fill in zero
                    transValues.append(0)
                    vtransValues.append(0)
                    inputChanValues.append(self.channelLimits[0])
                    outputChanValues.append(currentOutputChan)
                currentOutputChan += 1

        # Now, define our matrix, which is intended to multiply on the right
        # input channel number forms the row index
        # output channel number forms the column index

        matrixSize = (self.beginMappedArray.size, currentOutputChan)
        rowArray = scipy.array(inputChanValues, dtype=scipy.uint16)
        colArray = scipy.array(outputChanValues, dtype=scipy.uint16)
        mat = scipy.sparse.coo_matrix((scipy.array(transValues, dtype=scipy.float64), (rowArray, colArray)), matrixSize)
        varMat = scipy.sparse.coo_matrix((scipy.array(vtransValues, dtype=scipy.float64), (rowArray, colArray)), matrixSize)

        # Convert to compressed column format, for fast multiplication on the right
        self.matrix = mat.tocsc()
        self.varianceMatrix = varMat.tocsc()
        # define minimum st. deviation
        self.minimumStDeviation = scipy.array(minimumStDevs)

    def computeTransform(self, arr):
        if arr.shape[-1] != self.inputChannelSize:
            raise ValueError("Input spectra does not have final dimension of "
                             "the size specified by inputChannelSize")
        if len(arr.shape) == 2:
            return arr * self.matrix
        elif len(arr.shape) == 1:
            return (scipy.reshape(arr, (1, self.inputChannelSize)) * self.matrix).flatten()
        else:
            raise ValueError("Input with more than two dimensions cannot be transformed")

    def computeVarianceTransform(self, arr):
        if arr.shape[-1] != self.inputChannelSize:
            raise ValueError("Input spectra does not have final dimension of "
                             "the size specified by inputChannelSize")
        if len(arr.shape) == 2:
            return arr * self.varianceMatrix
        elif len(arr.shape) == 1:
            return (scipy.reshape(arr, (1, self.inputChannelSize)) * self.varianceMatrix).flatten()
        else:
            raise ValueError("Input with more than two dimensions cannot be transformed")

    def computeTransforms(self, arr):
        return self.computeTransform(arr), self.computeVarianceTransform(arr)


###########################
#  End Transform Methods  #
######################################################################################################################


#######################################################################################################################
#  Begin Neutron Methods  #
###########################

class ConstantCountRateThreshold(object):
    """
    This is a stupid class - I'm really just trying to simplify a poisson stats work flow
    """

    def __init__(self, countRateLimit, threshold, ceiling=128.):
        # we will examine the significance of rate relative to this
        self.countRateLimit = float(countRateLimit)  # assumed to be the rate/unit time
        self.threshold = float(threshold)  # assumed to be relative to -log10 of the "significance"
        self.ceiling = ceiling

    def calculateSignificance(self, counts, liveTime):
        relativeLimit = self.countRateLimit*liveTime
        significance = -poisson.logsf(counts, relativeLimit)  # negative log of the survival function (1 - cdf)
        if (self.ceiling is not None) and (significance > self.ceiling):
            significance = self.ceiling
        return significance, (significance >= self.threshold), relativeLimit


class NeutronEvaluationResult(object):
    """
    Helper class (really just a struct) for managing the most basic neutron rate evaluation
    """

    def __init__(self, foreground, fgLiveTime, estimate, significance, exceedsThreshold, measurementCount=None):
        self.foreground = foreground
        self.fgLiveTime = fgLiveTime
        self.estimate = estimate
        self.significance = significance
        self.exceedsThreshold = exceedsThreshold
        self.measurementCount = measurementCount


#########################
#  End Neutron Methods  #
######################################################################################################################


#######################################################################################################################
#  Begin Spectral Methods  #
############################

class Seminorm(object):
    def __init__(self, definitionDict, transform, mode='DEFAULT'):
        self.definitionDict = definitionDict
        self.name = definitionDict['name']
        self.mappingDefinition = definitionDict['mapping_definition']
        self.lpExponent = float(definitionDict['lp_exponent'])

        if ('count_rate_adjustment' in definitionDict) and \
                (definitionDict['count_rate_adjustment'] is not None):
            dd = definitionDict['count_rate_adjustment']
            self.adjustmentFactor = float(dd['adjustment_factor'])
            self.upperFraction = float(dd['upper_fraction'])
            self.lowerFraction = float(dd['lower_fraction'])
        else:
            self.adjustmentFactor = 0.0
            self.upperFraction = 1.0
            self.lowerFraction = 1.0
        # these are the two which depend on mode
        if 'thresholds' in definitionDict:
            self.threshDicts = definitionDict['thresholds']
        else:
            self.threshDicts = {'DEFAULT': {'base_scale_factor': 1.0, 'minimum_scale': 6.0}}

        self.setMode(mode)
        self.setTransform(transform)

    def setMode(self, newMode):
        if newMode in self.threshDicts:
            self.mode = newMode
            defDict = self.threshDicts[newMode]
            self.baseScaleFactor = float(defDict['base_scale_factor'])
            self.minimumScale = float(defDict['minimum_scale'])
        else:
            logging.error('No thresholds for seminorm {} and mode {}. No change possible!'.format(self.name, newMode))

    def updateThresholds(self, newDict):
        for key in newDict:
            self.threshDicts[key] = {}  # overwrites any old values
            for element, val in newDict[key].iteritems():
                self.threshDicts[key][element] = val
        self.setMode(self.mode)

    def setTransform(self, transform):
        numScales = len(transform.getOutputMapping())
        useChannels = []

        for scale, erange in self.mappingDefinition:
            if scale < numScales:
                energies = transform.getOutputMapping()[scale]
                channels = transform.getOutputChannels()[scale]
                boolc = ((energies >= erange[0]) & (energies <= erange[1]))
                if scipy.any(boolc):
                    useChannels += list(channels[boolc])
            else:
                logging.warning('Skipping inclusion of scale %s for seminorm, which exceeds feasible scale %s' % (scale, numScales))
        if len(useChannels) > 0:
            self.useChannels = scipy.array(useChannels)
            self.totalChannels = len(useChannels)
        else:
            self.useChannels = None
            self.totalChannels = 0

    def calculateValue(self, deviationVector, countRate, relativeRate=1.):
        if self.totalChannels < 1:
            return 0.0, False
        else:
            theScale = max(self.baseScaleFactor*countRate**0.25, self.minimumScale)
            relevantDeviation = deviationVector[self.useChannels]

            if (self.lpExponent == 'max') or (scipy.isinf(self.lpExponent)):
                rawSeminorm = scipy.absolute(relevantDeviation).max()
            else:
                rawSeminorm = (scipy.sum((scipy.absolute(relevantDeviation))**self.lpExponent)/float(self.totalChannels))**(
                1./self.lpExponent)
            adjustment = 1.0
            if ((self.adjustmentFactor > 0.0) and (relativeRate > self.upperFraction) and
                    (relevantDeviation.min() < -theScale) and (relevantDeviation.max() < theScale)):
                # This gets applied in the case that gross counts have drastically increased
                # and low energy contribution is too small
                # NOTE: THIS PREVENTS THIS SN FROM TRIGGERING AN ALARM!
                adjustment = 0.5/rawSeminorm  # yields 1/2 as normalized seminorm value
            elif ((self.adjustmentFactor > 0.0) and (relativeRate < self.lowerFraction) and
                    (relevantDeviation.max() > theScale) and (relevantDeviation.min() > -theScale)):
                # This gets applied in the case that gross counts have drastically decreased
                # and low energy contribution is too large
                adjustment = min(self.adjustmentFactor*(relativeRate**0.25), 1.0)

            adjustedSeminorm = adjustment*rawSeminorm
            scaledValue = adjustedSeminorm/theScale
            return scaledValue, (scaledValue >= 1.0)


class ScaleRatioCalculator(object):
    def __init__(self, channelLimits, mappedCoordinateRanges, channelMapping):
        self.channelLimits = channelLimits
        self.mappedCoordinateRanges = scipy.copy(mappedCoordinateRanges)
        self.setChannelMapping(channelMapping)

    def setChannelMapping(self, channelMapping):
        channelMapping = scipy.copy(channelMapping)
        chs = scipy.arange(channelMapping.size, dtype=scipy.uint16)
        boolc1 = ((chs >= self.channelLimits[0]) & (chs < self.channelLimits[1]))
        self.channelRanges = []
        for el in self.mappedCoordinateRanges:
            boolc = ((channelMapping >= el[0]) & (channelMapping <= el[1]) & boolc1)
            # choose the first and last true element
            if scipy.any(boolc):
                t_chs = chs[boolc]
                self.channelRanges.append((t_chs.min(), t_chs.max()))

    def calculateRatio(self, foreground, background, foregroundLiveTime=0., backgroundLiveTime=0.):
        if len(foreground.shape) == 1:
            fgcumsum = scipy.cumsum(foreground)
            bgcumsum = scipy.cumsum(background)
            fgsums = scipy.zeros((len(self.mappedCoordinateRanges),), dtype=scipy.float64)
            bgsums = scipy.zeros((len(self.mappedCoordinateRanges),), dtype=scipy.float64)
            for i, el in enumerate(self.channelRanges):
                fgsums[i] = (fgcumsum[el[1]] - fgcumsum[el[0]])
                bgsums[i] = (bgcumsum[el[1]] - bgcumsum[el[0]])
            del fgcumsum, bgcumsum
            valid = ((bgsums > 0) & (fgsums > 0))
            if scipy.any(valid):
                return scipy.mean(fgsums[valid]/bgsums[valid])
            else:
                return scipy.inf
        else:
            fgcumsum = scipy.cumsum(foreground, axis=1)
            bgcumsum = scipy.cumsum(background, axis=1)
            fgsums = scipy.zeros((foreground.shape[0], len(self.mappedCoordinateRanges)), dtype=scipy.float64)
            bgsums = scipy.zeros((foreground.shape[0], len(self.mappedCoordinateRanges)), dtype=scipy.float64)
            for i, el in enumerate(self.channelRanges):
                fgsums[:, i] = (fgcumsum[:, el[1]] - fgcumsum[:, el[0]])
                bgsums[:, i] = (bgcumsum[:, el[1]] - bgcumsum[:, el[0]])
            del fgcumsum, bgcumsum
            out = scipy.zeros((foreground.shape[0],), dtype=scipy.float64)
            for j in enumerate(out.size):
                valid = ((bgsums[:, j] > 0) & (fgsums[:, j] > 0))
                if scipy.any(valid):
                    out[j] = scipy.mean(fgsums[j, valid]/bgsums[j, valid])
                else:
                    out[j] = scipy.inf
            return out


class EvaluationResult(object):
    """
    Helper class for managing transform vectors, deviation vectors, and the various evaluation portions
    """

    def __init__(self, foreground, background, deviation, backgroundFraction, scaleRatio,
                 fgCounts, bgCounts, fgLiveTime, bgLiveTime, seminormList=None, measurementCount=None):

        self.foreground = foreground
        self.background = background
        self.deviation = deviation
        self.fgCounts = fgCounts
        self.bgCounts = bgCounts
        self.fgLiveTime = fgLiveTime
        self.bgLiveTime = bgLiveTime
        self.backgroundFraction = backgroundFraction
        self.scaleRatio = scaleRatio
        self.measurementCount = measurementCount

        if seminormList is None:
            self.seminormValues = None
            self.exceedsThresholdValues = None
            self.exceedsThreshold = None
        else:
            # Semi-norm workspace
            self.seminormValues = scipy.zeros((len(seminormList),))
            self.exceedsThresholdValues = scipy.zeros((len(seminormList),), dtype='bool')
            # Populate semi-norm values
            for i, sn in enumerate(seminormList):
                snv, al = sn.calculateValue(deviation, fgCounts, relativeRate=backgroundFraction)
                self.seminormValues[i] = snv
                self.exceedsThresholdValues[i] = al
            self.exceedsThreshold = scipy.any(self.exceedsThresholdValues)


class BaseSpectralAlgorithmParameters(object):
    def __init__(self):
        # construct the channel limits
        self.channelLimits = None
        # construct the transform object appropriately
        self.transform = None
        # construct the scaleRatioCalculator, if necessary
        self.scaleRatioCalculator = None
        # construct the respective semi-norms
        self.seminormList = None
        self.seminormIndex = {}

        # provide some idea of mode
        self.mode = 'DEFAULT'

        raise NotImplementedError

    def setMode(self, newMode):
        self.mode = newMode
        for el in self.seminormList:
            el.setMode(newMode)

    def modifySeminormThresholds(self, inputDictionary):
        for key, val in inputDictionary.iteritems():
            if key in self.seminormIndex:
                self.seminormList[self.seminormIndex].updateThresholds(val)
            else:
                logging.warning("No seminorm corresponding to {}".format(key))

    def setChannelMapping(self, channelMapping):
        self.transform.setChannelMapping(channelMapping)

        if self.scaleRatioCalculator is not None:
            self.scaleRatioCalculator.setChannelMapping(channelMapping)

        for el in self.seminormList:
            el.setTransform(self.transform)

    def getChannelLimits(self):
        return self.channelLimits

    def getBackgroundFraction(self, foreground, background, fgCounts, bgCounts, fgLiveTime, bgLiveTime):
        """
        Determine the relative count rate between the "foreground" and the "background". It turns out that this
        is a useful quantity in comparing spectra acquired from nearly coincident locations.
        """

        if len(foreground.shape) == 1:
            if (bgCounts > 0) and (fgLiveTime > 0):
                return (fgCounts*bgLiveTime)/(bgCounts*fgLiveTime)
            elif bgCounts == 0:  # this is retarded
                return 1.0
            else:  # this is more retarded
                return 0.0
        else:
            out = scipy.zeros(fgCounts.shape, )
            # main case
            boolc = ((bgCounts > 0) & (fgLiveTime > 0))
            out[boolc] = (fgCounts[boolc]*bgLiveTime[boolc])/(bgCounts[boolc]*fgLiveTime[boolc])
            # stupid fringe case
            boolc = (bgCounts == 0)
            out[boolc] = 1.0
            # done!
            return out

    def getScaleRatio(self, foreground, background, fgCounts, bgCounts, fgLiveTime, bgLiveTime):
        """
        This is only a stupid stub, and should be over-ridden appropriately
        """

        # do the simplest thing possible, just ratio of live times
        if len(foreground.shape) == 1:
            if bgLiveTime > 0:
                return fgLiveTime/bgLiveTime
            else:
                return 0.
        else:
            out = scipy.zeros(fgCounts.shape, )
            # main case
            boolc = (bgLiveTime > 0)
            out[boolc] = (fgLiveTime[boolc])/bgLiveTime[boolc]
            return out

    def evaluationProcedure(self, foreground, background, fgCounts, bgCounts, fgLiveTime, bgLiveTime):
        """
        Transform, scale the "background", and make the deviation vector
        """

        # this will crap out if foreground and background have different shapes
        # get background fraction
        backgroundFraction = self.getBackgroundFraction(foreground, background, fgCounts, bgCounts, fgLiveTime, bgLiveTime)
        # get appropriate scale ratio
        scaleRatio = self.getScaleRatio(foreground, background, fgCounts, bgCounts, fgLiveTime, bgLiveTime)
        # transform foreground
        foreTrans = self.transform.computeTransform(foreground)
        # transform background
        backTrans, backVar = self.transform.computeTransforms(background)
        # make deviation vector
        if len(foreground.shape) == 1:
            deviation = (foreTrans - scaleRatio*backTrans)/scipy.maximum(self.transform.getMinimumStDev(), scipy.sqrt(scaleRatio*backVar))
        else:
            minsigs = scipy.outer(scipy.ones((foreground.shape[0], )), self.transform.getMinimumStDev())
            deviation = (foreTrans - (backTrans.T*scaleRatio).T)/scipy.maximum(minsigs, scipy.sqrt((backVar.T*scaleRatio).T))
        deviation[scipy.isnan(deviation)] = 0.0
        return foreTrans, backTrans, deviation, backgroundFraction, scaleRatio

    def makeEvaluationResult(self, foreground, background, fgCounts, bgCounts, fgLiveTime, bgLiveTime, measurementCount):
        """
        Pass-through method, which just packages the results into a nice container
        """
        if len(foreground.shape) == 1:
            res = self.evaluationProcedure(foreground, background, fgCounts, bgCounts, fgLiveTime, bgLiveTime)
            return EvaluationResult(res[0], res[1], res[2], res[3], res[4],
                                    fgCounts, bgCounts, fgLiveTime, bgLiveTime,
                                    seminormList=self.seminormList, measurementCount=measurementCount)
        else:
            raise ValueError("Input array must be one-dimensional")


class LowCountRateAlgorithmParameters(BaseSpectralAlgorithmParameters):
    def __init__(self, channelLimits, channelMapping, transformParameters, mappedCoordinateRanges, seminormDefinitionList, mode='DEFAULT'):
        channelMapping = scipy.copy(channelMapping)
        if channelLimits is None:
            self.channelLimits = [0, channelMapping.size]
        else:
            self.channelLimits = channelLimits  # assuming this isn't stupid

        self.transform = RebinningTransform(channelMapping,
                                            transformParameters['initial_rebin'],
                                            transformParameters['depth'],
                                            channelLimits=self.channelLimits)

        if mappedCoordinateRanges is not None:
            self.scaleRatioCalculator = ScaleRatioCalculator(self.channelLimits, mappedCoordinateRanges, channelMapping)
        else:
            self.scaleRatioCalculator = None

        self.mode = mode
        self.seminormList = []
        self.seminormIndex = {}

        for i, el in enumerate(seminormDefinitionList):
            self.seminormList.append(Seminorm(el, self.transform, mode=self.mode))
            self.seminormIndex[el['name']] = i

    def getScaleRatio(self, foreground, background, fgCounts, bgCounts, fgLiveTime, bgLiveTime):
        """
        This overrides the stub in the base class, determines appropriate scale to compare the foreground and
        background spectra
        """

        if self.mode is 'STATIC':
            # do the simplest thing possible, just ratio of live times
            if len(foreground.shape) == 1:
                if bgLiveTime > 0:
                    return fgLiveTime/bgLiveTime
                else:
                    return 0.
            else:
                out = scipy.zeros(fgCounts.shape, )
                # main case
                boolc = (bgLiveTime > 0)
                out[boolc] = fgLiveTime[boolc]/bgLiveTime[boolc]
                return out
        else:
            lamb = 0.8

            if len(foreground.shape) == 1:
                if bgLiveTime > 0:
                    scale1 = fgLiveTime/bgLiveTime
                else:
                    scale1 = 0.
                scale2 = self.scaleRatioCalculator.calculateRatio(foreground, background)

                if scale2 > scale1:
                    # relative count rate indicates scale smaller than our spectral ratio determination
                    return lamb*scale1 + (1. - lamb)*scale2
                else:
                    return scale2
            else:
                scale1 = scipy.zeros(fgCounts.shape, )
                boolc = (bgLiveTime > 0)
                scale1[boolc] = fgLiveTime[boolc]/bgLiveTime[boolc]
                out = self.scaleRatioCalculator.calculateRatio(foreground, background)  # scale2
                boolc = (out > scale1)
                out[boolc] = lamb*scale1[boolc] + (1. - lamb)*out[boolc]
                return out

    def evaluationProcedure(self, foreground, background, fgCounts, bgCounts, fgLiveTime, bgLiveTime):
        """
        This overrides the stub in the base class. Transform, scale the "background", and make the deviation vector
        """

        # this will crap out if foreground and background have different shapes
        # get background fraction
        backgroundFraction = self.getBackgroundFraction(foreground, background, fgCounts, bgCounts, fgLiveTime, bgLiveTime)
        # get appropriate scale ratio
        scaleRatio = self.getScaleRatio(foreground, background, fgCounts, bgCounts, fgLiveTime, bgLiveTime)
        # transform foreground
        foreTrans = self.transform.computeTransform(foreground)
        # transform background, get variance transform too
        backTrans, backVar = self.transform.computeTransforms(background)
        # make deviation vector
        if len(foreground.shape) == 1:
            deviation = (foreTrans - scaleRatio*backTrans)/scipy.maximum(self.transform.getMinimumStDev(), scaleRatio*scipy.sqrt(backVar))
        else:
            minsigs = scipy.outer(scipy.ones((foreground.shape[0], )), self.transform.getMinimumStDev())
            deviation = (foreTrans - (backTrans.T*scaleRatio).T)/scipy.maximum(minsigs, scipy.sqrt((backVar.T*scaleRatio).T))

        ## for this particular method, we should not allow ourselves to be affected by negative elements of the deviation
        # TODO: testing!
        deviation[scipy.isnan(deviation)] = 0.0
        deviation[deviation < -0.5] = -0.5

        return foreTrans, backTrans, deviation, backgroundFraction, scaleRatio


class CoherentSpectralAlgorithmParameters(BaseSpectralAlgorithmParameters):
    def __init__(self, channelLimits, channelMapping, transformParameters, mappedCoordinateRanges, seminormDefinitionList, mode='DEFAULT'):
        channelMapping = scipy.copy(channelMapping)
        if channelLimits is None:
            self.channelLimits = [0, channelMapping.size - 1]  # just exclude the overflow channel
        else:
            self.channelLimits = channelLimits  # assuming this isn't stupid

        # for now, I'm just going to assume something that I think is sensible for scales & outputMapping
        # these allow nominal construction in mapped (energy) space

        baseScales = [[3.0, 0.5, 0.001],
                      [24.0, 0.75, 0.001],
                      [48.0, 1.25, 0.001],
                      [96.0, 2.5, 0.001]]

        outputMapping = [DEFAULT_COHERENT_BINS,
                         DEFAULT_COHERENT_BINS,
                         DEFAULT_COHERENT_BINS[::2],
                         DEFAULT_COHERENT_BINS[::4]]

        scales = []
        for el, en in zip(baseScales, outputMapping):
            scales.append(el[0] + el[1]*scipy.sqrt(en + el[2]*en*en))

        self.transform = AveragingTransform(channelMapping,
                                            outputMapping,
                                            scales,
                                            kernelName=transformParameters['kernel_name'],
                                            channelLimits=self.channelLimits,
                                            normalizeKernel=transformParameters['normalize_kernel']
                                            )

        self.scaleRatioCalculator = ScaleRatioCalculator(self.channelLimits, mappedCoordinateRanges, channelMapping)

        self.mode = mode
        self.seminormList = []
        self.seminormIndex = {}

        for i, el in enumerate(seminormDefinitionList):
            self.seminormList.append(Seminorm(el, self.transform, mode=self.mode))
            self.seminormIndex[el['name']] = i

    def getScaleRatio(self, foreground, background, fgCounts, bgCounts, fgLiveTime, bgLiveTime):
        """
        This overrides the stub in the base class, determines appropriate scale to compare the foreground and
        background spectra
        """

        if self.mode is 'STATIC':
            # do the simplest thing possible, just ratio of live times
            if len(foreground.shape) == 1:
                if bgLiveTime > 0:
                    return fgLiveTime/bgLiveTime
                else:
                    return 0.
            else:
                out = scipy.zeros(fgCounts.shape, )
                # main case
                boolc = (bgLiveTime > 0)
                out[boolc] = fgLiveTime[boolc]/bgLiveTime[boolc]
                return out
        else:
            return self.scaleRatioCalculator.calculateRatio(foreground, background)


##########################
#  End Spectral Methods  #
######################################################################################################################




