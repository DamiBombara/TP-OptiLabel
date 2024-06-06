import cv2 as cv
import numpy as np
import os

import auto_labeling.guided as alg
from auto_labeling.nn import PSTParametersEstimator

def waitUserExit(window_name):
   """Function to wait window with name window_name to be closed. Either with a keyboard or by system UI.
   The only purpose of this function to exist is that after using cv.waitKey() script stucks forever
   if user closed the window with X button.
   """
   while( cv.getWindowProperty(window_name,cv.WND_PROP_VISIBLE ) ):
      cv.waitKey(100)
   cv.destroyAllWindows()

# preview image size
psize = 1200

# path of exapmle image
script_folder = os.path.dirname(os.path.realpath(__file__))
img_path = os.path.join(script_folder, "resources", "example.jpg")

# function to resize image for a preview
def resize_preview(img):
    return cv.resize(img, (psize, int(psize*img.shape[0]/img.shape[1]) ))

# create labeler
labeler = alg.PSTLabeler()

# now we need to pass PST parameters
p = alg.PSTParameters(phase_strength=20, warp_strength=400, 
                      sigma_LPF=0.1, thresh_min=0.05, thresh_max=0.75)
labeler.set_params(p)

# or, one could use @property params
labeler.params = {  'phase_strength': 20, 
                    'warp_strength' : 400,
                    'sigma_LPF'     : 0.3,
                    'thresh_min'    : 0.05,
                    'thresh_max'    : 0.75  }

image = cv.imread(img_path)
image = np.pad(image,[(10,10), (10,10), (0,0)])
# or, we can try to use convolutional network to predict parameters
# (precision is still bad)
p = PSTParametersEstimator().apply(image, n_samples=100)
labeler.set_params(p)
print(f"Estimated parameters: {p}")

scale = image.shape[1]/psize
# suppress dropdown menu on right click
cv.namedWindow("preview", flags=cv.WINDOW_AUTOSIZE | cv.WINDOW_KEEPRATIO | cv.WINDOW_GUI_NORMAL)
cv.imshow("preview", resize_preview(image) )

image_gs = cv.cvtColor(image, cv.COLOR_BGR2GRAY)

pst_res = labeler.apply(image_gs)

pst_res.denoise(thresh_px=100).mask_reconstruction()

feature = np.zeros(image_gs.shape, dtype=np.uint8)

colored_edges =  np.pad(pst_res.edges[:,:,None], [(0, 0), (0, 0), (0,2)], mode='constant', constant_values=0)
image_and_mask = cv.addWeighted(resize_preview(image), 0.8,
                                resize_preview(colored_edges), 0.7, 0.0)
# event handler for user clicks
def event_handler(event, x, y, flags, params):
    global feature
    if event:
        print(f"{event=} {x=} {y=}")

    x = int(scale*x) % feature.shape[1]
    y = int(scale*y) % feature.shape[0]

    if event == cv.EVENT_LBUTTONDOWN:
        feature = np.logical_or( feature, pst_res.extract_at(x, y) )
    elif event == cv.EVENT_RBUTTONDOWN:
        feature = np.logical_xor( feature, pst_res.extract_at(x, y) )

    cv.imshow('preview', np.hstack([image_and_mask, 
                                    np.repeat(resize_preview(255*feature.astype(np.uint8))[:,:,None], 3, axis=2) 
                                   ]) 
             )

cv.setMouseCallback("preview", event_handler)
waitUserExit("preview")
