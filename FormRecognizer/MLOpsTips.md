# MLOps Tips and Tricks for Form Recognizer

[Azure Form Recognizer (FR)](https://docs.microsoft.com/en-us/azure/cognitive-services/form-recognizer/?branch=release-build-cogserv-forms-recognizer) is an AI powered service to extract text from documents. It comes with [pre-built ML models](https://docs.microsoft.com/en-us/azure/cognitive-services/form-recognizer/overview?tabs=v2-1#prebuilt-models) to support common use cases (i.e., invoices, business cards) and supports [training custom models](https://docs.microsoft.com/en-us/azure/cognitive-services/form-recognizer/overview?tabs=v2-1#custom-models) to handle other use cases.

This document discusses operational challenges and potential solutions when using FR custom models. Each section of this document discusses a specific challenge and how it can be addressed. This is not meant to be an extensive list, but rather an accumulation of experiences.

> **Note:** this document is based on v2.0 of Form Recognizer.

## Model Management

When submitting a request to train a custom model, FR generates a unique model id to refer to the model training attempt. FR expects the user to track this model id and pass it whenever they need to use or manage the trained custom model. In addition to the model id, FR tracks when the model was trained, when the training had been completed, and the status of the model (i.e., ready for inference, pending training...etc.).

As a user, you need to create a custom solution to track your model ids. The model id is a UUID, thus it would be beneficial to track additional information as part of your solution, such as a description of the model, readable labels, an audit trail of how the model came to exist, and keep track of previous versions of the model, among other things. One thing to note, FR does not support retraining an existing model, instead it would generate a new model with a new model id for each training request. Each version of your model would have a different model id to be tracked.

FR has a max limit on how many models it can persist at any given time. Training attempts contribute towards this limit, regardless of whether the training was successful or not. You can identify your FR instance limit via the [management APIs](https://docs.microsoft.com/en-us/azure/cognitive-services/form-recognizer/quickstarts/client-library?tabs=preview%2Cv2-1&pivots=programming-language-csharp#manage-custom-models).
Depending on your use case, you may need to manage which models to keep in your FR instance vs archive or remove. It might be beneficial to persist recent models to enable model rollback if needed. For archived models, the audit trail can persist the necessary information to re-train an archived model.
On the other hand, if your use case justifiably requires persisting a high number of models, the FR models limit can be increased by reaching out to Azure customer support. It would be beneficial to evaluate the needed capacity before engaging with customer support.

## Scale and Performance

There are a couple of things to keep in mind when considering the scalability and performance of FR.
For throughput, FR enforces a different concurrent requests limit per API, those are soft limits that can be increased by reaching out to the Azure customer support.
Before reaching out, it would be beneficial to identify the needed throughput and evaluate if FR limits need to be increased.

When it comes to latency, it is important to note that FR APIs are implemented as [long running operations](https://docs.microsoft.com/en-us/dotnet/api/overview/azure/ai.formrecognizer-readme-pre#long-running-operations) and the latency might be different based on what is being analyzed.

## Model Training and Deployment

Typically, software systems have multiple deployment environments, each with its own purpose. You have DEV for development purposes, Staging for testing and debugging issues occurring in production, Production to serve consumers, among others. In a similar fashion, your ML solution would benefit from having multiple FR instances: experimentation and training can take place in DEV, testing and verification in staging, and production to serve your consumers.

For deploying the models from one environment to another, FR provides a Copy API that copies a model from one FR instance to another, [this article discusses how to perform a copy operation](https://docs.microsoft.com/en-us/azure/cognitive-services/form-recognizer/disaster-recovery#copy-api-overview), the copied model would have a new model id generated for it.

In such systems, it is important to track which models exist in each environment and what version of the model exists, to relate that to any feedback mechanism you may have. The example tracking system discussed below demonstrates a simple solution to manage tracking the models and their state in each environment.

## Mapping File Approach

This approach addresses many of the challenges around model tracking, retraining, deletion, and deployment.
The core of this solution focuses on tracking the relationship between a form layout and the FR model id in a json file, referred to as the mapping file.

### Layout

A common use case for having multiple FR models is when you have multiple distinct forms you want to extract data from, where you train a FR model per form layout.
As stated above, in order to improve or retrain an existing FR model, you must train a new FR model with the updated dataset.
Thus, there is not a 1:1 mapping of layouts to model ids, as updating a layout will result in a new model id.

The mapping file will track the relationship between a layout and the current model id that processes that layout.

### Mapping

Here is a sample mapping json file showing this relationship:

```json
{
  "1040": "a2190780-1e47-4602-bf06-00b70548c63e",
  "1040V": "7eeb577b-3066-47de-929f-d00b7f9eaae1",
  "1040ES": "af1b07ea-3d53-4a2e-a629-f4c996e4ba96",
  "1099R": "937359c8-a40e-475b-9e8d-1891655ae394",
  "1099": "328e73d7-04ec-4da8-b0a2-631201d7fa48",
  "1040X": "70a798ac-b955-4c04-b47c-40ddba700c87"
}
```

The key represents a form layout, while the value is the FR model id that you trained for that layout.

### Training and Single Environment Deployment

This section assumes you are training with [Azure Machine Learning (AML)](https://azure.microsoft.com/en-us/services/machine-learning/), but can be adapted as needed.

Using AML pipelines and scripts, you can set up FR model training per layout as needed.
It is beneficial to setup the AML training pipelines to either take an input for, or determine from the training data, what layouts need to be retrained.
This way, your training script can "retrain" by training a new FR model with the updated dataset, and then merge the newly trained model ids with the existing mapping file.
The merge will replace the ids for any updated layouts with the new model ids.
Updating the mapping file in this way prevents having to retrain all models if only a subset needs to be retrained, thus reducing the cost of training and number of models kept in the FR instance.

You should track the old model ids that were replaced in a separate file, as these models will need to be deleted from the FR instance to save space.
It is preferred to delete these models only after the new models have been verified (either automated or manual) in case there was a regression.

When using AML, you can store the mapping file in the model registry, as it accepts json files.
This is powerful as you have access to the versioning, tagging, and audit trail that AML's model registry provides.
It also makes it easy to access this file during training, which is needed to merge the retrained layouts as discussed above.

Your inference service can access this mapping file and route inference requests to the appropriate FR model based on the incoming document layout.
Depending on the nature of your use case it might be easy to determine the form's layout, or you may need an separate ML model (i.e. not a Form Recognizer model) for this purpose may be needed.
One approach is to rely on the location, orientation or size of the form can change from instance to instance, as discussed [here](https://github.com/microsoft/knowledge-extraction-recipes-forms/tree/master/Analysis/Routing_Forms).

AML provides a few ways to access files stored in the model registry, and one solution is to have a python script download the mapping file to a Storage Account during a deployment pipeline.

### Multiple Environment Deployment

When dealing with multiple FR instance across multiple deployment environment and regions, you need to track more information in the mapping file.
By adding environment and region keys to the mapping file, you can overcome the additional challenges with migrating models across FR instance.

Here is an example mapping file that includes environment and region information:

```json
{
  "dev": {
    "westus": {
      "1040": "a2190780-1e47-4602-bf06-00b70548c63e",
      "1040V": "7eeb577b-3066-47de-929f-d00b7f9eaae1",
      "1040ES": "af1b07ea-3d53-4a2e-a629-f4c996e4ba96",
      "1099R": "937359c8-a40e-475b-9e8d-1891655ae394",
      "1099": "328e73d7-04ec-4da8-b0a2-631201d7fa48",
      "1040X": "70a798ac-b955-4c04-b47c-40ddba700c87"
    }
  },
  "staging": {
    "eastus2": {
      "1040": "442d6021-b6db-4ba9-a239-66e4110474c1",
      "1040V": "70a469b2-c962-47bc-9a1f-aadd7055b375",
      "1040ES": "218095cd-fb10-4f03-a7a7-677cdf217fc5",
      "1099R": "043cd574-38c9-4d5f-ad4a-b05f50f07b4f",
      "1099": "e10dad9a-cd03-4e96-a550-321cee950356",
      "1040X": "453d5f81-afda-4a32-893e-9f87ef4b017a"
    }
  }
}
```

In this situation, every possible environment + region combination represents a unique FR instance.
So in this example, there are two FR instances, one in westus dev and one in eastus2 staging.
For simplicity, the rest of this document will refer to these environment + region combinations simply as the environment.

Training should happen on a specific FR instance that is in one of these environments.
The additional environments in the file only come into play when deploying to subsequent environments, so the training steps and first deployment steps from above work in the same way.
After training, you should expect your full mapping file to look as follows (assuming you train in dev and westus):

```json
{
  "dev": {
    "westus": {
      "1040": "a2190780-1e47-4602-bf06-00b70548c63e",
      "1040V": "7eeb577b-3066-47de-929f-d00b7f9eaae1",
      "1040ES": "af1b07ea-3d53-4a2e-a629-f4c996e4ba96",
      "1099R": "937359c8-a40e-475b-9e8d-1891655ae394",
      "1099": "328e73d7-04ec-4da8-b0a2-631201d7fa48",
      "1040X": "70a798ac-b955-4c04-b47c-40ddba700c87"
    }
  }
}
```

### Migration Script

As part of your deployment pipeline, there should be a FR model migration script that interacts with mapping files and the FR copy API to migrate models between FR instances.
Each environment will have a mapping file that represents the current models on that FR instance.
These mapping files need to be stored somewhere and one solution is to use a Storage Account in each environment.
While each mapping file is representative of its environment's current state, in terms of migration it is convenient to think of the source environment's mapping file as the desired state for the target environment while the target environment's mapping file is the current state.

The core idea behind the script is to read in the source and target mapping files, diff them, and migrate any layouts that are present in the source but missing in the target environment by calling the FR copy API for those model ids.
The copy command returns new ids that are then updated in the target mapping file.
If layouts are in the target but missing in the source, they should be deleted (since source is the desired state).

This approach breaks down if a layout has been retrained.
Since retraining a layout in the source env will result in a new id, its impossible for the script to know if it needs to copy a model for a layout that is already tracked in the target mapping file.
To fix this, the target mapping file needs to contain a snapshot of what the source mappings were last time this migration happened.

Let's consider the example where the source mapping file is:

```json
{
  "dev": {
    "westus": {
      "1040": "a2190780-1e47-4602-bf06-00b70548c63e",
      "1040V": "7eeb577b-3066-47de-929f-d00b7f9eaae1",
      "1040ES": "af1b07ea-3d53-4a2e-a629-f4c996e4ba96",
      "1099R": "937359c8-a40e-475b-9e8d-1891655ae394",
      "1099": "328e73d7-04ec-4da8-b0a2-631201d7fa48",
      "1040X": "70a798ac-b955-4c04-b47c-40ddba700c87"
    }
  }
}
```

And the target mapping file is:

```json
{
  "dev": {
    "westus": {
      "1040": "a2190780-1e47-4602-bf06-00b70548c63e",
      "1040V": "89818d7e-a84b-40c3-ab39-0c2e83f28dbf",
      "1040ES": "af1b07ea-3d53-4a2e-a629-f4c996e4ba96",
      "1099R": "937359c8-a40e-475b-9e8d-1891655ae394",
      "1099": "328e73d7-04ec-4da8-b0a2-631201d7fa48"
    }
  },
  "staging": {
    "eastus2": {
      "1040": "442d6021-b6db-4ba9-a239-66e4110474c1",
      "1040V": "70a469b2-c962-47bc-9a1f-aadd7055b375",
      "1040ES": "218095cd-fb10-4f03-a7a7-677cdf217fc5",
      "1099R": "043cd574-38c9-4d5f-ad4a-b05f50f07b4f",
      "1099": "e10dad9a-cd03-4e96-a550-321cee950356"
    }
  }
}
```

In the target mapping file, the dev->westus object is the snapshot of the source environment when the previous migration happened.
So the script will compare dev->westus in source with dev->westus in target, and detect that the id for `1040V` has changed and `1040X` has been added since the previous migration.

Thus the script will know to migrate `1040V` and `1040X` ids to the target env.
Once the migration has completed, the target mapping file will be updated with the newly copied model ids, and the dev->westus object in the target file will be replaced with the dev->westus object in the source file, as you need to snapshot the source environment's state during this migration.
So the next time the migration script runs, it will be able to detect new or retrained layouts.

Like training, the script needs to track the ids that were replaced or removed from the target mapping file and delete these models from the target FR instance to save space.

While the target mapping file has multiple environment keys, the inference service for that environment can be set to target a specific path, i.e. the staging service will know to index into staging->eastus2 to find its mappings.
These mapping files can be chained together for as many environments as needed, meaning the updated target file can be used as the source file for the next environment.
Saving multiple environment's mapping in a single mapping file also helps with auditing, as you can see what the state of both environments were during the previous migration, and the script can be set to continuously build up this environment migration recorded if desired.

## Model Migration Script

This is the core logic of the model migration script, without the downloading and uploading of the various mapping files.
You need to get the mapping files into python dicts as well as get your FR keys, endpoints, and resource_ids in the `envConfigs` class for the script to work.
Currently, the script does not delete models from target that were removed in the source mapping file, but there is a `#TODO` where that logic should be added.

```python
#!/usr/bin/python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import FormTrainingClient, \
    FormRecognizerApiVersion, CustomFormModelStatus
import json
import os
import copy
import collections.abc

class envConfigs:
  """
  This class holds the configurations for a given environment.
  """

  def __init__(self, env, region, fr_endpoint,
                fr_resource_id, fr_key):
      self.environment = env
      self.region = region
      self.fr_endpoint = fr_endpoint
      self.fr_resource_id = fr_resource_id
      self.fr_key = fr_key

def get_layouts(mapping_file, env_config):
    """
    This function retrieves the layout config within
    the provided mapping file.
    :param mapping_file: The mapping file dict to get the layouts for
    :param env_config: The config for that environment
    """
    if mapping_file == {}:
        return {}
    if (env_config.environment not in mapping_file.keys())
    or (env_config.region not in mapping_file[env_config.environment].keys()):
        return {}
    return mapping_file[env_config.environment][env_config.region]

def identify_models_to_copy(previous_mapping, current_mapping):
    """
    This function identifies the delta between two mapping files.
    This delta will hold which models should be copied between two FR instances.
    :param previous_mapping: The previous mapping dict
    :param current_mapping: The current mapping dict
    """
    models_to_copy = {}
    for layout in current_mapping:
        if layout in previous_mapping.keys():
            if previous_mapping[layout] != current_mapping[layout]:
                models_to_copy[layout] = current_mapping[layout]
        else:
            models_to_copy[layout] = current_mapping[layout]
    return models_to_copy

def deep_update(d, u):
    """
    Updates dictionaries deeply
    :param d: The dict to update
    :param u: The data to update with
    """
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = deep_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d

def update_mapping_file(target_mapping, target_env_configs, source_layouts,
                        updated_layouts, source_env_configs):
    """
    This function will only update the layouts config in the given mappingFile
    It will persist the rest of the configurations as is.
    :param target_mapping: The current target mapping dict
    :param target_env_configs: The configs for the target env
    :param source_layouts: The layouts from the source mapping file
    :param updated_layouts: The layouts that were updated
    :param source_env_configs: The configs for the source env
    """
    updated_mapping_file = copy.deepcopy(target_mapping)
    deep_update(updated_mapping_file, {target_env_configs.environment: {
        target_env_configs.region: updated_layouts}})
    # Add source mappings to new mapping file to track the state of
    # source during this migration
    deep_update(updated_mapping_file, {source_env_configs.environment: {
        source_env_configs.region: source_layouts}})
    updated_layouts = (updated_mapping_file[target_env_configs.environment]
                       [target_env_configs.region])
    # Remove layouts deleted in source from the target mapping file
    # TODO add logic to remove these models from the target FR instance itself
    updated_layouts = {
        k: v for k, v in updated_layouts.items() if k in source_layouts.keys()}
    updated_mapping_file[target_env_configs.environment][target_env_configs.region] = \
     updated_layouts
    return updated_mapping_file

    def main():
    print('Form Recognizer models copy started!')
    # load the env configs
    source_env_configs = envConfigs()
    target_env_configs = envConfigs()
    source_current_mapping_file = # Load json from storage
    target_mapping_file = # Load json from storage
    if source_current_mapping_file == {}:
        raise ValueError(
            'Error: Source current mapping file is empty or does not exist')
    # load the new layouts
    source_current_layouts = get_layouts(
        source_current_mapping_file, source_env_configs)
    models_to_copy = {}
    # if there is no previous mapping file then copy over all of the new layouts.
    # otherwise, load the previous mapping and only copy what had changed.
    # Load the source model snapshot that is stored in the target mapping file
    # from the last migration to target
    source_previous_layouts = get_layouts(
        target_mapping_file, source_env_configs)
    if source_previous_layouts == {}:
        models_to_copy = copy.deepcopy(source_current_layouts)
    else:
        # identify delta in the models
        models_to_copy = identify_models_to_copy(
            source_previous_layouts, source_current_layouts)
    print(f'The following models will be copied {models_to_copy}')
    # create FR clients
    source_fr_client = FormTrainingClient(
        endpoint=source_env_configs.fr_endpoint,
        credential=AzureKeyCredential(source_env_configs.fr_key),
        api_version=FormRecognizerApiVersion.V2_0)
    target_fr_client = FormTrainingClient(
        endpoint=target_env_configs.fr_endpoint,
        credential=AzureKeyCredential(target_env_configs.fr_key),
        api_version=FormRecognizerApiVersion.V2_0)
    # Given that the nature of the copy process,
    # first, kick off the copy for all models
    # in the identified delta and track
    # the returned pollers.
    for key in models_to_copy:
        try:
            target_model = target_fr_client.get_copy_authorization(
                resource_region=target_env_configs.region,
                resource_id=target_env_configs.fr_resource_id
            )

            poller = source_fr_client.begin_copy_model(
                model_id=models_to_copy[key],
                target=target_model
            )
            result = poller.result()
            models_to_copy[key] = target_model['modelId']
            # Check status
            if (result.status is not None and
             result.status == CustomFormModelStatus.READY):
                print(
                    f'Model {source_current_layouts[key]}' \
                    ' copied successfully to {models_to_copy[key]}!')
            else:
                print(
                    f'Model {source_current_layouts[key]} ' \
                    'copy to {models_to_copy[key]} is taking ' \
                    'longer than expected and might need to be investigated!')
        except Exception as ex:
            print(
                f'Failed to copy model {source_current_layouts[key]} with error {ex}')
            # Remove the failed model to avoid updating it in the updated mapping file!
            models_to_copy.pop(key)
            raise
    # Finally, update the target mapping file
    new_target_mapping_file = update_mapping_file(
        target_mapping_file, target_env_configs, source_current_layouts,
        models_to_copy, source_env_configs)
    # update target mapping file for source layout to maintain previous version
    print(f'Updated target file {new_target_mapping_file}')
    # Upload new mapping file
    print('Done!')
if __name__ == "__main__":
    main()
```
