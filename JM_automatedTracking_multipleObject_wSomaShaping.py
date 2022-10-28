'''
Automated tracking, multiple object, with soma shaping
Julian Moran
''' 


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
from JM_somaShape import somaShape
from skimage import io










##########01 read in JM_areaBasedAlignment.py output##############################


'''
@user:
    [1] convert output .tif  from  JM_areaBasedAlignment.py to .avi in imageJ

    [2] set path to where your input .tif stack is located
            ensure path is delimited by '//' rather than escape keys
            ensure path DOES NOT terminate in '//'

    [3] set fileName to name of your input .avi and .tif stack, without file extension
            ignoring file extension, they should have the same name (e.g. 'temp6_aligned')
            name should not have any '.' characters in it
    
    [4] set listNeuronNames to the tags you would like in your output file name for each neuron (optional)
            if you don't want to name your neurons, set to []

    [5] set sizeCoeff to how large you would like the video to display (set to a whole integer)
            sizeCoeff = 2 is usually ideal
    
    [6] set strTracker to tracker you want to use
            see OPENCV_OBJECT_TRACKER dict for strings
            e.g. 'csrt'
            e.g. 'boosting'
    
    [7] set somaShapeCoverage to how much of each ROI box you want to shape the soma to
            e.g. somaShapeCoverage = 0.3 will draw a contour around the brightest 30% pixels in ROI box
    
    [8] set filterType to what kind of pre-blurring you want to do when soma-shaping
            i.e. 'mean' does mean pre-blurring; strongly advise using this
            i.e. 'medi' does median pre-blurring
            i.e. 'gaus' does gaussian pre-blurring; strongly advise against this
    
    [9] use autotracking video-stream GUI
        [a] when tracking GUI opens, press 's' to enter selection mode

        [b] press 's' again to begin selecting an ROI; click and drag box around your desired ROI

        [c] press 'enter' when you are happy with the ROI shape

        [d] repeat [2, 3] as needed for each desired ROI

        [e] press 'd' when all desired ROIs have been specified; tracking will now proceed

        [f] press 'q' to quit the GUI and destroy all windows
                note: this will terminate tracking immediately
                note: tracking typically terminates naturally when end of video is reached
'''



path = 'C://Users//julia//OneDrive//documents//MSc_UToronto_thesis//project_SNCI_pipeline//JM_areaBasedAlignment_output'
fileName = 'temp27_aligned'
filePath = path + '//' + fileName + '.avi'
listNeuronIDs = ['neuron1']
sizeCoeff = 2
strTracker = 'csrt'
somaShapeCoverage = 0.99
filterType = 'mean'


outputPath = './' + 'JM_automatedTracking_multipleObject_output/' + fileName


if os.path.isdir(outputPath) == False:
    os.mkdir(outputPath)










##########02 perform automated tracking of target soma##############################


(majorVer, minorVer, subminorVer) = (cv2.__version__).split('.')


#initialize variables, mostly so that VSCode will stop yammering
box = (None, None, None, None)
boxes = None
fps = None
tracker = None
trackers = None
listCoordMaster = []


OPENCV_OBJECT_TRACKER = {
    "csrt": cv2.TrackerCSRT_create,
    "kcf": cv2.TrackerKCF_create,
	"boosting": cv2.TrackerBoosting_create,
	"mil": cv2.TrackerMIL_create,
	"tld": cv2.TrackerTLD_create,
	"medianflow": cv2.TrackerMedianFlow_create,
	"mosse": cv2.TrackerMOSSE_create
}


#initialize video stream
vs = cv2.VideoCapture(filePath)
frameNumTemp = 0


