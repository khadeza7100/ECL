from datetime import date
from decimal import Decimal

import flet as ft
import mysql.connector

from components.ecl_calculations import build_ecl_calculations
from database import get_ecl_calculation_data, save_ecl_calculations


def _build_ecl_rows(calculation, error_message=""):
    rows = []
    for account in calculation["rows"]:
        apd = account["apd"]
        lgd = account["lgd"]
        ecl = account["ecl"]
        rows.append(ft.DataRow(cells=[
            ft.DataCell(ft.Text(account["customer_number"] or "-", color="white", size=11)),
            ft.DataCell(ft.Text(account["customer_name"] or "-", color="white", size=11)),
            ft.DataCell(ft.Text(account["account_type"], color="white", size=11)),
            ft.DataCell(ft.Text(account["account_number"] or "-", color="white", size=11)),
            ft.DataCell(ft.Text(account["facility_type"] or "-", color="white", size=11)),
            ft.DataCell(ft.Text(account["stage"], color="white", size=11)),
            ft.DataCell(ft.Text(
                f"{account['ead']:,.2f}" if account["ead"] is not None else "N/A",
                color="white",
                size=11,
            )),
            ft.DataCell(ft.Text(
                f"{apd * 100:.2f}%" if apd is not None else "N/A",
                color="white" if apd is not None else "#ffcc80",
                size=11,
            )),
            ft.DataCell(ft.Text(
                f"{lgd * 100:.2f}%" if lgd is not None else "N/A",
                color="white" if lgd is not None else "#ffcc80",
                size=11,
            )),
            ft.DataCell(ft.Text(
                f"{ecl:,.2f}" if ecl is not None else "N/A",
                color="#78eb64" if ecl is not None else "#ffcc80",
                weight="bold",
                size=11,
            )),
            ft.DataCell(ft.Text(
                account["status"],
                color="#78eb64" if ecl is not None else "#ffcc80",
                size=11,
            )),
        ]))

    if not rows:
        rows.append(ft.DataRow(cells=[
            ft.DataCell(ft.Text(
                error_message or "No funded or non-funded accounts found.",
                color="white70",
                italic=True,
                size=12,
            )),
            *[ft.DataCell(ft.Text("", size=11)) for _ in range(10)],
        ]))
    return rows


def _apply_saved_ecl_values(calculation, funded_accounts, non_funded_accounts):
    saved_values = {}
    for account_type, accounts in (
        ("Funded", funded_accounts),
        ("Non-Funded", non_funded_accounts),
    ):
        for account in accounts:
            account_number = str(account.get("ac_num") or "").strip()
            raw_ecl = account.get("ecl_amount")
            saved_values[(account_type, account_number)] = (
                Decimal(str(raw_ecl)) if raw_ecl is not None else None
            )

    total_ecl = Decimal("0")
    saved_count = 0
    for row in calculation["rows"]:
        saved_ecl = saved_values.get(
            (row["account_type"], row["account_number"])
        )
        row["ecl"] = saved_ecl
        if saved_ecl is None:
            row["status"] = "No saved ECL value; recalculate to update."
        else:
            total_ecl += saved_ecl
            saved_count += 1
            row["status"] = "Loaded saved ECL value."

    calculation["total_ecl"] = total_ecl.quantize(Decimal("0.01"))
    calculation["calculated_count"] = saved_count
    return saved_count


