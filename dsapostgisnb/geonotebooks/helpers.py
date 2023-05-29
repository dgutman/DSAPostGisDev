### Let's generate a simple function that just does grid size computations at different resolutions and magnifications
import large_image
import girder_client
import time, requests
import numpy as np
import pandas as pd

import hashlib

from sqlmodel import Field, Session, SQLModel, create_engine

from fastapifiles.models import featureSetExtractionParams


# https://dev.to/rexosei/how-to-make-a-field-unique-with-sqlmodel-4km9


dbApiUrl = "http://dsapostgisapi:82/"
DATABASE_URL = "postgresql://docker:docker@postgisdb/dsagis"


def getPostGisImageId(imgFileRoot, dsaApiUrl, dsaImageId):
    """Currently I am only allowing visualization of a small set of images, and so I am simply mapping
    the DSA image name, and creating a copy of this information in the DSAItems table in my app"""
    r = requests.post(dbApiUrl + f"add-DSAImage?imageId={dsaImageId}&dsaApiUrl={dsaApiUrl}")
    return r.json()


def getFeatureSetId(imageId, featureType, featureSetFile):
    fileMD5 = computeFileMD5(featureSetFile)
    print(fileMD5)
    engine = create_engine(DATABASE_URL)
    with Session(engine) as session:
        exist = (
            session.query(featureSetExtractionParams)
            .filter(featureSetExtractionParams.imageId == imageId)
            .filter(featureSetExtractionParams.resultsFileMD5 == fileMD5)
            .first()
        )
        if exist:
            return exist
        else:
            print("Not found")

    ## Check if I've already uploaded the feature set

    #     curFeatureSet = models.imageFeatureSets(
    #         featureType="nftFeature",
    #         imageId=imageId,
    #         totalObjects=len(df),
    #         imageFeatureParams={"embeddingNames": ["SIFT1", "SIFT2", "SIFT3"]},
    #     )

    # with Session(engine) as session:
    #     curFeatureSet = models.imageFeatureSets(
    #         featureType="nftFeature",
    #         imageId=imageId,
    #         totalObjects=len(df),
    #         imageFeatureParams={"embeddingNames": ["SIFT1", "SIFT2", "SIFT3"]},
    #     )
    #     session.add(curFeatureSet)
    #     session.commit()
    #     session.refresh(curFeatureSet)
    # print(curFeatureSet)

    return fileMD5


def computeFileMD5(inputFilePath):
    # Open,close, read file and calculate MD5 on its contents
    with open(inputFilePath, "rb") as file_to_check:
        # read contents of the file
        data = file_to_check.read()
        # pipe contents of the file through
        md5_returned = hashlib.md5(data).hexdigest()
    return md5_returned


def computeGridInfo(imagePath, magnification=20, tileSize="native", opType="iterateOnly"):
    ## Create a largeImage Pointed
    ts = large_image.open(imagePath)

    computationStats = {"imageName": imagePath, "opType": opType}
    tilesProcessed = 0
    bytesRead = 0

    ## Compute start time of algorithm
    st = time.time()
    computationStats["startTime"] = st

    if tileSize == "native":
        tileWidth = ts.tileWidth
        tileHeight = ts.tileHeight
    else:
        tileWidth = tileSize
        tileHeight = tileSize

    for tile_info in ts.tileIterator(
        region=dict(units="base_pixels"),
        scale=dict(magnification=magnification),
        tile_size=dict(width=tileWidth, height=tileHeight),
        format=large_image.tilesource.TILE_FORMAT_NUMPY,
    ):
        if opType == "pullNPArray":
            #            im_tile = np.array(tile_info["tile"])
            im_tile = tile_info["tile"]
            bytesRead += im_tile.size
        tilesProcessed += 1

    ## Export some of the stats for analtsis
    computationStats["elapsedTime"] = time.time() - st
    computationStats["tilesProcessed"] = tilesProcessed
    computationStats["tileWidth"] = tileWidth
    computationStats["tileHeight"] = tileHeight
    computationStats["sizeX"] = ts.sizeX
    computationStats["sizeY"] = ts.sizeY
    computationStats["bytesRead"] = bytesRead
    computationStats["magnification"] = magnification
    computationStats["tileSizeParam"] = tileSize

    return computationStats


