# CLI startup with uvicorn:
# uvicorn main:app --reload --host 0.0.0.0 --port <port number>
import logging
from fastapi import FastAPI, Request
from fastapi_utils.tasks import repeat_every
#import json
import asyncio
from pprint import pprint

try:
    import tomllib
except:
    import tomli as tomllib

import webex
settings = None

global userState
userState = {}

MAINTENANCE_HAS_NEVER_BEEN_RUN      = True        
#logging.basicConfig(level=logging.DEBUG)
MAINTENANCE_LOOP_INTERVAL_SECONDS   = 6000 # MODIFY THIS TO ADJUST MAINTENANCE FREQUENCY. 21600 seconds = 6 hours

### WEBHOOK LISTENERS ###


app = FastAPI()

@app.post("/webexMessage")

async def webex_create_message(request: Request):
    #This responds to the initial user message
    #print("DEBUG: in /webexMessage")
    
    rjson   = await request.json()
    processed_data = webex.process_message_webhook(rjson)
    if processed_data is not None:
        webex.send_message(processed_data['personEmail'], processed_data['text'])

    return {}
    
     
#### MAINTENANCE AND STARTUP TASKS ####

    
@repeat_every(seconds=MAINTENANCE_LOOP_INTERVAL_SECONDS)

async def maintenance_loop():
    print("in maintenance loop")
    global MAINTENANCE_HAS_NEVER_BEEN_RUN
    await webex.refresh_webhooks()
    print("webex refresh done")
    MAINTENANCE_HAS_NEVER_BEEN_RUN = False
        
@app.on_event("startup")
async def startup_procedures():
    global settings
    print("Loading settings...")
    with open("config/settings.toml", "rb") as f:
        settings = tomllib.load(f)
    if not settings is None:
        webex.initialize(settings)
        await maintenance_loop()
              
    else:
        print("Error: Unable to load config/settings.toml")
        
#### HELPER FUNCTIONS ####

async def send_webex_message(person_email, message):
    webex.send_message(person_email, markdown=message)
    return

def create_filters_from_str(filters_string):
    if filters_string is None:
        return ['all']
    result = []
    split = filters_string.split(',')
    for part in split:
        result.append(part.strip())
    return result
