import flet as ft

from components.collateral_distribution import (
    build_proportional_collateral_allocations,
)
from database import (
    get_collateral_distribution_data,
    save_collateral_distributions,
)


def _build_distribution_rows(distribution, error_message=""):
    rows = []
    for allocation in distribution["rows"]:
        allocated_pv = allocation["allocated_pv"]
        rows.append(ft.DataRow(cells=[
            ft.DataCell(ft.Text(allocation["customer_number"] or "-", color="white", size=11)),
            ft.DataCell(ft.Text(allocation["customer_name"] or "-", color="white", size=11)),
            ft.DataCell(ft.Text(allocation["account_type"], color="white", size=11)),
            ft.DataCell(ft.Text(allocation["account_number"] or "-", color="white", size=11)),
            ft.DataCell(ft.Text(f"{allocation['ead']:,.4f}", color="white", size=11)),
            ft.DataCell(ft.Text(f"{allocation['customer_ead']:,.4f}", color="white", size=11)),
            ft.DataCell(ft.Text(f"{allocation['customer_pv']:,.4f}", color="white", size=11)),
            ft.DataCell(ft.Text(
                f"{allocated_pv:,.4f}" if allocated_pv is not None else "N/A",
                color="#78eb64" if allocated_pv is not None else "#ffcc80",
                weight="bold",
                size=11,
            )),
            ft.DataCell(ft.Text(
                allocation["status"],
                color="#78eb64" if allocated_pv is not None else "#ffcc80",
                size=11,
            )),
        ]))

    if not rows:
        rows.append(ft.DataRow(cells=[
            ft.DataCell(ft.Text(
                f"Unable to calculate distribution: {error_message}"
                if error_message else "No funded or non-funded accounts found.",
                color="white70",
                italic=True,
                size=12,
            )),
            *[ft.DataCell(ft.Text("", size=11)) for _ in range(8)],
        ]))
    return rows


def _build_distribution_warnings(distribution):
    warnings = []
    if distribution["skipped_customers"]:
        warnings.append(
            f"{distribution['skipped_customers']} customer(s) have zero total EAD "
            "and were not allocated."
        )
    if distribution["customers_without_collateral"]:
        warnings.append(
            f"{distribution['customers_without_collateral']} customer(s) have "
            "accounts but no collateral records; existing account PV values were left unchanged."
        )
    if distribution["collateral_without_customer"]:
        warnings.append(
            f"{distribution['collateral_without_customer']} collateral record(s) "
            "are missing a customer number and were excluded."
        )
    if distribution["collateral_customers_without_accounts"]:
        warnings.append(
            f"{distribution['collateral_customers_without_accounts']} customer(s) "
            "have collateral but no funded or non-funded accounts."
        )
    return [
        ft.Text(warning, color="#ffcc80", size=12)
        for warning in warnings
    ]


