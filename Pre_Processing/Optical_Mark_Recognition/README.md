# Optical Mark Recognition

This folder contains a couple approaches for identifying checkboxes on filled forms. It can be incorporated into a pipeline to augment the rest of the form data captured via OCR or other forms understanding tools.

## Approach 1: OpenCV Templates

The OpenCV library can look for image templates within images using a technique called template matching. We have captured some sample checkboxes (both filled and unfilled) as jpgs and stored those in the templates directory. The tool loops over all of the templates and scans the input image for checkboxes.

Pros:

* More reliable in returning all the checkboxes on the clean test forms
Cons:
* Cannot handle scaled images unless a similarly scale template exists.
* Samples of each variant of checkbox are required to capture all of the boxes

## Approach 2: OpenCV contours to identify squares on the page

This approach is based off of the code at <https://github.com/craigmassie/PythonOMR>, please refer there for latest versions. It uses opencv to look for squares that and then counts dark pixels within the square to determine if it is filled or not.

Pros:

* Can handled squares of different sizes
Cons:
* May not return the checkbox if there is not a distinct whitespace boundary between the check and the surrounding box.

## Usage

`python checkbox_finder1.py --form <image_file_name> --template_folder <templates folder> --output_image <test image name>`

or

`python checkbox_finder2.py --form <image_file_name> --template_folder <templates folder> --output_image <test image name>`

## Sample Output

```python
.\checkbox_finder.py --form '..\data\forms\standardbank_forms\UAT 17 CHANGED.jpg' --template_folder .\templates\ --output_image output.jpg

[{'type': 'checked', 'boundingbox': [297, 1571, 326, 1599], 'id': 0}, {'type': 'empty', 'boundingbox': [324, 1606, 352, 1633], 'id': 1}, {'type': 'checked', 'boundingbox': [328, 278, 364, 313], 'id': 2}, {'type': 'empty', 'boundingbox': [328, 316, 364, 351], 'id': 3}, {'type': 'empty', 'boundingbox': [328, 354, 364, 389], 'id': 4}, {'type': 'empty', 'boundingbox': [388, 1571, 416, 1598], 'id': 5}, {'type': 'checked', 'boundingbox': [468, 1198, 497, 1226], 'id': 6}, {'type': 'checked', 'boundingbox': [627, 396, 656, 424], 'id': 7}, {'type': 'empty', 'boundingbox': [632, 1239, 660, 1266], 'id': 8}, {'type': 'empty', 'boundingbox': [651, 1198, 679, 1225], 'id': 9}, {'type': 'empty', 'boundingbox': [806, 1607, 834, 1634], 'id': 10}, {'type': 'empty', 'boundingbox': [833, 1239, 861, 1266], 'id': 11}, {'type': 'checked', 'boundingbox': [899, 396, 928, 424], 'id': 12}, {'type': 'empty', 'boundingbox': [1058, 205, 1086, 232], 'id': 13}, {'type': 'empty', 'boundingbox': [1072, 1239, 1100, 1266], 'id': 14}, {'type': 'checked', 'boundingbox': [1163, 205, 1192, 233], 'id': 15}, {'type': 'empty', 'boundingbox': [1323, 968, 1351, 995], 'id': 16}, {'type': 'empty', 'boundingbox': [1330, 479, 1358, 506], 'id': 17}, {'type': 'empty', 'boundingbox': [1427, 479, 1455, 506], 'id': 18}, {'type': 'empty', 'boundingbox': [1434, 968, 1462, 995], 'id': 19}]
```

## TODO

This project still needs a way to identify each checkbox to link to specific key values. It currently enumerates the found checkboxes so it can mislabel a checkbox if some are not found. Future plans are to reference checkboxes by a location vector relative to a top, left anchor on the form.

Back to the [Pre-Processing section](../README.md)
