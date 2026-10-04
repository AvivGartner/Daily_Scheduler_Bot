import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    """
    Function that returns a database connection.
    :return: PostgreSQL database connection.
    """
    connection = psycopg2.connect(database="schedule_bot",
                     user="postgres",
                     password=os.getenv("POSTGRESQL_PASSWORD"),
                     host="localhost",
                     port="5432")
    return connection

def add_slot(user_id: int, start_hour: int, end_hour: int, task_name:str) -> None:
    """
    Adds a time slot to the user's schedule.
    :param user_id: Telegram user ID.
    :param start_hour: Starting hour of the slot.
    :param end_hour: Ending hour of the slot (exclusive).
    :param task_name: Name of the task.
    :return: None
    """
    connection = get_connection()
    cursor = connection.cursor() # Creates an object used to execute SQL commands.
    cursor.execute(
        """
        INSERT INTO schedule (user_id, start_hour, end_hour, task_name)
        VALUES (%s, %s, %s, %s)
        """,
        (user_id, start_hour, end_hour, task_name)
    ) # Executes the INSERT command with the given values.
    connection.commit() # Saves the change permanently in the database.
    cursor.close() # Closes the SQL cursor.
    connection.close() # Closes the database connection.

def get_slots(user_id: int) -> list[tuple[int, int, str]]:
    """
    Returns all schedule slots belonging to a specific user.
    :param user_id: Telegram user ID.
    :return: List of tuples containing start hour, end hour, and task name.
    """
    connection = get_connection()
    cursor = connection.cursor()  # Creates an object used to execute SQL commands.
    cursor.execute(
        """
        SELECT start_hour, end_hour, task_name
        FROM schedule
        WHERE user_id = %s
        ORDER BY start_hour
        """,
        (user_id,)
    ) # Executes the SQL query with the given parameters.
    rows = cursor.fetchall() # Retrieves all rows returned by the query.
    cursor.close() # Closes the SQL cursor.
    connection.close() # Closes the database connection.
    return rows

def clear_slots(user_id: int) -> None:
    """
    Deletes all schedule slots belonging to a specific user.
    :param user_id: Telegram user ID.
    :return: None
    """
    connection = get_connection()
    cursor = connection.cursor()  # Creates an object used to execute SQL commands.
    cursor.execute(
        """
        DELETE FROM schedule
        WHERE user_id = %s
        """,
        (user_id,)
    )
    connection.commit()  # Saves the change permanently in the database.
    cursor.close()  # Closes the SQL cursor.
    connection.close()  # Closes the database connection.

def has_conflict(user_id: int, start_hour: int, end_hour: int) -> bool:
    """
    Checks whether a new schedule slot conflicts with an existing slot.
    :param user_id: Telegram user ID.
    :param start_hour: Starting hour of the new slot.
    :param end_hour: Ending hour of the new slot.
    :return: True if a conflict exists, otherwise False.
    """
    connection = get_connection()
    cursor = connection.cursor()  # Creates an object used to execute SQL commands.
    cursor.execute(
        """
        SELECT 1
        FROM schedule
        WHERE user_id = %s
            AND start_hour < %s
            AND end_hour > %s
        """,
        (user_id, end_hour, start_hour)
    )  # Executes the SQL query with the given parameters.
    row = cursor.fetchone() # Retrieves the first row returned by the query.
    cursor.close()  # Closes the SQL cursor.
    connection.close()  # Closes the database connection.
    return row is not None
