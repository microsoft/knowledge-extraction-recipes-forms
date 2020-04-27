# The training phase

This stage requires training the model(s) on the training datasets.

**Key Outcomes**:

* A model(s) that is clearly correlated to the data it was trained on (data lineage) and the seperated dataset(s) it will be validated and tested on.
* Baselines on simpler models or early versions have been captured for comparison.
* Clarity and confidence that the model(s) will generalise well against the production data.

## Checking representatives

**Key Questions**:

*Is the training dataset representative of the test dataset?*

Prior to training, it is important to validate that the training data is indeed representative of the test dataset to help ensure that a generalisable solution may be built.

Have a look at the following code accelerator [Representativeness](Representativeness/README.md) which illustrates a simple check to ensure that the average number of pages per form in the training dataset is similar to within the test dataset.

Further validation to check the form variation by measuring the standard deviation for the training dataset could be conducted to ensure it is consistent with the test dataset. Have a look at the code accelerator [Form Variation](../Analysis/Form_Variation/README.md) for a simple approach to check the standard deviation within a form layout across many instances of the layout.

## The autolabelling process

Have a look at the code accelerator for [AutoLabel Training](Auto_Labelling/README.md) which illlustrates how you can automate the labelling of forms using the Supervised version of Form Recognizer using your Ground Truth data.

## Named Entity Recognition

Named Entity Recognition can be a quick way to help the extraction process in conjunction with Form Recognizer. Have a look at [Text Analytics Named Entity Recognition](https://docs.microsoft.com/en-gb/azure/cognitive-services/text-analytics/how-tos/text-analytics-how-to-entity-linking?tabs=version-3) for both NER and entity linking.

[Language Understanding LUIS](https://www.luis.ai/home) is also worth looking at to quickly add a natural language machine learning-based service.

Have a look at the code accelerator for [Named Entity Recognition](Named_Entity_Recognition/README.md) which illustates how you can train and use [Spacy's Named Entity Recognition](https://spacy.io/usage/linguistic-features#named-entities) to identify entities of interest that need to be extracted.

Now refer to the [Extraction](../Extraction/README.md) section to for inference against models.
