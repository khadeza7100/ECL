import flet as ft
from datetime import datetime, timedelta

class CustomDatePicker:
    def __init__(self, page: ft.Page, label: str, width: int = 260, height: int = 40, on_change_callback=None):
        self.page = page
        self.label = label
        self.on_change_callback = on_change_callback
        self.value = None

        # Core Flet DatePicker component
        self.picker = ft.DatePicker(on_change=self._handle_change)
        page.overlay.append(self.picker)

        # TextField control with floating label styling matching standard inputs
        self.input_field = ft.TextField(
            label=label,
            read_only=True,
            width=width,
            height=height,
            content_padding=ft.Padding.symmetric(horizontal=10, vertical=5),
            border_color="#00e676",
            focused_border_color="#00e676",
            text_size=12,
            color="white",
            label_style=ft.TextStyle(color="white70"),
            suffix=ft.IconButton(
                icon=ft.Icons.CALENDAR_MONTH,
                icon_color="#00e676",
                icon_size=18,
                on_click=self.open,
                tooltip=f"Select {label}"
            ),
            on_click=self.open
        )

    def open(self, e=None):
        self.picker.open = True
        self.page.update()

    def _handle_change(self, e):
        if self.picker.value:
            self.value = self.picker.value + timedelta(hours=6)
            self.input_field.value = self.value.strftime('%d/%m/%Y')
            
            if self.on_change_callback:
                self.on_change_callback(e)
                
            self.page.update()

    def set_date_from_string(self, date_str):
        """Sets the date picker value and UI field from a string date."""
        if not date_str:
            self.clear()
            return

        parsed_date = None
        date_formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(str(date_str).strip(), fmt)
                break
            except ValueError:
                continue

        if parsed_date:
            self.value = parsed_date
            self.picker.value = parsed_date
            self.input_field.value = parsed_date.strftime('%d/%m/%Y')
        else:
            self.clear()
        
        self.input_field.update()

    def clear(self):
        """Resets the picker and UI text field."""
        self.value = None
        self.picker.value = None
        self.input_field.value = ""
        self.input_field.update()