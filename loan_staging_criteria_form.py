import flet as ft
from database import (
    save_loan_staging_criteria,
    get_loan_staging_criteria
)

def get_loan_staging_criteria_form(page: ft.Page):
    # Text field helper
    def create_field(label_text, default_val=""):
        return ft.TextField(
            value=default_val,
            height=40,
            width=350,
            content_padding=ft.Padding(12, 8, 12, 8),
            border_color="#00e676",
            focused_border_color="#00e676",
            border_radius=4,
            text_style=ft.TextStyle(color="white", size=13)
        )

    # Input Controls
    dpd_stage1 = create_field("DPD for Stage-1", "<=30")
    dpd_stage2 = create_field("DPD for Stage-2", ">30 AND <=90")
    dpd_stage3 = create_field("DPD for Stage-3", ">90")
    qj_stage2 = create_field("QJ for Stage-2", "SICR")
    qj_stage3 = create_field("QJ for Stage-3", "Impairment")

    # Populate from Database if record exists
    data = get_loan_staging_criteria()
    if data:
        dpd_stage1.value = data.get("dpd_stage1", "<=30")
        dpd_stage2.value = data.get("dpd_stage2", ">30 AND <=90")
        dpd_stage3.value = data.get("dpd_stage3", ">90")
        qj_stage2.value = data.get("qj_stage2", "SICR")
        qj_stage3.value = data.get("qj_stage3", "Impairment")

    def on_save_click(e):
        payload = {
            "dpd_stage1": (dpd_stage1.value or "").strip(),
            "dpd_stage2": (dpd_stage2.value or "").strip(),
            "dpd_stage3": (dpd_stage3.value or "").strip(),
            "qj_stage2": (qj_stage2.value or "").strip(),
            "qj_stage3": (qj_stage3.value or "").strip(),
        }
        try:
            save_loan_staging_criteria(payload)
            page.overlay.append(
                ft.SnackBar(
                    content=ft.Text("Loan Staging Criteria saved successfully!"),
                    bgcolor="#00e676",
                    open=True
                )
            )
        except Exception as err:
            page.overlay.append(
                ft.SnackBar(
                    content=ft.Text(f"Error saving criteria: {str(err)}"),
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
            shape=ft.RoundedRectangleBorder(radius=4)
        ),
        height=38,
        width=100
    )

    def build_row(label_text, input_control):
        return ft.Row(
            controls=[
                ft.Container(
                    content=ft.Text(label_text, size=15, color="white", weight="bold"),
                    width=200
                ),
                input_control
            ],
            spacing=20,
            alignment="start",
            vertical_alignment="center"
        )

    form_card = ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Text("Loan Staging Criteria", size=22, weight="bold", color="white"),
                padding=ft.Padding(0, 0, 0, 15)
            ),
            build_row("DPD for Stage-1", dpd_stage1),
            ft.Container(height=8),
            build_row("DPD for Stage-2", dpd_stage2),
            ft.Container(height=8),
            build_row("DPD for Stage-3", dpd_stage3),
            ft.Container(height=8),
            build_row("QJ for Stage-2", qj_stage2),
            ft.Container(height=8),
            build_row("QJ for Stage-3", qj_stage3),
            ft.Container(height=20),
            ft.Row([save_btn], alignment="end")
        ]),
        padding=30,
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