import logging
import common.storage_helpers as storage_helpers
import common.image_helpers as image_helpers

def correct_form(form, vision_key, vision_region):

    # Get form data
    form_data = image_helpers.get_form_data(form, vision_key, vision_region)

    # Fix orientation
    if form_data:
        angle_to_fix = form_data['orientation']
        logging.info("Fixing orientation of %d"%angle_to_fix)
        corrected_form = image_helpers.rotate_image(form, angle_to_fix, form_data['width'], form_data['height'])
        return corrected_form
    
    return None

def create_response_single(storage_name, storage_key, vision_key, vision_region, form_path, output_form_path):

    # get original form
    blob_service = storage_helpers.create_blob_service(storage_name, storage_key)
    path = form_path.split('/')
    blob_name = path[1]
    container_name = path[0]
    blob = storage_helpers.get_blob(blob_service, container_name, blob_name)
    form = image_helpers.blob_to_image(blob)

    if form:

        # correct form and save
        corrected_form = correct_form(form, vision_key, vision_region)

        if corrected_form:
            output_path = output_form_path.split('/')
            output_name = output_path[1]
            output_container = output_path[0]
            storage_helpers.upload_blob(corrected_form, blob_service, output_name, output_container)

            # Create json response
            response = {
                "name": blob_name,
                "output_path": output_form_path
            }

        else:

            response = {
                "name": blob_name,
                "status":"failed"
            }

        return response

    else:
        logging.error("Could not create response.")
        return None

def create_response_batch(storage_name, storage_key, vision_key, vision_region, container_name, output_container=''):
    
    blob_service = storage_helpers.create_blob_service(storage_name, storage_key)
    generator = storage_helpers.list_blobs(blob_service, container_name)

    corrected_forms = []

    if(generator != None):

        for blob in generator:

            # get form
            form = image_helpers.blob_to_image(storage_helpers.get_blob(blob_service, container_name, blob.name))
            
            if(form != None): 
                # correct form and save
                output_name = "corrected_" + blob.name
                output_path = output_container + "/" + output_name
                corrected_form = correct_form(form, vision_key, vision_region)
                if(corrected_form != None):
                    storage_helpers.upload_blob(corrected_form, blob_service, output_name, output_container)

                    # create json
                    corrected_form_json = {
                        "name": blob.name,
                        "outputPath": output_path
                    }
                else:
                    corrected_form_json = {
                        "name": blob.name,
                        "status": "failed"
                    }
                corrected_forms.append(corrected_form_json)
            else:
                logging.error("Error creating response.")

    # Create final json response
    response = {
        "correctedForms": corrected_forms
    }

    return response
