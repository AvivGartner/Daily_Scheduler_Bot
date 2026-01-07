from typing import Optional

def create_empty_schedule() -> list[Optional[str]]:
    """
    Creates an empty daily schedule initialized with free slots.
    The schedule is represented as a list of 24 items, where each index
    corresponds to an hour of the day (0-23). 'None' indicates a free slot.
    :return:
    List[Optional[str]]: A list of size 24 containing None values.
    """
    daily_schedule = [None] * 24
    return daily_schedule

def add_fixed_event(daily_schedule: list[Optional[str]], start_hour: int, end_hour: int, task_name: str) -> bool:
    """
    Assigns a task to a specific range of in the schedule, if available.
    This is used to add non-negotiable fixed constraints (e.g., classes, sleep).
    :param daily_schedule: The daily schedule list to modify (24 slots).
    :param start_hour: Event start time. (0-23).
    :param end_hour: Event end time. (0-23).
    :param task_name: The name of the task to schedule.
    :return: True if the schedule was successfully scheduled, False otherwise.
    """
    if start_hour > end_hour: # Checking whether the start time is before the end time
        print("Start hour must be smaller than end hour.")
        return False
    if start_hour < 0 or start_hour > 23: # Check whether the start hour is correct.
        print("Start hour must be between 0 and 23.")
        return False
    if end_hour < 1 or end_hour > 24: # Check whether the end hour is correct.
        print("End hour must be between 1 and 24.")
        return False
    for hour in range(start_hour, end_hour):
        if daily_schedule[hour] is not None: # Check whether the input hours is already full.
            print("You have already scheduled that hour.")
            return False
    for hour in range(start_hour, end_hour):
        daily_schedule[hour] = task_name # Insert the task at the hours time.
    print("The schedule has been successfully scheduled.")
    return True

def add_unfixed_event(daily_schedule: list[Optional[str]], hours_count: int, task_name: str) -> bool:
    """
    Adds a task with a number of hours but no specific hours to the schedule, if available.
    :param daily_schedule: The daily schedule list to modify (24 slots).
    :param hours_count: The number of hours required for the task
    :param task_name: The name of the task to schedule.
    :return: True if the schedule was successfully scheduled, False otherwise.
    """
    if hours_count < 1 or hours_count > 24: # Checking whether the number of hours of the task is possible for a day.
        print("Invalid hour count.")
        return False
    if daily_schedule.count(None) < hours_count: # Checking whether there are enough free hours in the day.
        print("You have not enough free hours to schedule.")
        return False
    sum_continuous_hour = 0  # Used to check the number of consecutive hours available, in order to find a suitable sequence for the task and enter it.
    for i, hour in enumerate(daily_schedule): # This loop is used to check whether there are enough consecutive hours available, and if so, inserts the task in the sequence.
        if hour is None:
            sum_continuous_hour += 1
            if sum_continuous_hour == hours_count:
                return add_fixed_event(daily_schedule, i - hours_count + 1, i + 1, task_name)
        else:
            sum_continuous_hour = 0
    remaining_hours = hours_count  # Used to accurately enter the task into the exact amount of hours required
    for i, hour in enumerate(daily_schedule): # This loop is used if there is not enough consecutive time, and inserts the task in the earliest available hours.
        if hour is None:
            daily_schedule[i] = task_name
            remaining_hours -= 1
            if remaining_hours == 0:
                return True
    return False

def get_schedule(daily_schedule: list[Optional[str]]) -> str:
    """
    Returns the daily calendar as an ordered string in Hebrew.
    :param daily_schedule: The daily schedule list.
    :return: Ordered string.
    """
    output = "\nהלוח היומי שלך:"
    for hour, task_name in enumerate(daily_schedule):
        time_label = f"{hour}:00"
        content = task_name if task_name is not None else "שעה פנויה"
        output += f"\n{time_label} - {content}\n"
    return output