def get_ecl_calculation_form(page: ft.Page):
    current_year = str(date.today().year)
    empty_calculation = {
        "rows": [],
        "total_ecl": 0,
        "total_funded_outstanding": 0,
        "total_non_funded_outstanding": 0,
        "total_outstanding": 0,
        "calculated_count": 0,
        "matched_years": [],
        "has_current_predictors": False,
    }
    initial_load_error = None
    initial_calculation = empty_calculation
    saved_ecl_count = 0
    try:
        (
            initial_funded_accounts,
            initial_non_funded_accounts,
            initial_economic_data,
            initial_migration_data,
        ) = get_ecl_calculation_data()
        initial_calculation = build_ecl_calculations(
            initial_funded_accounts,
            initial_non_funded_accounts,
            initial_economic_data,
            initial_migration_data,
            current_year,
        )
        saved_ecl_count = _apply_saved_ecl_values(
            initial_calculation,
            initial_funded_accounts,
            initial_non_funded_accounts,
        )
    except (
        mysql.connector.Error,
        ValueError,
        TypeError,
        KeyError,
    ) as error:
        initial_load_error = error

    data_table = ft.DataTable(
        width=1420,
        columns=[
            ft.DataColumn(ft.Text("Customer No.", color="white", weight="bold", size=11)),
            ft.DataColumn(ft.Text("Customer Name", color="white", weight="bold", size=11)),
            ft.DataColumn(ft.Text("Account Type", color="white", weight="bold", size=11)),
            ft.DataColumn(ft.Text("A/C No.", color="white", weight="bold", size=11)),
            ft.DataColumn(ft.Text("Facility Type", color="white", weight="bold", size=11)),
            ft.DataColumn(ft.Text("Stage", color="white", weight="bold", size=11)),
            ft.DataColumn(ft.Text("EAD", color="white", weight="bold", size=11)),
            ft.DataColumn(ft.Text("APD %", color="white", weight="bold", size=11)),
            ft.DataColumn(ft.Text("LGD %", color="white", weight="bold", size=11)),
            ft.DataColumn(ft.Text("ECL", color="white", weight="bold", size=11)),
            ft.DataColumn(ft.Text("Status", color="white", weight="bold", size=11)),
        ],
        rows=_build_ecl_rows(
            initial_calculation,
            (
                f"Could not load saved ECL data: {initial_load_error}"
                if initial_load_error
                else (
                    "Select Recalculate and Save to process all funded and non-funded accounts."
                    if not initial_calculation["rows"]
                    else ""
                )
            ),
        ),
        border=ft.Border.all(0.5, "#1e534b"),
        heading_row_color="#0c3832",
        heading_row_height=40,
        data_row_min_height=36,
        column_spacing=12,
    )
    total_funded_outstanding_text = ft.Text(
        (
            "Total Funded Outstanding: unavailable"
            if initial_load_error
            else "Total Funded Outstanding: "
            f"{initial_calculation['total_funded_outstanding']:,.2f}"
        ),
        color="white",
        size=13,
        weight="bold",
    )
    total_non_funded_outstanding_text = ft.Text(
        (
            "Total Nonfunded Outstanding: unavailable"
            if initial_load_error
            else "Total Nonfunded Outstanding: "
            f"{initial_calculation['total_non_funded_outstanding']:,.2f}"
        ),
        color="white",
        size=13,
        weight="bold",
    )
    total_outstanding_text = ft.Text(
        (
            "Total Outstanding: unavailable"
            if initial_load_error
            else "Total Outstanding: "
            f"{initial_calculation['total_outstanding']:,.2f}"
        ),
        color="white",
        size=13,
        weight="bold",
    )
    total_text = ft.Text(
        (
            "Total ECL: unavailable"
            if initial_load_error
            else f"Total ECL: {initial_calculation['total_ecl']:,.2f}"
        ),
        color="#ff8a80" if initial_load_error else "#78eb64",
        size=14,
        weight="bold",
    )
    initial_status = (
        f"Could not load saved ECL data: {initial_load_error}"
        if initial_load_error
        else (
            f"Loaded saved ECL values for {saved_ecl_count} account(s)."
            if saved_ecl_count
            else (
                "No saved ECL values are available. Recalculate and save to update."
                if initial_calculation["rows"]
                else ""
            )
        )
    )
    status_text = ft.Text(
        initial_status,
        color="#ff8a80" if initial_load_error else "white70",
        size=12,
    )
    progress_bar = ft.ProgressBar(
        value=1 if saved_ecl_count else 0,
        width=160,
        bar_height=5,
        color="#00e676",
        bgcolor="#1e534b",
        border_radius=4,
    )
    progress_percentage = ft.Text(
        "100% completed" if saved_ecl_count else "0% completed",
        color="white70",
        size=11,
    )
    calculate_button = ft.ElevatedButton(
        content=ft.Text("Recalculate and Save", color="#061d19", weight="bold", size=12),
        style=ft.ButtonStyle(
            bgcolor="#78eb64",
            shape=ft.RoundedRectangleBorder(radius=20),
        ),
        height=38,
        width=200,
    )

    def recalculate_and_save_ecl(_event):
        del _event
        calculate_button.disabled = True
        progress_bar.value = 0
        progress_percentage.value = "0% completed"
        status_text.value = f"Recalculating ECL for {current_year}..."
        status_text.color = "white70"
        page.update()

        try:
            (
                funded_accounts,
                non_funded_accounts,
                economic_data,
                migration_data,
            ) = get_ecl_calculation_data()
            calculation = build_ecl_calculations(
                funded_accounts,
                non_funded_accounts,
                economic_data,
                migration_data,
                current_year,
            )
        except Exception as error:
            progress_bar.value = 0
            progress_percentage.value = "0% completed"
            data_table.rows = _build_ecl_rows(
                empty_calculation,
                f"ECL calculation failed: {error}",
            )
            total_funded_outstanding_text.value = "Total Funded Outstanding: unavailable"
            total_non_funded_outstanding_text.value = "Total Nonfunded Outstanding: unavailable"
            total_outstanding_text.value = "Total Outstanding: unavailable"
            total_text.value = "Total ECL: unavailable"
            status_text.value = f"ECL calculation failed: {error}"
            status_text.color = "#ff8a80"
            calculate_button.disabled = False
            page.update()
            return

        data_table.rows = _build_ecl_rows(calculation)
        total_funded_outstanding_text.value = (
            "Total Funded Outstanding: "
            f"{calculation['total_funded_outstanding']:,.2f}"
        )
        total_non_funded_outstanding_text.value = (
            "Total Nonfunded Outstanding: "
            f"{calculation['total_non_funded_outstanding']:,.2f}"
        )
        total_outstanding_text.value = (
            f"Total Outstanding: {calculation['total_outstanding']:,.2f}"
        )
        total_text.value = f"Total ECL: {calculation['total_ecl']:,.2f}"
        unavailable_count = len(calculation["rows"]) - calculation["calculated_count"]
        missing_account_numbers = sum(
            not account["account_number"]
            for account in calculation["rows"]
        )
        funded_ecl = {}
        non_funded_ecl = {}
        for account in calculation["rows"]:
            account_number = account["account_number"]
            if not account_number:
                continue
            destination = (
                funded_ecl
                if account["account_type"] == "Funded"
                else non_funded_ecl
            )
            destination[account_number] = account["ecl"]

        if not (funded_ecl or non_funded_ecl):
            status_text.value = "No account numbers were available; nothing was saved."
            status_text.color = "#ffcc80"
            calculate_button.disabled = False
            page.update()
            return

        status_text.value = "Saving recalculated ECL values..."
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
            save_ecl_calculations(
                funded_ecl,
                non_funded_ecl,
                update_progress,
            )
        except Exception as error:
            progress_bar.value = 0
            progress_percentage.value = "0% completed"
            status_text.value = f"ECL was recalculated but not saved: {error}"
            status_text.color = "#ff8a80"
        else:
            progress_bar.value = 1
            progress_percentage.value = "100% completed"
            unavailable_saved_count = (
                sum(value is None for value in funded_ecl.values())
                + sum(value is None for value in non_funded_ecl.values())
            )
            status_text.value = (
                f"Recalculated and saved ECL for {len(funded_ecl) + len(non_funded_ecl)} "
                f"account(s); {unavailable_saved_count} unavailable ECL value(s) were saved as blank."
                + (
                    f" {missing_account_numbers} account(s) without account numbers were not saved."
                    if missing_account_numbers else ""
                )
            )
            status_text.color = (
                "#78eb64" if unavailable_count == 0 else "#ffcc80"
            )
        calculate_button.disabled = False
        page.update()

    calculate_button.on_click = recalculate_and_save_ecl

    note = (
        f"ECL = APD * LGD * EAD. APD is estimated for {current_year} from the "
        "Adjusted PD regression using current-year economic variables. Stage-3 "
        "accounts use 100% APD. ECL is marked unavailable when current-year APD "
        "cannot be determined; unavailable results are saved as blank."
    )

    return ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Text("Calculate Expected Credit Loss (ECL)", size=20, weight="bold", color="#00e676"),
                alignment=ft.Alignment(0, 0),
                padding=ft.Padding(0, 0, 0, 10),
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text(note, color="white70", size=12),
                    ft.Row(
                        controls=[
                            progress_bar,
                            progress_percentage,
                            ft.Container(expand=True),
                            calculate_button,
                        ],
                        alignment="spaceBetween",
                        vertical_alignment="center",
                    ),
                    ft.Row(
                        controls=[
                            total_funded_outstanding_text,
                            total_non_funded_outstanding_text,
                            total_outstanding_text,
                            total_text,
                        ],
                        alignment="end",
                        spacing=16,
                        wrap=True,
                    ),
                    status_text,
                    ft.Row([data_table], scroll=ft.ScrollMode.AUTO),
                ], spacing=10),
                padding=15,
                border=ft.Border.all(width=1, color="#00e676"),
                border_radius=8,
                bgcolor="#061d19",
            ),
        ], scroll=ft.ScrollMode.AUTO, expand=True),
        expand=True,
    )
