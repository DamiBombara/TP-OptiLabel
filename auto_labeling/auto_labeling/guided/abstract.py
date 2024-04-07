"""Base classes for guided labelers.
This module contains abstract base classes definitions (interface specification) to be implemented for guided labeling
"""
from abc         import ABC, abstractmethod
from typing      import Any, Optional, Mapping
from nptyping    import NDArray, Shape, Number
from dataclasses import dataclass, asdict

@dataclass
class GParametersBase: 
    """Base class for GLabeler parameters"""
    def keys(self):
        return asdict(self).keys()
    def __getitem__(self, key):
        return asdict(self).__getitem__(key)
    def __iter__(self):
        return asdict(self).values().__iter__()

class GResultBase(ABC):
    """Base GResult class.
    The point is to let user extract features from pre-computed by GLabelerBase
    data without the need to recompute it

    Methods
    -------
    @abstractmethod
    def extract_at(x: int, y: int, **kw_args: Any) -> NDArray[Shape["*, *"], Bool]
        extract feature at point x, y of original image. Returns mask.
    """
    @abstractmethod
    def extract_at(self, x: int, y: int) -> NDArray[Shape["*, *"], Number]: ...

 
class GLabelerBase(ABC):
    """Base guided labeler abstract class

    Attributes
    ----------
    params : ParametersBase
        stored parameters used for labeling

    Methods
    -------
    @abstractmethod
    def set_params(self, **kwargs: Unpack[GParametersBase]) -> None
        used for setting labeler's core parameters


    @abstractmethod
    def apply(self, image: NDArray[Shape["*, *"], Number]) -> GResultBase
        applies all needed computations before guided feature extraction, returns object GResultBase to interact with
    """
    _params: Optional[GParametersBase] = None

    @property
    def params(self) -> Optional[GParametersBase | Mapping]:
          return self._params
    
    @params.setter
    def params(self, new_params: Mapping) -> None:
          self.set_params(new_params)

    @abstractmethod
    def set_params(self, new_params: Mapping) -> None: ...

    @abstractmethod
    def apply(self, image: NDArray[Shape["*, *"], Number]) -> GResultBase: ...