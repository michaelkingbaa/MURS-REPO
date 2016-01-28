from baaMatplotlibAddons import *

import cStringIO
from PIL import Image

COLOR_SCALE_OPTIONS=('linear', 'squareroot', 'log')


def getColorArray(mapSize, cmapName='baa_spectral', integer=True):
    s = matplotlib.cm.get_cmap(cmapName, mapSize)
    if integer:
        # assign the proper 8-bit colors to the relevant integer level
        cols = scipy.zeros((int(mapSize), 4), dtype=scipy.uint8)
        for i in xrange(mapSize):
            for j, c in enumerate(s(i)):
                cols[i, j] = c*255
    else:
        cols = scipy.zeros((int(mapSize), 4), dtype=scipy.float64)
        for i in xrange(mapSize):
            for j, c in enumerate(s(i)):
                cols[i, j] = c
    return cols


def colormap(mapSize, minimumValue, maximumValue, units, cmapName='baa_spectral', colorScale='linear'):
    """
    Provides specific colormap facilities for baa tasks

    Args:
        mapSize - integer for the size of the colormap
        minimumValue - float minimum value for colorbar
        maximumValue - float maximum value for colorbar
        units - string of units to be displayed on colorbar image
        cmapName - string name of registered matplotlib colormap
        colorScale - string in COLOR_SCALE_OPTIONS for colorbar scale behavior

    Returns:
        cols - a numpy array of unsigned 8 bit integers of shape (mapSize, 4)
        img - a PIL Image object containing the colorbar plot
    """
    
    if maximumValue < minimumValue:
        raise ValueError("MaximumValue {} must be larger than minimumValue {}".format(maximumValue, minimumValue))

    cols = getColorArray(mapSize, cmapName=cmapName)
    # Prepare to create the colorbar image array
    if colorScale == 'linear':
        vmin = minimumValue
        vmax = maximumValue
    elif colorScale == 'squareroot':
        if minimumValue < 0:
            raise ValueError("minimumValue {} must be non-negative to apply square root colorScale".format(minimumValue))
        vmin = scipy.sqrt(minimumValue)
        vmax = scipy.sqrt(maximumValue)
    elif colorScale == 'log':
        if minimumValue <= 0:
            raise ValueError("minimumValue {} must be positive to apply log colorScale".format(minimumValue))
        vmin = scipy.log(minimumValue)
        vmax = scipy.log(maximumValue)

    # Generalize to linspace of transform applied to [minimumValue, maximumValue]
    # Then, apply inverse transform to recover the proper values
    x = scipy.array([0., 1.])
    y = scipy.linspace(vmin, vmax, num=mapSize)
    X, Z = scipy.meshgrid(x, y)
    if colorScale == 'linear':
        Y = Z
    if colorScale == 'squareroot':
        Y = Z**2
    elif colorScale == 'log':
        Y = scipy.exp(Z)

    # Now, create the colorbar plot
    fig = pyplot.figure(figsize=(1.0, 3.5))
    ax1 = fig.add_axes([0.55, 0.025, 0.4, 0.85])
    # Create the array as a colored image in the axes
    ax1.pcolorfast([0., 1.], [minimumValue, maximumValue], Z, cmap=cmapName, vmin=vmin, vmax=vmax)
    # Set appropriate y-axis scale, to reflect colorScale
    if colorScale != 'linear':
        ax1.set_yscale(colorScale)
    # Trim axis to correct range
    ax1.set_ylim([minimumValue, maximumValue])
    # x-axis values have no meaning here
    ax1.xaxis.set_visible(False)
    # turn on grid, for perspective on colorbar
    ax1.grid(True)
    # set title to units string
    ax1.set_title(units, fontsize=10, color=(0.0, 0.0, 0.0), weight=650)
    # set axis label font/weight to reasonable value
    for ti in ax1.yaxis.get_ticklabels():
        pyplot.setp(ti, fontsize=8, color=(0.0, 0.0, 0.0), weight=650)
    # Now, save data to png, in memory
    imgdat = cStringIO.StringIO()
    # set background to mostly transparent, for use of colorbar in overlay
    fig.patch.set_alpha(0.4)
    pyplot.savefig(imgdat, dpi=300, format='png')
    pyplot.close()
    imgdat.seek(0)  # return the cursor to the beginning?
    img = Image.open(imgdat)
    return cols, img

def getColorIndices(arrIn, maximumValue, minimumValue, cmapSize, colorScale):
    """
    General method for determining indices for colormap

    Args:
        arrIn - numpy array of values
        maximumValue - numerical maximum value for color scale
        minimumValue - numerical minimum value for color scale
        cmapSize - integer size of the colormap
        colorScale - string in COLOR_SCALE_OPTIONS

    Returns:
        indexArray - numpy array of (unisgned 16 bit integer) indices into the colormap
    
    NOTE: I've hand-jammed this linear/squareroot/log functionality. I should replace this with using the 
    matplotlib transform and inverse functionality. Then, the user could truly use any matplotlib scale object.
    """
    
    cmapSize = int(cmapSize)
    indexArray = scipy.zeros(arrIn.shape, dtype=scipy.uint16)

    if colorScale == 'linear':
        maxval = float(maximumValue)
        minval = float(minimumValue)
        workArray = scipy.cast[scipy.float64](scipy.clip(arrIn, minimumValue, maximumValue))
    elif colorScale == 'squareroot':
        if minimumValue < 0:
            raise ValueError("minimumValue {} must be non-negative to apply square root color scale".format(minimumValue))
        maxval = scipy.sqrt(maximumValue)
        minval = scipy.sqrt(minimumValue)
        workArray = scipy.sqrt(scipy.clip(arrIn, minimumValue, maximumValue))
    elif colorScale == 'log':
        if minimumValue <= 0:
            raise ValueError("minimumValue {} must be positive to apply log color scale".format(minimumValue))
        maxval = scipy.log(maximumValue)
        minval = scipy.log(minimumValue)
        workArray = scipy.log(scipy.clip(arrIn, minimumValue, maximumValue))
    # Use this scaling to calculate the index value into the colormap
    indexArray[:] = (float(cmapSize) - 1.0)*((workArray - minval)/(maxval - minval))
    return indexArray
