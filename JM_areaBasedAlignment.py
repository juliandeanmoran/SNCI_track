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

from JM_show_image import show_image
from skimage import io










##########01 align RFP to GFP channels##############################

'''
    [1] set path to dir where your input .tif stack is located
            make sure path is delimited by '//' instead of escape keys
            make sure path does not terminate in '//'

    [2] set fileName to name of your input .tif stack, without file extension (e.g. 'temp6')
            fileName should not have any '.' characters in it

    [3] if video is in form of individual 2D .tifs in a folder:
            open imageJ
            select Import > Image Sequence...
            click on first .tif in your video; imageJ will open it as .tif stack
            select File > Save as > Tiff...
            this will convert file to .tif stack, which this script needs as input

'''

#read in .tif stack as numpy.ndarray
path = ''
fileName = ''
filePath = path + '//' + fileName + '.tif'
inputStack = io.imread(filePath)
frame01 = inputStack[0, :, :]

path = './' + 'JM_areaBasedAlignment_output'
if os.path.isdir(path) == False:
    os.mkdir(path)

path = path + '//testFrameResults'
if os.path.isdir(path) == False:
    os.mkdir(path)

outputDir = fileName.split('.')[0]
outputPath = path + '//' + outputDir
if os.path.isdir(outputPath) == False:
    os.mkdir(outputPath)


#slice out first frames of both colors
frame01_size = frame01.shape
f1R = frame01[:,0:int(frame01_size[1]/2)]
f1G = frame01[:,int(frame01_size[1]/2):(frame01_size[1] + 1)]

f1R_f32 = np.float32(f1R)
f1G_f32 = np.float32(f1G)


#define preliminary variables, assemble pre-alignment image
(H, W) = np.shape(f1R_f32)
warpMode = cv2.MOTION_TRANSLATION

if warpMode == cv2.MOTION_HOMOGRAPHY:
    warpMatr = np.eye(3, 3, dtype = np.float32) #build matr w/ 1s on diagonal
else:
    warpMatr = np.eye(2, 3, dtype = np.float32)


RGB = np.array((*"RGB",))
f1R_redTint = np.multiply.outer(f1R_f32, RGB=='R')
f1R_redTint = cv2.normalize(f1R_redTint, None, 1, 0, cv2.NORM_MINMAX, cv2.CV_32FC1)
f1G_grnTint = np.multiply.outer(f1G_f32, RGB=='G')
f1G_grnTint = cv2.normalize(f1G_grnTint, None, 1, 0, cv2.NORM_MINMAX, cv2.CV_32FC1)
result_bfAlign = f1R_redTint + f1G_grnTint


titleTemp = outputPath + '//' + outputDir + '_t=0001_bfAlign.png'
show_image(result_bfAlign, title='pre-alignment', write=True, fileTitle=titleTemp)


#define iteration conditions
numIterations = 5000
terminationEPS = 1e-10


#define termination criteria
criteria = (
    cv2.TERM_CRITERIA_COUNT | cv2.TERM_CRITERIA_EPS,
    numIterations,
    terminationEPS
)


#find warpMatr w/ cv2.findTransformECC()
(cc, warpMatr) = cv2.findTransformECC(
    f1R_f32,
    f1G_f32,
    warpMatr,
    warpMode,
    criteria,
    inputMask = None,
    gaussFiltSize = 1
)


#apply warpMatr to f1G_f32 w/ cv2.warpPerspective(); iteratable later
if warpMode == cv2.MOTION_HOMOGRAPHY:
    f1G_f32_aligned = cv2.warpPerspective(
        f1G_f32,
        warpMatr,
        (W, H),
        flags = cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP
    )
else:
    f1G_f32_aligned = cv2.warpAffine(
        f1G_f32,
        warpMatr,
        (W, H),
        flags = cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP
    )


#assemble superimposed result ("testframe")
f1G_grnTint_aligned = np.multiply.outer(f1G_f32_aligned, RGB=='G')
f1G_grnTint_aligned = cv2.normalize(f1G_grnTint_aligned, None, 1, 0, cv2.NORM_MINMAX, cv2.CV_32FC1)

result = f1R_redTint + f1G_grnTint_aligned


titleTemp = outputPath + '//' + outputDir + '_t=0000_result.png'
show_image(result, title='aligned test frame', write=True, fileTitle=titleTemp)


#assemble output frame for test case
(output_h, output_w) = np.shape(frame01)

outputFrame = np.eye(output_h, output_w, dtype = np.float32)
outputFrame[:, 0:int(output_w/2)] = f1R_f32
outputFrame[:, int(output_w/2):(output_w + 1)] = f1G_f32_aligned
show_image(outputFrame, title = 'output frame')


#assemble output stack for final output
stackFrameNums = int(np.shape(inputStack)[0])
outputStack = np.zeros((stackFrameNums, output_h, output_w), dtype = np.float32)

for i in range(len(inputStack[:, 0, 0])):
    fR = np.float32(inputStack[i, :, 0:int(output_w/2)])
    fG = np.float32(inputStack[i, :, int(output_w/2):])

    if warpMode == cv2.MOTION_HOMOGRAPHY:
        fG_aligned = cv2.warpPerspective(
            fG,
            warpMatr,
            (W, H),
            flags = cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP
        )
    else:
        fG_aligned = cv2.warpAffine(
            fG,
            warpMatr,
            (W, H),
            flags = cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP
        )

    outputStack[i, :, 0:int(output_w/2)] = fR
    outputStack[i, :, int(output_w/2):] = fG_aligned










##########02 write outputStack as .tif##############################


outputDir = 'JM_areaBasedAlignment_output/'
outputPath = './' + outputDir

if os.path.isdir(outputPath) == False:
    os.mkdir(outputPath)

titleTemp = outputPath + fileName.split('.')[0] + '_aligned.tif'
io.imsave(titleTemp, outputStack)










bp = None