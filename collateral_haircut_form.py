import flet as ft
from datetime import date
from database import (
    save_collateral_haircut,
    get_all_collateral_haircuts,
    delete_collateral_haircut
)

def get_collateral_haircut_form(page: ft.Page):
    raw_cache = get_all_collateral_haircuts() or []
    current_year = str(date.today().year)
    
    property_options = ["Flat", "Land", "Building", "Project", "Fin Instrument"]

    # Form input fields
    year_dd = ft.Dropdown(
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

    property_dropdown = ft.Dropdown(
        label="Property Type",
        options=[ft.dropdown.Option(opt) for opt in property_options],
        height=45,
        content_padding=ft.Padding(12, 10, 12, 10),
        border_color="#00e676",
        focused_border_color="#00e676",
        label_style=ft.TextStyle(color="white70", size=14),
        text_style=ft.TextStyle(color="white", size=13),
        expand=True
    )

    market_value_tf = ft.TextField(
        label="Market Value",
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

    liquidation_value_tf = ft.TextField(
        label="Liquidation Value",
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

    haircut_rate_tf = ft.TextField(
        label="Collateral Haircut %",
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

    liquidation_time_tf = ft.TextField(
        label="Liquidation Time in Year",
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

    def parse_flt(val):
        try: return float(val) if val else 0.00
        except ValueError: return 0.00

    def calculate_haircut_rate(e=None):
        market_val = parse_flt(market_value_tf.value)
        liq_val = parse_flt(liquidation_value_tf.value)
        if market_val > 0:
            rate = (market_val - liq_val) / market_val
            haircut_rate_tf.value = f"{rate:.4f}"
        else:
            haircut_rate_tf.value = "0.0000"
        page.update()

    market_value_tf.on_change = calculate_haircut_rate
    liquidation_value_tf.on_change = calculate_haircut_rate

    # Form Layout Grid
    row1 = ft.Row([
        ft.Container(content=year_dd, expand=1),
        ft.Container(content=property_dropdown, expand=1),
        ft.Container(content=market_value_tf, expand=1)
    ], spacing=15)

    row2 = ft.Row([
        ft.Container(content=liquidation_value_tf, expand=1),
        ft.Container(content=haircut_rate_tf, expand=1),
        ft.Container(content=liquidation_time_tf, expand=1)
    ], spacing=15)

    def clear_form_fields():
        year_dd.value = current_year
        property_dropdown.value = None
        market_value_tf.value = ""
        liquidation_value_tf.value = ""
        haircut_rate_tf.value = "0.0000"
        liquidation_time_tf.value = ""
        page.update()

    def populate_fields(data_item):
        year_dd.value = str(data_item.get("year", ""))
        property_dropdown.value = str(data_item.get("property_type", ""))
        market_value_tf.value = f"{float(data_item.get('market_value', 0)):.2f}"
        liquidation_value_tf.value = f"{float(data_item.get('liquidation_value', 0)):.2f}"
        liquidation_time_tf.value = f"{float(data_item.get('liquidation_time_years', 0)):.2f}"
        calculate_haircut_rate()

    # Search fields (Search by Year and Search by Property Type)
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

    search_property_dropdown = ft.Dropdown(
        hint_text="All Types",
        options=[ft.dropdown.Option("All")] + [ft.dropdown.Option(opt) for opt in property_options],
        width=150,
        height=40,
        content_padding=ft.Padding(10, 0, 10, 0),
        border_color="#00e676",
        focused_border_color="#00e676",
        text_style=ft.TextStyle(color="white", size=13),
        value="All"
    )

    history_table_holder = ft.Container(expand=True)
    summary_table_holder = ft.Container(expand=True)

    def get_table_control(yr_search="", prop_search="All"):
        filtered = list(raw_cache)

        if yr_search.strip():
            filtered = [r for r in filtered if yr_search.strip().lower() in str(r.get("year", "")).lower()]

        if prop_search and prop_search != "All":
            filtered = [r for r in filtered if str(r.get("property_type", "")).lower() == prop_search.lower()]

        filtered = filtered[:10]

        if not filtered:
            return ft.Container(content=ft.Text("No records found.", color="white54", italic=True, size=13), padding=15)

        rows = []
        for item in filtered:
            yr = str(item.get("year", ""))
            ptype = str(item.get("property_type", ""))

            action_cell = ft.Row([
                ft.IconButton(icon=ft.Icons.EDIT, icon_color="#00e676", icon_size=18, tooltip="Edit", on_click=lambda e, d=item: populate_fields(d)),
                ft.IconButton(icon=ft.Icons.DELETE, icon_color="#ff5252", icon_size=18, tooltip="Delete", on_click=lambda e, y=yr, p=ptype: execute_delete(y, p))
            ], spacing=0, alignment="center")

            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(yr, weight="bold", color="#00e676", size=11)),
                ft.DataCell(ft.Text(ptype, color="white", size=11)),
                ft.DataCell(ft.Text(f"{float(item.get('market_value', 0)):.2f}", color="white", size=11)),
                ft.DataCell(ft.Text(f"{float(item.get('liquidation_value', 0)):.2f}", color="white", size=11)),
                ft.DataCell(ft.Text(f"{float(item.get('haircut_rate', 0)):.4f}", color="white", weight="bold", size=11)),
                ft.DataCell(ft.Text(f"{float(item.get('liquidation_time_years', 0)):.2f}", color="white", size=11)),
                ft.DataCell(action_cell)
            ]))

        return ft.DataTable(
            width=780,
            columns=[
                ft.DataColumn(ft.Text("Year", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Property Type", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Market Value", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Liquidation Value", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Haircut %", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Liq. Time (Yrs)", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Actions", color="white", weight="bold", size=11)),
            ],
            rows=rows,
            border=ft.Border.all(0.5, "#1e534b"),
            heading_row_color="#0c3832",
            heading_row_height=36,
            data_row_min_height=34,
            column_spacing=12
        )

    # Function to generate Summary Table
    def get_summary_table_control():
        if not raw_cache:
            return ft.Container(content=ft.Text("No summary data available.", color="white54", italic=True, size=13), padding=15)

        grouped = {}
        for item in raw_cache:
            ptype = str(item.get("property_type", "")).strip()
            if not ptype:
                continue
            if ptype not in grouped:
                grouped[ptype] = {"count": 0, "sum_haircut": 0.0, "sum_time": 0.0}
            grouped[ptype]["count"] += 1
            grouped[ptype]["sum_haircut"] += float(item.get("haircut_rate", 0))
            grouped[ptype]["sum_time"] += float(item.get("liquidation_time_years", 0))

        rows = []
        for ptype in sorted(grouped.keys()):
            count = grouped[ptype]["count"]
            avg_haircut = grouped[ptype]["sum_haircut"] / count if count > 0 else 0.0
            avg_time = grouped[ptype]["sum_time"] / count if count > 0 else 0.0

            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(ptype, weight="bold", color="#00e676", size=11)),
                ft.DataCell(ft.Text(str(count), color="white", size=11)),
                ft.DataCell(ft.Text(f"{avg_haircut:.4f}", color="white", weight="bold", size=11)),
                ft.DataCell(ft.Text(f"{avg_time:.2f}", color="white", weight="bold", size=11)),
            ]))

        return ft.DataTable(
            width=780,
            columns=[
                ft.DataColumn(ft.Text("Property Type", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Total Records", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Avg Collateral Haircut %", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Avg Liquidation Time (Yrs)", color="white", weight="bold", size=11)),
            ],
            rows=rows,
            border=ft.Border.all(0.5, "#1e534b"),
            heading_row_color="#0c3832",
            heading_row_height=36,
            data_row_min_height=34,
            column_spacing=25
        )

    def render_all_tables():
        history_table_holder.content = get_table_control(search_year_tf.value or "", search_property_dropdown.value or "All")
        summary_table_holder.content = get_summary_table_control()

    # Event handlers for search filtering
    def update_search_filter(e):
        history_table_holder.content = get_table_control(
            search_year_tf.value or "",
            search_property_dropdown.value or "All"
        )
        history_table_holder.update()

    search_year_tf.on_change = update_search_filter
    search_property_dropdown.on_select = update_search_filter

    search_header_row = ft.Row([
        ft.Text("Search Year:", size=14, weight="bold", color="#00e676"),
        search_year_tf,
        ft.Container(width=10),
        ft.Text("Property Type:", size=14, weight="bold", color="#00e676"),
        search_property_dropdown
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

    # Container 3: Averages Summary Table by Property Type
    summary_section_container = ft.Container(
        content=ft.Column([
            ft.Text("Property Type Averages Summary", size=16, weight="bold", color="#00e676"),
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
        raw_cache = get_all_collateral_haircuts() or []

    def update_all_containers():
        refresh_cache()
        clear_form_fields()
        render_all_tables()

    def on_save_click(e):
        yr = year_dd.value or ""
        prop = property_dropdown.value or ""

        if not yr or not prop:
            page.overlay.append(ft.SnackBar(content=ft.Text("Please enter Year and select Property Type!"), bgcolor="#ff9800", open=True))
            page.update()
            return

        if int(yr) > int(current_year):
            page.overlay.append(ft.SnackBar(content=ft.Text("Year cannot be greater than the current year."), bgcolor="#ff9800", open=True))
            page.update()
            return

        calculate_haircut_rate()

        payload = {
            "year": yr,
            "property_type": prop,
            "market_value": parse_flt(market_value_tf.value),
            "liquidation_value": parse_flt(liquidation_value_tf.value),
            "haircut_rate": parse_flt(haircut_rate_tf.value),
            "liquidation_time_years": parse_flt(liquidation_time_tf.value)
        }

        try:
            save_collateral_haircut(payload)
            update_all_containers()
            page.overlay.append(ft.SnackBar(content=ft.Text(f"Collateral Haircut for {yr} ({prop}) saved successfully!"), bgcolor="#00e676", open=True))
        except Exception as err:
            page.overlay.append(ft.SnackBar(content=ft.Text(f"Error saving Haircut: {str(err)}"), bgcolor="red", open=True))
        page.update()

    def execute_delete(yr, prop):
        try:
            delete_collateral_haircut(yr, prop)
            update_all_containers()
            page.overlay.append(ft.SnackBar(content=ft.Text(f"Collateral Haircut for {yr} ({prop}) deleted successfully!"), bgcolor="#ff5252", open=True))
        except Exception as err:
            page.overlay.append(ft.SnackBar(content=ft.Text(f"Error deleting: {str(err)}"), bgcolor="red", open=True))
        page.update()

    add_btn = ft.ElevatedButton(
        content=ft.Text("Save Haircut", color="black", weight="bold", size=14),
        on_click=on_save_click,
        style=ft.ButtonStyle(bgcolor="#78eb64", shape=ft.RoundedRectangleBorder(radius=20)),
        height=42, width=170
    )

    # Container 1: Input Form Card
    input_form_card = ft.Container(
        content=ft.Column([
            ft.Container(content=ft.Text("Collateral Haircut", size=20, weight="bold", color="#00e676"), alignment=ft.Alignment(0, 0), padding=ft.Padding(0, 0, 0, 15)),
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