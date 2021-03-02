# Data structure

This document walks through a recommended format for organizing your training data, when you have multiple form layouts to work with.
For assistance splitting your data into different layouts, please look at the code accelerator [Form Layout Clustering](../../Analysis/Form_Layout_Clustering/README.md).

## Key recommendations

The following are the top recommendations to consider when implementing your project:

* Keep all associated data in the same location. This includes the forms and ground truth data
* The natural top level split to organizer training data is by layout (form), as there is a 1 - 1 correlation between Form Recognizer models and form layouts.
* For each layout, split the training data into three groups in the folder structure. This way all code operates on the same train, test, validate splits.
  * Train - The group of data to train new models on
  * Validate - The group of data to test the newly trained models on. This group is used for validation at the end of each training cycle, which inherently influences which model is chosen.
  * Test - The group of data that should be held in reserve. This data should be used as a final step before releasing the models to production.
* Consider caching the results of consistent external API calls and keeping them with the training data itself.
  * An efficient way to do this is saving the JSON response from the endpoint as a file on disk, and checking for the existence of the file before making the call.
  * This drastically reduces training times and the amount of API calls
* Implement data loading as a class, so the complexities of data handling in different environments can be abstracted from the core training logic
  * See section [Example Data Loader](#example-data-loader) for more details
* Allow for a per layout configuration file to account for differences in the forms
  * One great candidate for the config is the fields that should be extracted from the form

## Example data structure

This structure was developed for an application which uses both [Auto Labelling](../../Training/Auto_Labelling/README.md) and a [Form Router](../../Analysis/Routing_Forms/README.md).
As such, we store two cached API results with the training data ([Computer Vision's OCR endpoint](https://westcentralus.dev.cognitive.microsoft.com/docs/services/computer-vision-v3-1-ga/operations/56f91f2e778daf14a499f20d) and [Form Recognizer's Analyze Layout endpoint](https://westus2.dev.cognitive.microsoft.com/docs/services/form-recognizer-api-v2/operations/AnalyzeLayoutAsync))

```
|- layout1 
    |- layout1config.json 
    |- train 
        |- layout1_train.csv 
        |- form11.jpg 
        |- form11.jpg.ocr.json (Computer Vision's OCR cache)
        |- form11.jpg.al.json (Form Recognizer's Analyze Layout cache)
        ... 
    |- test 
        |- layout1_test.csv 
        |- form12.jpg 
        |- form12.jpg.ocr.json 
        |- form12.jpg.al.json 
        ... 
    |- validate 
        |- layout1_validate.csv 
        |- form13.jpg 
        |- form13.jpg.ocr.json 
        |- form13.jpg.al.json
        ... 
|- layout2 
    |- layout1config.json 
    |- train 
        |- layout2_train.csv 
        |- form21.jpg 
        |- form21.jpg.ocr.json (Computer Vision's OCR cache)
        |- form21.jpg.al.json (Form Recognizer's Analyze Layout cache)
        ... 
    |- test 
        |- layout2_test.csv 
        |- form22.jpg 
        |- form22.jpg.ocr.json 
        |- form22.jpg.al.json 
        ... 
    |- validate 
        |- layout2_validate.csv 
        |- form23.jpg 
        |- form23.jpg.ocr.json 
        |- form23.jpg.al.json
        ... 
    ... 
```

## Example Data Loader

We have included an example of a data loading class in `StructuredDataLoader.py`.
The purpose of this class is to provide an easy way for data exploration/ model training scripts to access the training data.

The class takes three parameters:

* `top_level_path`: This is the path to the parent directory of the structure seen in the previous section
* `subdataset`: This will be a string in the list of ["train", "validate", "test"] and loads only a single type of data at a time. This is to prevent crossing training data with validation data and vice versa.
* `layouts`: This is an optional list of layouts to load. The default behavior is to load all available layouts.

It can then be used as follows:

```python
# Get an instance of the data loader
sdl = StructuredDataLoader(top_level_path, "train")

# Return a pandas dataframe with the contents of the selected csv files
#   * All selected layouts will be concatenated together
#   * A column is appended `qualified_filename` that has the full path to the form
#   * Throws if any forms listed in the csv are not found
data = sdl.load_dataframe()

# Get a dictionary of the config files for each layout
#  * Keys of the dictionary are the layout names and values are their configs
#  * Throws if any configs are missing
configs = sdl.load_form_recognizer_configs()
```
