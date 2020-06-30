# This function is a Blob Trigger action for Durable Functions.

import logging

import azure.functions as func
import azure.durable_functions as df


async def main(myblob: func.InputStream, starter: str):
    client = df.DurableOrchestrationClient(starter)

    logging.info(
        f"Python blob trigger function processed blob \n"
        f"Name: {myblob.name}\n"
        f"Blob Size: {myblob.length} bytes"
    )

    instance_id = await client.start_new(
        "Orchestrator",
        None,
        {"path": myblob.name, "uri": myblob.uri, "length": myblob.length},
    )

    logging.info(f"Started orchestration with ID = '{instance_id}'.")
