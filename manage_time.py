from datetime import datetime
import pytz


timezone_str = "Europe/Berlin"


def get_time():
    timezone = pytz.timezone(timezone_str)
    now = datetime.now(timezone)
    return now


def seconds_to_formatted_string(total_seconds):
    hours = total_seconds // 3600  # Convert seconds to hours
    minutes = (total_seconds % 3600) // 60  # Convert the remainder to minutes

    return f"{int(hours):02d}:{int(minutes):02d}"


def time_string_to_seconds(time_string):
    try:
        # Überprüfe, ob time_string None oder ein leerer String ist
        if time_string is None or time_string.strip() == "":
            raise ValueError("time_string is None or empty")

        hours, minutes = map(int, time_string.split(':'))
        total_seconds = (hours * 3600) + (minutes * 60)
    except Exception as error:
        total_seconds = 0
        print("Error while trying time_string_to_seconds", error)
    return total_seconds


def change_time_format(time_string):
    try:
        # Überprüfe, ob time_string None oder ein leerer String ist
        if time_string is None or time_string.strip() == "":
            raise ValueError("time_string is None or empty")

        # Split the time string into hours and minutes
        hours, minutes = time_string.split(':')
        # Format the string as "HHh MMm"
        new_format = f"{hours}h {minutes}m"
    except Exception as error:
        new_format = "00:00"
        print("Error while trying change_time_format", error)
    return new_format


def format_date_to_str(delta_date):
    return delta_date.strftime("%d.%m.%y")


def format_time_to_str(delta_time):
    return delta_time.strftime("%H:%M")
