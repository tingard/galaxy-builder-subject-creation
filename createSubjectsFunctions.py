import sdss_psf
import numpy as np
import sep
from astropy.wcs import WCS
from astropy.io import fits
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
from PIL import Image
import os
import time
from copy import copy

import sdssCutoutGrab as scg


def stretchArray(arr, a=0.1):
    arr = (arr - np.amin(arr)) / (np.amax(arr - np.amin(arr)))
    return np.arcsinh(
        (arr - np.amin(arr)) / (np.amax(arr - np.amin(arr))) / a
    ) / np.arcsinh(1 / a)


def inverseArcsinh(arr, a=0.1):
    return a * np.sinh(arr * np.arcsinh(1 / a))


def makeEllipseMask(e, x, y, threshold=0.01):
    a, b, angl = e['a'], e['b'], e['theta']
    x = x - e['x']
    y = y - e['y']
    return (np.cos(angl)**2 / a**2 + np.sin(angl)**2 / b**2) * x**2 +\
        2 * np.cos(angl) * np.sin(angl) * (1 / a**2 - 1 / b**2) * x * y +\
        (np.sin(angl)**2 / a**2 + np.cos(angl)**2 / b**2) * y**2 < 1 +\
        threshold


def sourceExtractImage(data, bkgArr, thresh=0.05):
    """Extract sources from data array and return enumerated objects sorted
    smallest to largest, and the segmentation map provided by source extractor
    """
    data = data.byteswap().newbyteorder()

    o = sep.extract(data, thresh, segmentation_map=True)
    sizeSortedObjects = sorted(
        enumerate(o[0]), key=lambda src: src[1]['npix']
    )
    return sizeSortedObjects, o[1]


def maskArr(arrIn, segMap, maskID):
    """Return a true/false mask given a segmentation map and segmentation ID
    True signifies the pixel should be masked
    """
    return np.logical_and(segMap != maskID, segMap != 0)


def maskArrWithEllipses(arrIn, objects):
    # plot background-subtracted image
    mask = np.zeros(arrIn.shape, dtype=bool)
    y, x = np.ogrid[0:mask.shape[0], 0:mask.shape[1]]
    for i in range(len(objects)):
        el = copy(objects[i])
        el['a'], el['b'] = 3 * el['a'], 3 * el['b']
        elMask = makeEllipseMask(el, x, y)
        mask[elMask] = True
    return mask


def showObjectsOnArr(arr, objects):
    fix, ax = plt.subplots()
    ax.imshow(
        stretchArray(arr),
        interpolation='nearest',
        cmap='gray',
        origin='lower',
        vmax=0.6
    )
    # plot an ellipse for each object
    for i in range(len(objects) - 1):
        e = Ellipse(xy=(objects[i]['x'], objects[i]['y']),
                    width=6 * objects[i]['a'],
                    height=6 * objects[i]['b'],
                    angle=objects[i]['theta'] * 180. / np.pi)
        e.set_facecolor('none')
        e.set_edgecolor('red')
        ax.add_artist(e)
    eMain = Ellipse(
        xy=(objects[-1]['x'], objects[-1]['y']),
        width=6 * objects[-1]['a'],
        height=6 * objects[-1]['b'],
        angle=objects[-1]['theta'] * 180. / np.pi
    )
    eMain.set_facecolor('none')
    eMain.set_edgecolor('green')
    ax.add_artist(eMain)
    plt.show()


def saveImage(
        arr, fname='testImage.png', resize=False, size=(512, 512),
        resample=Image.HAMMING):
    # ensure image is normalised to [0, 255]
    print('📷  Saving image to {}'.format(fname))
    arr = (arr - np.amin(arr)) / np.amax(arr - np.amin(arr)) * 255
    # cast to uint8 with a weird coordinate swap (idk why)
    im = Image.fromarray(
        np.uint8(np.flipud(np.swapaxes(np.flipud(arr), 0, 1)))
    )
    # want to preserve aspect ratio, so increase the width to provided width
    correctedSize = (size[0], int(im.size[1] / im.size[0] * size[0]))
    if resize:
        im = im.resize(correctedSize, resample)
    im.save(fname)
    return im


def getPSF(galCoord, frame, fitsFile,
           fname='./tmpPsfFile.fit', deleteOnComplete=True):
    wcs = WCS(fitsFile[0].header)
    coords = wcs.wcs_world2pix([galCoord], 1)
    psfQueryUrl = 'https://data.sdss.org/sas/dr14/eboss/photo/redux/' + \
        '{rerun}/{run}/objcs/{camcol}/' + \
        'psField-{run:06d}-{camcol}-{field:04d}.fit'
    scg.downloadFile(
        psfQueryUrl.format(**frame),
        fname,
        overwrite=True,
        decompress=False
    )
    psfield = fits.open(fname)
    bandnum = 'ugriz'.index('r')
    hdu = psfield[bandnum + 1]
    if deleteOnComplete:
        os.remove(fname)
    return sdss_psf.sdss_psf_at_points(hdu, *coords[0])
