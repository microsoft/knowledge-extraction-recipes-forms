# Checking datasets for representativeness

As with any machine learning project, we need to ensure that the data we train on is representative of the data we ultimately need to predict on. We want out models to generalise well to the data we expect them to predict on, and with high accuracy.

It thus imperative that we know that our datasets are representative of:

* The problem we are trying to solve, and this should have been confirmed in the Project Preparation and Analysis phases

* Each other, in other words, our training data set is representative of our test and validation test sets

It is recommended that the following checks are conducted:

* The training data set contains a similar number of pages to that of what is in the test set. Training on pages with invoices with one page for example but expecting the model to perform well on multi-page invoices is introducing uncertainty.

* In the case of invoices, the training data set contains representative amounts of line items to that of the test dataset

* The training set set contains handwriting representative to that of the test dataset

* The training data set contains checkboxes completed in sufficient variety to that of the test dataset, for example both tick marks and crosses are used.

Have a look at the code accelerator for a simple approach to [Getting the page variation](get_page_count_variation.py) between two datasets.

Back to the [Training section](../README.md)
