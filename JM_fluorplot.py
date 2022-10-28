'''
fluorplot() defn
Julian Moran
2021-02-11
'''










##########00: import modules##############################

import matplotlib.pyplot as plt









##########01: define fluorplot() function##############################


'''
fluorplot()
plot fluorescence intensity

@param listIntenGR
    lst; contains average GFP/RFP intensity values as f32s for a single neuron
@param listIntenR
    lst; contains average RFP intensity values as f32s for a single neuron
@param listIntenG
    lst; contains average GFP intensity values as f32s for a single neuron
@param outputPath
    str; name of output directory
@param fileName
    str; name to assign to plot file
@param neuronName
    str; name of neuron whose fluorescnece intensity is being plotted
@param ymax_singleChann
    int; sets maximum value for y-axis of 1st plot, i.e. fluorescence intensity of GFP and RFP in isolation
@param ymax_GR
    flt: sets maximum value for y-axis of 2nd plot, i.e. fluorescence intensity of GFP/RFP
@param sep_chan
    bool: if False, plot GFP and RFP in same subplot; else plot in different subplots

e.g.
fluorPlot(listAvgIntenGR_master[0], listAvgIntenR_master[0], listAvgIntenG_master[0], neuronName = 'VB2')
>> None #plot of fluorescence intensity
'''

def fluorPlot(
    listIntenGR,
    listIntenR,
    listIntenG,
    outputPath,
    fileName,
    neuronName = 'neuron',
    ymax_singleChann = 0,
    ymax_GR = 0,
    sep_chan = False
):
    
    if not sep_chan:
        spArgs = [1, 2, 2]
    else:
        spArgs = [1, 2, 3]

    if ymax_singleChann is 0:
        ymax_singleChann = int(round(max([max(listIntenG), max(listIntenR)]) + 200))

    plt.subplot(spArgs[2], spArgs[0], spArgs[0]) #2, 1, 1 / 3, 1, 1     
    plt.plot(listIntenG, color = 'green', label = 'GFP')

    if not sep_chan:
        plt.plot(listIntenR, color = 'red', label = 'RFP')

    plt.legend()
    plt.ylim((0, ymax_singleChann))
    # plt.ylabel('fluorescence intensity w/in ROI')

    if sep_chan:
        plt.subplot(spArgs[2], spArgs[0], spArgs[1]) #3, 1, 2
        plt.plot(listIntenR, color = 'red', label = 'RFP')
        plt.legend()
        plt.ylim((0, ymax_singleChann))
        # plt.ylabel('')

    if ymax_GR is 0:
        ymax_GR = int(round(max(listIntenGR) + 0.5))
    
    plt.subplot(spArgs[2], spArgs[0], spArgs[2]) #2, 1, 2 / 3, 1, 3
    plt.plot(listIntenGR, color = 'black')

    plt.ylim((0, ymax_GR))
    plt.xlabel('frame number')
    plt.ylabel('GFP / RFP')

    titleTemp = outputPath + '//' + fileName + '_' + neuronName + '_signalPlot.png'
    plt.savefig(titleTemp)

    plt.show()

    return(None)