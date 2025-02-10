import requests
#from requests_toolbelt.multipart.encoder import MultipartEncoder
import GPTInterface

BOT_ACCESS_TOKEN        = None
BOT_ID                  = None
MESSAGE_CALLBACK_URL    = None
FORM_CALLBACK_URL       = None
CONNECT_TIMEOUT         = None
TRANSMIT_TIMEOUT        = None
HEADERS                 = None
TIMEOUTS                = None
MESSAGE_WEBHOOK_DATA    = None
FORM_WEBHOOK_DATA       = None
BOT_USER_NAME           = None

API_BASE_URL            = "https://webexapis.com/v1"
WEBHOOK_NAME_PM         = "private message"
WEBHOOK_NAME_FORM       = "attachment action"

PERSON_ID_MAPPINGS      = {}

DEBUG_WEBHOOK_REFRESH_DISABLED  = True


#### API interaction fuctions ####    

    
def get_person_details(person_id):  
    url = '%s/people/%s' % (API_BASE_URL, person_id)
    try:
        r = requests.get(url, headers = HEADERS, timeout=TIMEOUTS)
    except:
        pass
        return None
        
    
    try:
        rjson = r.json()
    except:
        return None
        
    return rjson 
    
def get_webhooks():
    url = '%s/webhooks' % API_BASE_URL
    try:
        r = requests.get(url, headers = HEADERS, timeout=TIMEOUTS)
    except:
        return None
        
    
    try:
        rjson = r.json()
    except:
        return None
        
    if 'items' in rjson:
        return rjson['items']
    
    return None
    
def create_webhook(webhook_data):
    url = '%s/webhooks' % API_BASE_URL
    try:
        r = requests.post(url, headers = HEADERS, json = webhook_data, timeout=TIMEOUTS)
    except:
        return None
        
        
    if r.status_code >= 200 and r.status_code < 300:
        return True
        
    return None
    
def delete_webhook(webhook_id):
    url = '%s/webhooks/%s' % (API_BASE_URL, webhook_id)
    try:
        r = requests.delete(url, headers = HEADERS, timeout=TIMEOUTS)
    except:
        return None
        
    
    if r.status_code >= 200 and r.status_code < 300:
        return True
    
    return None
    
def update_webhook(webhook_id):
    url = '%s/webhooks/%s' % (API_BASE_URL, webhook_id)
    try:
        r = requests.put(url, headers = HEADERS, json = WEBHOOK_DATA, timeout=TIMEOUTS)
    except:
        return None
        
    
    if r.status_code >= 200 and r.status_code < 300:
        return True
    
    return None   
    
def get_message(message_id):
    url = '%s/messages/%s' % (API_BASE_URL, message_id)
    try:
        r = requests.get(url, headers = HEADERS, timeout=TIMEOUTS)
    except:
        return None
        
    
    try:
        rjson = r.json()
    except:
        return None
        
    return rjson
    
def send_message(toPersonEmail, text, markdown=None, attachments=None):
    #print(f"debug - enter send_message, incoming text = {text}\n")
    url = '%s/messages' % API_BASE_URL
    
    modified_headers = HEADERS    
    modified_headers["content-type"] = "application/json; charset=utf-8"
    
    data = {
        'toPersonEmail': toPersonEmail
    }
    text = GPTInterface.BridgeIT(toPersonEmail,text)
    #print(f"debug, in send_message, message = {text}")
    if not text is None:
        data['text'] = text
    if not markdown is None:
        data['markdown'] = markdown
    if not attachments is None:
        data['attachments'] = attachments
    
    try:
        r = requests.post(url, headers = modified_headers, json = data, timeout=TIMEOUTS)
    except:
        return None
        
        
    if r.status_code >= 200 and r.status_code < 300:
        return True
        
    return None
    
#### HELPER FUNCTIONS ####
  

def validate_user(user_email):
    if type(user_email) is str and user_email.endswith('@cisco.com'):
        return True
    return False
    
    
def get_person_email_for_id(person_id):
    global PERSON_ID_MAPPINGS
    
    if person_id in PERSON_ID_MAPPINGS:
        return PERSON_ID_MAPPINGS[person_id]['email']
    else:
        person_details = get_person_details(person_id)
        if not person_details is None and 'userName' in person_details:
            PERSON_ID_MAPPINGS[person_id] = {'email': person_details['userName']}
            if 'firstName' in person_details:
                PERSON_ID_MAPPINGS[person_id]['firstName'] = person_details['firstName']
            if 'lastName' in person_details:
                PERSON_ID_MAPPINGS[person_id]['lastName'] = person_details['lastName']
            if 'displayName' in person_details:
                PERSON_ID_MAPPINGS[person_id]['displayName'] = person_details['displayName']
            return PERSON_ID_MAPPINGS[person_id]['email']
    return None    
    
    
