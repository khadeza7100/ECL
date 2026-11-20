import flet as ft
from database import (
    save_discounting_factor,
    get_discounting_factor
)

def get_discounting_factor_form(page: ft.Page):
    # Single numeric input field
    df_input = ft.TextField(
        label="Discounting Factor",
        hint_text="e.g. 0.05",
        height=45,
        width=300,
        content_padding=ft.Padding(12, 10, 12, 10),
        border_color="#00e676",
        focused_border_color="#00e676",
        border_radius=6,
        label_style=ft.TextStyle(color="white70", size=15),
        text_style=ft.TextStyle(color="white", size=13),
        keyboard_type=ft.KeyboardType.NUMBER
    )

    # Automatically load existing record on form build
    existing_value = get_discounting_factor()
    if existing_value is not None:
        df_input.value = str(existing_value)

    def on_save_click(e):
        val = (df_input.value or "").strip()
        if not val:
            page.overlay.append(
                ft.SnackBar(
                    content=ft.Text("Please enter a valid Discounting Factor!"),
                    bgcolor="#ff9800",
                    open=True
                )
            )
            page.update()
            return

        try:
            numeric_val = float(val)
            save_discounting_factor(numeric_val)
            page.overlay.append(
                ft.SnackBar(
                    content=ft.Text("Discounting Factor updated successfully!"),
                    bgcolor="#00e676",
                    open=True
                )
            )
        except ValueError:
            page.overlay.append(
                ft.SnackBar(
                    content=ft.Text("Invalid number format!"),
                    bgcolor="red",
                    open=True
                )
            )
        except Exception as err:
            page.overlay.append(
                ft.SnackBar(
                    content=ft.Text(f"Error saving value: {str(err)}"),
                    bgcolor="red",
                    open=True
                )
            )
        page.update()

    save_btn = ft.ElevatedButton(
        content=ft.Text("Save", color="black", weight="bold", size=14),
        on_click=on_save_click,
        style=ft.ButtonStyle(
            bgcolor="#78eb64",
            shape=ft.RoundedRectangleBorder(radius=20)
        ),
        height=42,
        width=120
    )

    input_form_card = ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Text("Discounting Factor", size=20, weight="bold", color="#00e676"),
                alignment=ft.Alignment(-1, 0),
                padding=ft.Padding(0, 0, 0, 15)
            ),
            ft.Row(
                controls=[
                    ft.Text("Discounting Factor :", size=15, color="white", weight="bold"),
                    df_input
                ],
                spacing=20,
                alignment="start",
                vertical_alignment="center"
            ),
            ft.Container(height=20),
            ft.Row([save_btn], alignment="end")
        ]),
        padding=25,
        border=ft.Border.all(width=1, color="#00e676"),
        border_radius=8,
        bgcolor="#061d19"
    )

    return ft.Container(
        content=input_form_card,
        width=820,
        alignment=ft.Alignment(0, -1),
        padding=ft.Padding(0, 0, 0, 20)
    )