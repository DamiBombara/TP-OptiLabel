# Auto labeling

Module for semi-automatic labeling of vessels.

## Basic use

Create labeler object

```python
import auto_labeling.guided as alg

labeler = alg.PSTLabeler()
```

Then create parameters object and set it

```python
p = alg.PSTParameters(phase_strength=20, warp_strength=400, 
                      sigma_LPF=0.1, thresh_min=0.05, thresh_max=0.75)

labeler.set_params(p)
```

Apply the labeler to grey scaled image (if image is not grey scaled it will be converted automatically)

```python
pst_res = labeler.apply(image_gs)
```

`pst_res` is a container with result mask, you can get the mask

```python
vessels_mask = pst_res.edges
```

But it is recommended to use denoise and mask reconstruction before

```python
pst_res.denoise(thresh_px=300)
```

`thresh_px` is a threshold, the noise and clusters with less than `thresh_px` pixels will be deleted from the mask.
To further improve mask you can use mask reconstruction:

```python
pst_res.mask_reconstruction(ksize_closing=15, ksize_median=7)
```

`ksize_closing` - kernel size for closing morphological operation, `ksize_median` - kernel size for median blur.
After denoise and mask_reconstruction `pst_res.edges` can be used to extract vessels. Simulating user click at point x, y

```python
vessel_feature = pst_res.extract_at(x, y)
```

`vessel_feature` - is the result - mask with a connected component containing point x, y.

## Installation

[Poetry](https://python-poetry.org/) is used as a package manager. To install the package in virtual enviroment follow steps below:

1. install poetry
2. Actiavate the environment, for example `source myvenv/bin/activate`
3. Go to the package folder and run `poetry install`

The module will be installed with all dependencies and you can import it `import auto_labeling.guided as alg`.
