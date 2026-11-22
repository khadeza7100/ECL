import mysql.connector
import flet as ft

from components.ead_calculations import (
    calculate_funded_ead,
    calculate_non_funded_ead,
    get_average_credit_conversion_rate,
    get_non_funded_credit_conversion_rate,
)
from database import get_ead_recalculation_data, save_calculated_ead


def _format_ead(value):
    if value is None:
        return "N/A"
    return f"{float(value):,.2f}"


def _build_ead_rows(rows):
    if not rows:
        return [
            ft.DataRow(cells=[
                ft.DataCell(ft.Text("No account records to display.", color="white70")),
                *[ft.DataCell(ft.Text("")) for _ in range(4)],
            ])
        ]

    return [
        ft.DataRow(cells=[
            ft.DataCell(ft.Text(row["account_type"], color="white", size=12)),
            ft.DataCell(ft.Text(row["account_number"], color="white", size=12)),
            ft.DataCell(ft.Text(row["facility_type"] or "-", color="white", size=12)),
            ft.DataCell(ft.Text(_format_ead(row["previous_ead"]), color="white70", size=12)),
            ft.DataCell(ft.Text(
                _format_ead(row["calculated_ead"]),
                color="#78eb64",
                weight="bold",
                size=12,
            )),
        ])
        for row in rows
    ]


def _build_saved_ead_rows(funded_accounts, non_funded_accounts):
    rows = []
    for account in funded_accounts:
        rows.append({
            "account_type": "Funded",
            "account_number": str(account.get("ac_num") or "").strip(),
            "facility_type": account.get("nature") or "",
            "previous_ead": account.get("ead"),
            "calculated_ead": account.get("ead"),
        })
    for account in non_funded_accounts:
        rows.append({
            "account_type": "Non-Funded",
            "account_number": str(account.get("ac_num") or "").strip(),
            "facility_type": account.get("cont_type") or "",
            "previous_ead": account.get("ead"),
            "calculated_ead": account.get("ead"),
        })
    return rows


