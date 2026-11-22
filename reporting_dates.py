import calendar
from datetime import date, datetime, timedelta


def parse_reporting_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if value is None:
        return None

    text = str(value).strip()
    for date_format in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, date_format).date()
        except ValueError:
            continue
    return None


def is_valid_reporting_date(value, as_of=None):
    selected_date = parse_reporting_date(value)
    if selected_date is None:
        return False

    current_date = as_of or date.today()
    return (
        selected_date <= current_date
        and selected_date.day
        == calendar.monthrange(selected_date.year, selected_date.month)[1]
    )


def get_previous_month_end(as_of=None):
    current_date = as_of or date.today()
    first_day_of_month = current_date.replace(day=1)
    return first_day_of_month - timedelta(days=1)


def get_effective_reporting_date(value, as_of=None):
    selected_date = parse_reporting_date(value)
    if is_valid_reporting_date(selected_date, as_of):
        return selected_date
    return get_previous_month_end(as_of)
