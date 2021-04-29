# Custom Form Recognizer Training Pipeline

The Custom Form Recognizer Training Pipeline is responsible for training a new Custom Form Recognizer model, that will be used to extract and map text results from clapperboard images.
In other words, the model will extract text results from a clapperboard image and generate key value pairs for "scene", "take", "roll", etc.

## Training Pipeline

### What is Form Recognizer

**Azure Form Recognizer** is a cognitive service that uses machine learning technology to identify and extract key-value pairs and table data from form documents. It then outputs structured data that includes the relationships in the original file. Unsupervised learning allows the model to understand the layout and field data without manual data labeling or intensive coding. You can also do supervised learning with manually labeled data. Models trained with labeled data can perform better and can work with more complicated documents.

Resources:

* [What is Form Recognizer?](https://docs.microsoft.com/en-us/azure/cognitive-services/form-recognizer/overview?tabs=v2-0)
* [Quickstart: Use the Form Recognizer Client Library](https://docs.microsoft.com/en-us/azure/cognitive-services/form-recognizer/quickstarts/client-library?tabs=ga&pivots=programming-language-csharp)
* [Train a Form Recognizer model with labels using the sample labeling tool](https://docs.microsoft.com/en-us/azure/cognitive-services/form-recognizer/quickstarts/label-tool?tabs=v2-0)
* [Train a Form Recognizer model with labels using REST API and Python](https://docs.microsoft.com/en-us/azure/cognitive-services/form-recognizer/quickstarts/python-labeled-data?tabs=v2-0)

### Pipeline flow

![Form Recognizer Training Pipeline](images/form-training-pipeline.png =550x)

### Pipeline steps and artifacts

Step | Description | Input data | Output data | Artifacts | Parameters | Path to the step  
--- | --- | --- | --- | --- | --- | ---  
Training step | Uploads asset files to Custom Form Recognizer service for training | Images, ocr.json and labels.json asset files generated using sampling labeling tool, files containing ocr and label images lists | `model.json` file, describing the trained model | - | Path to asset files in blob storage used for training | [train.py](../mlops/form_training_pipeline/steps/train.py)
Evaluation step | Evaluates the model on the validation dataset | Images folder, labels folder,  `model.json` file, describing the trained model | Intermediate labels for validation dataset|- | - |  [evaluate.py](../mlops/form_training_pipeline/steps/evaluate.py)
Registration step | Registrates the model in AML workspace together with all the artifacts | `model.json` file, describing the trained model | - | Registered model| git hash, build id |  [register.py](../mlops/form_training_pipeline/steps/register.py)

### Suggestions Regarding Modification of Pipeline Steps

The goal of the Form Recognizer Training pipeline is to provide a means to train a custom Form Recognizer model. The code was written in a specific format to suit the needs for a previous engagement. Code can be rewritten to support user-specific needs or requirements. Here are some suggestions:

* **Change evalution metric used**: The evaluation step utilizes detection rates as a metric for evaluating the performance of the custom Form Recognizer model. Given the tight time constraints of a previous engagement, the team defaulted to this metric as there wasn't enough time to label all of the data that was accessible. If a user can provide ground truth labels for data they wish to test against the custom model, it is advisable to refactor this step to suit such needs. [View the Evaluation step here.](../mlops/form_training_pipeline/steps/evaluate.py)

* **Modify the default set of labels used**: Assuming a Form Recognizer model is trained on a different set of labels, it is advisable to modify the default set of labels ([can be found in the create and publish pipeline script for the evaluation step](../mlops/form_training_pipeline/create_and_publish_pipeline.py)) used to extract fields from the results of the custom model.

* **Automatically generate a SAS URI for the training step**: For simplicity, the training step simply reads in a SAS URI from the DevOps variable group. In some cases, mainly for security purposes, it might be reasonable to generate SAS tokens that expire short term. In that case, it might be advisable to make use of utility functions provided to automatically generate a new SAS token for each pipeline run. [View the Training step here.](../mlops/form_training_pipeline/steps/train.py)

* **Modify the code as you please**: Different scenarios might involve code to be written differently, so you are encouraged to refactor code appropriately while utilizing helper functions for the scoring pipeline.
