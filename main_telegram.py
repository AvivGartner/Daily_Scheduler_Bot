import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler
from llm_parser import parse_user_request
from scheduler_logic import create_empty_schedule, add_fixed_event, add_unfixed_event, get_schedule

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") # Token for the bot in Telegram.

# Dictionary mapping Telegram User ID (int) -> user-specific schedule list (list)
user_schedules = {}

async def handle_telegram_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    This function is triggered when the user sends a free-text message to the bot.
    It is responsible for receiving the user's request, sending it to be parsed by the language model (LLM),
    and executing the required actions on the schedule (adding fixed/unfixed tasks, clearing, or viewing).

    :param update: A Telegram object containing all the information about the incoming message (text, sender ID, etc.).
    :param context: A Telegram "context" object, providing additional background tools from the library.
    :return: None. The function sends the responses (msg) directly to the user in Telegram.
    """
    # Defensive guard to ensure message and text exist (prevents AttributeErrors)
    if not update.message or not update.message.text:
        return

    # Identify the user and retrieve/initialize their specific schedule
    user_id = update.effective_user.id
    if user_id not in user_schedules:
        user_schedules[user_id] = create_empty_schedule()
    user_schedule = user_schedules[user_id]

    user_text = update.message.text
    await update.message.reply_text("חושב על זה...\n")
    ai_response = await parse_user_request(user_text) # Text processing by AI (Gemini) asynchronously.
    if ai_response is None: # Return an error message if there was an internet failure.
        await update.message.reply_text("שגיאת תקשורת, נסה שנית\n")
        return
    actions_list = ai_response.get("actions", [])
    for action in actions_list: # A loop runs through all the commands in a variable, executing each of them by calling the relevant function.
        if action.get("action_type") == "add_fixed":
            is_success, msg = add_fixed_event(user_schedule, action.get("start_hour"), action.get("end_hour"), action.get("task_name"))
            if msg != "":
                await update.message.reply_text(msg)
        elif action.get("action_type") == "add_unfixed":
            is_success, msg = add_unfixed_event(user_schedule, action.get("hours_count"), action.get("task_name"))
            if msg != "":
                await update.message.reply_text(msg)
        elif action.get("action_type") == "view_schedule":
            msg = get_schedule(user_schedule)
            await update.message.reply_text(msg)
        elif action.get("action_type") == "clear_all":
            user_schedules[user_id] = create_empty_schedule()
            await update.message.reply_text("הלוח נמחק בהצלחה")
        else:
            continue

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    This function is triggered only when the user initiates a new chat and presses the Start button,
    or explicitly types the /start command.
    Its purpose is to welcome the user and present the instructions for using the system.

    :param update: A Telegram object containing information about the user's start action.
    :param context: A Telegram "context" object (a mandatory requirement by the Telegram library for handler functions).
    :return: None. The function sends the welcome message directly to the user.
    """
    welcome_text = ("ברוך הבא למנהל הלוז היומי שלך!.\n"
                    "הכנס משימה או משימות, וציין עבור כל משימה שעת התחלה ושעת סיום,"
                    " או לחלופין כמה שעות עבור משימה או משימות."
                    " ניתן גם לבקש לראות את הלוז היומי ולאפס אותו.")
    await update.message.reply_text(welcome_text)

def main():
    """
    The main entry point of the bot.
    Initializes the application, attaches the handlers, and starts the polling loop.
    """
    print("Initializing...")
    print("Connecting to Telegram...")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_telegram_message))
    print("Bot is up and running! Waiting for messages...")
    print("press Ctrl+C to stop.")
    app.run_polling()
if __name__ == "__main__":
    main()