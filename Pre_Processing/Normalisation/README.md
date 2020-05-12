# Normalization

Have a look at the [jupyter notebook](preprocess_document.ipynb) which contains helper functions for preprocessing scanned documents prior to performing knowledge extraction using Forms Understanding or OCR.

The included functionality:

* Descriptive statistics on scanned document
* Normalization
* Turn into grayscale
* Binarization

## Removing boxes around text

The [form_boxes.py](form_boxes.py) module contains methods for handling forms with boxes to retrieve the individual characters. For a related technique see the accelerator [Projection to correct image skew and identify text lines](../Projection/README.md#Projection-to-correct-image-skew-and-identify-text-lines)

The included functionality:

* Form alignment based on the orientation of the boxes
* Background cleaning
* Conversion into grayscale
* Field detection and outlining

Back to the [Pre-Processing section](../README.md)
