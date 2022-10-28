'''
SNCI autotracking master script
Julian Moran
2021-01-24
'''









##########00 import modules##############################

#standard library imports
import tkinter as tk
from copy import deepcopy
import os
import time
import csv


#third  party imports
import cv2
import ffmpeg
import imutils
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from skimage import io


#local application imports
from JM_show_image import show_image
from JM_somaShape import somaShape
from JM_fluorplot import fluorPlot
from SNCI_track_autotrackGUI import autotrackGUI










##########01 define arguments##############################

#define input video for streaming
path = ''
fileName = ''
filePath = path + '//' + fileName + '.avi'

#define neuron ID label for filenaming purposes
list_neuronID = ['neuron']

#define autotrackGUI constructor arguments
sizeCoeff = 2
str_tracker = 'csrt'

#define somaShape() arguments
use_somaShape = False
somaShape_cvrg = 1.0
somaShape_filter = 'mean'

#define fluorPlot() arguments
sep_chan = True

#define script output path
outputPath = './' + 'SNCI_track_autotrack_output/'
if os.path.isdir(outputPath) == False:
    os.mkdir(outputPath)

outputPath = outputPath + '/' + fileName
if os.path.isdir(outputPath) == False:
    os.mkdir(outputPath)











##########02 autotrack and proofread target soma##############################

#initialise video stream
print('[INFO] loading video stream...')
vs  = cv2.VideoCapture(filePath)
time.sleep(2.0)

#run SNCI_track's autotracking and proofreading GUI
gui = autotrackGUI(vs = vs, outputPath = outputPath, strTracker = 'csrt', sizeCoeff = sizeCoeff)
gui.root.mainloop()


roiCoords = gui.roiCoordList_master #each coordList follows [x, y, w, h] pattern
titleTemp = outputPath + '//roiCoords_XYWH.tsv'


with open(titleTemp, 'w', newline='') as f_output:
    tsv_output = csv.writer(f_output, delimiter='\n')
    tsv_output.writerow(roiCoords)










##########03 preprocess data###########################


'''
structure data such that:
    each tracked neuron has its own array, featuring every frame
    each tracked neuron's list stores intensity values instead of coordinates
    each tracked neuron's list is contained in a master list for that channel
    red, grn, and red/grn have their own master lists
'''

#read in .tif stack to preserve dynamic range
filePath = path + '/' + fileName + '.tif'
stack = io.imread(filePath)
(H,W) = stack.shape[1:]


#build master lists of avg intensity for red and grn channels in gui.frameList
lst_avgIntenR_master = []
lst_avgIntenG_master = []
x_shift = int(np.shape(stack[0])[1] / 2)


for i in range(len(roiCoords[0])): #iterate once per neuron

    #define lists of all ROI intensity values for each neuron; pulls one ROI from each frame
    lst_avgIntenR_neuron = []
    lst_avgIntenG_neuron = []

    for j in range(len(roiCoords)): #iterate once per frame

        #check for whether any roi coordinates fall outside of frame bounds
        (x, y, w, h) = roiCoords[j][i]
        x = int(x / 2)
        y = int(y / 2)
        w = int(w / 2)
        h = int(h / 2)
        
        if x < 0:
            w = w + x
            x = 0
        if (x + w) > np.shape(stack[j])[1]:
            w = np.shape(stack[j])[1] - x

        if y < 0:
            h = h + y
            y = 0
        if (y + h) > np.shape(stack[j])[0]:
            h = np.shape(stack[j])[0] - y

        roi_red = stack[j][y:(y + h), x:(x + w)]
        x = x + x_shift
        roi_grn = stack[j][y:(y + h), x:(x + w)]


        #build soma-shaped mask within ROI
        if use_somaShape:
            roi_soma = somaShape(
                ROI = roi_red,
                cvrg = somaShape_cvrg,
                blurType = somaShape_filter
            )

            #calculate avg pixel intensity w/in red and grn ROIs
            avgInt_R = cv2.mean(roi_red, roi_soma) #use mask output by somaShape() to find mean
            avgInt_G = cv2.mean(roi_grn, roi_soma) #same

        else:
            #calculate avg pixel intensity w/in red ROI
            avgInt_R = cv2.mean(roi_red)
            avgInt_G = cv2.mean(roi_grn)

        #append avg intensity measures to neuron's lists 
        lst_avgIntenR_neuron.append(avgInt_R[0])
        lst_avgIntenG_neuron.append(avgInt_G[0])

    #append neuron's lists to its appropriate master lists
    lst_avgIntenR_master.append(lst_avgIntenR_neuron)
    lst_avgIntenG_master.append(lst_avgIntenG_neuron)




