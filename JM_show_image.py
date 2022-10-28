'''
function defn for show_image()
2020-05-04
'''

import matplotlib.pyplot as plt


def show_image(image, title = 'Image', cmap_type = 'gray', fileTitle = 'output.png', write=False):
    plt.imshow(image, cmap = cmap_type)
    plt.title(title)
    plt.axis('off')
    
    if write == True:
        plt.savefig(fileTitle, bbox_inches='tight')
        
    plt.show()




