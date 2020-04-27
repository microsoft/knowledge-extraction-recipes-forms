# Pipelines

Pipelines represent our ability to scale, orchestrate and schedule our processes via underlying infrastructure. Azure offers a number of different options in this space. This Playbook will provide some basic options as there are a number of more detailed repositories available to help here, namely:

* [MLOps](https://github.com/microsoft/MLOps)
* [MLOpsPython](https://github.com/Microsoft/MLOpsPython)
* [Microsoft AI Samples, Reference Architectures & Best Practices](https://github.com/microsoft/AI)

## Azure Cognitive Search

Azure Cognitive Search provides an [enrichment pipeline](https://docs.microsoft.com/en-us/azure/search/cognitive-search-concept-intro#components-of-an-enrichment-pipeline) which provides the ability to extract information, chain the invocation of custom APIs alongside Microsoft Cognitive Services and store the output to a datastore, all as a managed service.

Have a look at the sample pipeline accelerator for [Azure Cognitive Search](Azure_Cognitive_Search/README.md)

## Azure Kubernetes Service

Azure Kubernetes Service (AKS) makes it simple to deploy a managed Kubernetes cluster in Azure. AKS reduces the complexity and operational overhead of managing Kubernetes by offloading much of that responsibility to Azure. As a hosted Kubernetes service, Azure handles critical tasks like health monitoring and maintenance for you.

Have a look at the sample Helm charts for [Azure Kubernetes Service](Azure_Kubernetes_Service/README.md)

## Azure Machine Learning

[Azure Machine Learning service](https://azure.microsoft.com/en-us/services/machine-learning-service/) is a cloud
service used to train, deploy, automate, and manage machine learning models, all at the broad scale that the cloud provides.

Have a look at the sample pipeline accelerator for [Azure Machine Learning](Azure_Machine_Learning/README.md)

## Azure Logic Apps

Connect your business-critical apps and services with [Azure Logic Apps](https://docs.microsoft.com/en-us/azure/logic-apps/), automating your workflows without writing a single line of code.

Have a look at the sample pipeline accelerator for [Azure Logic Apps with Form Recognizer](Azure_Logic_Apps/README.md)
