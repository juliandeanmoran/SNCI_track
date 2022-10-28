'''
SNCI_track GUI for autotracking and proofreading
Julian Moran
2021-01-24
'''










##########00: import modules##############################

import imutils
from imutils.video import VideoStream
from imutils.video import FPS

from skimage import io

from copy import deepcopy

from PIL import Image
from PIL import ImageTk

import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk

import cv2
import os
import time
import ffmpeg
import threading

from JM_show_image import show_image
from JM_somaShape import somaShape










##########01: define GUI object class##############################

'''
class: autotrackGUI

@param vs
    cv2.VideoCapture; instantiation of video to be streamed

@param outputPath
    str; storage path for output screenshots

@param tracker
    str; openCV tracker for use during autotracking; 'csrt' recommended

@desc
    open widget for autotracking, displaying frame 0 of video stream in panel

    btn; autotrack      stream video forward for autotracking
    btn; rewind         stream video in reverse for proofreading
    btn; pause          freeze video on current frame
    btn; initialize     allow user to draw ROI(s) for initializing autotracking
    btn; proofread      allow user to re-draw ROI(s) for proofreading

    key; forw frame     move forward one frame upon keypress of right arrow key
    key; back frame     move backward one frame upon keypress of left arrow key
        
'''


class autotrackGUI:

    def __init__ (self, vs, outputPath, strTracker, sizeCoeff):
        #store video stream object and output path
        self.vs = vs
        self.outputPath = outputPath
        self.strTracker = strTracker
        self.sizeCoeff = sizeCoeff

        #build local tracker dict
        self.OPENCV_OBJECT_TRACKER = {
            "csrt": cv2.TrackerCSRT_create,
            "kcf": cv2.TrackerKCF_create,
            "boosting": cv2.TrackerBoosting_create,
            "mil": cv2.TrackerMIL_create,
            "tld": cv2.TrackerTLD_create,
            "medianflow": cv2.TrackerMedianFlow_create,
            "mosse": cv2.TrackerMOSSE_create
        }

        #initialise root window and image panel
        self.root = tk.Tk()
        self.panel = None

        #build button "Rewind"
        btn_reverseStream = tk.Button(
            self.root,
            text = 'Rewind',
            command = lambda:[self.revS_mode(), self.reverse_stream()]
        )
        btn_reverseStream.place(
            height = 30,
            width = 100,
            x = 10,
            y = 50
        )
        
        #build button "Autotrack"
        btn_autotrack = tk.Button(
            self.root,
            text = 'Autotrack',
            command = lambda:[self.autS_mode(), self.autotrack_stream()]
        )
        btn_autotrack.place(
            height = 30,
            width = 100,
            x = 10,
            y = 10

        )

        #build button 'Pause'
        btn_pause = tk.Button(
            self.root,
            text = 'Pause',
            command = self.pause
        )
        btn_pause.place(
            height = 30,
            width = 100,
            x = 10,
            y = 90
        )

        #build button 'Proofread ROI(s)'
        btn_proofread = tk.Button(
            self.root,
            text = 'Proofread ROI(s)',
            command = self.proofread
        )
        btn_proofread.place(
            height = 30,
            width = 100,
            x = 10,
            y = 240
        )

        #build button 'Initialize ROI(s)'
        btn_initROI = tk.Button(
            self.root,
            text = 'Initialize ROI(s)',
            command = self.initialize_ROIs
        )
        btn_initROI.place(
            height = 30,
            width = 100,
            x = 10,
            y = 200
        )

        #initialize control flow variables
        self.is_paus = False
        self.is_init = False
        self.is_autS = False
        self.is_revS = False

        self.roiCoordList_master = [] #for storing final list of roi coordinates

        #read in vs and store in list
        #@juli: ensure cv2.VideoCapture() is called in-driver before running GUI
        self.check, self.frame = self.vs.read()
        self.frameList = []
        self.frameList_backup = []
        self.frameIndX = 0
        self.autotIndX = 0

        # if os.path.isdir(outputPath + '/frames/') == False:
        #     os.mkdir(outputPath + '/frames/')

        while (self.check == True):
            # cv2.imwrite(self.outputPath + '//frames//' + 'frame%d.tif' %self.frameNum,
            #     self.frame
            # )
            
            self.frameList.append(self.frame)
            self.check, self.frame = self.vs.read()

        
        #remove final element in frameList, which is NoneType
        self.frameList.pop()

        #set callback to handle when GUI is closed
        self.root.wm_protocol('WM_DELETE_WINDOW', self.onClose)
        self.root.wm_title('SNCI_track: autotracker GUI')

        #upsize all frames for easier ROI-drawing
        for i in range(len(self.frameList)):

            #upsize frame
            self.W = self.frameList[i].shape[1]
            self.frameList[i] = imutils.resize(self.frameList[i], width = int(self.W * sizeCoeff))
            # self.W = self.frameList[i].shape[1]
            self.H, self.W = self.frameList[i].shape[:2]
            self.H = int(self.H)
            self.W = int(self.W)

        #deepcopy to backup
        self.frameList_backup = deepcopy(self.frameList)

        #display frame 0 of vs in panel
        image = cv2.cvtColor(self.frameList[0], cv2.COLOR_BGR2RGB)
        image = Image.fromarray(image)
        image = ImageTk.PhotoImage(image)

        self.panel = tk.Label(image = image)
        self.panel.image = image #blocks python's garbage collection protocol
        self.panel.place(
            bordermode = 'outside',
            height = self.H,
            width = self.W,
            x = 120,
            y = 10
        )

        geom_w = self.W + 130
        geom_h = self.H + 20
        strGeom = str(geom_w) + 'x' + str(geom_h)
        self.root.geometry(strGeom)


    #define protocol for drawing ROIs, callable during ROI initialization or proofreading
    #runs when user presses 's' key during initialzation or proofreading
    def drawROI(self, keyBind):

        #prompt user to draw ROI in cv2's ROI selector
        self.roi = cv2.selectROI(
            'Frame',
            self.frameList[self.frameIndX],
            fromCenter = False,
            showCrosshair = False
        )

        #close cv2's ROI selector
        cv2.destroyAllWindows()
    
        #create new tracker for ROI and add to cv2.MultiTracker object
        self.tracker = self.OPENCV_OBJECT_TRACKER[self.strTracker]()
        self.trackers.add(self.tracker, self.frameList[self.frameIndX], self.roi)

        #add to running count of number of ROIs
        if (not self.is_init):
            self.numROIs_init += 1
        
        elif self.is_init:
            self.numROIs_pfrd += 1

        #append new roi to frame-specific list
        self.roiCoordList_frame.append(list(self.roi))

        #draw red and green circles at ROI on frame 0
        (x, y, w, h) = self.roi

        cv2.circle(
            self.frameList[self.frameIndX],
            (int(x + w/2), int(y + h/2)),#circle centrpoint
            int(w/2),#circle radius
            (0, 0, 255),#circle colour in BGR format
            1#circle fill
        )

        cv2.circle(
            self.frameList[self.frameIndX],
            (int(x + w/2 + (self.W)/2), int(y + h/2)),
            int(w/2),
            (0, 255, 0),
            1
        )

        #update panel to display ellipse on frame
        image = cv2.cvtColor(self.frameList[self.frameIndX], cv2.COLOR_BGR2RGB)
        image = Image.fromarray(image)
        image = ImageTk.PhotoImage(image)

        self.panel.configure(image = image)
        self.panel.image = image



    #define protocol that designates ROI initialization as complete
    #runs when user presses 'd' key during ROI initialization
    def doneROI_init(self, keyBind):

        print('[INFO] ROI initialization complete. N = ' + str(self.numROIs_init))

        self.is_init = True
        self.frameIndX += 1
        self.autotIndX = self.frameIndX

        self.root.unbind_all('s')
        self.root.unbind_all('d')

        #append all drawn ROIs in this frame to master coordinate list
        self.roiCoordList_master.append(self.roiCoordList_frame)



    #define protocol for initializing ROI(s) for autotracking; calls drawROI()
    def initialize_ROIs(self):

        if not self.is_init:
            #create cv2.MultiTracker object
            self.trackers = cv2.MultiTracker_create()
            self.numROIs_init = 0

            #initialize frame-specific list, for storing roi coordinates
            self.roiCoordList_frame = []

            #prompt user to draw ROIs for tracking
            print('[INFO] press s key to open ROI draw tool; press d key to finalize initializaion')

            self.root.bind_all('s', self.drawROI)
            self.root.bind_all('d', self.doneROI_init)
        
        elif self.is_init:
            print('[ERROR] ROIs already initialized')



    #define protocol for moving 1 frame forward during pause
    def frame_forw(self, keyBind):

        if self.frameIndX < len(self.frameList):

            #move forward 1 frame index
            self.frameIndX += 1

            #convert frame from cv2 to TkImage format
            image = cv2.cvtColor(self.frameList[self.frameIndX], cv2.COLOR_BGR2RGB)
            image = Image.fromarray(image)
            image = ImageTk.PhotoImage(image)

            #display frame on gui panel
            self.panel.configure(image = image)
            self.panel.image = image #blocks Python's garbage collection protocols
        
        else:
            print('[ERROR] frame index out of range')



    #define protocol for moving 1 frame backward during pause
    def frame_back(self, keyBind):

        if self.frameIndX >= 0:

            #move backward 1 frame index
            self.frameIndX -= 1

            #convert frame from cv2 to TkImage format
            image = cv2.cvtColor(self.frameList[self.frameIndX], cv2.COLOR_BGR2RGB)
            image = Image.fromarray(image)
            image = ImageTk.PhotoImage(image)

            #display frame on gui panel
            self.panel.configure(image = image)
            self.panel.image = image #blocks Python's garbage collection protocols
        
        else:
            print('[ERROR] frame index out of range')
    

    
    #define protocol for pausing
    def pause(self):

        #flag as being paused
        # self.is_paus =  not self.is_paus
        self.is_paus = True
        self.is_autS = False
        self.is_revS = False

        if self.is_paus:
            print('[INFO] video stream paused')

            self.root.bind_all('<Right>', self.frame_forw)
            self.root.bind_all('<Left>', self.frame_back)



    #define protocol for designating autotrack mode
    def autS_mode(self):

        #flag as being in autotrack mode
        if self.is_init:
            self.is_autS = True
            self.is_revS = False
            self.is_paus = False

            self.root.unbind_all('<Right>')
            self.root.unbind_all('<Left>')
        
        else:
            return(None)



    #define protocol for autotracking and forward streaming simultaneously
    def autotrack_stream(self):

        #initialize variables
        self.rois = None

        #autotrack and stream to gui panel
        if self.is_init & (self.autotIndX < len(self.frameList)) & (not self.is_paus) & (not self.is_revS):

            #update tracker
            self.frameIndX = self.autotIndX
            (success, self.rois) = self.trackers.update(self.frameList[self.frameIndX])

            #initialize list for storing ROI coordinates for current frame
            self.roiCoordList_frame = []

            #loop over updated ROIs and draw on frame
            for r in self.rois:
                (x, y, w, h) = [int(v) for v in r]

                #use coords to draw read and green circles on frame
                cv2.circle(
                    self.frameList[self.frameIndX],
                    (int(x + w/2), int(y + h/2)),
                    int(w/2),
                    (0, 0, 255),
                    1
                )

                cv2.circle(
                    self.frameList[self.frameIndX],
                    (int(x + w/2 + (self.W)/2), int(y + h/2)),
                    int(w/2),
                    (0, 255, 0),
                    1
                )

                #append ROI to list of ROIs for this frame
                self.roiCoordList = [x, y, w, h]
                self.roiCoordList_frame.append(self.roiCoordList)
            
            #append ROIs for this frame to ROI master list
            self.roiCoordList_master.append(self.roiCoordList_frame)

            #build info, a list of tuples about tracking performance
            self.info = [
                ('Tracker', self.strTracker),
                ('Success', 'Yes' if success else 'No'),
                ('Frame', self.frameIndX),
                ('Proofread', 'No')
            ]

            #loop over info tuples and draw on frame
            H = self.frameList[self.frameIndX].shape[0]

            for (i, (k, v)) in enumerate(self.info):
                self.str = '{}: {}'.format (k, v)

                cv2.putText(
                    self.frameList[self.frameIndX],
                    self.str,
                    (10, H - ((i * 20) + 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 0, 255),
                    2
                )
            
            #convert frame from cv2 to TkImage format
            image = cv2.cvtColor(self.frameList[self.frameIndX], cv2.COLOR_BGR2RGB)
            image = Image.fromarray(image)
            image = ImageTk.PhotoImage(image)

            #display frame on gui panel, with ellipses and tracker info drawn on
            self.panel.configure(image = image)
            self.panel.image = image #blocks Python's garbage collection protocols

            self.autotIndX += 1
            self.panel.after(10, self.autotrack_stream)
            
        elif (not self.is_init) & (not self.is_revS) & (not self.is_paus):
            print('[ERROR] ROIs have not been initialized')

        elif self.is_revS and (not self.is_paus):
            return(None)

        elif self.is_paus:
            return(None)

        elif (self.autotIndX == (len(self.frameList))):
            print('[INFO] video endpoint reached')



    #define protocol for designating reverse-stream mode
    def revS_mode(self):

        #flag as being in reverse-stream mode
        if (self.is_init):
            self.is_revS = True
            self.is_autS = False
            self.is_paus = False

            self.root.unbind_all('<Right>')
            self.root.unbind_all('<Left>')

        else:
            return(None)



    #define protocol for reverse streaming
    def reverse_stream(self):

        if (self.is_init) & (self.frameIndX > 1) & (not self.is_paus) & (not self.is_autS):

            #flag as being in reverse-streaming mode
            self.is_revS = True
            self.is_autS = False
            self.is_paus = False

            self.frameIndX -= 1

            #convert frame from cv2 to TkImage format
            image = cv2.cvtColor(self.frameList[self.frameIndX], cv2.COLOR_BGR2RGB)
            image = Image.fromarray(image)
            image = ImageTk.PhotoImage(image)

            #display frame on gui panel
            self.panel.configure(image = image)
            self.panel.image = image #blocks Python's garbage collection protocols

            self.panel.after(10, self.reverse_stream)

        elif (not self.is_init) & (not self.is_autS) & (not self.is_paus):
            print('[ERROR] ROIs have not been initialized')

        elif self.is_autS and (not self.is_paus):
            return(None)

        elif (self.is_paus):
            return(None)
                
        elif self.frameIndX == 1 & self.is_init:
            print('[INFO] video frame 1 reached')
        


    #define protocol for designating that ROI proofreading is complete
    #runs when user presses 'd' key during ROI proofreading
    def doneROI_pfrd(self, keyBind):

        if self.numROIs_init != self.numROIs_pfrd:
            print('[WARNING] proofread ROIs is not equal to initialized ROIs; you should re-start SNCI_track, or else you may return un-plottable data')

        else:
            print('[INFO] ROI proofreading complete. N = ' + str(self.numROIs_pfrd))
            self.root.unbind_all('s')
            self.root.unbind_all('d')

            #append coordinates of all ROIs in this frame to master coordinate list
            self.roiCoordList_master.append(self.roiCoordList_frame)

            #build info, a list of tuples about tracking performance
            self.info = [
                ('Tracker', self.strTracker),
                ('Success', 'Na'),
                ('Frame', self.frameIndX),
                ('Proofread', 'Yes')
            ]

            #loop over info tuples and draw on this frame
            H = self.frameList[self.frameIndX].shape[0]

            for (i, (k, v)) in enumerate(self.info):
                self.str = '{}: {}'.format (k, v)

                cv2.putText(
                    self.frameList[self.frameIndX],
                    self.str,
                    (10, H - ((i * 20) + 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 0, 255),
                    2
                )
            
            #convert frame from cv2 to TkImage format
            image = cv2.cvtColor(self.frameList[self.frameIndX], cv2.COLOR_BGR2RGB)
            image = Image.fromarray(image)
            image = ImageTk.PhotoImage(image)

            #display frame on gui panel, with ellipses and info drawn on
            self.panel.configure(image = image)
            self.panel.image = image #blocks Python's garbage collection protocols

            #update frame index for autotracking
            self.frameIndX += 1
            self.autotIndX = self.frameIndX



    #define protocol for proofreading; calls drawROI()
    def proofread(self):

        if self.is_init & (self.frameIndX <= self.autotIndX) & (not self.is_autS) & (not self.is_revS) & self.is_paus:
        
            #create new cv2.MultiTracker object
            self.trackers = None
            self.trackers = cv2.MultiTracker_create()
            self.numROIs_pfrd = 0

            #prompt user to re-draw ROIs for tracking
            print('[INFO] proofreading enabled; press s key to open ROI draw tool; press d key to finalize selections')
            
            #delete already-tracked frames after current frame by overwriting from back-up
            self.frameList[self.frameIndX : (self.autotIndX + 1)] = deepcopy(self.frameList_backup[self.frameIndX : (self.autotIndX + 1)])
            #self.frameList[self.frameIndX : len(self.frameList)] = deepcopy(self.frameList_backup[self.frameIndX : len(self.frameList)])
            
            #truncate roiCoordList_master to match current position, frameIndX-non-inclusive
            self.roiCoordList_master = self.roiCoordList_master[:self.frameIndX]
            #present frame will populate master list when roi's are drawn

            #initialize frame-specific list for storing ROI coordinates
            self.roiCoordList_frame = []

            self.root.bind_all('s', self.drawROI)
            self.root.bind_all('d', self.doneROI_pfrd)


        elif (not self.is_init) and self.is_paus:
            print('[ERROR] ROIs have not been initialized')
        
        elif not self.is_paus:
            print('[INFO] you must pause video before proofreading')

        elif (self.frameIndX > self.autotIndX):
            print('[ERROR] cannot proofread when frame has not been autotracked yet')



    #define protocol for closing GUI when user presses close window
    def onClose(self):

        print('[INFO] closing...')
        self.is_paus = True
        self.vs.release()
        self.root.quit()