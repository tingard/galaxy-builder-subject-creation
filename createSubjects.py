import os
import json
import gzip
import shutil
from numpy import sum
import astropy.units as u
from astropy.io import fits
import sdssCutoutGrab as scg
import createSubjectsFunctions as csf


# TODO: replace indexing with some kind of proper object ID
def main(objList, outFolder='subjects'):
    # objList is list of (ra, dec, petrotheta)s for target galaxies
    # make sure the outfolder exists
    if not os.path.exists(outFolder):
        os.mkdir(outFolder)
    psfs = []
    # cycle through the input objects
    for i, (ra, dec, petrotheta) in enumerate(objList):
        # search by ra, dec
        print('🛰  Looking for galaxy at {}, {}'.format(ra, dec))
        frame = scg.queryFromRaDec(ra, dec)
        if not len(frame):
            print("💩  Couldn\'t find any galaxies")
            continue
        fileLoc = scg.getBandFits(frame[0])
        # read it in and crop out around the galaxy
        imageData = scg.cutFits(
            fileLoc,
            ra, dec,
            size=(4 * petrotheta * u.arcsec, 4 * petrotheta * u.arcsec)
        )
        if imageData is False:
            print('\t💀  \033[31mReturned False from image Data\033[0m')
            print('\tRa: {} Dec: {}'.format(ra, dec))
            continue

        # Use source extractor to identify objects TODO proper deblending
        objects, segmentation_map = csf.sourceExtractImage(
            imageData,
            fits.open(fileLoc)[2].data[0][0]
        )
        # create a true/false masking array
        mask = csf.maskArr(imageData, segmentation_map, objects[-1][0] + 1)

        # create the masked image
        maskedImageData = imageData[:]
        maskedImageData[mask] = 0

        # apply an asinh stretch and save the image to the outfolder
        csf.saveImage(
            csf.stretchArray(maskedImageData),
            fname="{}/image_{}.png".format(outFolder, i),
            resize=True
        )
        # Now we find the PSF
        psf = csf.getPSF((ra, dec), frame[0], fileLoc)
        c = 20
        # crop out most of the 0-ish stuff
        psfCut = psf[c:-c, c:-c]
        # normalise so we don't lose flux
        psfCut = psfCut / sum(psfCut)
        psfs += [[str(i) for i in psfCut.reshape(psfCut.size)]]

        # generate the model json
        model = {
            'psf': psfCut.tolist(),
            'mask': mask.tolist(),
            'width': imageData.shape[1],
            'height': imageData.shape[0],
        }
        # and the difference json
        difference = {
            'imageData': imageData.tolist(),
            'psf': psfCut.tolist(),
            'psfWidth': psfCut.shape[1],
            'psfHeight': psfCut.shape[0],
            'width': imageData.shape[1],
            'height': imageData.shape[0],
        }
        # write out the model (saving a gzipped and non-gzipped version)
        modelFileName = '{}/model_{}.json'.format(outFolder, i)
        with open(modelFileName, 'w') as f:
            json.dump(model, f)
        with open(modelFileName, 'rb') as f_in, \
                gzip.open(modelFileName + '.gz', 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

        # write out the difference
        diffFileName = '{}/difference_{}.json'.format(outFolder, i)
        with open(diffFileName, 'w') as f:
            json.dump(difference, f)
        with open(diffFileName, 'rb') as f_in, \
                gzip.open(diffFileName + '.gz', 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)


if __name__ == '__main__':
    main((
        (236.14108, 10.29315, 27.98376),
    ))
