# Azure Machine Learning

## Azure Machine Learning service intro

[Azure Machine Learning service](https://azure.microsoft.com/en-us/services/machine-learning-service/) is a cloud
service used to train, deploy, automate, and manage machine learning models, all at the broad scale that the cloud
provides. AzureML is presented in notebooks across different scenarios to enhance the efficiency of developing Natural
Language systems at scale and for various AI model development related tasks.

In this repository we would like to demonstrate 4 Azure Machine Learning pipelines that train Form Recognizer service under different conditions:

- `create_basic_scoring_pipeline.ipynb`: this notebook allows you to create a pipeline that trains a Form Recognizer model based on one folder only. The pipeline is not very useful in real life, but it demonstrate some basics of the process including how to start working with Azure Machine Learning service;
- `create_multifolder_training_pipeline.ipynb`: this pipeline is a small extension of the previous one, but it allows us to train several models assuming that initial data already prepared and located in sub-folders (each sub-folder is a set to train a single Form Recognizer model). This pipeline train all models in synchronous way, and it allows us to use Form Recognizer Preview with existing limitations about number of calls per minute;
- `create_parallel_training_pipeline.ipynb`: the most complex pipeline that you can use in order to train several Form Recognizer models in parallel. This pipeline is useful if you don't have any limitations about training calls to Form Recognizer or use the service in containers;
- `create_basic_scoring_pipeline.ipynb`: this is an example of a scoring pipeline. Using it you can see how to reach AML model store in order to read metadata about trained Form Recognizer models. We provide just one scoring pipeline, because all of them are similar;

If you are looking for more information about Azure Machine Learning, you can find some useful links below:

* [**Accessing Datastores**](https://docs.microsoft.com/en-us/azure/machine-learning/service/how-to-access-data)
to easily read and write your data in Azure storage services such as blob storage or file share.
* Scaling up and out on [**Azure Machine Learning Compute**](https://docs.microsoft.com/en-us/azure/machine-learning/service/how-to-set-up-training-targets#amlcompute).
* [**Automated Machine Learning**](https://docs.microsoft.com/en-us/azure/machine-learning/service/how-to-configure-auto-train) which builds high quality machine learning models by automating model and hyperparameter selection.
* [**Tracking experiments and monitoring metrics**](https://docs.microsoft.com/en-us/azure/machine-learning/service/how-to-track-experiments) to enhance the model creation process.
* [**Distributed Training**](https://docs.microsoft.com/en-us/azure/machine-learning/service/how-to-train-ml-models#distributed-training-and-custom-docker-images)
* [**Hyperparameter tuning**](https://docs.microsoft.com/en-us/azure/machine-learning/service/how-to-tune-hyperparameters)
* Deploying the trained machine learning model as a web service to [**Azure Container Instance**](https://azure.microsoft.com/en-us/services/container-instances/) for deveopment and test,  or for low scale, CPU-based workloads.
* Deploying the trained machine learning model as a web service to [**Azure Kubernetes Service**](https://azure.microsoft.com/en-us/services/kubernetes-service/) for high-scale production deployments and provides autoscaling, and fast response times.

To successfully run these notebooks, you will need an [**Azure subscription**](https://azure.microsoft.com/en-us/)
or can [**try Azure for free**](https://azure.microsoft.com/en-us/free/). There may be other Azure services or products
used in the notebooks. Introduction and/or reference of those will be provided in the notebooks themselves.

Back to the [Pipelines section](../README.md)
