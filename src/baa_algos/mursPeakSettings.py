import scipy
from mursAnomalySettings import DEFAULT_BINS as DEFAULT_REBIN

DEFAULT_SETTINGS = {
    'nominalRange': 6.,  # sigma range to search within, by default
    'integrationLimit': 300.,  # in seconds
    'peakBounds': [200., 260.],  # "good" channel range
    #'peakBounds': [220., 260.],  # "good" channel range
    'badPeakBounds': [180., 320.],  # widest possible peak search area
    'countRange': [200., 2000.],  # valid bounds for the average count rate, do not fit
    'widthBounds': [3., 8.],  # "good" bounds for width
    'badWidthBounds': [2., 12.],  # ignore the fit results if this is not satisfied
    'peakSizeBounds': [3., 50.],  # acceptable peak area in cps, ignore if not satisfied
    'channel': [0.0, 22.00, 58.73, 127.84, 156.74, 225.56, 402.51],
    'energy': [0.0, 121.7817, 344.2785, 778.904, 964.079, 1408.006, 2614.533],
    'resolution_coefficients': [0.60538, 0.71676, 0.0002645],
    'referenceEnergy': 1460.83,
    'messageAge': 120,  # seconds, reset on gap larger than this
}


DEFAULT_CHARACTERIZATION = {
    "channel": [0.0, 22.399660831426115, 59.638187273167055, 129.53105288427571, 158.57931810085162,
                228.15067768144243, 405.74711668041033],
    "energy": [0.0, 121.7817, 344.2785, 778.904, 964.079, 1408.006, 2614.533],
    "reference_channel": 236.29933853462785,
    "reference_energy": 1460.83,
    "resolution_coefficients": [0.60927244113046497, 0.72086471661835128, 0.00030386606502753188]
}
