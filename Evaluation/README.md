# Evaluation

This stage determines the accuracy of the overall training process and scores against the Ground Truth (GT) or labelled data to determine the accuracy of the models. During the prediction pipeline in a production environment, the confidence of the predictions here are assessed and a threshold is set to hand off for manual intervention if required.

Active learning may be implemented here, a simple example could may be identifying if a new form has been introduced and to hand it off for automated training once the required number of sample forms have been received with automated iterations to increase the accuracy.

Have a look at the code accelerator for a simple approach to [Scoring](Scoring/evaluation_gt.py) a prediction from a Forms Recognizer output. **Note, this is highly specific to the format of your data, the specific business rules that need to be applied, and the format the data needs to ultimately be transformed to.**

## evaluation_gt.py

In summary, this script will evaluate the output from the [Extraction accelerators](../Extraction/README.md) file and provide some basic scoring metrics which it will output to a file specified by ENV VAR ```LOCAL_WORKING_DIR``` +
predict_supervised + [issuer_name].txt.This script process all .json files on the directory specified by
ENV VAR ```LOCAL_WORKING_DIR``` unless the ENV VAR ```RUN_FOR_SINGLE_ISSUER``` is specified.
