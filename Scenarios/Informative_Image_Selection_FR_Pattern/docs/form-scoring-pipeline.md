# Custom Form Recognizer Scoring Pipeline

*Please make sure to take a look at [documentation](form-training-pipeline.md) regarding training a custom form recognizer model before attempting to set up the scoring pipeline*

The scoring pipeline is used for predicting and extracting text elements from clapperboard images. The model will then assign a label to each of the predicted elements (roll, scene, take, etc). In this example, the model utilized was trained on clapperboard images, but this approach can be adapted to other data types such as images of forms, business cards, receipts and more.

## Scoring Pipeline

### Pipeline flow

![Form Recognizer Training Pipeline](images/form-scoring-pipeline.png =550x)

### Pipeline steps and artifacts

Step | Description | Input data | Output data | Artifacts | Parameters | Path to the step  
--- | --- | --- | --- | --- | --- | ---  
Clapperboard Selection Step | Read API service runs OCR and scores each clapperboards on a per action event basis. Each clapperboard with highest character level frequency will be selected for each action event | Images folder pointing to clapperboard images with associated timestamps. This is needed so that the step can group clapperboards into a set of events based on interval tolerance. For example, with an interval of 1 second, assuming we have a set of clapperboards with timestamps [1,2,3,7,8,9], the clapperboards will be split into the following events: [1,2,3], [7,8,9]. Naming convention for clapperboards should end with a t=? string. For example, `image1_t=13.jpeg` | CSV files containing best clapperboards for each action event in each video | - | List of stop words used in preprocessing step for clapperboard scoring function; tolerance threshold (seconds) used to isolate clapperboards into a set of events will be obtained from the model file |  [select_clapperboards.py](../mlops/form_scoring_pipeline/steps/select_clapperboards.py)
Custom Form Recognizer Step | Extract clapperboard metadata using OCR and map results to respective class types | Images folder, files containing clapperboard images | CSV files containing extracted metadata text from clapperboard images. Files containing Scene, Take, Roll, etc | - | - |  [extract_forms.py](../mlops/form_scoring_pipeline/steps/extract_forms.py)
Postprocessing Step (Custom Form Recognizer) | Use rules-based approach to improve results from Custom Form Recognizer Step | Images folder, files containing extracted clapperboard metadata from Custom Form Recognizer Step | CSV files containing postprocessed extracted metadata text from clapperboard images. Files containing Scene, Take, Roll, etc |- | - |  [postprocess.py](../mlops/form_scoring_pipeline/steps/postprocess.py)

### Suggestions Regarding Modification of Pipeline Steps

The goal of the Form Recognizer Scoring pipeline is to provide a means to score a custom Form Recognizer model. The code was written in a specific format to suit the needs for a previous engagement. Code can be rewritten to support user-specific needs or requirements. Here are some suggestions:

* **Modify the default set of labels used**: Assuming a Form Recognizer model is trained on a different set of labels, it is advisable to modify the default set of labels ([can be found in the create and publish pipeline script](../mlops/form_scoring_pipeline/create_and_publish_pipeline.py)) used to extract fields from the results of the custom model.

* **Remove the postprocessing step**: This step was used to improve the results of the Form Recognizer scoring step as we worked with low resolution images. This was also tailored to a specific set of clapperboard images that followed a set of rules, so it may not generalize to all images. Thus, it may be advisable to remove the step for some scenarios.

* **Modify how data is passed into the form extraction step**: The step assumes data is read from a non-nested directory. Assuming data is contained in a nested directory, it is advisable to refactor the code to meet those needs accordingly. The same logic may apply to how outputs from the step are saved. [Form extraction step.](../mlops/form_scoring_pipeline/steps/extract_forms.py)

* **Modify the code as you please**: Different scenarios might involve code to be written differently, so you are encouraged to refactor code appropriately while utilizing helper functions for the scoring pipeline.
