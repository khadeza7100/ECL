import flet as ft
from database import (
    save_collateral_profile,
    get_all_collateral_profiles,
    delete_collateral_profile_by_id,
    get_customer_name_by_number,
    is_customer_exists_in_table,
    get_all_collateral_haircuts,
    get_discounting_factor
)
from components.custom_datepicker import CustomDatePicker

def get_avg_collateral_metrics(property_type: str) -> tuple[float, float]:
    """Returns the average haircut and liquidation time for a collateral type."""
    if not property_type:
        return 0.0, 0.0
    haircut_records = get_all_collateral_haircuts() or []
    matching_records = [
        r
        for r in haircut_records
        if str(r.get("property_type", "")).strip().lower() == str(property_type).strip().lower()
    ]
    if not matching_records:
        return 0.0, 0.0
    avg_haircut = sum(float(r.get("haircut_rate", 0.0)) for r in matching_records) / len(matching_records)
    avg_liquidation_time = sum(float(r.get("liquidation_time_years", 0.0)) for r in matching_records) / len(matching_records)
    return avg_haircut, avg_liquidation_time

def process_raw_collateral_cache(raw_cache):
    """
    Keys the cache dictionary by primary key 'id' instead of 'customer_number'[cite: 14, 15].
    This ensures that multiple collateral properties belonging to the same customer are preserved[cite: 15].
    """
    processed = {}
    if isinstance(raw_cache, list):
        for item in raw_cache:
            if isinstance(item, dict):
                # Unique record ID takes primary precedence
                key = str(item.get("id") or item.get("customer_number") or "").strip()
                if key:
                    processed[key] = item
    elif isinstance(raw_cache, dict):
        processed = {str(k).strip(): v for k, v in raw_cache.items()}
    return processed

