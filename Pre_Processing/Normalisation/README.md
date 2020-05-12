# Normalization

Have a look at the [jupyter notebook](preprocess_document.ipynb) which contains helper functions for preprocessing scanned documents prior to performing knowledge extraction using Forms Understanding or OCR.

The included functionality:

* Descriptive statistics on scanned document
* Normalization
* Turn into grayscale
* Binarization

The [form_boxes.py](form_boxes.py) module contains methods for handling forms with boxes for individual characters.

The included functionality:

* Form alignment based on the orientation of the boxes
* Background cleaning
* Conversion into grayscale
* Field detection and outlining

Back to the [Pre-Processing section](../README.md)