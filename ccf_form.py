from datetime import datetime

import flet as ft
from database import (
    save_credit_conversion_factor,
    get_all_credit_conversion_factors,
    delete_credit_conversion_factor
)

def get_ccf_form(page: ft.Page):
    raw_cache = get_all_credit_conversion_factors() or []
    
    facility_options = ["CCOD", "BG", "Cash LC", "BBLC"]
    current_year = str(datetime.now().year)

    # Form input fields
    year_tf = ft.Dropdown(
        label="Year",
        options=[ft.dropdown.Option(str(year)) for year in range(2020, int(current_year) + 1)],
        value=current_year,
        height=45,
        content_padding=ft.Padding(12, 10, 12, 10),
        border_color="#00e676",
        focused_border_color="#00e676",
        label_style=ft.TextStyle(color="white70", size=14),
        text_style=ft.TextStyle(color="white", size=13),
        expand=True
    )

    facility_dropdown = ft.Dropdown(
        label="Facility Type",
        options=[ft.dropdown.Option(opt) for opt in facility_options],
        height=45,
        content_padding=ft.Padding(12, 10, 12, 10),
        border_color="#00e676",
        focused_border_color="#00e676",
        label_style=ft.TextStyle(color="white70", size=14),
        text_style=ft.TextStyle(color="white", size=13),
        expand=True
    )

    facility_issued_tf = ft.TextField(
        label="Facility Issued",
        hint_text="0.00",
        height=45,
        content_padding=ft.Padding(12, 10, 12, 10),
        border_color="#00e676",
        focused_border_color="#00e676",
        label_style=ft.TextStyle(color="white70", size=14),
        text_style=ft.TextStyle(color="white", size=13),
        keyboard_type=ft.KeyboardType.NUMBER,
        expand=True
    )

    demand_loan_tf = ft.TextField(
        label="Demand Loan Created",
        hint_text="0.00",
        height=45,
        content_padding=ft.Padding(12, 10, 12, 10),
        border_color="#00e676",
        focused_border_color="#00e676",
        label_style=ft.TextStyle(color="white70", size=14),
        text_style=ft.TextStyle(color="white", size=13),
        keyboard_type=ft.KeyboardType.NUMBER,
        expand=True
    )

    cc_rate_tf = ft.TextField(
        label="Credit Conversion Rate",
        value="0.0000",
        read_only=True,
        height=45,
        content_padding=ft.Padding(12, 10, 12, 10),
        border_color="#00e676",
        focused_border_color="#00e676",
        label_style=ft.TextStyle(color="white70", size=14),
        text_style=ft.TextStyle(color="white", size=13),
        expand=True
    )

    def parse_flt(val):
        try: return float(val) if val else 0.00
        except ValueError: return 0.00

    def calculate_cc_rate(e=None):
        issued = parse_flt(facility_issued_tf.value)
        demand = parse_flt(demand_loan_tf.value)
        if issued > 0:
            rate = demand / issued
            cc_rate_tf.value = f"{rate:.4f}"
        else:
            cc_rate_tf.value = "0.0000"
        page.update()

    facility_issued_tf.on_change = calculate_cc_rate
    demand_loan_tf.on_change = calculate_cc_rate

    # Form Layout Grid
    row1 = ft.Row([
        ft.Container(content=year_tf, expand=1),
        ft.Container(content=facility_dropdown, expand=1),
        ft.Container(content=facility_issued_tf, expand=1)
    ], spacing=15)

    row2 = ft.Row([
        ft.Container(content=demand_loan_tf, expand=1),
        ft.Container(content=cc_rate_tf, expand=1),
        ft.Container(expand=1)
    ], spacing=15)

    def clear_form_fields():
        year_tf.value = current_year
        facility_dropdown.value = None
        facility_issued_tf.value = ""
        demand_loan_tf.value = ""
        cc_rate_tf.value = "0.0000"
        page.update()

    def populate_fields(data_item):
        year_tf.value = str(data_item.get("year", ""))
        facility_dropdown.value = str(data_item.get("facility_type", ""))
        facility_issued_tf.value = f"{float(data_item.get('facility_issued', 0)):.2f}"
        demand_loan_tf.value = f"{float(data_item.get('demand_loan_created', 0)):.2f}"
        calculate_cc_rate()

    # Search fields (Search by Year and Search by Facility Type)
    search_year_tf = ft.TextField(
        hint_text="YYYY",
        hint_style=ft.TextStyle(color="white38", size=13),
        width=100,
        height=40,
        content_padding=ft.Padding(10, 8, 10, 8),
        border_color="#00e676",
        focused_border_color="#00e676",
        text_style=ft.TextStyle(color="white", size=13, weight="bold"),
        keyboard_type=ft.KeyboardType.NUMBER
    )

    search_facility_dropdown = ft.Dropdown(
        hint_text="All Types",
        options=[ft.dropdown.Option("All")] + [ft.dropdown.Option(opt) for opt in facility_options],
        width=130,
        height=40,
        content_padding=ft.Padding(10, 0, 10, 0),
        border_color="#00e676",
        focused_border_color="#00e676",
        text_style=ft.TextStyle(color="white", size=13),
        value="All"
    )

    history_table_holder = ft.Container(expand=True)
    summary_table_holder = ft.Container(expand=True)

    def get_table_control(yr_search="", fac_search="All"):
        filtered = list(raw_cache)

        if yr_search.strip():
            filtered = [r for r in filtered if yr_search.strip().lower() in str(r.get("year", "")).lower()]

        if fac_search and fac_search != "All":
            filtered = [r for r in filtered if str(r.get("facility_type", "")).lower() == fac_search.lower()]

        filtered = filtered[:10]

        if not filtered:
            return ft.Container(content=ft.Text("No records found.", color="white54", italic=True, size=13), padding=15)

        rows = []
        for item in filtered:
            yr = str(item.get("year", ""))
            ftype = str(item.get("facility_type", ""))

            action_cell = ft.Row([
                ft.IconButton(icon=ft.Icons.EDIT, icon_color="#00e676", icon_size=18, tooltip="Edit", on_click=lambda e, d=item: populate_fields(d)),
                ft.IconButton(icon=ft.Icons.DELETE, icon_color="#ff5252", icon_size=18, tooltip="Delete", on_click=lambda e, y=yr, f=ftype: execute_delete(y, f))
            ], spacing=0, alignment="center")

            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(yr, weight="bold", color="#00e676", size=11)),
                ft.DataCell(ft.Text(ftype, color="white", size=11)),
                ft.DataCell(ft.Text(f"{float(item.get('facility_issued', 0)):.2f}", color="white", size=11)),
                ft.DataCell(ft.Text(f"{float(item.get('demand_loan_created', 0)):.2f}", color="white", size=11)),
                ft.DataCell(ft.Text(f"{float(item.get('cc_rate', 0)):.4f}", color="white", weight="bold", size=11)),
                ft.DataCell(action_cell)
            ]))

        return ft.DataTable(
            width=760,
            columns=[
                ft.DataColumn(ft.Text("Year", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Facility Type", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Facility Issued", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Demand Loan Created", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("CC Rate", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Actions", color="white", weight="bold", size=11)),
            ],
            rows=rows,
            border=ft.Border.all(0.5, "#1e534b"),
            heading_row_color="#0c3832",
            heading_row_height=36,
            data_row_min_height=34,
            column_spacing=15
        )

    # Function to generate Summary Table by Facility Type
    def get_summary_table_control():
        if not raw_cache:
            return ft.Container(content=ft.Text("No summary data available.", color="white54", italic=True, size=13), padding=15)

        grouped = {}
        for item in raw_cache:
            ftype = str(item.get("facility_type", "")).strip()
            if not ftype:
                continue
            if ftype not in grouped:
                grouped[ftype] = {"count": 0, "sum_cc_rate": 0.0}
            grouped[ftype]["count"] += 1
            grouped[ftype]["sum_cc_rate"] += float(item.get("cc_rate", 0))

        rows = []
        for ftype in sorted(grouped.keys()):
            count = grouped[ftype]["count"]
            avg_cc_rate = grouped[ftype]["sum_cc_rate"] / count if count > 0 else 0.0

            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(ftype, weight="bold", color="#00e676", size=11)),
                ft.DataCell(ft.Text(str(count), color="white", size=11)),
                ft.DataCell(ft.Text(f"{avg_cc_rate:.4f}", color="white", weight="bold", size=11)),
            ]))

        return ft.DataTable(
            width=760,
            columns=[
                ft.DataColumn(ft.Text("Facility Type", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Total Records", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Avg Credit Conversion Rate", color="white", weight="bold", size=11)),
            ],
            rows=rows,
            border=ft.Border.all(0.5, "#1e534b"),
            heading_row_color="#0c3832",
            heading_row_height=36,
            data_row_min_height=34,
            column_spacing=35
        )

    def render_all_tables():
        history_table_holder.content = get_table_control(search_year_tf.value or "", search_facility_dropdown.value or "All")
        summary_table_holder.content = get_summary_table_control()

    # Event handlers for search filtering
    def update_search_filter(e):
        history_table_holder.content = get_table_control(
            search_year_tf.value or "",
            search_facility_dropdown.value or "All"
        )
        history_table_holder.update()

    search_year_tf.on_change = update_search_filter
    search_facility_dropdown.on_select = update_search_filter

    search_header_row = ft.Row([
        ft.Text("Search Year:", size=14, weight="bold", color="#00e676"),
        search_year_tf,
        ft.Container(width=10),
        ft.Text("Facility Type:", size=14, weight="bold", color="#00e676"),
        search_facility_dropdown
    ], vertical_alignment="center", spacing=10)

    # Container 2: Detailed Records & Search Table
    history_section_container = ft.Container(
        content=ft.Column([
            search_header_row,
            ft.Container(height=10),
            ft.Row([history_table_holder], scroll=ft.ScrollMode.AUTO, expand=True)
        ], horizontal_alignment="stretch"),
        padding=15,
        border=ft.Border.all(width=1, color="#00e676"),
        border_radius=8,
        bgcolor="#061d19"
    )

    # Container 3: Averages Summary Table by Facility Type
    summary_section_container = ft.Container(
        content=ft.Column([
            ft.Text("Facility Type Averages Summary", size=16, weight="bold", color="#00e676"),
            ft.Container(height=8),
            ft.Row([summary_table_holder], scroll=ft.ScrollMode.AUTO, expand=True)
        ], horizontal_alignment="stretch"),
        padding=15,
        border=ft.Border.all(width=1, color="#00e676"),
        border_radius=8,
        bgcolor="#061d19"
    )

    def refresh_cache():
        nonlocal raw_cache
        raw_cache = get_all_credit_conversion_factors() or []

    def update_all_containers():
        refresh_cache()
        clear_form_fields()
        render_all_tables()

    def on_save_click(e):
        yr = year_tf.value.strip() if year_tf.value else ""
        fac = facility_dropdown.value or ""

        if not yr or not fac:
            page.overlay.append(ft.SnackBar(content=ft.Text("Please enter Year and select Facility Type!"), bgcolor="#ff9800", open=True))
            page.update()
            return

        if int(yr) > int(current_year):
            page.overlay.append(ft.SnackBar(content=ft.Text("Year cannot be greater than the current year."), bgcolor="#ff9800", open=True))
            page.update()
            return

        calculate_cc_rate()

        payload = {
            "year": yr,
            "facility_type": fac,
            "facility_issued": parse_flt(facility_issued_tf.value),
            "demand_loan_created": parse_flt(demand_loan_tf.value),
            "cc_rate": parse_flt(cc_rate_tf.value)
        }

        try:
            save_credit_conversion_factor(payload)
            update_all_containers()
            page.overlay.append(ft.SnackBar(content=ft.Text(f"CCF for {yr} ({fac}) saved successfully!"), bgcolor="#00e676", open=True))
        except Exception as err:
            page.overlay.append(ft.SnackBar(content=ft.Text(f"Error saving CCF: {str(err)}"), bgcolor="red", open=True))
        page.update()

    def execute_delete(yr, fac):
        try:
            delete_credit_conversion_factor(yr, fac)
            update_all_containers()
            page.overlay.append(ft.SnackBar(content=ft.Text(f"CCF for {yr} ({fac}) deleted successfully!"), bgcolor="#ff5252", open=True))
        except Exception as err:
            page.overlay.append(ft.SnackBar(content=ft.Text(f"Error deleting: {str(err)}"), bgcolor="red", open=True))
        page.update()

    add_btn = ft.ElevatedButton(
        content=ft.Text("Save CCF", color="black", weight="bold", size=14),
        on_click=on_save_click,
        style=ft.ButtonStyle(bgcolor="#78eb64", shape=ft.RoundedRectangleBorder(radius=20)),
        height=42, width=170
    )

    # Container 1: Input Form Card
    input_form_card = ft.Container(
        content=ft.Column([
            ft.Container(content=ft.Text("Credit Conversion Factor", size=20, weight="bold", color="#00e676"), alignment=ft.Alignment(0, 0), padding=ft.Padding(0, 0, 0, 15)),
            row1,
            ft.Container(height=5),
            row2,
            ft.Container(height=20),
            ft.Row([add_btn], alignment="center")
        ]),
        padding=20, border=ft.Border.all(width=1, color="#00e676"), border_radius=8, bgcolor="#061d19"
    )

    render_all_tables()

    return ft.Container(
        content=ft.Column([
            input_form_card,
            history_section_container,
            summary_section_container
        ], scroll=ft.ScrollMode.AUTO, spacing=15),
        width=820, alignment=ft.Alignment(0, -1), padding=ft.Padding(0, 0, 0, 20)
    )