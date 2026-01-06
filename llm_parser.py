import requests
import json
import time
import urllib3
from typing import Optional, Dict, List

# Designed to overcome antivirus software (and in this case, NetSpark).
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Define the connectivity to the AI model: API key, model type, and link to it.
apiKey = "AIzaSyBQW5HdrmChvmS2BN2OyqW9Vlrg5TaaQiY"
MODEL_NAME = "gemini-2.5-flash-preview-09-2025"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={apiKey}"

# Define the desired json file structure.
ACTION_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "actions": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "action_type": {
                        "type": "STRING",
                        "enum": ["add_fixed", "add_unfixed", "view_schedule", "clear_all"],
                        "description": "The type of action to perform based on user intent."
                    },
                    "task_name": {
                        "type": "STRING",
                        "description": "The name of the task (e.g, 'Meeting', 'study')."
                    },
                    "start_hour": {
                        "type": "INTEGER",
                        "description": "Start hour (0-23). Required only for 'add_fixed'."
                    },
                    "end_hour": {
                        "type": "INTEGER",
                        "description": "End hour (1-24). Required only for 'add_fixed'."
                    },
                    "hours_count": {
                        "type": "INTEGER",
                        "description": "Duration in hours. Required only for 'add_unfixed'."
                    }
                },
                "required": ["action_type", "task_name"]
            }
        }
    },
    "required": ["actions"]
}

# Instructions to AI regarding user input and how to analyze it.
SYSTEM_PROMPT = """
You are a professional schedule assistant. Your task is to extract scheduling actions from the user's text.
The user speaks Hebrew. You must analyze their request and return a list of actions in JSON format.

Guidelines:
- If a user specifies a time range (e.g., 10:00 to 12:00), use 'add_fixed'.
- If a user specifies a duration (e.g., 3 hours) without a specific time, use 'add_unfixed'.
- If the user wants to see their day, use 'view_schedule'.
- If the user wants to start over, use 'clear_all'.
- Be precise with hours (e.g., '10 PM' is 22).
"""

def parse_user_request(user_text: str) -> Optional[Dict]:
    """
    Send free text to Gemini and returning a corresponding json file.
    This function handles the API communication, including constructing the payload with the defined schema and system prompts.
    It also implements an exponential backoff mechanism to handle temporary server errors gracefully.
    :param user_text: Free text entered by the user.
    :return: A Python dictionary containing the parsed actions if successful, or None if the API call failed or the response couldn't be parsed.
            The dictionary structure follows ACTION_SCHEMA.
    """
    # Prepare the message payload in the format expected by Gemini
    payload = {
        "contents": [{"parts": [{"text": user_text}]}],
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": ACTION_SCHEMA,
        }
    }
    # Retry mechanism (Exponential Backoff)
    for delay in [1, 2, 4, 8]:
        try:
            response = requests.post(
                API_URL,
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload),
                timeout = 10,
                verify=False
            )
            # Check for success (HTTP 200)
            if response.status_code == 200:
                result = response.json()
                # Extract text from nested response
                # Structure: result -> candidates -> content -> parts -> text
                json_content = result['candidates'][0]['content']['parts'][0]['text']
                # Convert JSON string to Python dictionary
                return json.loads(json_content)
            # Handle temporary server errors (like overload)
            if response.status_code in [429, 500, 503]:
                print(f"Server busy (Status Code: {response.status_code}), retrying in {delay} seconds...")
                time.sleep(delay)
                continue
            else:
                # Critical error (e.g., wrong key) - no point retrying
                print(f"Error: API return status code {response.status_code}")
                print (response.text)
                break
        except Exception as e:
            print(f"Network or parsing error: {e}")
            time.sleep(delay)
    return None