while True:

    #read in frame as uint8; fine for purposes of defining ROI
    frameTemp = vs.read()
    frameTemp = frameTemp[1]


    #check if loop has reached end of the stream
    if frameTemp is None:
        break

    
    #resize frameTemp as per user-defined sizeCoeff
    (H,W) = frameTemp.shape[:2]
    frameTemp = imutils.resize(frameTemp, width = W * sizeCoeff)
    (H,W) = frameTemp.shape[:2]


    #loop over bounding boxes and draw on frame
    if tracker is not None:
        (success, boxes) = trackers.update(frameTemp)
        listFrameTemp = []

        for box in boxes:
            (x, y, w, h) = [int(v) for v in box]
            cv2.rectangle(frameTemp, (x, y), (x + w, y + h), (0, 255, 0), 2)

            #append x, y, w, h to listCoordBoxTemp
            #listCoordBoxTemp stores position of single box
            listCoordBoxTemp = [x, y, w, h]
            for i in range(len(listCoordBoxTemp)):
                listCoordBoxTemp[i] = int(listCoordBoxTemp[i] / sizeCoeff)

            #append each listCoordBox to listFrameTemp
            #listFrameTemp stores all boxes from a single frame
            listFrameTemp.append(listCoordBoxTemp)


        #append each listFrameTemp to listCoordMaster
        #listCoordMaster stores full dataset to be read while building plots
        listCoordMaster.append(listFrameTemp)

        fps.update()
        fps.stop()

        info = [
            ('Tracker:', strTracker),
            ('Success', 'Yes' if success else 'No'),
            ('FPS', '{:2.2f}'.format(fps.fps()))
        ]   

        #loop over info tuples and draw on frameTemp
        for (i, (k, v)) in enumerate(info):
            strTemp = '{}: {}'.format (k, v)
            cv2.putText(
                frameTemp,
                strTemp,
                (10, H - ((i * 20) + 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 255),
                2
            )



    #display output frame and wait for user input
    cv2.imshow('Frame', frameTemp)

    if frameNumTemp == 0:
        key = cv2.waitKey(0) & 0xFF

    elif frameNumTemp != 0:
        key = cv2.waitKey(1) & 0xFF


    #@user: press 's' key and draw bounding box around soma
    #   press ENTER or SPACE to confirm selection once bounding box is drawn
    #   press 'q' to quit video stream
    if key == ord('s'):
        trackers = cv2.MultiTracker_create()
        numBoxesTemp = 0

        while True:
            key = cv2.waitKey(0) & 0xff

            if key == ord('s'):
                #build user-specified bounding box
                box = cv2.selectROI('Frame', frameTemp, fromCenter = False, showCrosshair = True)

                #create new tracker for box and add to multi-object tracker
                tracker = OPENCV_OBJECT_TRACKER[strTracker]()
                trackers.add(tracker, frameTemp, box) #equivalent to tracker.init() in single-object script
                fps = FPS().start()

                numBoxesTemp = numBoxesTemp + 1

            elif key == ord('d'):
                break

    
    elif key == ord('q'):
        break

    frameNumTemp = frameNumTemp + 1


vs.release()
cv2.destroyAllWindows()










##########04 calculate avg pixel intensity for each ROI##############################


#read in .tif stack as numpy.ndarray; this step exists to keep dynamic range of f32 format
filePath = path + '//' + fileName + '.tif'
stack = io.imread(filePath)


#build list of average pixel intensity for every red and grn ROI in stack
listAvgIntenR_master = []
listAvgIntenG_master = []
x_shift = int(np.shape(stack)[2] / 2)

for i in range(len(listFrameTemp)): #iterates once per neuron
    #lists of all ROI intensity values for given neuron; pulls one ROI from each frame:
    listAvgIntenR_neuronTemp = [] 
    listAvgIntenG_neuronTemp = []

    for j in range(len(listCoordMaster)): #iterate once per frame
        
        #calculate avg pixel intensity within red ROI
        (x, y, w, h) = listCoordMaster[j][i]
        sliceROI = stack[j, y:(y+h), x:(x+w)]

        sliceROI_somaShape = somaShape(
            ROI = sliceROI,
            cvrg = somaShapeCoverage,
            blurType = filterType
        )

        avgTemp = cv2.mean(sliceROI, sliceROI_somaShape)
        listAvgIntenR_neuronTemp.append(avgTemp[0])

        #calculate avg pixel intensity within grn ROI
        x = x + x_shift
        sliceROI = stack[j, y:(y+h), x:(x+w)]

        #@juli: re-write this next line as cv2.mean(sliceROI, mask = sliceROISomaShape)
        avgTemp = cv2.mean(sliceROI, sliceROI_somaShape)
        listAvgIntenG_neuronTemp.append(avgTemp[0])



    print(np.var(listAvgIntenR_neuronTemp))

    listAvgIntenR_master.append(listAvgIntenR_neuronTemp)
    listAvgIntenG_master.append(listAvgIntenG_neuronTemp)


listAvgIntenGR_master = []

for i in range(len(listAvgIntenR_master)):
    listAvgIntenGR_neuronTemp = []

    for j in range(len(listAvgIntenR_master[0])):
        fltTemp = (listAvgIntenG_master[i][j] / listAvgIntenR_master[i][j])

        listAvgIntenGR_neuronTemp.append(fltTemp)
    
    listAvgIntenGR_master.append(listAvgIntenGR_neuronTemp)










##########05 build fluorescence intensity plot##############################


#define fluorPlot() function
'''
fluorplot()
plot fluorescence intensity

@param listIntenGR
    lst; contains average GFP/RFP intensity values as f32s for a single neuron
@param listIntenR
    lst; contains average RFP intensity values as f32s for a single neuron
@paramlistIntenG
    lst; contains average GFP intensity values as f32s for a single neuron
@param ymax_singleChann
    int; sets maximum value for y-axis of 1st plot, i.e. fluorescence intensity of GFP and RFP in isolation
@param ymax_GR
    flt: sets maximum value for y-axis of 2nd plot, i.e. fluorescence intensity of GFP/RFP
@param neuronName
    str; name of neuron whose fluorescnece intensity is being plotted

e.g.
fluorPlot(listAvgIntenGR_master[0], listAvgIntenR_master[0], listAvgIntenG_master[0], neuronName = 'VB2')
>> None #plot of fluorescence intensity
'''

def fluorPlot(listIntenGR, listIntenR, listIntenG, ymax_singleChann = 0, ymax_GR = 0, neuronName = 'neuron'):
    
    if ymax_singleChann is 0:
        ymax_singleChann = int(round(max([max(listIntenG), max(listIntenR)]) + 200))

    plt.subplot(2,1,1)
    plt.plot(listIntenG, color = 'green', label = 'GFP')
    plt.plot(listIntenR, color = 'red', label = 'RFP')

    plt.legend()
    plt.ylim((0, ymax_singleChann))
    plt.ylabel('fluorescence intensity w/in ROI')

    if ymax_GR is 0:
        ymax_GR = int(round(max(listIntenGR) + 0.5))
    
    plt.subplot(2,1,2)
    plt.plot(listIntenGR, color = 'black')

    plt.ylim((0, ymax_GR))
    plt.xlabel('frame number')
    plt.ylabel('GFP / RFP')

    titleTemp = outputPath + '//' + fileName + '_' + neuronName + '_signalPlot.png'
    plt.savefig(titleTemp)

    plt.show()

    return(None)


#ymax_R = max(max(listAvgIntenR_master))
lstTemp = []
for i in range(len(listAvgIntenR_master)):
    fltTemp = max(listAvgIntenR_master[i])
    lstTemp.append(fltTemp)
ymax_R = max(lstTemp)

lstTemp = []
for i in range(len(listAvgIntenG_master)):
    fltTemp = max(listAvgIntenG_master[i])
    lstTemp.append(fltTemp)
ymax_G = max(lstTemp)

ymax_singleChann_arg = int(max(ymax_G, ymax_R) + 500)
ymax_GR_arg = max(max(listAvgIntenGR_master)) + 0.5


if listNeuronIDs is [] or len(listNeuronIDs) != len(listAvgIntenGR_master):
    numTemp = 1

    for i in range(len(listAvgIntenGR_master)):
        
        fluorPlot(
            listAvgIntenGR_master[i],
            listAvgIntenR_master[i],
            listAvgIntenG_master[i],
            ymax_singleChann = ymax_singleChann_arg,
            ymax_GR = ymax_GR_arg,
            neuronName = 'neuron' + str(numTemp)
        )

        numTemp = numTemp + 1



else:
    for i in range(len(listAvgIntenGR_master)):
        
        fluorPlot(
            listAvgIntenGR_master[i],
            listAvgIntenR_master[i],
            listAvgIntenG_master[i],
            ymax_singleChann = ymax_singleChann_arg,
            ymax_GR = ymax_GR_arg,
            neuronName = listNeuronIDs[i]
        )
    









##########06 save screenshot of which neurons were tracked##############################


#f32 approach w/ .tif
if listNeuronIDs is [] or len(listNeuronIDs) != len(listAvgIntenGR_master):
    numTemp = 1

    for i in range(len(listFrameTemp)):
    
        testFrame = stack[50, :, :]
        (H,W) = testFrame.shape

        (x, y, w, h) = listCoordMaster[49][i]
        cv2.rectangle(testFrame, (x, y), (x + w, y + h), (4095, 4095, 4095), 1)

        testFrame = testFrame[:, 0:int(W/2)]
        neuronName = 'neuron' + str(numTemp)
        titleTemp = outputPath + '//' + fileName + '_' + neuronName + '_t=0050.png'

        show_image(
            testFrame,
            title = fileName + 't = 0001',
            write = True,
            fileTitle = titleTemp
        )

        numTemp = numTemp + 1


else:
    for i in range(len(listFrameTemp)):
    
        testFrame = stack[50, :, :]
        (H,W) = testFrame.shape

        (x, y, w, h) = listCoordMaster[49][i]
        cv2.rectangle(testFrame, (x, y), (x + w, y + h), (4095, 4095, 4095), 1)

        testFrame = testFrame[:, 0:int(W/2)]
        neuronName = str(listNeuronIDs[i])
        titleTemp = outputPath + '//' + fileName + '_' + neuronName + '_t=0001.png'

        show_image(
            testFrame,
            title = fileName + ' ' + neuronName,
            write = True,
            fileTitle = titleTemp
        )








bp = None