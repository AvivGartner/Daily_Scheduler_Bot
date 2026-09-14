Markdown
# Smart NLP Daily Scheduler Bot 📅🤖

An asynchronous, AI-powered scheduling bot that converts natural language requests into a structured daily schedule. Built with Python, this project integrates the **Telegram Bot API** and **Google Gemini LLM** to process complex time-management prompts in Hebrew.

## Features

* **Natural Language Processing (NLP):** Utilizes Google Gemini to parse messy, multi-action user inputs into structured JSON payloads.
* **Smart Time Allocation:** 
  * **Fixed Tasks:** "I need to sleep from 00:00 to 08:00" translates directly to specific time slots.
  * **Flexible Tasks:** "I need to study for 5 hours" automatically finds and fills the earliest available consecutive (or fragmented) hours in the daily schedule.
* **Task Normalization:** Automatically converts contextual actions into clean, infinitive verb formats (e.g., "I am studying algorithms" -> "To study algorithms") while preserving user context.
* **Conflict Resolution & Priorities:** Manages execution order seamlessly (e.g., processing deletions and fixed-time tasks before fitting in flexible-time tasks).
* **Multi-Interface Support:** Includes both an asynchronous Telegram interface (`aiogram`) for real-world usage and a Console application for local testing.
* **Message Batching:** Aggregates execution results into clean, single-message outputs to prevent chat spam.

## Architecture

* `main_telegram.py` / `main_console.py`: The presentation and execution layer. Handles user input, API communication, and message batching.
* `llm_parser.py`: The AI integration layer. Sends the user's raw text alongside a strict `SYSTEM_PROMPT` to the Gemini API, enforcing JSON-only output with specific schemas.
* `scheduler_logic.py`: The core business logic. Manages the state of the 24-hour schedule array, validates constraints, and executes additions/deletions.

## Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git)
   cd YOUR_REPOSITORY_NAME
Install dependencies:
Make sure you have Python 3.9+ installed.

Bash
pip install -r requirements.txt
Environment Variables:
Create a .env file in the root directory and add your API keys. Never commit this file.

קטע קוד
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
GEMINI_API_KEY=your_google_gemini_api_key_here
Run the Bot:
To run the Telegram bot:

Bash
python main_telegram.py
To run the local console version:

Bash
python main_console.py
Usage Example
User:

"I want one hour to work out, sleep from 00 to 8, and go back to sleep at 23. During the day I want to eat at 9 AM, 2 PM, and 8 PM. I am studying algorithms for 5 hours, using the bot for two hours, and working on my resume for one hour."

Bot Output:

📅 Your Daily Schedule:
⏰ 00:00 - 08:00 : To sleep
⏰ 08:00 - 09:00 : To work out
⏰ 09:00 - 10:00 : To eat
⏰ 10:00 - 12:00 : To use the bot
⏰ 12:00 - 13:00 : To work on resume
⏰ 13:00 - 14:00 : Free hour
⏰ 14:00 - 15:00 : To eat
⏰ 15:00 - 20:00 : To study algorithms
⏰ 20:00 - 21:00 : To eat
⏰ 21:00 - 23:00 : Free hour
⏰ 23:00 - 24:00 : To sleep

Contact
Created by Aviv Gartner.
