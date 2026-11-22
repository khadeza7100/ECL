import flet as ft

from components.dropdown_configuration import (
    DROPDOWN_CONFIGURATIONS,
    get_configured_dropdown_options,
)
from database import replace_dropdown_options


def get_dropdown_configuration_form(page: ft.Page):
    dropdown_keys = list(DROPDOWN_CONFIGURATIONS)
    selected_key = {"value": dropdown_keys[0]}
    status_text = ft.Text("", size=13, color="#00e676")
    items_column = ft.Column(spacing=8)

    def save_options(options, success_message):
        replace_dropdown_options(selected_key["value"], options)
        status_text.value = success_message
        status_text.color = "#00e676"
        render_options()

    def validate_option(value, existing_options, current_index=None):
        normalized_value = value.strip().casefold()
        if not normalized_value:
            status_text.value = "Dropdown item cannot be empty."
            status_text.color = "#ff5252"
            page.update()
            return None

        if selected_key["value"] == "year" and (
            len(normalized_value) != 4 or not normalized_value.isdigit()
        ):
            status_text.value = "Year must be a four-digit number."
            status_text.color = "#ff5252"
            page.update()
            return None

        for index, option in enumerate(existing_options):
            if index != current_index and option.strip().casefold() == normalized_value:
                status_text.value = "This dropdown item already exists."
                status_text.color = "#ff5252"
                page.update()
                return None
        return value.strip()

    def render_options():
        options = get_configured_dropdown_options(selected_key["value"])
        items_column.controls.clear()

        if not options:
            items_column.controls.append(
                ft.Text("No dropdown items configured.", color="white54", italic=True)
            )

        for index, option in enumerate(options):
            option_field = ft.TextField(
                value=option,
                expand=True,
                height=42,
                content_padding=ft.Padding(10, 8, 10, 8),
                border_color="#16483d",
                focused_border_color="#00e676",
                text_style=ft.TextStyle(color="white", size=13),
            )

            def make_update_handler(item_index, item_field):
                def update_option(e):
                    current_options = get_configured_dropdown_options(selected_key["value"])
                    updated_value = validate_option(
                        item_field.value or "",
                        current_options,
                        current_index=item_index,
                    )
                    if updated_value is None:
                        return
                    current_options[item_index] = updated_value
                    save_options(current_options, "Dropdown item updated.")
                return update_option

            def make_delete_handler(item_index):
                def delete_option(e):
                    current_options = get_configured_dropdown_options(selected_key["value"])
                    del current_options[item_index]
                    save_options(current_options, "Dropdown item deleted.")
                return delete_option

            items_column.controls.append(
                ft.Row([
                    option_field,
                    ft.IconButton(
                        icon=ft.Icons.SAVE,
                        icon_color="#00e676",
                        tooltip="Save item",
                        on_click=make_update_handler(index, option_field),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE,
                        icon_color="#ff5252",
                        tooltip="Delete item",
                        on_click=make_delete_handler(index),
                    ),
                ], spacing=4)
            )
        page.update()

    def select_dropdown(e):
        selected_key["value"] = e.control.value
        status_text.value = ""
        status_text.color = "#00e676"
        render_options()

    dropdown_selector = ft.Dropdown(
        label="Dropdown",
        options=[
            ft.dropdown.Option(key, DROPDOWN_CONFIGURATIONS[key][0])
            for key in dropdown_keys
        ],
        value=selected_key["value"],
        width=420,
        border_color="#00e676",
        focused_border_color="#00e676",
        label_style=ft.TextStyle(color="white70", size=14),
        text_style=ft.TextStyle(color="white", size=13),
        on_select=select_dropdown,
    )

    new_item_field = ft.TextField(
        label="New dropdown item",
        expand=True,
        height=45,
        content_padding=ft.Padding(12, 10, 12, 10),
        border_color="#00e676",
        focused_border_color="#00e676",
        label_style=ft.TextStyle(color="white70", size=14),
        text_style=ft.TextStyle(color="white", size=13),
    )

    def add_option(e):
        current_options = get_configured_dropdown_options(selected_key["value"])
        new_value = validate_option(new_item_field.value or "", current_options)
        if new_value is None:
            return
        current_options.append(new_value)
        save_options(current_options, "Dropdown item added.")
        new_item_field.value = ""
        page.update()

    add_button = ft.ElevatedButton(
        "Add Item",
        icon=ft.Icons.ADD,
        on_click=add_option,
        bgcolor="#00e676",
        color="#061d19",
    )

    render_options()
    return ft.Container(
        content=ft.Column([
            ft.Text("Dropdown Configuration", size=18, weight="bold", color="white"),
            dropdown_selector,
            ft.Row([new_item_field, add_button], spacing=10),
            status_text,
            ft.Divider(color="#16483d"),
            items_column,
        ], spacing=14),
        padding=20,
        width=620,
        bgcolor="#0a2e27",
        border=ft.Border.all(1, "#16483d"),
        border_radius=8,
    )
