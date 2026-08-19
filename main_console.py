import asyncio
import llm_parser
import scheduler_logic
from llm_parser import parse_user_request
from scheduler_logic import create_empty_schedule, add_fixed_event, add_unfixed_event, get_schedule


async def main():
    """
    The main function ran on the console only (and not on the bot itself).
    Receives commands from the user regarding the schedule and calls the relevant functions.
    :return: whether the commands were executed, if not then what the errors were, and the full schedule if there was such a command from the user.
    """
    schedule = create_empty_schedule()
    while True: # The loop runs as long as there is input from the user.
        user_text = input("הכנס משימה או משימות. ציין עבור משימה שעת התחלה ושעת סיום, או לחלופין כמות שעות עבור המשימה. ניתן לבקש גם לראות את הלוח שלך.\n")
        ai_response = await parse_user_request(user_text) # Text processing by AI (Gemini).
        if ai_response is None: # Return an error message if there was an internet failure.
            print("Network error, Try again.")
            continue
        actions_list = ai_response.get("actions", []) # Creating a variable containing a list of commands from the user that were processed in AI into a list of actions
        
        # Prioritize action execution order: clear_all -> add_fixed -> add_unfixed -> view_schedule
        action_priority = {"clear_all": 0, "add_fixed": 1, "add_unfixed": 2, "view_schedule": 3}
        sorted_actions = sorted(actions_list, key=lambda a: action_priority.get(a.get("action_type"), 4))
        
        for action in sorted_actions: # A loop runs through all the commands in a variable, executing each of them by calling the relevant function.
            if action.get("action_type") == "add_fixed":
                is_success, msg = add_fixed_event(schedule, action.get("start_hour"), action.get("end_hour"), action.get("task_name"))
                print(msg)
            elif action.get("action_type") == "add_unfixed":
                is_success, msg = add_unfixed_event(schedule, action.get("hours_count"), action.get("task_name"))
                if msg != "":
                    print(msg)
            elif action.get("action_type") == "view_schedule":
                msg = get_schedule(schedule)
                print(msg)
            elif action.get("action_type") == "clear_all":
                schedule = create_empty_schedule()
            else:
                continue
if __name__ == "__main__":
    asyncio.run(main())