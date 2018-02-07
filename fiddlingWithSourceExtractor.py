# fiddling with source extractor
import numpy as np
import matplotlib.pyplot as plt
import sep
from astropy.io import fits
from astropy.coordinates import SkyCoord
from astropy.nddata.utils import NoOverlapError
import astropy.units as u
from astropy.nddata import Cutout2D
from astropy.wcs import WCS
import createSubjectsFunctions as csf


def cutFits(fFile, ra, dec, size=(4 * u.arcsec, 4 * u.arcsec)):
    try:
        if len(size) != 2:
            return
    except Exception as e:
        print(
            "\033[31msize must be an int or length-2 list/tuple/array\033[0m"
        )
    frame = fFile[0].header['SYSTEM'].strip()
    p = SkyCoord(ra=ra * u.degree, dec=dec * u.degree, frame=frame.lower())
    sizeQuant = u.Quantity(size, u.arcsec)
    wcs = WCS(header=fFile[0].header)
    try:
        cutout = Cutout2D(fFile[0].data, p, sizeQuant, wcs=wcs)
        return cutout.data
    except NoOverlapError:
        print(
            'Ra, Dec not inside frame for Ra:' +
            ' {ra}, Dec: {dec}, and frame: {f}'.format(
                ra=ra, dec=dec, f=fFile[0]
            )
        )
    return False


ra, dec, petrotheta = (236.14108, 10.29315, 27.98376)  # ra, dec, petrotheta

f = fits.open('images/3996/5/frame-r-003996-5-0212.fits')
data = cutFits(
    f,
    ra, dec,
    size=(4 * petrotheta * u.arcsec, 4 * petrotheta * u.arcsec)
)
if data is not False:
    bkgArr = f[2].data[0][0]

    data = data.byteswap().newbyteorder()

    o = sep.extract(data, 0.05, segmentation_map=True)
    sizeSortedObjects = sorted(
        enumerate(o[0]), key=lambda src: src[1]['npix']
    )

    mask = csf.maskArr(data, o[1], sizeSortedObjects[-1][0] + 1)
    data[mask] = 0
    plt.imshow(csf.stretchArray(data))
    plt.show()
    # csf.showObjectsOnArr(
    #     data,
    #     [i[1] for i in sizeSortedObjects]
    # )
else:
    print('\033[31mCould not extract cutout, exiting\n\033[0m')
