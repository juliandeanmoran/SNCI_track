## SNCI_track
Align GCaMP and RFP channels, autotrack, and generate traces for C. elegans small-number calcium imaging (SNCI) videos recorded from a single 2D plane.



## Installation

1. clone git repository:
    navigate to dir you want to clone to

    ```bash
    git clone https://github.com/zhenlab-ltri/SNCI_track
    ```


2. install following libraries to current environment (prefer conda over pip), except for ffmpeg:
    - cv2 (version 4.2.0 -- otherwise SNCI_track won't run)
    - ffmpeg (use pip to install instead)
    - imutils
    - numpy
    - matplotlib
    - pandas
    - PIL
    - skimage
    - threading
    


## Running SNCI_track

1. align GFP and RFP channels
    - ensure input video is saved as single .tif
    - open JM_areaBasedAlignment.py in python IDE of choice (e.g. VScode)
    - follow instructions in JM_area_based_alignment.py's section 01 doc string
    - run

    - check alignment result test frame; automatically writes to SNCI_track/JM_areaBasedAlignmentOutput/testFrameResults/
    - output aligned .tif automatically writes to SNCI_track/JM_areaBasedAlignmentOutput/


2. convert output aligned .tif to .avi
    - open Fiji / imageJ
    - File > Open > #open output aligned .tif
    - File > Save as > AVI > Compression=None, Frame Rate=#recording frame rate > OK > #give same file name as aligned .tif, in same dir


3. set up autotracker run
    - open SNCI_track_autotrack_masterScript.py in python IDE of choice

    * set path variable to full path for JM_areaBasedAlignmentOutput dir

    + ensure path is separated by '//' rather than '\'; e.g. path = 'C://Users//julia//Documents//SNCI_track//JM_areaBasedAlignment_output'
    
    * set fileName to shared name of aligned .avi and .tif files, without extension; e.g. fileName = 'temp2_aligned'

    - set list_neuronID to contain the names of your neurons in the order you plan to track them
    ```python
    list_neuronID = ['AVA']                          #if planning to track only AVA in that run
    list_neuronID = ['AVA', 'AVG', 'AVB']            #if planning to track all 3 somas in that run
    list_neuronID = ['neuron1']                      #if neuron name not known
    list_neuronID = ['neuron1', 'neuron2']           #if planning to track multiple somas and names not known
    ```
    * set str_tracker to tracker you want to use; 'csrt' recommended; e.g. str_tracker = 'csrt'
    
    + set sep_chan to True or False
    ```python
    sep_chan = True #if want RFP and GFP traces displayed on separate axes in final plot
    sep_chan = False #if want RFP anf GFP traces displayed on same axes in final plot
    ```

    - run SNCI_track_autotrack_masterScript.py

    
4. operate autotracker GUI
    - GUI will open automatically when running SNCI_track_autotrack_masterScript.py
    + left panel displays RFP channel
    * right panel displays GFP channel
    
    - click Initialize ROI(s) to enter ROI draw mode; press s key to add an ROI; ROI draw window will open; always track from the left (RFP) channel; on ROI draw window, click and drag rectangular ROI around soma you want to track; press ENTER after drawing; draw window will close and ROI will be drawn on GUI as circles; draw all the ROIs around somas you want to track for that run; 1 per run currently recommended; press d key to exit ROI draw mode
    
    + click Autotrack to enter autotrack streaming mode; video will stream to GUI; watch stream for autotacker errors; e.g. ROI balloons too large or ROI falls off soma of interest
    
    - in the event of an autotracking error, click Pause button to pause the stream; use backward and forward arrow keys to rewind to frame at which error first occurs; click Proofread ROI(s) to re-enter ROI draw mode; re-draw the ROI(s) to their correct position (press s key, click and drag, press ENTER as before); press d key to exit ROI draw mode; click Autotrack to resume autotrack streaming mode

    * when autoracking completes, '[INFO] video endpoint reached' will print to terminal
    
    + close the GUI ((X) button in top right corner)



5. save plots, test frames, and data .tsv to disk (saves automatically to ./SNCI_track_autotrack_output)

    * calcium imaging trace plot will automatically display
    
    - close it to save to disk
    
    + test frame (taken from 50th frame) will automatically display; shows ROI configuration so that you know which somas were tracked that session
    
    - close it to save to disk
    
    * .tsv of average pixel intensity data for RFP, GFP, and GFP / RFP will automatically save to disk

    + if GUI does not close and script appears to stall, try clicking close (X) button on GUI window again; you may need to do this after every time you close another window (e.g. plot window, test frame window); this is a known issue if using some versions of tkinter; author is currently working on fixing it