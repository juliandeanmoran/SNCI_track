'''
function defn for somaShape()
2020-12-15
'''


import numpy as np
import matplotlib.pyplot as plt
import cv2
import os

from JM_show_image import show_image











'''
somaShape()

@param ROI
    arra; numpy array sliced from coordinates, containing rectangular ROI of soma bright spot
        must by greyscale single-channel f32
@param cvrg
    flt; size of brightest ROI percentile used to create soma-shaped mask
@param blurType
    str; type of low-pass filter technique to use in pre-processing ROI
        if blurType == 'medi'; use median blur
        if blurType == 'mean'; use mean blur
        if blurType == 'gaus'; use gaussian blur
@desc
    binarize input ROI as per percentile threshold, using user-specified pre-blurring

e.g. somaShape(sliceROI, 0.3, 'mean')
>> #binarized array with soma-shape contour filled in bright-white, background black
'''

def somaShape(ROI, cvrg, blurType):

    #threshold / binarize ROI
    if blurType is 'mean':
        ROI_blur = cv2.blur(ROI, (5, 5))

    elif blurType is 'medi':
        ROI_blur = cv2.medianBlur(ROI, 5)

    elif blurType is 'gaus':
        ROI_blur = cv2.GaussianBlur(ROI, (5, 5), 0)
    
    else:
        print('Error: blurType is not specified or has an unacceptable value')
        return(None)


    #determine threshold for isolating cvrg portion of ROI
    maxInt = int(np.max(ROI_blur)) + 1
    hist = cv2.calcHist(
        [ROI_blur],
        [0],
        None,
        [maxInt],
        [0, maxInt]
    ).flatten()

    totalCount = ROI_blur.shape[0] * ROI_blur.shape[1]
    targetCount = cvrg * totalCount

    countTemp = 0
    for i in range(maxInt - 1, 0, -1):
        countTemp = countTemp + int(hist[i])
        if targetCount <= countTemp:
            hiThresh = i
            break
        
        else:
            hiThresh = 0

    if hiThresh is 0:
        print('[WARNING] could not determine a threshold for ROI binarization.')
    

    #binarize ROI using simple binarization
    ROI_somaShaped = cv2.threshold(ROI_blur, hiThresh, 4095, cv2.THRESH_BINARY)
    ROI_somaShaped = ROI_somaShaped[1]

    #convert ROI_somaShaped to np.uint8
    ROI_somaShaped_uint8 = ROI_somaShaped.astype(np.float64) / 4095
        #@juli: see ./notes/_pythonArrayTypes_notes.txt for why 4095 is the number i used
    ROI_somaShaped_uint8 = 255 * ROI_somaShaped_uint8
    ROI_somaShaped_uint8 = ROI_somaShaped_uint8.astype(np.uint8)


    return(ROI_somaShaped_uint8)










bp = None
