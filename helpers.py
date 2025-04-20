import datetime

from constants import DATE_FORMAT, DATETIME_FORMAT

# --- Helper Function for Display Formatting ---


def format_due_date_display(iso_date_str: str):
    """
    Formats an ISO datetime string for display.
    Shows time only if it's not midnight.
    Returns formatted string or 'None'.
    """
    if not iso_date_str:
        return 'None'
    try:
        dt_obj = datetime.datetime.fromisoformat(iso_date_str)
        if dt_obj.time() == datetime.time(0, 0):
            # If only date was given (stored as midnight), display only date
            return dt_obj.strftime(DATE_FORMAT)
        else:
            # Otherwise, display date and time
            return dt_obj.strftime(DATETIME_FORMAT)
    except (ValueError, TypeError):
        # Fallback if stored string is not valid ISO (e.g., old data)
        return str(iso_date_str)  # Display as is

# --- Helper Function for Sorting/Filtering Key ---


def get_datetime_from_iso(iso_date_str: str):
    """
    Parses an ISO datetime string for comparison.
    Returns a datetime object, or datetime.max if None/invalid.
    """
    if not iso_date_str:
        return datetime.datetime.max  # Sort tasks without dates last
    try:
        return datetime.datetime.fromisoformat(iso_date_str)
    except (ValueError, TypeError):
        # Try parsing as just a date if ISO fails (backward compatibility?)
        try:
            # Treat date-only strings as midnight for comparison
            return datetime.datetime.strptime(iso_date_str, DATE_FORMAT)
        except (ValueError, TypeError):
            return datetime.datetime.max  # Treat invalid strings as last


# --- Helper Function for Robust Datetime Parsing ---


def parse_datetime_flexible(date_str: str):
    """
    Tries to parse a string into a datetime object using multiple formats.
    Returns a datetime object or None if parsing fails.
    """
    if not date_str:
        return None
    try:
        # Try datetime format first
        return datetime.datetime.strptime(date_str, DATETIME_FORMAT)
    except ValueError:
        try:
            # Try date format next, assume midnight
            dt_obj = datetime.datetime.strptime(date_str, DATE_FORMAT)
            # Return it as datetime (even though time is 00:00)
            # This standardizes the type we store/compare
            return dt_obj
        except ValueError:
            return None  # Could not parse in known formats
