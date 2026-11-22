from datetime import date, datetime, timedelta

import flet as ft

from components.reporting_dates import (
    get_effective_reporting_date,
    is_valid_reporting_date,
    parse_reporting_date,
)
from database import get_reporting_date, save_reporting_date


def get_reporting_date_form(page: ft.Page):
    today = date.today()
    stored_date = get_reporting_date()
    current_date = get_effective_reporting_date(stored_date, today)

    status_text = ft.Text("", size=13, color="#00e676")
    if stored_date and not is_valid_reporting_date(stored_date, today):
        status_text.value = (
            "The saved Reporting Date is invalid. Select a month-end date on or before today."
        )
        status_text.color = "#ff5252"

    date_field = ft.TextField(
        label="Reporting Date",
        value=current_date.strftime("%d/%m/%Y"),
        read_only=True,
        width=260,
        height=45,
        content_padding=ft.Padding(12, 10, 12, 10),
        border_color="#00e676",
        focused_border_color="#00e676",
        label_style=ft.TextStyle(color="white70", size=14),
        text_style=ft.TextStyle(color="white", size=13),
    )

    def on_date_change(e):
        nonlocal current_date
        selected_value = e.control.value
        if isinstance(selected_value, datetime):
            selected_value += timedelta(hours=6)
        selected = parse_reporting_date(selected_value)

        if not is_valid_reporting_date(selected, today):
            status_text.value = (
                "Reporting Date must be a month-end date on or before today."
            )
            status_text.color = "#ff5252"
            date_field.value = current_date.strftime("%d/%m/%Y")
        else:
            current_date = selected
            date_field.value = selected.strftime("%d/%m/%Y")
            save_reporting_date(selected.isoformat())
            status_text.value = "Reporting Date saved successfully."
            status_text.color = "#00e676"
        page.update()

    date_picker = ft.DatePicker(
        value=current_date,
        current_date=current_date,
        first_date=date.min,
        last_date=today,
        on_change=on_date_change,
    )
    page.overlay.append(date_picker)

    def open_calendar(e):
        date_picker.open = True
        page.update()

    date_field.suffix = ft.IconButton(
        icon=ft.Icons.CALENDAR_MONTH,
        icon_color="#00e676",
        on_click=open_calendar,
        tooltip="Select Reporting Date",
    )
    date_field.on_click = open_calendar

    return ft.Container(
        content=ft.Column([
            ft.Text("Reporting Date", size=18, weight="bold", color="white"),
            ft.Container(height=10),
            date_field,
            ft.Container(height=8),
            status_text,
        ], spacing=8),
        padding=20,
        width=420,
        bgcolor="#0a2e27",
        border=ft.Border.all(1, "#16483d"),
        border_radius=8,
    )
