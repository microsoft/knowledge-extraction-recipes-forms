# Extraction or inference

This stage of the project involves the evaluation of the model against the validation and test datasets.

**Key Outcomes**:

* Versions of model improvements and iterations captured.

Note, during the extraction post-processing will need to take place alongside application of business rules to ensure that the data is transformed into a state or format required for further downstream tasks and integration. The code accelerators below provide the scaffolding utilising simple python scripts to:

* Retrieve the storage containers that contain the test datasets
* Get the associated model to the issuer of the form via a lookup
* Sample a configurable number of test forms randomly
* OCR the test forms
* Evaluate the forms

**Note**, this assumes that a classification step has taken place before to infer the correlation between the issuer of the form and the trained model associated with that form type/layout. Have a look at the code accelerator [Attribute Search](../Analysis/Attribute_Search_Classification/README.md) for a simple approach that can help implement this.

## Supervised Form Recognizer Evaluation

Have a look at the code accelerator for evaluating a model with the [Supervised Form Recognizer](Supervised/README.md)

## Unsupervised Form Recognizer Evaluation

Have a look at the code accelerator for evaluating a model with the [Unsupervised Form Recognizer](Unsupervised/README.md)

Now refer to the [Evaluation](../Evaluation/README.md) section to for the final stage of forms extraction.

Back to the [Training section](../Training/README.md)