def get_collateral_distribution_form(page: ft.Page):
    calculation_error = ""
    try:
        collateral_records, funded_accounts, non_funded_accounts = (
            get_collateral_distribution_data()
        )
    except Exception as error:
        calculation_error = f"Unable to load account and collateral data: {error}"
        distribution = None
    else:
        distribution = None
        try:
            distribution = build_proportional_collateral_allocations(
                collateral_records,
                funded_accounts,
                non_funded_accounts,
            )
        except ValueError as error:
            calculation_error = str(error)

    if distribution is None:
        distribution = {
            "rows": [],
            "funded_allocations": {},
            "non_funded_allocations": {},
            "skipped_customers": 0,
            "customers_without_collateral": 0,
            "collateral_without_customer": 0,
            "collateral_customers_without_accounts": 0,
        }

    rows = _build_distribution_rows(distribution, calculation_error)

    funded_allocations = distribution["funded_allocations"]
    non_funded_allocations = distribution["non_funded_allocations"]
    status_text = ft.Text(
        f"Calculation error: {calculation_error}" if calculation_error else "",
        color="#ff8a80" if calculation_error else "white70",
        size=12,
    )
    progress_bar = ft.ProgressBar(
        value=0,
        width=180,
        bar_height=5,
        color="#00e676",
        bgcolor="#1e534b",
        border_radius=4,
    )
    progress_percentage = ft.Text("0% completed", color="white70", size=11)

    def apply_distribution(_e):
        del _e
        apply_button.disabled = True
        progress_bar.value = 0
        progress_percentage.value = "0% completed"
        progress_row.visible = True
        status_text.value = "Recalculating collateral distribution..."
        status_text.color = "white70"
        page.update()

        try:
            collateral_records, current_funded_accounts, current_non_funded_accounts = (
                get_collateral_distribution_data()
            )
            updated_distribution = build_proportional_collateral_allocations(
                collateral_records,
                current_funded_accounts,
                current_non_funded_accounts,
            )
        except Exception as error:
            progress_bar.value = 0
            progress_percentage.value = "0% completed"
            status_text.value = (
                f"Distribution failed; no changes were committed: {error}"
            )
            status_text.color = "#ff8a80"
            apply_button.disabled = False
            page.update()
            return

        data_table.rows = _build_distribution_rows(updated_distribution)
        warnings_container.controls = _build_distribution_warnings(updated_distribution)
        funded_allocations.clear()
        funded_allocations.update(updated_distribution["funded_allocations"])
        non_funded_allocations.clear()
        non_funded_allocations.update(updated_distribution["non_funded_allocations"])

        if not (funded_allocations or non_funded_allocations):
            status_text.value = "Distribution recalculated; no account allocations need saving."
            status_text.color = "#ffcc80"
            apply_button.disabled = False
            page.update()
            return

        status_text.value = "Saving recalculated distribution..."
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
            save_collateral_distributions(
                funded_allocations,
                non_funded_allocations,
                update_progress,
            )
        except Exception as error:
            progress_bar.value = 0
            progress_percentage.value = "0% completed"
            status_text.value = (
                f"Distribution failed; no changes were committed: {error}"
            )
            status_text.color = "#ff8a80"
        else:
            progress_bar.value = 1
            progress_percentage.value = "100% completed"
            status_text.value = (
                f"Recalculated distribution saved for {len(funded_allocations)} funded and "
                f"{len(non_funded_allocations)} non-funded account(s)."
            )
            status_text.color = "#78eb64"
        apply_button.disabled = False
        page.update()

    apply_button = ft.ElevatedButton(
        content=ft.Text("Distribute & Save", color="#061d19", weight="bold", size=12),
        on_click=apply_distribution,
        style=ft.ButtonStyle(
            bgcolor="#78eb64",
            shape=ft.RoundedRectangleBorder(radius=20),
        ),
        height=38,
        width=180,
    )
    progress_row = ft.Row(
        controls=[
            progress_bar,
            progress_percentage,
            ft.Container(expand=True),
            apply_button,
        ],
        spacing=10,
        vertical_alignment="center",
    )

    note = (
        "For each customer, total collateral PV is the sum of Present Value (PV) "
        "from all collateral records. Each funded and non-funded account receives "
        "a share calculated as customer collateral PV × account EAD ÷ the "
        "customer's combined funded and non-funded EAD. Distribute & Save "
        "recalculates using current account and collateral data, then saves the "
        "shares into each account's PV of Collateral field."
    )
    warnings_container = ft.Column(
        controls=_build_distribution_warnings(distribution),
        spacing=4,
    )
    data_table = ft.DataTable(
        width=1220,
        columns=[
            ft.DataColumn(ft.Text("Customer No.", color="white", weight="bold", size=11)),
            ft.DataColumn(ft.Text("Customer Name", color="white", weight="bold", size=11)),
            ft.DataColumn(ft.Text("Account Type", color="white", weight="bold", size=11)),
            ft.DataColumn(ft.Text("A/C No.", color="white", weight="bold", size=11)),
            ft.DataColumn(ft.Text("EAD", color="white", weight="bold", size=11)),
            ft.DataColumn(ft.Text("Customer Total EAD", color="white", weight="bold", size=11)),
            ft.DataColumn(ft.Text("Customer Total PV", color="white", weight="bold", size=11)),
            ft.DataColumn(ft.Text("Allocated PV", color="white", weight="bold", size=11)),
            ft.DataColumn(ft.Text("Status", color="white", weight="bold", size=11)),
        ],
        rows=rows,
        border=ft.Border.all(0.5, "#1e534b"),
        heading_row_color="#0c3832",
        heading_row_height=40,
        data_row_min_height=36,
        column_spacing=12,
    )

    return ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Text(
                    "Distribute Collateral - Proportional Method",
                    size=20,
                    weight="bold",
                    color="#00e676",
                ),
                alignment=ft.Alignment(0, 0),
                padding=ft.Padding(0, 0, 0, 10),
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text(note, color="white70", size=12),
                    warnings_container,
                    progress_row,
                    status_text,
                    ft.Row([
                        data_table
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
