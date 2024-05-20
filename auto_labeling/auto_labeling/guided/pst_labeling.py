"""Base classes for guided labelers.
This module contains code used for guided labeling (feature mask extraction) using PST (Phase Stretch Transform) + floodFill algorithm
"""

from .abstract   import GParametersBase, GResultBase, GLabelerBase
from dataclasses import dataclass
from warnings    import warn
from typing      import Optional, Mapping, Tuple
from phycv       import PST_GPU # type: ignore
from nptyping    import NDArray, Shape, Number, UInt8
from cv2         import floodFill, FLOODFILL_MASK_ONLY, dilate, morphologyEx, \
                        getStructuringElement, MORPH_ELLIPSE, MORPH_CLOSE, \
                        medianBlur
from cv2.typing  import MatLike

from torch._prims_common import DeviceLikeType

import torch
import numpy as np
import pipe  as pp # type: ignore

from sklearn.cluster  import DBSCAN     # type: ignore
from collections      import Counter

@dataclass
class PSTParameters(GParametersBase):
    """Parameters for PSTLabeler. 
    For more detailed information check https://downloads.hindawi.com/journals/ijbi/2015/687819.pdf

    Attributes
    ----------
    phase_strength : float
        Phase strength (S) to initialize the PST kernel
    warp_strength  : float
        Warp strength (W) to initialize the PST kernel
    sigma_LPF   : float
        Low-pass filter parameter
    thresh_min  : Optional[float]
        Min threshold in the morphological operation 
    thresh_max  : Optional[float]
        Max threshold in the morphological operation 
    morph_flag  : bool  = True
        Flag controls whether to run the morphological operation or not
    """
    phase_strength : float
    warp_strength  : float
    sigma_LPF   : float
    thresh_min  : Optional[float]
    thresh_max  : Optional[float]
    morph_flag  : bool  = True

    def __post_init__(self):
        if self.morph_flag:
            assert self.thresh_min is not None and self.thresh_max is not None, \
                "morph_flag = True requires thresh_min and thresh_max."
        if not self.morph_flag and (self.thresh_min is not None or self.thresh_max is not None):
            warn("thresh_min or thresh_max has no effect since morph_flag is not True.")
        

class PSTResult(GResultBase):
    """Result of PSTLabeler image preprocess. 
    User can extract a feature using .extract_at(x,y) providing point
    in connected region of interest. 
    """
    _mask: NDArray[Shape["*, *"], UInt8]
    _connectivity: int = 4

    def __init__(self, mask: NDArray[Shape["*, *"], UInt8]):
        self._mask = mask

    @property
    def edges(self) -> NDArray[Shape["*, *"], UInt8]:
        """returns preprocessed by PSTLabeler image
        """
        return self._mask.copy()

    def extract_at(self, x: int, y: int) -> NDArray[Shape["*, *"], UInt8]:
        """extracts a feature in connected region containing point x, y
        """
        s = self._mask.shape
        feature = np.zeros( (s[0]+2, s[1]+2) , dtype=np.uint8)
        flags   = self._connectivity | ( 1 << 8 ) | FLOODFILL_MASK_ONLY
        floodFill(self._mask, feature, seedPoint=(x,y), newVal=0, flags=flags) # type: ignore
        return feature[1:-1, 1:-1]
    
    def denoise(self, thresh_px: int, eps_px: int=2, __MinPts: int=4):
        _X = np.vstack(np.where(self._mask > 0)).T
        clustered = DBSCAN(eps=eps_px, min_samples=__MinPts).fit(_X)
        labels = set(clustered.labels_)
        if -1 in labels:
            labels.remove(-1)
        rlabels = list(Counter(clustered.labels_).items()) | pp.filter(lambda p: p[1]>=thresh_px)
        _buf = self._mask
        self._mask = np.zeros(self._mask.shape, dtype=np.uint8)
        for ll, _ in rlabels:
            if ll == -1:
                continue
            idx = _X[clustered.labels_ == ll]
            self._mask[idx[:,0],idx[:,1]] = _buf[idx[:,0],idx[:,1]]
        return self
    
    def mask_reconstruction(self, kzise_closing=15, ksize_median=7):
        kernel     = getStructuringElement(MORPH_ELLIPSE,(kzise_closing,kzise_closing))
        kernel_sm  = getStructuringElement(MORPH_ELLIPSE,(3,3))
        self._mask = morphologyEx(self._mask, MORPH_CLOSE, kernel)
        self._mask = dilate(self._mask, kernel_sm, iterations = 1)
        self._mask = medianBlur(self._mask, ksize_median)
        return self

    def copy(self):
        return PSTResult(self._mask.copy())


class PSTLabeler(GLabelerBase):
    """PSTLabeler class for guided labeling. 
    Requires to set parameters before using method .apply(image).
    Check PSTParameters for further information.
    """
    _params: Optional[PSTParameters] = None
    _PST:    PST_GPU

    def __init__(self, torch_device: Optional[DeviceLikeType]=None):
        if torch_device is None:
            torch_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._PST = PST_GPU(device=torch_device)

    def set_params(self, parameters: PSTParameters | Mapping) -> None:
        """Sets parameters for PSTLabeler. Parameters should be an PSTParameters instance or
        mapping (dict like). 
        """
        self._params = PSTParameters(**parameters)

        if self._PST.h and self._PST.w:
            self._PST.init_kernel( S = self._params.phase_strength,
                                   W = self._params.warp_strength  )

    def apply(self, image: MatLike, flag_raw: bool = False) -> PSTResult:
        """Preprocesses image and returns PSTResult to provide feature extraction by user later on.
        """
        assert self._params is not None, "use .set_params before applying labeler"

        if image.shape[0] != self._PST.h or image.shape[1] != self._PST.w:
            self._PST.h = image.shape[0]
            self._PST.w = image.shape[1]
            self._PST.init_kernel( S = self._params.phase_strength,
                                   W = self._params.warp_strength  )

        self._PST.load_img(img_array=torch.from_numpy(image))

        self._PST.apply_kernel( self._params.sigma_LPF, 
                                self._params.thresh_min, 
                                self._params.thresh_max, 
                                self._params.morph_flag  )
        if not flag_raw:
            mask = (255*self._PST.pst_output.cpu().numpy()).astype("uint8")
        else:
            mask = self._PST.pst_output.cpu().numpy()
        return PSTResult(mask)