# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
This is a helper for all Azure ML Pipelines
"""
from azureml.core.runconfig import Environment, CondaDependencies  # type: ignore
from azureml.pipeline.core import Pipeline, PublishedPipeline  # type: ignore
from .workspace import get_workspace
from .attach_compute import get_compute

# following line will load all the necessary env vars
from .env_vars import workspace_name, resource_group, \
    subscription_id, tenant_id, app_id, app_secret, \
    region, compute_name, vm_size, vm_priority, min_nodes, max_nodes, scale_down


def pipeline_base():
    """
    Gets AzureML artifacts: AzureML Workspace, AzureML Compute Tagret and AzureMl Run Config
    Returns:
        Workspace: a reference to the current workspace
        ComputeTarget: compute cluster object
        Environment: environment for compute instances
    """
    # Get Azure machine learning workspace
    aml_workspace = get_workspace(workspace_name,
                                  resource_group,
                                  subscription_id,
                                  tenant_id,
                                  app_id,
                                  app_secret,
                                  region,
                                  create_if_not_exist=False)
    print(aml_workspace)

    # Get Azure machine learning cluster
    aml_compute = get_compute(aml_workspace, compute_name, vm_size,
                              vm_priority, min_nodes, max_nodes, scale_down)

    if aml_compute is not None:
        print(aml_compute)

        batch_conda_deps = CondaDependencies.create(
            conda_packages=[],
            pip_packages=[
                'argparse==1.4.0',
                'azureml-sdk==1.18.0',
                'azure-storage-blob==12.5.0',
                'azure-identity==1.4.1',
                'azure-mgmt-resource==10.2.0',
                'azure-mgmt-network==16.0.0',
                'azure-mgmt-compute==17.0.0',
                'pyjwt==1.7.1',
                'numpy==1.18.5',
                'pandas==1.1.3',
                'pillow==7.2.0',
                'pyarrow==1.0.1',
                'scikit-image==0.17.2',
                'scikit-learn==0.23.2',
                'scipy==1.5.2',
                'tqdm==4.48.2',
                'opencv-python-headless',
                'tensorflow==2.3.0',
                'azure-cognitiveservices-vision-customvision==3.0.0',
                'PyYAML==5.3.1',
                'ipywidgets==7.5.1',
                'click==7.1.2',
                'python-dotenv==0.10.3'
            ])
        batch_env = Environment(name="train-env")
        batch_env.docker.enabled = True
        batch_env.python.conda_dependencies = batch_conda_deps

    return aml_workspace, aml_compute, batch_env


def publish_pipeline(aml_workspace, steps, pipeline_name,
                     build_id) -> PublishedPipeline:
    """
    Publishes a pipeline to the AzureML Workspace
    Parameters:
      aml_workspace (Workspace): existing AzureML Workspace object
      steps (list): list of PipelineSteps
      pipeline_name (string): name of the pipeline to be published
      build_id (string): DevOps Pipeline Build Id

    Returns:
        PublishedPipeline
    """
    train_pipeline = Pipeline(workspace=aml_workspace, steps=steps)
    train_pipeline.validate()
    published_pipeline = train_pipeline.publish(
        name=pipeline_name,
        description="Model training/retraining pipeline",
        version=build_id)
    print(
        f'Published pipeline: {published_pipeline.name} for build: {build_id}')

    return published_pipeline