#build master list of red/grn intensity for gui.frameList
lst_avgIntenGR_master = []

for i in range(len(roiCoords[0])): #iterate once per neuron
    lst_avgIntenGR_neuron = []

    for j in range(len(roiCoords)): #iterate once per frame
        avgInt_GR = (lst_avgIntenG_master[i][j] / lst_avgIntenR_master[i][j])
        lst_avgIntenGR_neuron.append(avgInt_GR)
    
    lst_avgIntenGR_master.append(lst_avgIntenGR_neuron)










##########04 build fluorescence plots###########################


#define maximum values for plotting
maxInts_R = []
maxInts_G = []
maxInts_GR = []

for i in range(len(roiCoords[0])): #iterate once per neuron
    maxInt = max(lst_avgIntenR_master[i])
    maxInts_R.append(maxInt)

    maxInt = max(lst_avgIntenG_master[i])
    maxInts_G.append(maxInt)

    maxInt = max(lst_avgIntenGR_master[i])
    maxInts_GR.append(maxInt)

ymax_R = max(maxInts_R)
ymax_G = max(maxInts_G)

ymax = int(max(ymax_R, ymax_G))
ymax = int(1.1 * ymax)

ymax_GR = max(maxInts_GR)
ymax_GR = 1.1 * ymax_GR



#build and write fluorescence plots to disk
for i in range(len(roiCoords[0])):

    fluorPlot(
        listIntenR = lst_avgIntenR_master[i],
        listIntenG = lst_avgIntenG_master[i],
        listIntenGR = lst_avgIntenGR_master[i],
        neuronName = list_neuronID[i],
        ymax_singleChann = ymax,
        ymax_GR = ymax_GR,
        outputPath = outputPath,
        fileName = fileName,
        sep_chan = sep_chan
    )


#capture frame 50 of image and write to disk
titleTemp = outputPath + '//' + fileName + '_' + list_neuronID[0] + '_t=49.png'

show_image(
    gui.frameList[49],
    title = list_neuronID[0] + ', t = 49',
    write = True,
    fileTitle = titleTemp
)


#build array of intensity data and write to disk for each tracked neuron
# ar_master = []
ar_names = ['GFP_intensity', 'RFP_intensity', 'GFP/RFP']

for i in range(len(roiCoords[0])): #iterate once per neuron
    ar = np.zeros((len(lst_avgIntenGR_neuron), 3))

    ar[0:len(lst_avgIntenGR_neuron), 0] = lst_avgIntenG_master[i]
    ar[0:len(lst_avgIntenGR_neuron), 1] = lst_avgIntenR_master[i]
    ar[0:len(lst_avgIntenGR_neuron), 2] = lst_avgIntenGR_master[i]

    df = pd.DataFrame(ar, columns = ar_names)
    titleTemp = outputPath + '//' + fileName + '_' + list_neuronID[i] + '.tsv'
    df.to_csv(titleTemp, index = False, header = True, sep = '\t')




bp = None






'''   
problems

    sizeCoeff has no value
        please define it as a variable in your autotrackergui class


to do; polishing

    change output folder directories such that they are stored under one ./output_temp dir

    implement windows explorer solution to definining input data file path

    implement run-from-terminal functionality

    implement version control w/ numbering system (start making git branches)

    automatically output a .txt showing input parameters
        e.g. use_somaShape
        e.g. cvrg
        e.g. version control

    figure out how to run .py scripts from GPU / minimise RAM stick usage
'''