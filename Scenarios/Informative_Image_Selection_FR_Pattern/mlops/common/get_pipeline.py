# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
get_pipeline function for finding a pipeline by name and version.
"""
from logging import getLogger

from azureml.core.workspace import Workspace
from azureml.pipeline.core.graph import PublishedPipeline

log = getLogger(__name__)


def get_pipeline(workspace: Workspace, name: str, build_id: str) -> PublishedPipeline:
    """
    _get_pipeline returns a published pipeline with name and build_id.
    Raises an exception if the pipeline is not found.

    Parameters:
        workspace (Workspace): The Azure ML workspace
        name (str): Name of the published pipeline
        build_id (str): Build ID (version) for the published pipeline

    Raises:
        Exception: Pipeline not found.

    Returns:
        PublishedPipeline: The published pipeline
    """
    pipelines = PublishedPipeline.list(workspace)
    pipeline_match = list(filter(
        lambda p: p.name == name and p.version == str(build_id),
        pipelines,
    ))

    if len(pipeline_match) == 0:
        log.error("Could not find pipeline %s", name)
        raise Exception("Published pipeline not found", name)

    return pipeline_match[0]
