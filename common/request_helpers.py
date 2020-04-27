import requests
import logging


def get_request(uri, headers):
    logging.info("GET Request to: %s"%uri)
    response = None
    try:
        response = requests.get(uri,headers=headers) 
    except Exception as e:
        logging.error("Error executing GET request: %s"%e)
    if(response != None):
        try:
            result = response.json()
            #logging.info(result)
            return result
        except AttributeError:
            logging.info(response)
            return response  
        except Exception as e:
            logging.error("Could not execute GET request: %s"%e)
    return None


def post_request(uri, body, headers):
    logging.info("POST request to: %s"%uri)
    response = None
    try:
        response = requests.post(url=uri,data=body,headers=headers)
    except Exception as e:
        logging.error("Error executing POST request: %s"%e)
    if(response != None):
        try:
            result = response.json()
            #logging.info(result)
            return result
        except AttributeError:
            logging.info(response)
            return response
        except Exception as e:
            logging.error("Could not execute POST request: %s"%e)  
    return response