#### UTILITIES FOR USE BY OTHER MODULES ####


def initialize(settings):

    global BOT_ACCESS_TOKEN
    global BOT_ID
    global CONNECT_TIMEOUT
    global TRANSMIT_TIMEOUT
    global MESSAGE_CALLBACK_URL
    global FORM_CALLBACK_URL
    global HEADERS
    global TIMEOUTS
    global MESSAGE_WEBHOOK_DATA
    global FORM_WEBHOOK_DATA
    global BOT_USER_NAME
    global DEBUG_WEBHOOK_REFRESH_DISABLED
    
    DEBUG_WEBHOOK_REFRESH_DISABLED = settings['webex']['debug_webhooks_disabled']
    BOT_ACCESS_TOKEN        = settings['webex']['bot_access_token']
    BOT_ID                  = settings['webex']['bot_id']
    CONNECT_TIMEOUT         = settings['webex']['connect_timeout_sec']
    TRANSMIT_TIMEOUT        = settings['webex']['transmit_timeout_sec']
    MESSAGE_CALLBACK_URL    = settings['webex']['message_callback_url']
    #FORM_CALLBACK_URL       = settings['webex']['form_callback_url']
    BOT_USER_NAME           = settings['webex']['bot_user_name']
    HEADERS                 = {
                                "Authorization": "Bearer %s" % BOT_ACCESS_TOKEN
                            }
    TIMEOUTS                = (CONNECT_TIMEOUT, TRANSMIT_TIMEOUT)
    MESSAGE_WEBHOOK_DATA    = {
                                'name'      : WEBHOOK_NAME_PM,
                                'targetUrl' : MESSAGE_CALLBACK_URL,
                                'resource'  : "messages",
                                'event'     : "created",
                                'filter'    : "roomType=direct"
                            }
    FORM_WEBHOOK_DATA       = {
                                'name'      : WEBHOOK_NAME_FORM,
                                'targetUrl' : FORM_CALLBACK_URL,
                                'resource'  : "attachmentActions",
                                'event'     : "created"
                            }
                                              
    webhooks = get_webhooks()
    if not webhooks is None:
        for webhook in webhooks:
            if not DEBUG_WEBHOOK_REFRESH_DISABLED:
                delete_webhook(webhook['id'])
            else:
                pass   
       
def process_message_webhook(webhook_json):
    
    if webhook_json['name'] == WEBHOOK_NAME_PM:
        if 'data' in webhook_json and 'personEmail' in webhook_json['data']:
            person_email = webhook_json['data']['personEmail']
            
            # cache personId to personEmail mapping to speed up process_attachment_action_webhook()
            if 'personId' in webhook_json['data']:
                person_id = webhook_json['data']['personId']
                if not person_id in PERSON_ID_MAPPINGS:
                    PERSON_ID_MAPPINGS[person_id] = {}
                PERSON_ID_MAPPINGS[person_id]['email'] = person_email
                
            if validate_user(person_email):
                if 'id' in webhook_json['data']:
                    message = get_message(webhook_json['data']['id'])
                    if not message is None:
                        result = {
                            'type'          : 'directMessage',
                            'personEmail'   : message['personEmail'],
                            'text'          : message['text']
                        }
                        return result
            else:
                if person_email != BOT_USER_NAME:
                    pass
                   
    return None 
    
    
async def refresh_webhooks():
    print("in webex.refresh_webhooks")
    if not DEBUG_WEBHOOK_REFRESH_DISABLED:
        existing_webhooks = get_webhooks()
        message_webhook_id  = None
        form_webhook_id     = None
        if not existing_webhooks is None:
            for webhook in existing_webhooks:
                if webhook['name'] == WEBHOOK_NAME_PM:
                    message_webhook_id = webhook['id']
                if webhook['name'] == WEBHOOK_NAME_FORM:
                    form_webhook_id = webhook['id']
                    
            if message_webhook_id is None:
                create_webhook(MESSAGE_WEBHOOK_DATA)
            else:
                update_webhook(message_webhook_id)
                
            if form_webhook_id is None:
                create_webhook(FORM_WEBHOOK_DATA)
            else:
                update_webhook(form_webhook_id)
    else:
        pass
    
    #GPTInterface.token_refresh2()
    return None
