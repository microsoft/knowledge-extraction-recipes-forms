# Informative Image Selection using OCR and Knowledge Extraction with Form Recognizer #

## Introduction ##

There are instances in which customers may want to make use of the Form Recognizer to extract metadata from items like clapperboards, receipts and more. However, in some of these scenarios, a lot of redundant data points may end up being fed into the Form Recognizer service, which will essentially increase costs incurred by utilzing the service as well as increase the amount of time spent on computing results. Here are two example scenarios:

### Scenario 1: Filming a movie scene with multiple instances of a clapperboard ###

A director is filming a take for a particular movie scene. In this scenario, a clapperboard is used to signify the start of an action event. A customer may want to make use of the Form Recognizer service to extract valubale information from the clapperboard such as:

- The movie title
- The name of the director
- The name of the camera man/co-director
- The current scene
- The current take
- The current roll
- The date the scene was filmed

Assuming a set of image frames are extracted from the raw video footage, one may notice that there are multiple instances of a clapperboard images for each action event:

- The blurry clapperboard image, where the clapperboard is being placed in front of the camera frame
- The still clapperboard image, where the clapperboard is held in front of the camera frame
- The blurry clapperboard image, where the clapperboard is being taken out of the camera frame

Logically, for this single scene or action event, it would make sense to feed in all of the images to the Form Recognizer for knowledge extraction purposes. However, given that multiple instances of clapperboard images that contain very similar data are being fed into the Form Recognizer service, there is the high likelihood that a bunch of duplicate results will be produced. We can also infer that extremely blurry images will offer very little meaninguful information (if any at all) given that the OCR technology will have difficulties predicting text. At this point, it will feel like redundant data points are being fed into the service. Furthermore, this solution may not scale efficiently; a single movie scene could contain hundreds of action events with thousands of clapperboard images (assuming we have 3-5 clapperboard images for each action event). This becomes more challenging when the solution is to be applied to hundreds, if not thousands of movies or video files.

In situations such as this, it may be meaningful to select the most "informative" image that contains the most metadata that can be extracted by the Form Recognizer service for each action event. By utilzing this approach we ensure that only one clapperboard image is selected for each action event, thus, reducing the time and cost spent on performing predictions and computing results.

## Proposed Solution ##

The proposed solution involves utilizing an OCR service (Read API) and a character-level frequncy scoring function to idenfity and select the most "informative" image in an action event. The idea is that the image with the most predictable text will have the highest character count. Thus, the image with the highest character count will be identified as the most “informative”.  From here, the selected set of most "informative" images will be fed into the Form Recognizer service.

Given that the Read API computes results much faster than the Form Recognizer service and costs much less to run (costs for computing 1000 images with the Read API is $2.50 vs $50 for the custom Form Recognizer service), it's a very useful tool that can be used to perform this preprocessing step. Furthermore, given that the Form Recognizer utilizes the same OCR technology that the Read API makes use of under the hood, it is reasonable to assume the most "informative" image selected for each action event will yield the best results for the Form Recognizer knowledge extraction step.

## Workflow ##

### Training Pipeline ###

Initially, we make use of a Training Pipeline to train a custom Form Recognizer model to detect and extract metadata from clapperboard images, as the default service may not perform well on this type of data. The Training pipeline consists of the following steps:

- A Train step - Train a Custom From Recognizer model
- An Evaluation Step - Evaluate model performance on a test dataset
- A Register Step - Register the Trained model to the Azure Machine Learning workspace

In depth documentation regarding the training pipeline can be found [here](docs/form-training-pipeline.md)

### Scoring Pipeline ####

The Scoring pipeline utilizes the trained Custom Form Recognizer service to extract metadata from clapperboard images and generate a set of key-value pairs where each predicted artifact points to its corresponding label (scene, take, roll, etc).

The scoring pipeline consists of the following steps

- Clapperboard Selection Step - Select most "informative" clapperboard for each action event
- Form Recognizer Step - Extract metadata from clapperboard images and generate key-value pairs
- Postprocessing step - Improve results from the Form Recognizer Step

As mentioned above, the goal of the clapperboard selection step is to identify the most representative clapperboard images by scoring an image based off of it's character level-frequency. This will reduce time and costs incurred when computing results in the next subsequent steps.

Another potentially useful step, is the postprocessing step. The goal of this step is to improve the results of the Form Recognizer step by utilizing a rules-based approach. As mentioned before, the Form Recognizer relies on the OCR service to predict and extract text from images before key-value pair generation. In some instances, we may work with low resolution images. With these images, pixel quality is fairly poor. In addition to this low pixel quality, the service may resize images under the hood before making predictions. This may result in smaller text and as a result, the OCR service may generate bounding boxes around multiple text elements. Thus, rather than identifying for example 3 text elements as seperate entities, the service may identify them as one single entity. This problem may be better explained with a table:

Filename | Roll | Scene | Take | Title |
--- | --- | --- | --- | --- | --- | ---  
Image1.jpeg| AA01 | 607B | 3 | Knowledge Extraction Recipes |
Image2.jpeg| AA03 32C 7 |  |  | Knowledge Extraction Recipes |
Image3.jpeg|  | BB09 21D | 9 | Knowledge Extraction Recipes |  

If we view the following table, we can see that the results generated for the first row are clean and concise. Exactly the type of output that is desired from the Form Recognizer service. However, the results on the second and third row are much poorer. For instance, on the second row, "roll", "scene" and "take" are identified as just "roll". We also have a similar situation on the third row where "roll" and "scene" are identified as just "scene".

With these results, the model is telling us that it couldn't predict anything for "scene" and "take" (row 2) or "roll" (row 3). However, we can tell that these artifacts were extracted by the service; they just weren't assigned appropriate labels. This might be because the bounding boxes generated by the OCR service span more than one item. In situations such as this, it may be reasonable to introduce a postprocessing method that follows a rules based approach.

By viewing the results, we can tell that:

- "Roll" elements are alphanumeric. They start wit a letter and end with a digit.
- "Scene" elements are alphanumeric. They start with a digit and end with a letter.
- "Take" elements are simply numerical values.

With these rules, we can generate a rule-based method that "checks" if an elements follows any of the rules listed above. With the postprocessing step we do the following:

Check if an element is empty (no prediction was made by the model for the associated class).
If an element is empty, check for other non-empty fields to see if something that looks similar to the element was identifed.
If the element is identied in another non-empty field, swap the element over to its corresponding field.

We only perform checks and swaps on empty fields as we still want to rely on the predictions made by the model as much as possible. With the postprocessing step, the following table should be generated:

Filename | Roll | Scene | Take | Title |
--- | --- | --- | --- | --- | --- | ---  
Image1.jpeg| AA01 | 607B | 3 | Knowledge Extraction Recipes |
Image2.jpeg| AA03 | 32C | 7 | Knowledge Extraction Recipes |
Image3.jpeg| BB09 |  21D | 9 | Knowledge Extraction Recipes |

In depth documentation regarding the scoring pipeline can be found [here](docs/form-scoring-pipeline.md)
