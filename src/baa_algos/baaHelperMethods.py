import os
import logging
import scipy
from scipy.interpolate import UnivariateSpline

try:
    import matplotlib
    import matplotlib.pyplot as pyplot
    matplotlib.rc('font', **{'family': 'sans-serif', 'sans-serif': 'Arial', 'weight': 'normal', 'size': 10})
    matplotlib.rc('figure', **{'dpi': 150, 'facecolor': 'white', 'edgecolor': 'white'})
except ImportError:
    logging.warning('No matplotlib available. May cause errors if proceeding carelessly.')


def validateDirectory(filename):
    """
    Given filename, create any missing directory structure in the path
    """

    fname, extension=os.path.splitext(filename)
    if extension == '':
        proposedDir = fname
    else:
        proposedDir = os.path.dirname(filename)
    if (proposedDir != '') and not (os.path.exists(proposedDir)):
        # the file is not to be written to the cwd
        # and the proposed directory does not exist
        os.makedirs(proposedDir)
        # recursively create the directory structure, final leaf directory must not already exist
        # Will throw exception if user does not have write permission for the first directory in
        # the path which does not exist


def getSensorMakeAndModel(sensor):
    try:
        make = sensor.make.lower()
        model = sensor.model.lower()
    except Exception:
        return None, None, None

    if hasattr(sensor, 'serialNumber'):
        sn = sensor.serialNumber
    else:
        sn = None

    if (make == 'kromek') and (model == 'd3'):
        model = 'd3s'
        if sn is not None:
            if ('0000' <= sn <= '0040') or ('120000' <= sn <= '120040'):
                model = 'd3-rev2a'
            elif ('120040' <= sn <= '120150'):
                model = 'd3-rev2b'
            elif ('100000' <= sn <= '100149'):
                model = 'd3s'
            elif ('SGM00150' <= sn <= 'SGM999999'):
                model = 'd3s2'
    return make, model, sn


def expandSpectrum(compressedSpec, numChannels=512):
    """
    Helper method for expanding sparsely represented spectra to full spectra
    """

    if isinstance(compressedSpec, scipy.ndarray):
        # it's already a numpy array, and presumably has been expanded somewhere else!
        return compressedSpec
    else:
        out = scipy.zeros((numChannels,), dtype=scipy.uint32)
        # 16 bits is probably sufficient, but just in case?
        for i in xrange(0, len(compressedSpec), 2):
            out[compressedSpec[i]] = compressedSpec[i + 1]
        return out


def makeCalibrationSpline(energies, channels, multiplier=1.0):
    # this is for the "forward" direction
    # channels -> energies

    if scipy.__version__ > '0.14.1':
        return UnivariateSpline(multiplier*scipy.array(channels), scipy.array(energies), k=2, s=0, ext=0)
    else:
        return UnivariateSpline(multiplier*scipy.array(channels), scipy.array(energies), k=2, s=0)


def makeEnergySpline(energies, channels, multiplier=1.0, numChannels=512):
    tSp = makeCalibrationSpline(energies, channels, multiplier=multiplier)
    chans = scipy.arange(numChannels)
    interpolatedEnergies = tSp(chans)
    if scipy.__version__ > '0.14.1':
        return UnivariateSpline(interpolatedEnergies, chans, k=1, s=0, ext=0)
    else:
        return UnivariateSpline(interpolatedEnergies, chans, k=1, s=0)


def resolutionEnergyFunction(energy, coeffs=[3.0, 0.5, 0.001]):
    # returning the standard deviation parameter in energy space
    return coeffs[0] + coeffs[1]*scipy.sqrt(energy + coeffs[2]*energy*energy)


def resolutionChannelsFunction(energy, channel, coeffs=[3.0, 0.5, 0.001], numChannels=512):
    binEnergies = makeCalibrationSpline(energy, channel)(scipy.arange(numChannels))
    # create appropriate resolution scale in "channel space"
    res = resolutionEnergyFunction(binEnergies, coeffs=coeffs)  # resolution in energy space, so divide by "slope"
    slope = scipy.zeros(binEnergies.shape, dtype=scipy.float64)
    slope[:-1] = (binEnergies[1:] - binEnergies[:-1])  # keV / channel
    slope[-1] = slope[-2]
    slope[slope < 0.1] = 0.1  # avoid zero...
    channelResolution = res/slope
    if scipy.__version__ > '0.14.1':
        return UnivariateSpline(scipy.arange(numChannels), channelResolution, k=1, s=0, ext=0)
    else:
        return UnivariateSpline(scipy.arange(numChannels), channelResolution, k=1, s=0)

