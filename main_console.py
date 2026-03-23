import llm_parser
import scheduler_logic
from llm_parser import parse_user_request
from scheduler_logic import create_empty_schedule, add_fixed_event, add_unfixed_event, get_schedule


def main():
    schedule = create_empty_schedule()
    while True:
        user_text = input("הכנס משימה או משימות. ציין עבור משימה שעת התחלה ושעת סיום, או לחלופין כמות שעות עבור המשימה. ניתן לבקש גם לראות את הלוח שלך.\n")
        ai_response = parse_user_request(user_text)
        if ai_response is None:
            print("Network error, Try again.")
            continue
        actions_list = ai_response.get("actions", [])
        for action in actions_list:
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
    main()