# This function an HTTP starter function for Durable Functions.
# Before running this sample, please:
# - create a Durable orchestration function
# - create a Durable activity function (default name is "Hello")
# - add azure-functions-durable to requirements.txt
# - run pip install -r requirements.txt

import logging

import azure.functions as func
import azure.durable_functions as df


async def main(myblob: func.InputStream, starter: str):
    client = df.DurableOrchestrationClient(starter)

    instance_id = await client.start_new(
        "Orchestrator",
        None,
        {"path": myblob.name, "uri": myblob.uri, "length": myblob.length},
    )

    logging.warning(
        f"Python blob trigger function processed blob \n"
        f"Name: {myblob.name}\n"
        f"Blob Size: {myblob.length} bytes"
    )

    logging.warning(f"Started orchestration with ID = '{instance_id}'.")
