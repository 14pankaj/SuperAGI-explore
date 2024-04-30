import json
import requests
import traceback
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_random_exponential

from superagi.config.config import get_config
from superagi.lib.logger import logger
from superagi.llms.base_llm import BaseLlm

MAX_RETRY_ATTEMPTS = 5
MIN_WAIT = 30 # Seconds
MAX_WAIT = 300 # Seconds

'''
Query body:

{
  "query": "Where was it founded?",
  "use_case": "generic",
  "temperature": 0.5,
  "inference_model": "azure.openai.gpt.3.5",
  "stream": false,
  "token_limit": 600,
  "tags": []
}

Response body:

data: 
{
    "conversation_id":"389f8d2d0e1a4fffa221bd2364c37d67",
    "message":{"message_id":"6411804ce17d47ddbab24eb5f22db2cd",
    "human":"Where was it founded?",
    "assistant":"Intel",
    "inference_settings":
        {
            "model":"",
            "temperature":"0.5",
            "token_limit":600,
            "input_token":null,
            "output_token":null,
            "tags":null
        },
    "timestamp":1713349390,
    "sources":[],
    "feedback":null}
}

'''
class Mi6(BaseLlm):
    def __init__(self, auth_token, model="azure.openai.gpt.4", temperature=0.5, use_case='generic', tags=None):
        self.auth_token = auth_token
        self.model = model
        self.temperature = temperature
        self.use_case = use_case
        self.tags = tags

    def get_source(self):
        return "MI6 API"
    
    def get_api_key(self):
        return self.auth_token
    
    def prepare_prompt(self, prompt):
        '''
        Since we don't use the system and human prompt distinction in MI6, 
        we need to collate the available prompt types from the agent prompt into one string.
        The agent prompts are of the format [{"role":"system", "content":"content"}, {"role":"user", "content":"content"}]
        '''
        prepared_prompt = []
        for role in prompt:
            if "{" in role["content"] and "}" in role["content"]:
                j_string = json.dumps(role["content"])
                prepared_prompt.append(j_string[1:-1])
            else:
                prepared_prompt.append(role["content"])
        prepared_prompt = ". ".join(prepared_prompt)
        return prepared_prompt

    def chat_completion(self, prompt, max_tokens = 4000):
        url = "https://apis-dev.intel.com/mi6/ui/v1/conversations" 
        header = {
            'Content-Type': 'application/json',
            "Authorization": f"Bearer {self.auth_token}"
        }
        prompt = self.prepare_prompt(prompt)
        payload = json.dumps({
                    "query": prompt,
                    "use_case": self.use_case,
                    "temperature": self.temperature,
                    "inference_model": self.model,
                    "stream": False,
                    "token_limit": max_tokens,
                    "tags": []
        })
        try:
            response = requests.request("POST", url, headers=header, data=payload)
            response.raise_for_status()
            logger.info(response)
            content = response.json()
            logger.info("the final respone",content["last_message"])
            return {"response": content, "content": content["last_message"]["assistant"]}
        except requests.exceptions.HTTPError as e:
            logger.error("Http Error:",e, e.response.text)
        except requests.exceptions.ConnectionError as e:
            logger.error("Connection Error:",e, e.response.text)
        except requests.exceptions.Timeout as e:
            logger.error("Timeout:",e, e.response.text)
        except requests.exceptions.RequestException as err:
            logger.error("Request error:",err, err.response.text)
        except Exception as e:
            logger.error(traceback.format_exc(), prompt)
            logger.error(response.json())
            logger.error(e)
            
    def verify_access_key(self):
        return True
    
    def get_models(self):
        return "models"
    
    def get_model(self):
        return self.model