def rgb2lab(rgb):
    r = rgb[0] / 255
    g = rgb[1] / 255
    b = rgb[2] / 255
    x, y, z = 0, 0, 0

    r = r**2.4 if r > 0.04045 else r / 12.92
    g = g**2.4 if g > 0.04045 else g / 12.92
    b = b**2.4 if b > 0.04045 else b / 12.92

    x = (r * 0.4124 + g * 0.3576 + b * 0.1805) / 0.95047
    y = (r * 0.2126 + g * 0.7152 + b * 0.0722) / 1.00000
    z = (r * 0.0193 + g * 0.1192 + b * 0.9505) / 1.08883

    x = x ** (1 / 3) if x > 0.008856 else (7.787 * x) + 16 / 116
    y = y ** (1 / 3) if y > 0.008856 else (7.787 * y) + 16 / 116
    z = z ** (1 / 3) if z > 0.008856 else (7.787 * z) + 16 / 116

    return [(116 * y) - 16, 500 * (x - y), 200 * (y - z)]


def loadFeatureCSVFile(wsiFileName, featureCSVname, featureNamePrefix, colReMappings=None):
    """This takes a csv file path, and a wsiFilename, and a feature_prefix
    and will load it into a dataframe , and collapses the feature vector into
    a single column"""

    df = pd.read_csv(featureCSVname)

    ## This stores the full name of the feature columns to be collapsed..
    featureColumnNames = []
    for c in df.columns:
        if c.startswith(featureNamePrefix):
            featureColumnNames.append(c)

    featureOnly_df = df[featureColumnNames]

    ## Feature embeddings is when I have collapsed the feature vectors into a single column
    df["featureEmbeddings"] = featureOnly_df.apply(lambda row: tuple(row), axis=1).apply(np.array)
    df.drop(columns=featureOnly_df.columns, axis=1, inplace=True)

    if colReMappings:
        df.rename(columns=colReMappings, inplace=True)

    return df


# ## Will use the native tileWidth and tileHeight, seems like it would be faster anyway
# # computeGridInfo(imagePath, opType="pullNPArray")


# import matplotlib.pyplot as plt
# rng = np.random.RandomState(10)  # deterministic random data
# a = np.hstack((rng.normal(size=1000),
#                 rng.normal(loc=5, scale=2, size=1000)))
# _ = plt.hist(a, bins='auto')  # arguments are passed to np.histogram
# plt.title("Histogram with 'auto' bins")

# # plt.show()

# import matplotlib.pyplot as plt
# rng = np.random.RandomState(10)  # deterministic random data
# a = np.hstack((nparr,
#                 rng.normal(loc=5, scale=2, size=1000)))
# _ = plt.hist(a, bins='auto')  # arguments are passed to np.histogram
# plt.title("Histogram with 'auto' bins")

# plt.show()

# #img = cv2.imread('/Users/mustafa/test.jpg')
# gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)

# plt.imshow(gray)
# plt.title('my picture')
# plt.show()

# # grab the image channels, initialize the tuple of colors,
# # the figure and the flattened feature vector
# chans = cv2.split(img_np)
# colors = ("b", "g", "r")
# plt.figure()
# plt.title("'Flattened' Color Histogram")
# plt.xlabel("Bins")
# plt.ylabel("# of Pixels")
# features = []

# # loop over the image channels
# for (chan, color) in zip(chans, colors):
# 	# create a histogram for the current channel and
# 	# concatenate the resulting histograms for each
# 	# channel
# 	hist = cv2.calcHist([chan], [0], None, [256], [0, 256])
# 	features.extend(hist)

# 	# plot the histogram
# 	plt.plot(hist, color = color)
# 	plt.xlim([0, 256])

# # here we are simply showing the dimensionality of the
# # flattened color histogram 256 bins for each channel
# # x 3 channels = 768 total values -- in practice, we would
# # normally not use 256 bins for each channel, a choice
# # between 32-96 bins are normally used, but this tends
# # to be application dependent
# print("flattened feature vector size: %d" % (np.array(features).flatten().shape))


# tif = TIFF.open(tiffFile, mode='r')
# imagetif = tif.read_image()
# imarr=np.array(imagetif)
# # from mpld3 import plugins
# mpld3.enable_notebook()
# fig, ax = plt.subplots(figsize=(10, 10))
# im = ax.imshow(imarr, extent=(10, 20, 10, 20),
#                 origin='lower', zorder=1, interpolation='nearest')

# plt.show()

# result = Image.fromarray(imarr.astype(np.uint32))
# result.save(tiffFile.split('.')[0]+'.png')
# img=cv2.imread(tiffFile.split('.')[0]+'.png')
# print(img.shape)
# img_ch0 = img[:,:,0]
# img_ch1 = img[:,:,1]
# img_ch2 = img[:,:,2]
# img_minor = img_ch2
# img_major = img_ch1
# img_gray = 256 * img_major.astype(np.int) + img_minor.astype(np.int) +1 ##Allows > 256 Channels
# # save gray file
# cv2.imwrite(tiffFile.split('.')[0]+'Gray.png',img_gray)