def get_collateral_profile_form(page: ft.Page):
    input_fields = {}

    # Auto-fill Customer Name handler
    def on_customer_number_change(e):
        cust_num = (input_fields["Customer Number"].value or "").strip()
        if cust_num:
            name = get_customer_name_by_number(cust_num)
            input_fields["Customer Name"].value = name if name else ""
        else:
            input_fields["Customer Name"].value = ""
        page.update()

    # Base input field style for consistent boundary and dimensions
    base_field_style = {
        "height": 45,
        "content_padding": ft.Padding(12, 10, 12, 10),
        "border_color": "#00e676",
        "focused_border_color": "#00e676",
        "border_radius": 6,
        "label_style": ft.TextStyle(color="white70", size=14),
        "text_style": ft.TextStyle(color="white", size=13),
        "expand": True
    }

    raw_cache = get_all_collateral_profiles() or []
    full_db_cache = process_raw_collateral_cache(raw_cache)
    stored_discounting_factor = get_discounting_factor()
    discounting_factor_value = (
        f"{stored_discounting_factor:.4f}"
        if stored_discounting_factor is not None
        else "0.0000"
    )

    # Field options definitions
    dropdown_options = {
        "Collateral Type": ["Flat", "Land", "Building", "Project", "Fin.Instrument", "Share", "Gold", "Govt.Guarantee"],
        "Measurement Unit": ["Decimal", "Ton", "Vori", "Number", "Squre Feet"],
        "Quality of Collateral": ["Genuinge", "Disputed", "Major Audit Obj.", "Fake", "NA"]
    }

    numeric_fields = ["Quantity of Security", "Market Value"]

    # Custom DatePicker Component Instance
    cp_datepicker = CustomDatePicker(
        page, 
        "Valuation Date", 
        width=None, 
        height=45
    )
    cp_datepicker.input_field.expand = True
    cp_datepicker.input_field.border_color = "#00e676"
    cp_datepicker.input_field.focused_border_color = "#00e676"
    cp_datepicker.input_field.border_radius = 6

    # Input Fields Definition including FSV
    all_field_names = [
        "Customer Number", "Customer Name", "Collateral Type",
        "Quantity of Security", "Measurement Unit", "Valuation Date",
        "Market Value", "Average Haicut %", "FSV",
        "Average Liquidation Time (Yr.)", "Discounting Factor", "Present Value (PV)", "Quality of Collateral"
    ]

    def parse_flt(val):
        try:
            return float(str(val).replace(',', '')) if val else 0.00
        except ValueError:
            return 0.00

    present_value_is_valid = True

    def calculate_fsv(e=None):
        nonlocal present_value_is_valid
        market_val = parse_flt(input_fields["Market Value"].value)
        sec_type = input_fields["Collateral Type"].value
        avg_haircut, avg_liquidation_time = get_avg_collateral_metrics(sec_type)

        input_fields["Average Haicut %"].value = f"{avg_haircut:.4f}"
        input_fields["Average Liquidation Time (Yr.)"].value = f"{avg_liquidation_time:.2f}"
        fsv_val = market_val * (1 - avg_haircut)
        input_fields["FSV"].value = f"{fsv_val:.2f}"
        discount_rate = (stored_discounting_factor or 0.0) / 100
        discount_base = 1 + discount_rate
        present_value_is_valid = discount_base > 0
        if present_value_is_valid:
            present_value = fsv_val / (discount_base ** avg_liquidation_time)
            input_fields["Present Value (PV)"].value = f"{present_value:.4f}"
        else:
            input_fields["Present Value (PV)"].value = "Invalid discount rate"
        page.update()

    for label_name in all_field_names:
        if label_name == "FSV":
            tf = ft.TextField(
                label="Forced Sale Value (FSV)",
                value="0.00",
                read_only=True,
                **base_field_style
            )
        elif label_name == "Discounting Factor":
            tf = ft.TextField(
                label=label_name,
                value=discounting_factor_value,
                read_only=True,
                **base_field_style
            )
        elif label_name in ("Average Haicut %", "Average Liquidation Time (Yr.)"):
            tf = ft.TextField(
                label=label_name,
                value="0.0000" if label_name == "Average Haicut %" else "0.00",
                read_only=True,
                **base_field_style
            )
        elif label_name == "Present Value (PV)":
            tf = ft.TextField(
                label=label_name,
                value="0.0000",
                read_only=True,
                **base_field_style
            )
        elif label_name in dropdown_options:
            tf = ft.Dropdown(
                label=label_name,
                options=[ft.dropdown.Option(opt) for opt in dropdown_options[label_name]],
                **base_field_style
            )
            if label_name == "Collateral Type":
                tf.on_select = calculate_fsv
        elif label_name == "Valuation Date":
            tf = cp_datepicker.input_field
        else:
            is_num = label_name in numeric_fields
            tf = ft.TextField(
                label=label_name,
                keyboard_type=ft.KeyboardType.NUMBER if is_num else ft.KeyboardType.TEXT,
                **base_field_style
            )
            if label_name == "Customer Number":
                tf.on_change = on_customer_number_change
            elif label_name == "Market Value":
                tf.on_change = calculate_fsv

        input_fields[label_name] = tf

    # Build 3-Column Uniform Grid Layout
    grid_rows = []
    for i in range(0, len(all_field_names), 3):
        row_controls = []
        for j in range(3):
            if i + j < len(all_field_names):
                f_name = all_field_names[i + j]
                row_controls.append(ft.Container(content=input_fields[f_name], expand=1))
            else:
                row_controls.append(ft.Container(expand=1))
        grid_rows.append(ft.Row(controls=row_controls, spacing=15))

    grid_column = ft.Column(controls=grid_rows, spacing=15)

    def populate_fields_by_id(record_id):
        data = full_db_cache.get(str(record_id), {})
        if not data:
            return

        input_fields["Customer Number"].value = str(data.get("customer_number") or "")
        input_fields["Customer Name"].value = str(data.get("customer_name") or "")
        input_fields["Collateral Type"].value = str(data.get("security_type") or "")
        input_fields["Quantity of Security"].value = str(data.get("quantity") or "0.00")
        input_fields["Measurement Unit"].value = str(data.get("measurement_unit") or "")
        input_fields["Valuation Date"].value = str(data.get("valuation_date") or "")
        input_fields["Market Value"].value = str(data.get("market_value") or "0.00")
        input_fields["FSV"].value = str(data.get("fsv") or "0.00")
        input_fields["Discounting Factor"].value = discounting_factor_value
        input_fields["Present Value (PV)"].value = str(data.get("lgd") or "0.0000")
        input_fields["Quality of Collateral"].value = str(data.get("collateral_quality") or "")

        calculate_fsv()
        page.update()

    def clear_form_fields():
        for k, tf in input_fields.items():
            if k == "FSV":
                tf.value = "0.00"
            elif k == "Discounting Factor":
                tf.value = discounting_factor_value
            elif k == "Average Haicut %":
                tf.value = "0.0000"
            elif k == "Average Liquidation Time (Yr.)":
                tf.value = "0.00"
            elif k == "Present Value (PV)":
                tf.value = "0.0000"
            else:
                tf.value = ""
        page.update()

    # Search Bar Field
    grid_search_tf = ft.TextField(
        hint_text="Cust No.",
        hint_style=ft.TextStyle(color="white38", size=13),
        width=130, height=40,
        content_padding=ft.Padding(12, 8, 12, 8),
        border_color="#00e676", focused_border_color="#00e676", border_radius=6,
        text_style=ft.TextStyle(color="white", size=13, weight="bold")
    )

    history_table_holder = ft.Container(expand=True)

    def get_table_control(search_query=""):
        # Iterate over all stored dictionary records instead of dict keys
        records = list(full_db_cache.values())

        if search_query.strip():
            records = [
                r for r in records 
                if search_query.strip().lower() in str(r.get("customer_number", "")).lower()
            ]

        if not records:
            return ft.Container(content=ft.Text("No records found.", color="white54", italic=True, size=13), padding=15)

        rows = []
        for c_data in records:
            rec_id = str(c_data.get("id") or "")
            cust_no = str(c_data.get("customer_number") or "")

            edit_btn = ft.IconButton(
                icon=ft.Icons.EDIT, icon_color="#00e676", icon_size=18, tooltip="Edit",
                on_click=lambda e, r_id=rec_id: populate_fields_by_id(r_id)
            )
            del_btn = ft.IconButton(
                icon=ft.Icons.DELETE, icon_color="#ff5252", icon_size=18, tooltip="Delete",
                on_click=lambda e, r_id=rec_id: execute_delete(r_id)
            )

            action_cell = ft.Row([edit_btn, del_btn], spacing=0, alignment="center")

            data_cells = [
                ft.DataCell(ft.Text(cust_no, weight="bold", color="#00e676", size=11)),
                ft.DataCell(ft.Text(str(c_data.get("customer_name", "")), color="white", size=11)),
                ft.DataCell(ft.Text(str(c_data.get("security_type", "")), color="white", size=11)),
                ft.DataCell(ft.Text(str(c_data.get("market_value", "")), color="white", size=11)),
                ft.DataCell(ft.Text(str(c_data.get("fsv", "0.00")), color="white", weight="bold", size=11)),
                ft.DataCell(ft.Text(discounting_factor_value, color="white", weight="bold", size=11)),
                ft.DataCell(ft.Text(str(c_data.get("lgd", "0.0000")), color="white", weight="bold", size=11)),
                ft.DataCell(ft.Text(str(c_data.get("collateral_quality", "")), color="white", size=11)),
                ft.DataCell(action_cell)
            ]
            rows.append(ft.DataRow(cells=data_cells))

        return ft.DataTable(
            width=800,
            columns=[
                ft.DataColumn(ft.Text("Cust No", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Name", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Coll. Type", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Market Value", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Forced Sale Value (FSV)", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Discounting Factor", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Present Value (PV)", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Quality", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Actions", color="white", weight="bold", size=11)),
            ],
            rows=rows, border=ft.Border.all(0.5, "#1e534b"),
            heading_row_color="#0c3832", heading_row_height=36, data_row_min_height=34, column_spacing=12
        )

    def render_history_table(search_query=""):
        history_table_holder.content = get_table_control(search_query)

    grid_search_tf.on_change = lambda e: (render_history_table(grid_search_tf.value or ""), history_table_holder.update())

    search_header_row = ft.Row([
        ft.Text("Search by Cust No :", size=15, weight="bold", color="#00e676"),
        grid_search_tf
    ], vertical_alignment="center", spacing=12)

    history_section_container = ft.Container(
        content=ft.Column([
            search_header_row,
            ft.Container(height=10),
            ft.Row([history_table_holder], scroll=ft.ScrollMode.AUTO, expand=True)
        ], horizontal_alignment="stretch"),
        padding=15, border=ft.Border.all(width=1, color="#00e676"), border_radius=8, bgcolor="#061d19"
    )

    def refresh_cache():
        nonlocal full_db_cache
        fetched = get_all_collateral_profiles() or []
        full_db_cache = process_raw_collateral_cache(fetched)

    def on_save_click(e):
        cust_num = input_fields["Customer Number"].value.strip() if input_fields["Customer Number"].value else ""
        if not cust_num:
            page.overlay.append(ft.SnackBar(ft.Text("Please enter a valid Customer Number first!"), bgcolor="#ff9800", open=True))
            page.update()
            return

        exists_corp = is_customer_exists_in_table(cust_num, "corporate_profiles")
        exists_ind = is_customer_exists_in_table(cust_num, "individual_profiles")

        if not (exists_corp or exists_ind):
            page.overlay.append(ft.SnackBar(
                ft.Text(f"Customer Number '{cust_num}' does not exist in Corporate or Individual profiles!"),
                bgcolor="#ff9800", open=True
            ))
            page.update()
            return

        calculate_fsv()
        if not present_value_is_valid:
            page.overlay.append(ft.SnackBar(
                content=ft.Text("Discounting Factor must be greater than -100% to calculate Present Value."),
                bgcolor="#ff9800",
                open=True
            ))
            page.update()
            return

        payload = {
            "customer_number": cust_num,
            "customer_name": input_fields["Customer Name"].value.strip() if input_fields["Customer Name"].value else "",
            "security_type": input_fields["Collateral Type"].value or "",
            "quantity": parse_flt(input_fields["Quantity of Security"].value),
            "measurement_unit": input_fields["Measurement Unit"].value or "",
            "valuation_date": input_fields["Valuation Date"].value or "",
            "market_value": parse_flt(input_fields["Market Value"].value),
            "fsv": parse_flt(input_fields["FSV"].value),
            "lgd": parse_flt(input_fields["Present Value (PV)"].value),
            "collateral_quality": input_fields["Quality of Collateral"].value or ""
        }

        try:
            save_collateral_profile(payload)
            refresh_cache()
            clear_form_fields()
            render_history_table(grid_search_tf.value or "")
            page.overlay.append(ft.SnackBar(ft.Text(f"Collateral Profile for {cust_num} saved successfully!"), bgcolor="#00e676", open=True))
        except Exception as err:
            page.overlay.append(ft.SnackBar(ft.Text(f"Error saving collateral profile: {str(err)}"), bgcolor="red", open=True))
        page.update()

    def execute_delete(record_id):
        if not record_id: return
        try:
            delete_collateral_profile_by_id(record_id)
            refresh_cache()
            clear_form_fields()
            render_history_table(grid_search_tf.value or "")
            page.overlay.append(ft.SnackBar(ft.Text(f"Collateral Profile record deleted successfully!"), bgcolor="#ff5252", open=True))
        except Exception as err:
            page.overlay.append(ft.SnackBar(ft.Text(f"Error deleting profile: {str(err)}"), bgcolor="red", open=True))
        page.update()

    add_btn = ft.ElevatedButton(
        content=ft.Text("Save Collateral Profile", color="black", weight="bold", size=14),
        on_click=on_save_click,
        style=ft.ButtonStyle(bgcolor="#78eb64", shape=ft.RoundedRectangleBorder(radius=20)),
        height=42, width=220
    )

    input_form_card = ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Text("Collateral Profile Entry", size=20, weight="bold", color="#00e676"),
                alignment=ft.Alignment(0, 0), padding=ft.Padding(0, 0, 0, 15)
            ),
            grid_column,
            ft.Container(height=20),
            ft.Row([add_btn], alignment="center")
        ]),
        padding=20, border=ft.Border.all(width=1, color="#00e676"), border_radius=8, bgcolor="#061d19"
    )

    main_layout = ft.Column(
        controls=[input_form_card, history_section_container],
        scroll=ft.ScrollMode.AUTO, spacing=15
    )

    render_history_table()

    return ft.Container(
        content=main_layout, width=820, alignment=ft.Alignment(0, -1), padding=ft.Padding(0, 0, 0, 20)
    )