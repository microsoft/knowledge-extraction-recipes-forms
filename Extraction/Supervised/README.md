# Predicting forms with Supervised Form Recognizer

This section illustrates how to extract/infer/predict unseen forms with the Supervised version of Form Recognizer. At this stage, the relevant model associated with the form to extact has been identified and we are now ready to run our prediction.

In summary, these files will download files from a Storage Container that represent the Test set, i.e. files not
trained in the autolabel_training step and perform a prediction on each one. The corresponding Ground Truth (GT) value will also
be retrieved. Formatting should be applied and both the extracted and formatted value, alongside the GT value will
be written to a json file.

## The logical flow of prediction_supervised.py

This script will:

* Iterate through every container if the name of the container contains ENV VAR ```CONTAINER_SUFFIX``` + ENV VAR
```TRAIN_TEST``` . If the ENV VAR ```RUN_FOR_SINGLE_ISSUER``` is set, only this vendor/issuer will be processed.
* Load the corresponding ground truth record (GT) for a form. The GT file is specified by the ENV VAR
```GROUND_TRUTH_PATH```
* Download the files to a local directory specified by the ENV VAR ```LOCAL_WORKING_DIR```. Note, the files will
be randomly sampled for evaluation and the number sampled is specified by the ENV VAR ```SAMPLE_NUMBER```
* Retrieve the values from the GT for the keys we want to extract/tag/label. The keys to be extracted are
specified by the ENV VAR ```KEY_FIELD_NAMES```
* Call Read Layout (OCR) for the invoice if no OCR file exists for the form. The endpoint for the OCR is
specified by the ENV VAR ```ANALYZE_END_POINT``` with the Cognitive Subscription endpoint specified by the ENV VAR
```SUBSCRIPTION_KEY```
* Invoke the prediction/evaluation of Form Recognizer, apply some basic formatting and write to a local directory
specified by the ENV VAR ```LOCAL_WORKING_DIR``` + '/predict_supervised' + [issuername].json

Have a look at the accelerator [Predict Form Recognizer Supervised](prediction_supervised.py)

Back to the [Extraction section](../README.md)
