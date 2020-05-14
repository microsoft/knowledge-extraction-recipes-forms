# The analysis phase

During this vital stage of the project, analysis of the viability and representativeness of the data is conducted to determine whether the data available is relevant to business problem. This stage typically requires implementing techniques to better understand the variability, distribution and datasets available.

**Key Outcomes**:

* The data available is relevant to the business problem to be solved.
* An approach of how the data can be segmented is defined for further experimentation.
* The data has been analysed and informs the hypotheses, the approach and the initial experiments.

For forms extraction, the following are key areas to explore:

## Understanding the distribution

Understanding the exact distribution of the document types is vital in building an accurate and maintainable solution. We need to know:

**Key Questions**:

*Do any documents feature more highly in the overall distribution?*

If yes, we should start here as they represent a large proportion of the documents to be extracted. It is also worth investing time here on a specific layout.

Have a look at a simple pandas query in the [Distribution jupyter notebook](./Distribution/Distribution.ipynb) code accelerator.

## Understanding the variation within form layouts

*How many different form types or layouts exist?*
*Is there variation within a form type or layout?*

With Form Recognizer, there is a 1:1 mapping between a form layout and a model trained for that layout, thus is it important to not only understand how many different form types there are but also whether there is variation with a form type.

Forms may change and thus a model that was performing well no longer returns the required accuracy. In the case of invoices, some vendors may have multiple form layouts in existence at a time, and in these cases this variation would need to be identified and catered for.

Have a look at the code accelerators for [Form Variation](Form_Variation/README.md). These scripts use some simple techniques to analyse the OCR scans of forms to:

* Check for a standard deviation that exceeds a predefined threshold
* Check maximum differences in their bounding boxes

Both of these points above are strong indicators that there may be significant variation in the forms of that layout.

## Classifying forms with multiple layouts

**Key Questions**:

*If the documents have variation in layouts, do they need to be classified to map them to the correct model? What features are available to classify the documents?*

If only a few form layouts exist from which to extract information, then this is simple, however, should thousands of different layouts exist, some form of classification will need to take place to map the forms to the relevant model.

This could be a vendor logo on an invoice, a background colour on a scanned document, or a table or word that exists in a particular location. By identifying a specific document type, more options become available to process that document. It could be
a declaritive rules based approach or data driven.

Our goal is to automate the identification of the correct model trained for the form layout as there is a 1:1 correlation between the Form Recognizer model and the respective form layout.

Have a look at the code accelerator [Search based classification](Attribute_Search_Classification/README.md) for a simple but effective search based approach on text features.

Alternatively have a look at the code accelerator [Form Layout Clustering](Form_Layout_Clustering/README.md) for a clustering approach based on text features.

### The data

Needless to say having sufficient, representative and well distributed data with Ground Truth (an known data set against which you can compare your predicted results) is mandatory for any machine learning project. Options do exist if no Ground Truth is available but these will be limited.

**Key Questions**:

*Will the data available be useful in building a generalisable solution?*

Ensure the data is not seasonal or the distribution is not limited to a small window in time that may skew the data and not be representative of the end solution.

Now refer to the [Pre-Processing](../Pre_Processing/README.md) section to determine whether the Form Recognizer service is a good fit.
