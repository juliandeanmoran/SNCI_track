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










##########01 read in MIP .tif##############################

'''
        [1] set path to dir where your input .tif stack is located
                make sure path is delimited by '//' instead of escape keys
                make sure path does not terminate in '//'

        [2] set fileName to name of your input .tif stack, without file extension (e.g. 'temp6')
                fileName should not have any '.' characters in it


        [3] ensure input MIP is formatted as collows:
                shape: [n_frames, n_channels, h, w]
                RFP channel index = 0
                GFP channel index = 1

        [4] script assumes RFP and GFP channels already aligned
                see testFrame to validate
                
'''


#read in .tif stack as numpy.ndarray
path = ''
fileName = ''
filePath = path + '//' + fileName + '.tif'
inputMIP = io.imread(filePath)












##########02 reformat .tif to match SNCI microscope output##############################


(MIP_l, MIP_c, MIP_h, MIP_w) = np.shape(inputMIP)

outputMIP = np.zeros((MIP_l, MIP_h, MIP_w * 2), dtype = np.float32)

for i in range(0, len(inputMIP[:, 0, 0, 0])):

        frame_r = inputMIP[i, 0, :, :]
        frame_g = inputMIP[i, 1, :, :]

        outputMIP[i, :, 0:int(MIP_w)] = frame_r
        outputMIP[i, :, int(MIP_w):] = frame_g



show_image(outputMIP[0])












##########03 write preprocessed MIP to source dir##############################

titleTemp = path + '//' + fileName + '_processed.tif'
io.imsave(titleTemp, outputMIP)










bp = None