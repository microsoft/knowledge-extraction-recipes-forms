# Using word and word layout features with a clustering algorithm to aid discovery of layout designs

Python code along with the notebooks under this directory can be used to speed up the data curation for training images for Form Recognizer models.

The intended use case is for users with a large collection of document images without groundtruth for the number of layouts or the labeling thereof. The procedure outlined in this section helps to identify, in an unsupervised manner, groups of images that correspond to a similar layout.

The main difference between this approach and the [Form_Layout_Clustering](https://github.com/microsoft/knowledge-extraction-recipes-forms/tree/master/Analysis/Form_Layout_Clustering) example is that this approach assumes a lower density of text per page and is more sensitive to where texts are placed on a page. This is particularly helpful in compact images with various ordering of similar information, e.g. in membership cards, driver's licenses, or IDs. This method has also worked well for images with a large variation in lighting condition, size, orientation, etc due to the way they were captured.

This approach is also developed to work well in tandem with the approach in the [Routing_Forms](https://github.com/microsoft/knowledge-extraction-recipes-forms/tree/master/Analysis/Routing_Forms) section. The resulting clusters of images can be further curated and organized into the directory structure needed to train both a routing model across layouts, as well as a custom form recognizer model per layout.

## Table of content

1. [Getting started](#1-Getting-started)
1. [Approach in a nutshell](#2-Approach-in-a-nutshell)

## 1. Getting started

In order to run the example in this section, you would need the following:

1. Create a directory with a collection of images
1. Copy `example.env` to a file next to it called `.env`. This is where the code gets the OCR endpoint and key from.
1. Add your endpoint and key for an [Azure Computer Vision](https://azure.microsoft.com/en-us/services/cognitive-services/computer-vision/) instance to the `.env` file.
1. (optional) Create a stopword list in a text file. The repo contains a sample list with all the single letters and digits.
1. You can then run `clustering.py` from its directory as shown below

```bash
python clustering.py \
    --data_dir {path-to-image-directory} \
    --env_file {path-to-env-file} \
    --layout_shape {dimension-of-image} \
    --vocabulary_size {size-of-vocabulary-for-word-encoding} \
    --stopwords_file {path-to-stopwords-file}
```

e.g.

```bash
python clustering.py \
    --data_dir ../sample-data \
    --env_file ../../../.env \
    --layout_shape 50 79 \
    --vocabulary_size 50 \
    --stopwords_file ../stopwords.txt
```

## 2. Approach in a nutshell

The approach described in this section can be summarized as follows:

1. Extract text from document images with Cognitive Service OCR API
1. Encode the images using text and text location based encoding:
    1. Construct a vocabulary from the collection of extracted text based on frequent words
    1. Use the vocabulary to encode presence or absence of vocabulary word on each image ("word encoding")
    1. Use the detected bounding boxes to encode presence or absence of text at each location on each image ("layout encoding")
    1. Apply PCA to reduce dimensionality of the word encoding and the layout encoding
    1. Generate a resulting feature vector by concatenating the two encodings
1. Apply density-based clustering (DBSCAN) on the encodings to determine groups of document images with similar layout

The `ClusteringModel` returns a Pandas DataFrame containing the file names and cluster labels which can then be written out to file, along with other information for further data visualization and debugging purposes.

For further explanation and intuition behind the encoding logic, please see the [Routing Forms README](https://github.com/microsoft/knowledge-extraction-recipes-forms/blob/master/Analysis/Routing_Forms/README.md)

There are a few additional parameters that can be tuned in the `clustering.py` script itself as constants. These are:

* `N_PCA_COMPONENTS`: number of PCA components to use
* `MIN_SAMPLES`: minimum size of a cluster in DBSCAN
* `EPSILON`: maximum distance between two points for them to be included in the same cluster in DBSCAN
The values in the repo are for a toy dataset.

The layout-clustering-and-labeling.ipynb notebook in the Form Layout Clustering section contains an excellent example of using the IPyPlot to render images in a cluster to aid with further cluster curation.
