##########00 import modules##############################


import imutils
from imutils.video import VideoStream
from imutils.video import FPS

import numpy as np
import matplotlib.pyplot as plt
import cv2
import os
import time
import ffmpeg
import csv

from JM_show_image import show_image
from skimage import io










##########01 read in JM_areaBasedAlignment.py output##############################


'''
@user:
    [1] manually set variables num_blockS and num_constant
            see https://docs.opencv.org/master/d7/d4d/tutorial_py_thresholding.html for explanation

    [2] when video frame opens, draw box around soma to slice out ROI
    
    [3] script will write sliced ROI to disc and then binarize it
'''


path = 'C://Users//julia//OneDrive//documents//MSc_UToronto_thesis//project_SNCI_pipeline//JM_areaBasedAlignment_output'
fileName = 'temp13_aligned'
filePath = path + '//' + fileName + '.avi'
sizeCoeff = 2


#num_blockS = 7 #always ensure num_blockS % 2 == 1 && num_blockS > 1
#num_constant = 2










##########02 open first frame of .avi, slice out square ROI##############################


(majorVer, minorVer, subminorVer) = (cv2.__version__).split('.')

#initialize variables
box = (None, None, None, None)
boxes = None
fps = None

#initialize video stream
vs = cv2.VideoCapture(filePath)
frameNumTemp = 0

#store coordinates for ROI based on user-drawn box
while frameNumTemp is 0:

    #read in frame as uint8; fine for purposes of defining ROI
    frameTemp = vs.read()
    frameTemp = frameTemp[1]

    #resize frameTemp as per user-defined sizeCoeff
    (H,W) = frameTemp.shape[:2]
    frameTemp = imutils.resize(frameTemp, width = W * sizeCoeff)
    (H,W) = frameTemp.shape[:2]

    #display first frame and wait for user input
    cv2.imshow('Frame', frameTemp)
    key = cv2.waitKey(0) & 0xFF

    #start user GUI to slice out ROI
    if key == ord('s'):
        box = cv2.selectROI('Frame', frameTemp, fromCenter = False, showCrosshair = True)
    
    (x, y, w, h) = [int(v) for v in box]


    frameNumTemp = frameNumTemp + 1

vs.release()
cv2.destroyAllWindows()

#slice out ROI
filePath = path + '//' + fileName + '.tif'
stack = io.imread(filePath)
frameTemp = stack[0, :, :]

x = int(x / sizeCoeff)
y = int(y / sizeCoeff)
w = int(w / sizeCoeff)
h = int(h / sizeCoeff)

sliceROI = frameTemp[y:(y+h), x:(x+w)]

#show ROI and write to disc as .png for documentation purposes
outputDir = 'JM_binarizationTest_output/'
outputPath = './' + outputDir

if os.path.isdir(outputPath) == False:
    os.mkdir(outputPath)

titleTemp = outputPath + fileName.split('.')[0] + '_ROIslice.png'
show_image(sliceROI, title = 'pre-binarization ROI', write = True, fileTitle = titleTemp)










##########03 convert ROI slice to uint8 manually##############################
#@juli: never comment out or delete this section because it is a good fleshed-out example


#store info on sliceROI datatype; in this case f32
info = np.finfo(sliceROI.dtype)

#convert data to f64 and normalize by maximum value possible for f32 arrays
sliceROI_uint8 = sliceROI.astype(np.float64) / 4095
#@juli: see ./notes/_pythonArrayTypes_notes.txt for why 4095 is the number i used

#scale normalized values by 255, max value for uint8
sliceROI_uint8 = 255 * sliceROI
sliceROI_uint8 = sliceROI.astype(np.uint8)
sliceROI_uint8 = cv2.medianBlur(sliceROI_uint8, 5)









##########04 convert ROI slice to uint8 using cv2.imread##############################


#@juli: this doesn't work because cv2.imread() is broken

# #write out sliceROI as .tiff for compression purposes
# titleTemp = outputPath + fileName.split('.')[0] + '_ROIslice_uint8.tiff'
# cv2.imwrite(titleTemp, sliceROI)

# #read back in with cv2.imread(), which reads in as uint8
# sliceROI_uint8 = cv2.imread(titleTemp, 0)









##########05 threshold/binarize ROI##############################


#median-blur image for pre-processing
sliceROI_mediBlur = cv2.medianBlur(sliceROI, 5)
titleTemp = outputPath + fileName.split('.')[0] + '_ROIslice_mediBlur.png'

show_image(
    sliceROI_mediBlur,
    title = 'median-blurred ROI',
    write = True,
    fileTitle = titleTemp
)


#mean-blur image for pre-processing
sliceROI_meanBlur = cv2.blur(sliceROI_uint8, (5, 5))
titleTemp = outputPath + fileName.split('.')[0] + '_ROIslice_meanBlur.png'

show_image(
    sliceROI_meanBlur,
    title = 'mean-blurred ROI',
    write = True,
    fileTitle = titleTemp
)


#gaussian-blur image for pre-processing
sliceROI_gausBlur = cv2.GaussianBlur(sliceROI, (5, 5),0)
titleTemp = outputPath + fileName.split('.')[0] + '_ROIslice_gausBlur.png'

show_image(
    sliceROI_gausBlur,
    title = 'gaussian-blurred ROI',
    write = True,
    fileTitle = titleTemp
)


#pick one to use for binarization
sliceROI_blur = sliceROI_meanBlur


# #find threshold that parses out top (hi_pnctg * 100)% of pixels
# maxInt = int(np.max(sliceROI_blur)) + 1
# hi_pcntg = 0.3

# hist = cv2.calcHist(
#     [sliceROI_blur],
#     [0],
#     None,
#     [maxInt],
#     [0, maxInt]
# ).flatten()

