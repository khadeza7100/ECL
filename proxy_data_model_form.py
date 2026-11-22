import flet as ft
from database import get_discounting_factor

def get_proxy_data_model_form(page: ft.Page):
    # Read-only Text field helper
    def create_read_only_field(default_val=""):
        return ft.TextField(
            value=default_val,
            read_only=True,
            disabled=True,
            height=36,  # Reduced field height
            width=400,
            content_padding=ft.Padding(12, 6, 12, 6),
            border_color="#00e676",
            focused_border_color="#00e676",
            border_radius=4,
            text_style=ft.TextStyle(color="#4db6ac", size=13)
        )

    # Static Input Controls
    ccod = create_read_only_field("20%, Table 12 of Basel III Guideline of BB")
    bglc = create_read_only_field("Use Average Forced Loan Creation Rate")
    historical_pd = create_read_only_field("Transition rate of loans from stage to stage")
    suggestive_pd = create_read_only_field("Multiple Linear Regression (MLR) [PD, EVs]")
    stored_discounting_factor = get_discounting_factor()
    discounting_factor_value = (
        f"{stored_discounting_factor:.4f}"
        if stored_discounting_factor is not None
        else "0.0000"
    )
    discounting_factor = create_read_only_field(discounting_factor_value)
    economic_variables = create_read_only_field("Use data from BB website")

    def build_row(label_text, input_control):
        return ft.Row(
            controls=[
                ft.Container(
                    content=ft.Text(label_text, size=14, color="white", weight="bold"),
                    width=250
                ),
                input_control
            ],
            spacing=10,  # Reduced horizontal gap between label and input box
            alignment="start",
            vertical_alignment="center"
        )

    form_card = ft.Container(
        content=ft.Column(
            controls=[
                ft.Container(
                    content=ft.Text("Proxy Data & Model", size=22, weight="bold", color="white"),
                    padding=ft.Padding(0, 0, 0, 10)
                ),
                build_row("Credit Conversion Factor CCOD", ccod),
                build_row("Credit Conversion Factor BGLC", bglc),
                build_row("Historical PD", historical_pd),
                build_row("Adjusted PD (APD)", suggestive_pd),
                build_row("Discounting Factor", discounting_factor),
                build_row("Economic Variables (EV)", economic_variables),
                ft.Container(height=10)
            ],
            spacing=6  # Reduced vertical gap between consecutive rows
        ),
        padding=25,
        border=ft.Border.all(width=1, color="#00e676"),
        border_radius=6,
        bgcolor="#061d19"
    )

    return ft.Container(
        content=form_card,
        width=750,
        alignment=ft.Alignment(0, -1),
        padding=ft.Padding(0, 0, 0, 20)
    )