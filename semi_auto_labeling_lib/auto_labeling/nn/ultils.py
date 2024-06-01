from typing              import Any, Optional, Mapping
from nptyping            import NDArray, Shape, Number
from cv2.typing          import MatLike
from warnings            import warn
from torch._prims_common import DeviceLikeType

import torch
import os
import numpy as np

from ..guided import PSTParameters

models_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), "models")

class PSTParametersEstimator:
    def __init__(self, model_version: int = 1, torch_device: Optional[DeviceLikeType] = None):
        self.model = torch.jit.load(os.path.join(models_folder, 
                                            f'PST_EST_model_scripted_v{model_version}.pt'))
        self.model.eval()
        metadata = torch.load(os.path.join(models_folder, 
                                            f'PST_EST_model_metadata_v{model_version}.pkl'))
        self._shape = metadata['shape']
        self._shift = np.array(metadata['shift'])
        self._gain  = np.array(metadata['gain'])
        self._image_mean = torch.Tensor(metadata['image_mean'])
        self._image_std  = torch.Tensor(metadata['image_std'])

        self._device = torch_device
        if self._device is None:
            self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self._device)
        self._image_mean = self._image_mean.to(self._device)
        self._image_std  =  self._image_std.to(self._device)


    def apply(self, image: MatLike, mask: Optional[MatLike] = None, n_samples: int = 10) -> PSTParameters:
        img_shape = image.shape
        def check_origin(origin, mask):
            if(origin[0]+self._shape[0] >= img_shape[0] or origin[1]+self._shape[1] >= img_shape[1]):
                return False
            if not mask:
                return True
            partial_m = mask[origin[0] : (origin[0]+self._shape[0]), origin[1] : (origin[1]+self._shape[1])]
            if((partial_m == 0).sum() > 0):
                return False
            return True
        def slice_img(source, ii, jj):
            return source[ii:(ii+self._shape[0]), jj:(jj+self._shape[1])]
        
        estimated_params = np.zeros((n_samples, 5))
        n_done = 0
        n_failed = 0
        while(n_done < n_samples):
            if n_failed >= n_samples**3:
                raise InterruptedError("Failed to extract samples, inconsistent data provided.")
            ii, jj = np.random.default_rng().integers(0, max(img_shape), 2)
            if not check_origin((ii, jj), mask):
                n_failed += 1
                continue
            partial_img = slice_img(image, ii, jj)
            x = (torch.Tensor(partial_img).to(self._device).permute(2, 0, 1) / 255 - self._image_mean)/self._image_std
            with torch.no_grad():
                self.model.eval()
                estimated_params[n_done] = self.model(x).cpu().detach().numpy()

            n_done += 1

        estimated_params = self._shift + estimated_params*self._gain
        res = np.median(estimated_params, axis=0)
        
        return PSTParameters(*res)

    