# #hist = hist[hist != 0]
# #maxTemp = len(hist)

# totalCount = sliceROI_blur.shape[0] * sliceROI_blur.shape[1]
# targetCount = hi_pcntg * totalCount

# countTemp = 0
# for i in range(maxInt - 1, 0, -1):
#     countTemp = countTemp + int(hist[i])
#     if targetCount <= countTemp:
#         hiThresh = i
#         break

#     else:
#         hiThresh = 0


# sliceROI_simpleThresh = cv2.threshold(sliceROI_blur, hiThresh, 4095, cv2.THRESH_BINARY)
# sliceROI_simpleThresh = sliceROI_simpleThresh[1]


# titleTemp = outputPath + fileName.split('.')[0] + '_ROIslice_simplThresh.png'
# show_image(
#     sliceROI_simpleThresh,
#     title = 'simple-threshold ROI',
#     write = True,
#     fileTitle = titleTemp
# )


#perform otsu thresholding
sliceROI_otsuThresh = cv2.threshold(
    sliceROI_blur,
    0,
    4095,
    cv2.THRESH_BINARY+cv2.THRESH_OTSU
)
sliceROI_otsuThresh = sliceROI_otsuThresh[1]


titleTemp = outputPath + fileName.split('.')[0] + '_ROIslice_otsuThresh.png'
show_image(
    sliceROI_otsuThresh,
    title = 'otsu-threshold ROI',
    write = True,
    fileTitle = titleTemp
)



# #perform adaptive thresholding from uint8 version of sliceROI using adaptive mean
# #num_blockS = 7 #always ensure num_blockS % 2 == 1 && num_blockS > 1
# #num_constant = 2

# sliceROI_dynamiThresh = cv2.adaptiveThreshold(
#     sliceROI_uint8,
#     4095,
#     cv2.ADAPTIVE_THRESH_MEAN_C,
#     cv2.THRESH_BINARY,
#     blockSize = num_blockS,
#     C = num_constant
# )

# titleTemp = (
#     outputPath + 
#     fileName.split('.')[0] +
#     '_ROIslice' +
#     '_' +
#     str(num_blockS) +
#     '_' +
#     str(num_constant) +
#     '_adaptMeanThresh.png')

# show_image(
#     sliceROI_dynamiThresh,
#     title = 'mean-adaptive-threshold ROI, blockSize = ' + str(num_blockS) + ', C = ' + str(num_constant),
#     write = True,
#     fileTitle = titleTemp
# )




# #perform adaptive thresholding from uint8 version of sliceROI using adaptive gaussian
# num_blockS = 7 #always ensure num_blockS % 2 == 1 && num_blockS > 1
# num_constant = 2

# sliceROI_dynamiThresh = cv2.adaptiveThreshold(
#     sliceROI_uint8,
#     4095,
#     cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
#     cv2.THRESH_BINARY,
#     blockSize = num_blockS,
#     C = num_constant
# )

# titleTemp = (
#     outputPath + 
#     fileName.split('.')[0] +
#     '_ROIslice' +
#     '_' +
#     str(num_blockS) +
#     '_' +
#     str(num_constant) +
#     '_adaptGausThresh.png')

# show_image(
#     sliceROI_dynamiThresh,
#     title = 'Gauss-adaptive-threshold ROI, blockSize = ' + str(num_blockS) + ', C = ' + str(num_constant),
#     write = True,
#     fileTitle = titleTemp
# )










##########06 contour detection##############################


#convert sliceROI_simpleThresh to uint8
sliceROI_simpleThresh_uint8 = sliceROI_otsuThresh.astype(np.float64) / 4095
#@juli: see ./notes/_pythonArrayTypes_notes.txt for why 4095 is the number i used

sliceROI_simpleThresh_uint8 = 255 * sliceROI_simpleThresh_uint8
sliceROI_simpleThresh_uint8 = sliceROI_simpleThresh_uint8.astype(np.uint8)


#find contours
contours, hierarchy = cv2.findContours(
    sliceROI_simpleThresh_uint8,
    cv2.RETR_TREE,
    cv2.CHAIN_APPROX_NONE
)
cont = contours[0] #contours should be of length 1 only


#build mask
mask = np.zeros(sliceROI_simpleThresh_uint8.shape, np.uint8)
cv2.drawContours(mask, [cont], 0, 255, -1)
#@juli: calling show_image() on mask right now should show you why contour detection is redundant
#           compare mask with sliceROI_simpleThresh; they look the exact same

titleTemp = outputPath + fileName.split('.')[0] + '_ROIslice_contMask.png'

show_image(
    mask,
    title = 'all-black mask with white-filled contour drawn on',
    write = True,
    fileTitle = titleTemp
)










##########07 calculate average pixel intensity within soma##############################


#calculate average pixel intensity in sliceROI using contour-drawn mask for indexing
meanInt_cont = cv2.mean(sliceROI, mask = mask)
meanInt_cont = meanInt_cont[0]


#calculate average pixel intensity in sliceROI using sliceROI_simpleThresh for indexing
meanInt_thre = cv2.mean(sliceROI, mask = sliceROI_simpleThresh_uint8)
meanInt_thre = meanInt_thre[0]


#write output
titleTemp = outputPath + fileName.split('.')[0] + '_ROIslice_pixelInt.tsv'


with open(titleTemp, 'w') as out_file:
    tsv_writer = csv.writer(out_file, delimiter = '\t')
    tsv_writer.writerow(['masking_substrate', 'mean_pixel_intensity'])
    tsv_writer.writerow(['contMask', meanInt_cont])
    tsv_writer.writerow(['simpThre', meanInt_thre])













bp = None






