import flet as ft

from components.lgd_calculations import build_lgd_calculations
from database import get_lgd_calculation_data, save_lgd_calculations


def get_lgd_calculation_form(page: ft.Page):
    calculation_error = ""
    try:
        funded_accounts, non_funded_accounts = get_lgd_calculation_data()
    except Exception as error:
        calculation_error = f"Unable to load account data: {error}"
        calculation = None
    else:
        calculation = None
        try:
            calculation = build_lgd_calculations(
                funded_accounts,
                non_funded_accounts,
            )
        except ValueError as error:
            calculation_error = str(error)

    if calculation is None:
        calculation = {
            "rows": [],
            "funded_lgd": {},
            "non_funded_lgd": {},
            "skipped_zero_ead": 0,
        }

    def build_table_rows(current_calculation, error_message=""):
        table_rows = []
        for account in current_calculation["rows"]:
            lgd = account["lgd"]
            table_rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(account["customer_number"] or "-", color="white", size=11)),
                ft.DataCell(ft.Text(account["customer_name"] or "-", color="white", size=11)),
                ft.DataCell(ft.Text(account["account_type"], color="white", size=11)),
                ft.DataCell(ft.Text(account["account_number"] or "-", color="white", size=11)),
                ft.DataCell(ft.Text(f"{account['ead']:,.4f}", color="white", size=11)),
                ft.DataCell(ft.Text(f"{account['pv_collateral']:,.4f}", color="white", size=11)),
                ft.DataCell(ft.Text(
                    f"{lgd * 100:.2f}%" if lgd is not None else "N/A",
                    color="#78eb64" if lgd is not None else "#ffcc80",
                    weight="bold",
                    size=11,
                )),
                ft.DataCell(ft.Text(
                    account["status"],
                    color="#78eb64" if lgd is not None else "#ffcc80",
                    size=11,
                )),
            ]))

        if not table_rows:
            table_rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(
                    f"Unable to calculate LGD: {error_message}"
                    if error_message else "No funded or non-funded accounts found.",
                    color="white70",
                    italic=True,
                    size=12,
                )),
                *[ft.DataCell(ft.Text("", size=11)) for _ in range(7)],
            ]))
        return table_rows

    funded_lgd = calculation["funded_lgd"]
    non_funded_lgd = calculation["non_funded_lgd"]
    save_button = ft.ElevatedButton(
        content=ft.Text("Calculate and Save LGD", color="#061d19", weight="bold", size=12),
        style=ft.ButtonStyle(
            bgcolor="#78eb64",
            shape=ft.RoundedRectangleBorder(radius=20),
        ),
        height=38,
        width=190,
    )
    status_text = ft.Text(
        f"Calculation error: {calculation_error}" if calculation_error else "",
        color="#ff8a80" if calculation_error else "white70",
        size=12,
    )
    progress_bar = ft.ProgressBar(
        value=0,
        width=160,
        bar_height=5,
        color="#00e676",
        bgcolor="#1e534b",
        border_radius=4,
    )
    progress_percentage = ft.Text("0% completed", color="white70", size=11)
    zero_ead_warning = ft.Text(
        f"{calculation['skipped_zero_ead']} account(s) have zero EAD and were skipped."
        if calculation["skipped_zero_ead"] else "",
        color="#ffcc80",
        size=12,
        visible=bool(calculation["skipped_zero_ead"]),
    )
    lgd_table = ft.DataTable(
        width=1120,
        columns=[
            ft.DataColumn(ft.Text("Customer No.", color="white", weight="bold", size=11)),
            ft.DataColumn(ft.Text("Customer Name", color="white", weight="bold", size=11)),
            ft.DataColumn(ft.Text("Account Type", color="white", weight="bold", size=11)),
            ft.DataColumn(ft.Text("A/C No.", color="white", weight="bold", size=11)),
            ft.DataColumn(ft.Text("EAD", color="white", weight="bold", size=11)),
            ft.DataColumn(ft.Text("PV of Collateral", color="white", weight="bold", size=11)),
            ft.DataColumn(ft.Text("LGD %", color="white", weight="bold", size=11)),
            ft.DataColumn(ft.Text("Status", color="white", weight="bold", size=11)),
        ],
        rows=build_table_rows(calculation, calculation_error),
        border=ft.Border.all(0.5, "#1e534b"),
        heading_row_color="#0c3832",
        heading_row_height=40,
        data_row_min_height=36,
        column_spacing=12,
    )

    def save_calculated_lgd(_e):
        del _e
        save_button.disabled = True
        progress_bar.value = 0
        progress_percentage.value = "0% completed"
        status_text.value = "Recalculating LGD values..."
        status_text.color = "white70"
        page.update()

        try:
            funded_accounts, non_funded_accounts = get_lgd_calculation_data()
            refreshed_calculation = build_lgd_calculations(
                funded_accounts,
                non_funded_accounts,
            )
        except Exception as error:
            status_text.value = f"LGD was not saved; recalculation failed: {error}"
            status_text.color = "#ff8a80"
            save_button.disabled = False
            page.update()
            return

        funded_lgd.clear()
        funded_lgd.update(refreshed_calculation["funded_lgd"])
        non_funded_lgd.clear()
        non_funded_lgd.update(refreshed_calculation["non_funded_lgd"])
        lgd_table.rows = build_table_rows(refreshed_calculation)
        zero_ead_warning.value = (
            f"{refreshed_calculation['skipped_zero_ead']} account(s) have zero EAD and were skipped."
            if refreshed_calculation["skipped_zero_ead"] else ""
        )
        zero_ead_warning.visible = bool(refreshed_calculation["skipped_zero_ead"])

        if not (funded_lgd or non_funded_lgd):
            status_text.value = "No accounts with positive EAD were found. Nothing was saved."
            status_text.color = "#ffcc80"
            save_button.disabled = False
            page.update()
            return

        status_text.value = "Saving recalculated LGD values..."
        page.update()

        def update_progress(completed_updates, total_updates):
            progress_bar.value = (
                completed_updates / (total_updates + 1)
                if total_updates else 0
            )
            progress_percentage.value = (
                f"{round(progress_bar.value * 100)}% completed"
            )
            page.update()

        try:
            save_lgd_calculations(
                funded_lgd,
                non_funded_lgd,
                update_progress,
            )
        except Exception as error:
            progress_bar.value = 0
            progress_percentage.value = "0% completed"
            status_text.value = f"LGD values were not saved: {error}"
            status_text.color = "#ff8a80"
            save_button.disabled = False
        else:
            progress_bar.value = 1
            progress_percentage.value = "100% completed"
            status_text.value = (
                f"Recalculated LGD saved for {len(funded_lgd)} funded and "
                f"{len(non_funded_lgd)} non-funded account(s)."
            )
            status_text.color = "#78eb64"
        save_button.disabled = False
        page.update()

    save_button.on_click = save_calculated_lgd

    note = (
        "LGD = (EAD - PV of Collateral) / EAD. LGD is displayed as a percentage; "
        "negative results are set to 0%. Accounts with zero EAD are skipped and "
        "their existing LGD values are left unchanged."
    )
    return ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Text("Calculate Loss Given Default (LGD)", size=20, weight="bold", color="#00e676"),
                alignment=ft.Alignment(0, 0),
                padding=ft.Padding(0, 0, 0, 10),
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text(note, color="white70", size=12),
                    zero_ead_warning,
                    ft.Row(
                        controls=[
                            progress_bar,
                            progress_percentage,
                            ft.Container(expand=True),
                            save_button,
                        ],
                        spacing=10,
                        vertical_alignment="center",
                    ),
                    status_text,
                    ft.Row([
                        lgd_table
                    ], scroll=ft.ScrollMode.AUTO),
                ], spacing=10),
                padding=15,
                border=ft.Border.all(width=1, color="#00e676"),
                border_radius=8,
                bgcolor="#061d19",
            ),
        ], scroll=ft.ScrollMode.AUTO, expand=True),
        expand=True,
    )
