import os
import db
from typing import Optional
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler

from db import get_slots
from llm_parser import parse_user_request
from scheduler_logic import create_empty_schedule, add_fixed_event, add_unfixed_event, get_schedule

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") # Token for the bot in Telegram.



def build_schedule_from_db(user_id: int) -> list[Optional[str]]:
    """
       Reconstructs a user's daily schedule from the schedule stored in the database.
       :param user_id: Telegram user ID.
       :return: A 24-slot schedule list reconstructed from the database.
       """
    schedule = create_empty_schedule() # Creates an empty 24-slot schedule.
    slots = db.get_slots(user_id) # Retrieves the user's schedule slots from the database.
    for start_hour, end_hour, task_name in slots:
        for hour in range(start_hour, end_hour):
            schedule[hour] = task_name # Fills each hour in the slot with the task name.
    return schedule

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

    # Identify the user and reconstruct their schedule from the database
    user_id = update.effective_user.id
    user_schedule = build_schedule_from_db(user_id)


    user_text = update.message.text
    await update.message.reply_text("חושב על זה...\n")
    ai_response = await parse_user_request(user_text) # Text processing by AI (Gemini) asynchronously.
    if ai_response is None: # Return an error message if there was an internet failure.
        await update.message.reply_text("שגיאת תקשורת, נסה שנית\n")
        return
    actions_list = ai_response.get("actions", [])
    
    # Prioritize action execution order: clear_all -> add_fixed -> add_unfixed -> view_schedule
    action_priority = {"clear_all": 0, "add_fixed": 1, "add_unfixed": 2, "view_schedule": 3}
    sorted_actions = sorted(actions_list, key=lambda a: action_priority.get(a.get("action_type"), 4))

    for action in sorted_actions: # A loop runs through all the commands in a variable, executing each of them by calling the relevant function.
        if action.get("action_type") == "add_fixed":
            start_hour = action.get("start_hour")
            end_hour   = action.get("end_hour")
            task_name  = action.get("task_name")
            is_success, msg = add_fixed_event(user_schedule, start_hour, end_hour, task_name)
            if msg != "":
                await update.message.reply_text(msg)
            if is_success:
                db.add_slot(user_id, start_hour, end_hour, task_name) # Persist the new slot to the database.
        elif action.get("action_type") == "add_unfixed":
            task_name     = action.get("task_name")
            hours_count   = action.get("hours_count")
            schedule_before = user_schedule[:] # Save a copy of the schedule before the call to detect newly assigned hours.
            is_success, msg = add_unfixed_event(user_schedule, hours_count, task_name)
            if msg != "":
                await update.message.reply_text(msg)
            if is_success:
                # Find which hours were newly assigned to task_name by comparing before and after.
                # A slot is "new" only if it was None before the call and is task_name after;
                # this avoids mistaking pre-existing same-named slots for newly scheduled ones.
                new_hours = [
                    i for i in range(24)
                    if schedule_before[i] is None and user_schedule[i] == task_name
                ]
                # Convert the list of individual hours into contiguous [start_hour, end_hour) spans.
                if new_hours:
                    span_start = new_hours[0]
                    prev_hour  = new_hours[0]
                    for h in new_hours[1:]:
                        if h == prev_hour + 1:
                            prev_hour = h # Extend the current span.
                        else:
                            db.add_slot(user_id, span_start, prev_hour + 1, task_name) # Gap found: persist completed span.
                            span_start = h
                            prev_hour  = h
                    db.add_slot(user_id, span_start, prev_hour + 1, task_name) # Persist the final span.
        elif action.get("action_type") == "view_schedule":
            msg = get_schedule(user_schedule)
            await update.message.reply_text(msg)
        elif action.get("action_type") == "clear_all":
            db.clear_slots(user_id) # Erase all of this user's slots from the database.
            user_schedule = create_empty_schedule() # Also reset the local list so subsequent actions in the same message start from a clean state.
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