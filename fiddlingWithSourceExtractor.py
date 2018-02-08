# fiddling with source extractor
import matplotlib.pyplot as plt
import sep
import sys
from astropy.io import fits
import astropy.units as u
import sdssCutoutGrab as scg
import createSubjectsFunctions as csf


ra, dec, petrotheta = (236.14108, 10.29315, 27.98376)

f = fits.open('images/3996/5/frame-r-003996-5-0212.fits')
data = scg.cutFits(
    f,
    ra, dec,
    size=(4 * petrotheta * u.arcsec, 4 * petrotheta * u.arcsec)
)
if data is not False:
    bkgArr = f[2].data[0][0]
    frame = scg.queryFromRaDec(ra, dec)
    if not len(frame):
        print("💩  Couldn\'t find any galaxies")
        sys.exit(0)
    data = data.byteswap().newbyteorder()

    o = sep.extract(data, 0.05, segmentation_map=True)
    sizeSortedObjects = sorted(
        enumerate(o[0]), key=lambda src: src[1]['npix']
    )

    mask = csf.maskArr(data, o[1], sizeSortedObjects[-1][0] + 1)
    data[mask] = 0
    plt.imshow(csf.stretchArray(data))
    plt.show()
    psf = csf.getPSF((ra, dec), frame[0], f)
    # csf.showObjectsOnArr(
    #     data,
    #     [i[1] for i in sizeSortedObjects]
    # )
else:
    print('\033[31mCould not extract cutout, exiting\n\033[0m')


def getGalDeets(raDecPetro):
    ra, dec = raDecPetro['ra'], raDecPetro['dec']
    petrotheta = raDecPetro['petrotheta']

    print('🛰  Looking for galaxy at {}, {}'.format(ra, dec))
    frame = scg.queryFromRaDec(ra, dec)
    if not len(frame):
        print("💩  Couldn\'t find any galaxies")
        return False
    fileLoc = scg.getBandFits(frame[0])
    fitsFile = fits.open(fileLoc)
    # read it in and crop out around the galaxy
    imageData = scg.cutFits(
        fitsFile,
        ra, dec,
        size=(4 * petrotheta * u.arcsec, 4 * petrotheta * u.arcsec)
    )
    if imageData is False:
        print('\t💀  \033[31mReturned False from image Data\033[0m')
        print('\tRa: {} Dec: {}'.format(ra, dec))
        return False

    # Use source extractor to identify objects TODO proper deblending
    objects, segmentation_map = csf.sourceExtractImage(
        imageData,
        fitsFile[2].data[0][0]
    )
    # create a true/false masking array
    mask = csf.maskArr(imageData, segmentation_map, objects[-1][0] + 1)

    # create the masked image
    maskedImageData = imageData[:]
    maskedImageData[mask] = 0

    # Now we find the PSF
    psf = csf.getPSF((ra, dec), frame[0], fitsFile)
    c = 20
    # crop out most of the 0-ish stuff (guessing)
    psfCut = psf[c:-c, c:-c]
    # normalise so we don't lose flux
    psfCut = psfCut / sum(psfCut)
    finalPsf = psfCut.reshape(psfCut.size)
    return frame[0], maskedImageData, finalPsf, segmentation_map
