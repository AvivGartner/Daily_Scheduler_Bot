import requests
import json
import asyncio
import urllib3
import os
from dotenv import load_dotenv
from typing import Optional, Dict, List
import sys
sys.set_int_max_str_digits(10000)

# Read the information from the .env file.
load_dotenv()

# Designed to overcome antivirus software (and in this case, NetSpark).
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Define the connectivity to the AI model: API key, model type, and link to it.
apiKey = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-3.5-flash-lite"
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
                        "description": "The type of action to perform."
                    },
                    "task_name": {
                        "type": "STRING",
                        "description": "Task name. Use 'none' if action is view_schedule or clear_all."
                    },
                    "start_hour": {
                        "type": "INTEGER",
                        "description": "Start hour (0-23). If not provided, MUST be -1."
                    },
                    "end_hour": {
                        "type": "INTEGER",
                        "description": "End hour (0-24). If not provided, MUST be -1."
                    },
                    "hours_count": {
                        "type": "INTEGER",
                        "description": "Duration. If not provided, MUST be -1."
                    }
                },
                "required": ["action_type", "task_name", "start_hour", "end_hour", "hours_count"]
            }
        }
    },
    "required": ["actions"]
}
# Instructions to AI regarding user input and how to analyze it.
SYSTEM_PROMPT = """
You are a professional schedule assistant. The user speaks Hebrew.
Extract actions into JSON. 

CRITICAL RULES:
1. Task Name Normalization & Context:
   - Keep the FULL context and description of the user's task. DO NOT delete words.
   - ALWAYS convert the main action verb (usually the first word) to its Hebrew infinitive form (צורת מקור).
   - Examples: "לומד אלגוריתמים" -> "ללמוד אלגוריתמים", "עובד על קורות חיים" -> "לעבוד על קורות חיים", "אוכל" -> "לאכול".
   - 'task_name' should be 'none' if the action is clear_all or view_schedule.

2. Time Fields:
   - If the user gives a start and end time (e.g., 8 to 17), use 'add_fixed' and set start_hour=8, end_hour=17.
   - If the user gives only a duration (e.g., 2 hours), use 'add_unfixed' and set hours_count=2.
   - For ANY field that is not provided by the user or not relevant to the action (like end_hour in 'add_unfixed'), you MUST output -1. Do not omit the key.
"""

async def parse_user_request(user_text: str) -> Optional[Dict]:
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
            "temperature": 0.0
        }
    }
    # Retry mechanism (Exponential Backoff)
    for delay in [1, 2, 4, 8]:
        try:
            response = await asyncio.to_thread(
                requests.post,
                API_URL,
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload),
                timeout=30,
                verify=False
            )
            # Check for success (HTTP 200)
            if response.status_code == 200:
                result = response.json()
                try:
                    # Extract text safely
                    json_content = result['candidates'][0]['content']['parts'][0]['text']

                    print("\n--- RAW MODEL OUTPUT START ---")
                    print(json_content)
                    print("--- RAW MODEL OUTPUT END ---\n")

                    # Convert JSON string to Python dictionary
                    return json.loads(json_content)
                except (KeyError, IndexError, json.JSONDecodeError) as parse_error:
                    print(f"Error parsing Gemini JSON response: {parse_error}")
                    print(f"Raw response structure: {result}")
                    return None
            # Handle temporary server errors (like overload)
            if response.status_code in [429, 500, 503]:
                print(f"Server busy (Status Code: {response.status_code}), retrying in {delay} seconds...")
                await asyncio.sleep(delay)
                continue
            else:
                # Critical error (e.g., wrong key) - no point retrying
                print(f"Error: API return status code {response.status_code}")
                print (response.text)
                break
        except Exception as e:
            print(f"Network or parsing error: {e}")
            await asyncio.sleep(delay)
    return None