def get_calculated_ead_form(page: ft.Page):
    load_error = None
    try:
        saved_funded_accounts, saved_non_funded_accounts, _ = (
            get_ead_recalculation_data()
        )
        rows = _build_saved_ead_rows(
            saved_funded_accounts,
            saved_non_funded_accounts,
        )
    except (
        mysql.connector.Error,
        ValueError,
        TypeError,
        KeyError,
    ) as error:
        rows = []
        load_error = error

    data_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Account Type", color="white", weight="bold")),
            ft.DataColumn(ft.Text("A/C No.", color="white", weight="bold")),
            ft.DataColumn(ft.Text("Facility Type", color="white", weight="bold")),
            ft.DataColumn(ft.Text("Current EAD", color="white", weight="bold")),
            ft.DataColumn(ft.Text("Calculated EAD", color="white", weight="bold")),
        ],
        rows=_build_ead_rows(rows),
        heading_row_color="#0c3832",
        heading_row_height=40,
        data_row_min_height=36,
        column_spacing=24,
    )
    if load_error:
        status_value = f"Could not load saved EAD values: {load_error}"
        status_color = "#ff8a80"
        summary_value = "Total EAD: unavailable"
        summary_color = "#ff8a80"
    elif rows:
        status_value = f"Loaded saved EAD values for {len(rows)} account(s)."
        status_color = "white70"
        saved_total = sum(
            float(row["calculated_ead"] or 0)
            for row in rows
        )
        summary_value = f"Total EAD: {saved_total:,.2f}"
        summary_color = "#78eb64"
    else:
        status_value = "No Funded or Non-Funded account records were found."
        status_color = "white70"
        summary_value = "Total EAD: 0.00"
        summary_color = "#78eb64"

    status_text = ft.Text(status_value, color=status_color, size=13)
    summary_text = ft.Text(
        summary_value,
        color=summary_color,
        size=13,
        weight="bold",
    )
    progress_bar = ft.ProgressBar(
        value=0,
        width=260,
        bar_height=6,
        color="#00e676",
        bgcolor="#1e534b",
        border_radius=4,
    )
    progress_percentage = ft.Text("0% completed", color="white70", size=12)
    calculate_button = ft.ElevatedButton(
        "Calculate and Save EAD",
        icon=ft.Icons.CALCULATE,
        bgcolor="#78eb64",
        color="#061d19",
    )

    def recalculate_and_save(_event):
        calculate_button.disabled = True
        progress_bar.value = 0
        progress_percentage.value = "0% completed"
        status_text.value = "Calculating EAD for all accounts..."
        status_text.color = "white70"
        summary_text.value = ""
        page.update()

        try:
            funded_accounts, non_funded_accounts, ccf_records = (
                get_ead_recalculation_data()
            )
            if not funded_accounts and not non_funded_accounts:
                rows.clear()
                data_table.rows = _build_ead_rows(rows)
                progress_bar.value = 1
                progress_percentage.value = "100% completed"
                status_text.value = "No Funded or Non-Funded accounts were found."
                status_text.color = "#ffcc80"
                return

            total_accounts = len(funded_accounts) + len(non_funded_accounts)
            completed_calculations = 0

            def update_progress(phase, completed_steps):
                progress_bar.value = min(
                    0.99,
                    0.99 * completed_steps / (2 * total_accounts),
                )
                progress_percentage.value = (
                    f"{round(progress_bar.value * 100)}% completed"
                )
                status_text.value = (
                    f"{phase} EAD: {completed_steps} of "
                    f"{2 * total_accounts} steps completed."
                )
                status_text.color = "white70"
                page.update()

            funded_ead = {}
            non_funded_ead = {}
            calculated_rows = []

            for account in funded_accounts:
                account_number = str(account.get("ac_num") or "").strip()
                facility_type = account.get("nature") or ""
                ccf_rate = get_average_credit_conversion_rate(
                    facility_type,
                    ccf_records,
                )
                _, calculated_ead = calculate_funded_ead(
                    float(account.get("loan_limit") or 0),
                    float(account.get("loan_out") or 0),
                    float(account.get("accrued_int") or 0),
                    float(account.get("calc_int") or 0),
                    facility_type,
                    ccf_rate,
                )
                funded_ead[account_number] = calculated_ead
                calculated_rows.append({
                    "account_type": "Funded",
                    "account_number": account_number,
                    "facility_type": facility_type,
                    "previous_ead": account.get("ead"),
                    "calculated_ead": calculated_ead,
                })
                completed_calculations += 1
                update_progress("Calculating", completed_calculations)

            for account in non_funded_accounts:
                account_number = str(account.get("ac_num") or "").strip()
                facility_type = account.get("cont_type") or ""
                ccf_rate = get_non_funded_credit_conversion_rate(
                    facility_type,
                    ccf_records,
                )
                calculated_ead = calculate_non_funded_ead(
                    float(account.get("amt_liability") or 0),
                    float(account.get("margin_kept") or 0),
                    ccf_rate,
                )
                non_funded_ead[account_number] = calculated_ead
                calculated_rows.append({
                    "account_type": "Non-Funded",
                    "account_number": account_number,
                    "facility_type": facility_type,
                    "previous_ead": account.get("ead"),
                    "calculated_ead": calculated_ead,
                })
                completed_calculations += 1
                update_progress("Calculating", completed_calculations)

            status_text.value = "Saving calculated EAD values..."
            page.update()

            def update_save_progress(completed_updates, _total_updates):
                update_progress(
                    "Saving",
                    total_accounts + completed_updates,
                )

            save_calculated_ead(
                funded_ead,
                non_funded_ead,
                update_save_progress,
            )
            rows[:] = calculated_rows
            data_table.rows = _build_ead_rows(rows)
            progress_bar.value = 1
            progress_percentage.value = "100% completed"
            total_ead = sum(row["calculated_ead"] for row in calculated_rows)
            status_text.value = (
                f"Calculated and saved EAD for {len(calculated_rows)} account(s)."
            )
            status_text.color = "#78eb64"
            summary_text.value = f"Total EAD: {total_ead:,.2f}"
        except (
            mysql.connector.Error,
            ValueError,
            TypeError,
            KeyError,
        ) as error:
            progress_bar.value = 0
            progress_percentage.value = "0% completed"
            status_text.value = f"EAD calculation failed: {error}"
            status_text.color = "#ff8a80"
        finally:
            calculate_button.disabled = False
            page.update()

    calculate_button.on_click = recalculate_and_save

    return ft.Container(
        content=ft.Column([
            ft.Text("Calculate EAD", size=20, weight="bold", color="#00e676"),
            ft.Text(
                "Recalculate EAD for all accounts using the formulas from the "
                "Funded A/C Profile and Non-Funded A/C Profile pages. Results "
                "are saved to the existing profile records.",
                size=13,
                color="white70",
            ),
            ft.Row(
                [
                    calculate_button,
                    ft.Container(expand=True),
                    progress_bar,
                    progress_percentage,
                ],
                spacing=12,
                vertical_alignment="center",
            ),
            status_text,
            summary_text,
            ft.Row([data_table], scroll=ft.ScrollMode.AUTO),
        ], spacing=14),
        width=1100,
        padding=20,
        bgcolor="#061d19",
        border=ft.Border.all(1, "#16483d"),
        border_radius=8,
    )
